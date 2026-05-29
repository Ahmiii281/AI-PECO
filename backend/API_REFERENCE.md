## AI-PECO Backend API Reference

This reference summarizes the **actual FastAPI endpoints implemented in code**.  
Use this when wiring the React frontend, ESP32 firmware, or external API clients.

---

### Authentication (`routes/auth.py`)

- **POST** `/api/auth/register`  
  - **Body:** `name`, `email`, `password`  
  - **Returns:** Created user (id, name, email, role, energy_limit, created_at)  
  - **Auth:** Public

- **POST** `/api/auth/login`  
  - **Body:** `email`, `password`  
  - **Returns:** `{ access_token, token_type, user }` where `user` matches `UserResponse`  
  - **Auth:** Public

- **GET** `/api/auth/me`  
  - **Headers:** `Authorization: Bearer <access_token>`  
  - **Returns:** Current user profile  
  - **Auth:** Required

---

### Devices (`routes/devices.py`)

- **GET** `/api/devices`  
  - List devices for current user.  
  - **Auth:** Required

- **POST** `/api/devices`  
  - **Body:** `{ name, location, relay_pin }`  
  - **Returns:** Created device (id, name, location, status, is_relay_on, relay_pin, created_at)  
  - **Auth:** Required

- **GET** `/api/devices/{device_id}`  
  - Get one device (ownership is checked).  
  - **Auth:** Required

- **PUT** `/api/devices/{device_id}`  
  - **Body:** Partial update `{ name?, location?, relay_pin? }`  
  - **Auth:** Required

- **DELETE** `/api/devices/{device_id}`  
  - Delete device owned by current user.  
  - **Auth:** Required

---

### Energy & Alerts (`routes/energy.py`)

> These endpoints are used by **ESP32** and the analytics layer.

- **POST** `/api/energy/data`  
  - **Body (`EnergyDataCreate`):**  
    - `device_id: str`  
    - `current: float` (amps – can be simulated)  
    - `voltage: float` (e.g. 220)  
    - `power: float` (watts)  
    - `temperature: float` (°C)  
    - `humidity: float` (%)  
  - **Headers (optional for ESP32 dev):** `X-API-Key`  
  - **Returns (`EnergyDataResponse`):** Saved reading + `is_anomaly` flag  
  - **Auth:** No JWT required (secured by API key in production)

- **GET** `/api/energy/device/{device_id}?hours=24`  
  - Get last _N_ hours of readings for one device.  
  - **Auth:** Required (JWT, verifies device ownership)

- **POST** `/api/energy/alerts`  
  - Manually create an alert.  
  - **Body:** `{ message, alert_type? = "warning" }`  
  - **Auth:** Required

- **GET** `/api/energy/alerts?resolved=false`  
  - List alerts for current user.  
  - **Auth:** Required

- **PUT** `/api/energy/alerts/{alert_id}`  
  - Mark alert as resolved.  
  - **Auth:** Required

Internally, `EnergyService` also supports anomaly detection and writes alerts when `ENABLE_AUTO_ALERTS` is enabled in settings.

---

### Dashboard & AI (`routes/dashboard.py`)

- **GET** `/api/dashboard/stats`  
  - Aggregated stats for the current user (last ~1 hour), from `EnergyService.get_dashboard_stats`:  
    - `total_power` (sum of power across user devices)  
    - `avg_temperature`  
    - `avg_humidity`  
    - `alert_count` (unresolved)  
    - `device_count`
  - **Auth:** Required

- **POST** `/api/dashboard/relay/{device_id}`  
  - Send relay command for a device (stored for ESP32 to poll).  
  - **Body (`RelayCommand`):** `{ device_id, command: "ON" | "OFF" }`  
  - **Auth:** Required, verifies device ownership

- **GET** `/api/dashboard/recommendation/{device_id}`  
  - Uses `EnergyModel` to analyze last 24h of readings and return:  
    - `message` (human text)  
    - `estimated_savings` (PKR/day)  
    - `device_name`, `current_daily_cost`, `all_readings_count`, `anomaly_count`, etc.  
  - **Auth:** Required, verifies device ownership

- **GET** `/api/dashboard/device-command/{device_id}`  
  - Polled by ESP32 to get the latest relay command and pin mapping.  
  - **Auth:** No JWT (device uses just `device_id`); ownership is enforced when commands are created.

---

### Recommendations (`EnergyModel` + future routes)

The main AI entrypoints are:

- `/api/dashboard/recommendation/{device_id}` – online AI recommendation per device  
- Automatic alerts when anomalies are detected after `POST /api/energy/data`

For detailed AI behavior and worked examples, see `AI_MODEL_EXAMPLES.md` in this folder.

