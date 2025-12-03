# 🩸 MediFlow - Blood Bank Management System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

**MediFlow** is a comprehensive, 3-tier web application designed to digitize and automate the operations of a blood bank. It streamlines the entire workflow from donor registration and health screening to blood collection, inventory management, and distribution to hospitals.

The system replaces manual record-keeping with a secure, centralized database, ensuring **data integrity**, **zero redundancy**, and **real-time tracking** of life-saving blood units.

---

## 🚀 Key Features

### 1. Donor Management
* **Registration:** Securely register new donors.
* **Search:** Instant donor lookup by last name.
* **Profiling:** Track donor details and history.

### 2. Intelligent Workflows
* **Automated Screening:** System automatically validates donor vitals (Hemoglobin, BP, Weight) against medical standards to determine eligibility.
* **Smart Transitions:** Automatically guides staff from a successful screening to the donation collection form, pre-filling IDs to prevent errors.

### 3. Inventory & Logistics
* **Collection:** Transaction-based recording of donations and blood unit creation.
* **Inventory Management:** Real-time status updates (In Stock, Issued, Reserved, Discarded).
* **Traceability:** Every blood unit is linked back to its specific donation and donor.

### 4. Organization Hub (New!)
* **Partner Management:** Register external entities (Hospitals, NGOs, Clinics).
* **Blood Requests:** Organizations can submit digital requests for blood stock.
* **Issuance:** Issue blood units directly to registered organizations for full audit trails.

### 5. Administration
* **Staff Management:** Manage employees, assign roles (Admin, Phlebotomist, Lab Tech), and delegate specific tasks.
* **Reporting:** Generate instant inventory reports grouped by blood type and status.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3 (Custom Modern UI), JavaScript (Fetch API for async operations).
* **Backend:** Python (Flask Framework), RESTful API Architecture.
* **Database:** MySQL (Relational Schema with strict Foreign Key constraints).

---

<img width="1468" height="925" alt="Screenshot 2025-12-03 110553" src="https://github.com/user-attachments/assets/607452da-8dcc-462d-9187-47b936a5b8e9" />
<img width="1447" height="843" alt="Screenshot 2025-12-03 110559" src="https://github.com/user-attachments/assets/29ffddfd-6f1a-48da-9e83-0527fb934928" />
<img width="1627" height="877" alt="Screenshot 2025-12-03 110402" src="https://github.com/user-attachments/assets/8e69cb9d-7e3c-439c-bd3e-c906c7129770" />
<img width="1553" height="873" alt="Screenshot 2025-12-03 110434" src="https://github.com/user-attachments/assets/7e572515-36ae-42dc-9923-ac5e4c95ad5a" />
<img width="1578" height="779" alt="Screenshot 2025-12-03 110528" src="https://github.com/user-attachments/assets/8b9d0766-fb85-45b9-b061-ae44e763c2dd" />
<img width="1518" height="857" alt="Screenshot 2025-12-03 110538" src="https://github.com/user-attachments/assets/0eff9a88-c850-4ded-bce3-ef2d51e0e326" />
<img width="1452" height="791" alt="Screenshot 2025-12-03 110545" src="https://github.com/user-attachments/assets/cdd7f1fa-5c65-4339-b662-3c490fac9be3" />


## 📂 Project Structure

```text
MediFlow/
│
├── app.py                   # Main Application Server (Flask)
├── database_setup.sql       # SQL script to create the empty database & tables
├── database_population.sql  # SQL script to populate tables with 10+ dummy records
├── templates/
│   └── index.html           # Complete Frontend (Single Page Application)
└── README.md                # Project Documentation
