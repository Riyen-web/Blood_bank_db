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
