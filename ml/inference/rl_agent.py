"""
AI-PECO: Reinforcement Learning Agent for Energy Optimization
================================================================
Tabular Q-Learning agent that learns optimal energy-saving actions
based on device states, usage patterns, time-of-day, and temperature.

The agent operates online -- it updates its Q-table every time new
sensor data arrives from the ESP32, so it continuously improves
its suggestions as it learns the user's specific patterns.

State space:
    (time_bucket, power_bucket, temp_bucket, devices_on_bucket)

Action space:
    0 = no_change
    1 = shift_load_offpeak
    2 = reduce_cooling_setpoint
    3 = turn_off_idle_devices
    4 = schedule_heavy_appliance
    5 = enable_power_saving_mode
"""

import os
import json
import random
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAVED_MODELS_DIR = os.path.join(_THIS_DIR, "saved_models")
RL_MODEL_PATH = os.path.join(SAVED_MODELS_DIR, "rl_qtable.json")

# ---------------------------------------------------------------------------
# Discretization buckets
# ---------------------------------------------------------------------------
TIME_BUCKETS = 6       # 4-hour blocks: 0-3, 4-7, 8-11, 12-15, 16-19, 20-23
POWER_BUCKETS = 5      # very_low, low, medium, high, very_high
TEMP_BUCKETS = 4       # cold (<15), mild (15-25), warm (25-35), hot (>35)
DEVICES_BUCKETS = 4    # 0, 1-2, 3-4, 5+

NUM_ACTIONS = 6

# Action definitions
ACTIONS = {
    0: {
        "action": "no_change",
        "title": "System Operating Normally",
        "description": "Your energy consumption is within efficient limits. No changes needed right now.",
        "estimated_savings_pkr": 0,
    },
    1: {
        "action": "shift_load_offpeak",
        "title": "Shift Load to Off-Peak Hours",
        "description": "Move heavy appliances (washing machine, iron, water heater) to off-peak hours (10 PM - 6 AM) to take advantage of lower tariff rates.",
        "estimated_savings_pkr": 1500,
    },
    2: {
        "action": "reduce_cooling_setpoint",
        "title": "Adjust Cooling Temperature",
        "description": "Set your AC thermostat 2 degrees higher (e.g., 24C to 26C). Each degree saves roughly 6-8% on cooling costs. Use ceiling fans to assist circulation.",
        "estimated_savings_pkr": 2200,
    },
    3: {
        "action": "turn_off_idle_devices",
        "title": "Turn Off Idle Devices",
        "description": "Multiple devices are drawing standby power. Unplug or switch off devices that are not actively in use to eliminate phantom load.",
        "estimated_savings_pkr": 800,
    },
    4: {
        "action": "schedule_heavy_appliance",
        "title": "Schedule Heavy Appliances",
        "description": "Run one heavy appliance at a time instead of simultaneously. Stagger usage of water heater, washing machine, and iron to avoid peak demand charges.",
        "estimated_savings_pkr": 1800,
    },
    5: {
        "action": "enable_power_saving_mode",
        "title": "Enable Power Saving Mode",
        "description": "Your current power draw is high relative to the time of day. Consider switching non-essential devices to power-saving mode or turning them off temporarily.",
        "estimated_savings_pkr": 1200,
    },
}


class EnergyRLAgent:
    """
    Tabular Q-learning agent for energy optimization.

    The Q-table is pre-seeded with domain-knowledge values so the
    agent gives sensible suggestions from the very first query,
    even before any training data has been collected.
    """

    def __init__(
        self,
        alpha: float = 0.1,       # learning rate
        gamma: float = 0.95,      # discount factor
        epsilon: float = 0.15,    # exploration rate
        model_path: str = RL_MODEL_PATH,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self._model_path = model_path

        # Total states = TIME_BUCKETS * POWER_BUCKETS * TEMP_BUCKETS * DEVICES_BUCKETS
        self.state_dims = (TIME_BUCKETS, POWER_BUCKETS, TEMP_BUCKETS, DEVICES_BUCKETS)
        total_states = 1
        for d in self.state_dims:
            total_states *= d

        self.q_table: Dict[str, List[float]] = {}

        self._last_state: Optional[str] = None
        self._last_action: Optional[int] = None
        self._episode_count = 0

        # Try loading from disk first
        if os.path.isfile(self._model_path):
            self._load_model()
            logger.info("RL agent loaded from %s (%d states)", self._model_path, len(self.q_table))
        else:
            self._preseed_qtable()
            self._save_model()
            logger.info("RL agent initialized with pre-seeded Q-table")

    # ------------------------------------------------------------------
    # State discretization
    # ------------------------------------------------------------------
    @staticmethod
    def discretize_state(
        hour: int,
        power_watts: float,
        temperature: float,
        devices_on: int,
    ) -> Tuple[int, int, int, int]:
        """Convert continuous values to discrete bucket indices."""

        # Time bucket (4-hour blocks)
        time_b = min(hour // 4, TIME_BUCKETS - 1)

        # Power bucket
        if power_watts < 100:
            power_b = 0
        elif power_watts < 500:
            power_b = 1
        elif power_watts < 1500:
            power_b = 2
        elif power_watts < 3000:
            power_b = 3
        else:
            power_b = 4

        # Temperature bucket
        if temperature < 15:
            temp_b = 0
        elif temperature < 25:
            temp_b = 1
        elif temperature < 35:
            temp_b = 2
        else:
            temp_b = 3

        # Devices bucket
        if devices_on == 0:
            dev_b = 0
        elif devices_on <= 2:
            dev_b = 1
        elif devices_on <= 4:
            dev_b = 2
        else:
            dev_b = 3

        return (time_b, power_b, temp_b, dev_b)

    @staticmethod
    def _state_key(state: Tuple[int, int, int, int]) -> str:
        return f"{state[0]}_{state[1]}_{state[2]}_{state[3]}"

    # ------------------------------------------------------------------
    # Q-table operations
    # ------------------------------------------------------------------
    def _get_q_values(self, state_key: str) -> List[float]:
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * NUM_ACTIONS
        return self.q_table[state_key]

    def choose_action(self, state: Tuple[int, int, int, int]) -> int:
        """Epsilon-greedy action selection."""
        state_key = self._state_key(state)
        q_values = self._get_q_values(state_key)

        if random.random() < self.epsilon:
            return random.randint(0, NUM_ACTIONS - 1)
        else:
            max_q = max(q_values)
            best_actions = [i for i, q in enumerate(q_values) if q == max_q]
            return random.choice(best_actions)

    def get_best_action(self, state: Tuple[int, int, int, int]) -> int:
        """Greedy action selection (no exploration)."""
        state_key = self._state_key(state)
        q_values = self._get_q_values(state_key)
        max_q = max(q_values)
        best_actions = [i for i, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def update(
        self,
        state: Tuple[int, int, int, int],
        action: int,
        reward: float,
        next_state: Tuple[int, int, int, int],
    ) -> None:
        """Q-learning update rule."""
        state_key = self._state_key(state)
        next_key = self._state_key(next_state)

        q_values = self._get_q_values(state_key)
        next_q_values = self._get_q_values(next_key)

        old_q = q_values[action]
        best_next_q = max(next_q_values)

        new_q = old_q + self.alpha * (reward + self.gamma * best_next_q - old_q)
        self.q_table[state_key][action] = new_q

        self._episode_count += 1

        # Periodically save
        if self._episode_count % 50 == 0:
            self._save_model()

    # ------------------------------------------------------------------
    # Reward calculation
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_reward(
        power_watts: float,
        energy_limit_watts: float = 3000.0,
        is_peak_hour: bool = False,
    ) -> float:
        """
        Calculate reward signal.

        Lower power = higher reward. Using power during peak hours
        gets an extra penalty. Staying under the user's energy limit
        gives a bonus.
        """
        # Base reward: negative cost proportional to power
        reward = -power_watts / 1000.0

        # Peak hour penalty
        if is_peak_hour:
            reward -= 0.5

        # Under-limit bonus
        if power_watts < energy_limit_watts:
            reward += 1.0

        # Very low consumption bonus
        if power_watts < 200:
            reward += 0.5

        return reward

    # ------------------------------------------------------------------
    # Get suggestion (public API)
    # ------------------------------------------------------------------
    def get_suggestion(
        self,
        hour: int,
        power_watts: float,
        temperature: float,
        devices_on: int,
    ) -> Dict[str, Any]:
        """
        Get the RL agent's recommendation for the current state.

        Returns a dict with action details, estimated savings, and
        confidence based on how many times this state has been visited.
        """
        state = self.discretize_state(hour, power_watts, temperature, devices_on)
        action_idx = self.get_best_action(state)
        action_info = ACTIONS[action_idx].copy()

        # Calculate confidence based on state visit frequency
        state_key = self._state_key(state)
        q_values = self._get_q_values(state_key)
        q_range = max(q_values) - min(q_values) if len(q_values) > 1 else 0
        confidence = "high" if q_range > 1.0 else ("medium" if q_range > 0.3 else "low")

        action_info["confidence"] = confidence
        action_info["state"] = {
            "time_bucket": state[0],
            "power_bucket": state[1],
            "temp_bucket": state[2],
            "devices_bucket": state[3],
        }
        action_info["source"] = "reinforcement_learning"
        action_info["episodes_trained"] = self._episode_count

        return action_info

    def online_update(
        self,
        hour: int,
        power_watts: float,
        temperature: float,
        devices_on: int,
        energy_limit_watts: float = 3000.0,
    ) -> None:
        """
        Perform one step of online learning when new sensor data arrives.

        This method is called from the energy data route each time
        the ESP32 sends a reading.
        """
        current_state = self.discretize_state(hour, power_watts, temperature, devices_on)
        is_peak = 8 <= hour <= 22
        reward = self.calculate_reward(power_watts, energy_limit_watts, is_peak)

        if self._last_state is not None and self._last_action is not None:
            self.update(self._last_state, self._last_action, reward, current_state)

        # Choose action for next step (exploration)
        action = self.choose_action(current_state)
        self._last_state = current_state
        self._last_action = action

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _save_model(self) -> None:
        os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
        data = {
            "q_table": self.q_table,
            "episode_count": self._episode_count,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
        }
        with open(self._model_path, "w") as f:
            json.dump(data, f)
        logger.debug("RL Q-table saved (%d states, %d episodes)", len(self.q_table), self._episode_count)

    def _load_model(self) -> None:
        with open(self._model_path, "r") as f:
            data = json.load(f)
        self.q_table = data.get("q_table", {})
        self._episode_count = data.get("episode_count", 0)
        self.alpha = data.get("alpha", self.alpha)
        self.gamma = data.get("gamma", self.gamma)
        self.epsilon = data.get("epsilon", self.epsilon)

    def _preseed_qtable(self) -> None:
        """
        Initialize Q-table with domain-knowledge values so the agent
        gives useful suggestions before it has learned from data.
        """
        for t in range(TIME_BUCKETS):
            for p in range(POWER_BUCKETS):
                for temp in range(TEMP_BUCKETS):
                    for d in range(DEVICES_BUCKETS):
                        key = f"{t}_{p}_{temp}_{d}"
                        q = [0.0] * NUM_ACTIONS

                        # No change is baseline
                        q[0] = 0.0

                        # Peak hours (buckets 2,3,4 = 8AM-8PM) -> shift load is good
                        if t in (2, 3, 4):
                            q[1] = 2.0  # shift_load_offpeak
                        else:
                            q[1] = 0.5

                        # Hot temperature -> reduce cooling setpoint helps
                        if temp >= 2:
                            q[2] = 2.5  # reduce_cooling_setpoint
                        elif temp == 1:
                            q[2] = 0.8

                        # Many devices on -> turn off idle
                        if d >= 2:
                            q[3] = 2.0  # turn_off_idle
                        elif d == 1:
                            q[3] = 0.5

                        # High power -> schedule heavy appliance
                        if p >= 3:
                            q[4] = 2.2  # schedule_heavy_appliance
                        elif p == 2:
                            q[4] = 1.0

                        # Very high power at any time -> power saving mode
                        if p >= 4:
                            q[5] = 2.8  # enable_power_saving_mode
                        elif p >= 3:
                            q[5] = 1.5

                        self.q_table[key] = q

        logger.info("Pre-seeded Q-table with %d states", len(self.q_table))


# ---------------------------------------------------------------------------
# Module-level singleton (lazy init)
# ---------------------------------------------------------------------------
_rl_agent_instance: Optional[EnergyRLAgent] = None


def get_rl_agent() -> EnergyRLAgent:
    """Get or create the global RL agent singleton."""
    global _rl_agent_instance
    if _rl_agent_instance is None:
        _rl_agent_instance = EnergyRLAgent()
    return _rl_agent_instance
