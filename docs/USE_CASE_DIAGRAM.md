# AI-PECO: UML Use Case Diagram

The following diagram outlines the interactions between the primary actors (**User**, **Administrator**, **ESP32 Device**) and the **AI-PECO System**.

```mermaid
useCaseDiagram
    actor "User" as U
    actor "Administrator" as A
    actor "System" as S <<System>>
    actor "ESP32 Device" as E <<IoT>>

    package "AI-Powered Energy Consumption Optimizer (AI-PECO)" {
        usecase "Register/Login" as UC1
        usecase "View Dashboard" as UC2
        usecase "View Anomaly Alerts" as UC3
        usecase "View Energy Forecast" as UC4
        usecase "Receive Optimization Suggestions" as UC5
        usecase "Control Appliances" as UC6
        usecase "Issue Voice/Text Commands" as UC7
        usecase "Configure Preferences" as UC8
        usecase "View Energy Reports" as UC9
        usecase "Logout" as UC10

        usecase "Manage Devices" as UC11
        usecase "Configure NILM & ML Models" as UC12
        usecase "Monitor System Health & Logs" as UC13
        usecase "Update Policies & Parameters" as UC14
        usecase "Manage User Accounts" as UC15

        usecase "Run Prediction Model" as UC16
        usecase "Run AI Optimization" as UC17
        usecase "Update Relay State" as UC18

        usecase "Send Sensor Data" as UC19
        usecase "Send Relay Status" as UC20
        usecase "Receive Optimized Relay Commands" as UC21
    }

    %% User Associations
    U --> UC1
    U --> UC2
    U --> UC3
    U --> UC4
    U --> UC5
    U --> UC6
    U --> UC7
    U --> UC8
    U --> UC9
    U --> UC10

    %% Admin Associations
    A --> UC11
    A --> UC12
    A --> UC13
    A --> UC14
    A --> UC15

    %% System Associations (Internal/Automated)
    S --> UC16
    S --> UC17
    S --> UC18
    UC18 ..> UC21 : <<includes>>

    %% ESP32 Associations
    E --> UC19
    E --> UC20
    E <-- UC21

    %% Cross-Actor Associations
    UC6 -- UC18 : triggers
    UC19 -- UC16 : inputs
    UC17 -- UC5 : generates
```

### Key Components

- **User**: Primary beneficiary. Interacts with the dashboard to visualize energy data, receive AI-driven insights, and manually override device states.
- **Administrator**: Technical actor. Manages the underlying ML models (NILM/LSTM), monitors system health, and maintains user security policies.
- **System**: The automated core. Runs background processes for energy forecasting and optimization without direct human intervention.
- **ESP32 Device**: The hardware layer. Collects real-time environmental data (Temperature, Humidity, Load) and executes the relay commands received from the AI.
