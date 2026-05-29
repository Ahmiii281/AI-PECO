
import json
import os
from typing import Dict, Any, List

class BillingService:
    def __init__(self):
        self.tariffs_path = os.path.join(os.path.dirname(__file__), "..", "data", "fesco_tariffs.json")
        self.tariffs = self._load_tariffs()

    def _load_tariffs(self) -> Dict[str, Any]:
        with open(self.tariffs_path, 'r') as f:
            return json.load(f)

    def calculate_bill(self, 
                       consumer_type: str, 
                       units: float, 
                       peak_units: float = 0, 
                       offpeak_units: float = 0, 
                       sanctioned_load: float = 1.0, 
                       phase: int = 1, 
                       is_protected: bool = False) -> Dict[str, Any]:
        """
        Calculates electricity bill based on FESCO tariff structure.
        """
        if consumer_type not in self.tariffs:
            raise ValueError(f"Unknown consumer type: {consumer_type}")

        tariff = self.tariffs[consumer_type]
        breakdown = []
        total_energy_charges = 0
        fixed_charges = 0
        min_charges = 0

        # Handle TOU (Time of Use) if applicable (> 5kW or commercial/industrial)
        use_tou = (sanctioned_load >= 5.0) or (consumer_type in ["A-2", "B"] and (peak_units > 0 or offpeak_units > 0))

        if use_tou and "tou" in tariff.get("sub_categories", tariff):
            tou_config = tariff.get("sub_categories", tariff).get("tou")
            peak_cost = peak_units * tou_config["peak_rate"]
            offpeak_cost = offpeak_units * tou_config["off_peak_rate"]
            total_energy_charges = peak_cost + offpeak_cost
            breakdown.append({"slab": "Peak", "units": peak_units, "rate": tou_config["peak_rate"], "cost": peak_cost})
            breakdown.append({"slab": "Off-Peak", "units": offpeak_units, "rate": tou_config["off_peak_rate"], "cost": offpeak_cost})
            
            # Fixed charges based on max(25% of load, MDI - assumed MDI is actual load here)
            mdi = sanctioned_load # Defaulting MDI to sanctioned load for estimation
            chargeable_load = max(0.25 * sanctioned_load, mdi)
            fixed_charges = chargeable_load * tou_config.get("fixed_charges_per_kw", 0)
        
        # Handle Residential (A-1) Slab Logic
        elif consumer_type == "A-1":
            cat = "protected" if is_protected else "unprotected"
            config = tariff["sub_categories"][cat]
            remaining_units = units
            
            for slab in config["slabs"]:
                if remaining_units <= 0:
                    break
                
                slab_min = slab["min"]
                slab_max = slab["max"]
                rate = slab["rate"]
                
                if slab_max is None:
                    # Last open-ended slab
                    units_in_slab = remaining_units
                else:
                    capacity = (slab_max - slab_min + 1)
                    units_in_slab = min(remaining_units, capacity)
                
                cost = units_in_slab * rate
                total_energy_charges += cost
                breakdown.append({
                    "slab": f"{slab_min}-{slab_max if slab_max else '+'}",
                    "units": units_in_slab,
                    "rate": rate,
                    "cost": round(cost, 2)
                })
                remaining_units -= units_in_slab
            
            fixed_charges = config.get("fixed_charges", 0)
            
            # Minimum charges check
            min_val = tariff["min_monthly_charges"]["single_phase"] if phase == 1 else tariff["min_monthly_charges"]["three_phase"]
            if total_energy_charges < min_val:
                min_charges = min_val - total_energy_charges
                breakdown.append({"slab": "Minimum Charges Adjustment", "units": 0, "rate": 0, "cost": round(min_charges, 2)})

        # General Fixed rate categories (Commercial A-2, etc. non-TOU)
        else:
            rate = tariff["slabs"][0]["rate"]
            total_energy_charges = units * rate
            breakdown.append({"slab": "Flat Rate", "units": units, "rate": rate, "cost": total_energy_charges})
            fixed_charges = tariff.get("fixed_charges", 0)

        total_bill = total_energy_charges + fixed_charges + min_charges
        
        # AI Optimization Suggestion
        optimization = self._generate_optimization(consumer_type, units, breakdown)

        return {
            "consumer_type": tariff["name"],
            "total_units": units,
            "energy_charges": round(total_energy_charges, 2),
            "fixed_charges": round(fixed_charges, 2),
            "total_bill": round(total_bill, 2),
            "breakdown": breakdown,
            "optimization_suggestion": optimization
        }

    def _generate_optimization(self, consumer_type: str, units: float, breakdown: List[Dict]) -> str:
        if consumer_type == "A-1" and units > 200:
            return "Your usage has entered higher cost slabs (>200 units). Reducing usage by just 20% could shift you to a lower-cost slab and save up to 30% on your bill."
        if any(b["slab"] == "Peak" and b["units"] > 50 for b in breakdown):
            return "High peak usage detected. Shifting heavy appliances (AC, iron, motor) to off-peak hours can significantly reduce your bill."
        return "Your energy consumption is within efficient limits. Keep it up!"

billing_service = BillingService()
