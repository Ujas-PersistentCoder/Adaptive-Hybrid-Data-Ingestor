# Adaptive Hybrid Ingestion System

An autonomous data pipeline that dynamically determines the optimal storage backend (SQL vs. NoSQL) based on real-time schema profiling.

## 🚀 Key Features

- **Dynamic Normalization**: Resolves naming ambiguities (e.g., `IP` vs `ip_address`) using fuzzy matching.
- **Autonomous Classification**: Uses a 1000-record learning buffer to establish type stability and frequency heuristics.
- **Schema Drift Detection**: Live monitoring that re-routes fields to MongoDB if data types become inconsistent.
- **Bi-Temporal Traceability**: Tracks both Client and Server timestamps for cross-database joins.

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI (Mock Stream API)
- **Logic**: Regex, Difflib, Custom Heuristics

## 🚦 Getting Started

1. Clone the repo.
2. To start afresh clear the registry json
3. Set the number of records in the main.py file
4. Run the automation script:
   ```bash
   python run_project.py
   ```
5. Monitor log.txt for real-time routing decisions.

---

app.py inspired from simulation_code.py from https://github.com/YogeshKMeena/Course_Resources/tree/main/CS432_Databases/Assignments/T2
