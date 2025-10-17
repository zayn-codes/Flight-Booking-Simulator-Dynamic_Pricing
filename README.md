# ✈️ Flight Booking Simulator (FastAPI + Streamlit + SQLite)

This project implements a full-stack flight reservation simulator, focusing on robust backend transactional logic, dynamic pricing algorithms, and concurrent seat management. It was developed to meet the requirements of a multi-week internship milestone project.

## ✨ Project Highlights

* **Milestone 1 (Database Foundation):** Implemented a clean SQL schema for flights, bookings, and users.
* **Milestone 2 (Dynamic API & Pricing Engine):** Built a REST API using FastAPI and integrated a real-time dynamic pricing model based on seat availability, demand simulation, and a time factor.
* **Milestone 3 (Transactional Workflow):** Developed a concurrency-safe booking endpoint using atomic database transactions (PNR generation, seat decrement) and implemented PDF ticket generation for confirmation.
* **Frontend:** A responsive Streamlit application for searching, booking, and user authentication, simulating a modern flight booking experience.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI** | High-performance, asynchronous web framework (Python). |
| **Database** | **SQLite** | Simple, file-based SQL database for local persistence. |
| **Frontend UI** | **Streamlit** | Fast application development framework for the web interface. |
| **Pricing/Tasks** | **APScheduler** | Handles the background job for simulating demand changes. |
| **PDF Generation** | **ReportLab** | Library used to structure and generate the e-ticket PDF. |

---

***

## 📋 Milestone Implementation Breakdown

This table details the fulfillment of all project requirements across the three milestones, providing a clear map of functionality within the codebase.

| Milestone/Module | Task/Requirement | Status | Implementation Details (File & Function) |
| :--- | :--- | :--- | :--- |
| **M1: Foundational Database** | Design & implement schema; Populate data (Flights, Users, Bookings). | Complete | **`db.sql`** defines the finalized schema (using City/Country names). Data is initialized via `initialize_db.py`. |
| **M2, T1-3: Search & Validation** | Retrieve all flights; Search by Origin/Destination; Input Validation & Sorting. | Complete | **`main.py`**: `/flights` and `/flights/all` endpoints handle retrieval and sorting. **`frontend.py`** uses Pydantic validation and typeahead search. |
| **M2, T4, 5: Dynamic Pricing** | Design logic (seats, time, demand) and integrate into search API. | Complete | **`main.py`**: `calculate_dynamic_price()` function integrates all factors and is applied to all flight results. |
| **M2, T6: Background Simulation** | Build background process to simulate demand/availability changes. | Complete | **`main.py`**: **APScheduler** runs the `update_demand_factor()` function every 5 minutes to simulate market shifts. |
| **M3: Transaction Management** | **Concurrency Control** (PNR/Seat safety). | Complete | **`main.py`**: The `POST /bookings` endpoint uses **SQLite database transactions** to ensure atomic decrement of `seats_remaining`. |
| **M3: Booking Confirmation** | Generate unique PNR; Simulated Payment/Confirmation. | Complete | **`main.py`**: PNR is generated on successful transaction. **ReportLab** generates the PDF ticket in the `/tickets/{pnr}` endpoint. |
| **M3: Cancellation/History** | Build booking cancellation endpoint. | Complete | **`main.py`**: **`DELETE /bookings/{pnr}`** restores the seat count and removes the booking record from the database. |

---## 🚀 How to Run the Project Locally

Follow these steps to set up and run the simulator on your machine.

### Prerequisites

* Python 3.8+
* `git` (optional, for cloning the repo)

### Step 1: Clone the Repository and Set Up Environment

```bash
# Clone the repository
git clone [[https://github.com/YourUsername/flight-booking-simulator.git](https://github.com/YourUsername/flight-booking-simulator.git)](https://github.com/zayn-codes/Flight-Booking-Simulator-Dynamic_Pricing-.git)
cd flight-booking-simulator

# Create and activate a virtual environment
python -m venv venv
# On macOS/Linux
source venv/bin/activate
# On Windows PowerShell
.\venv\Scripts\activate

Step 2: Install Dependencies
Install all required Python packages:

Bash

pip install -r requirements.txt
Step 3: Initialize the Database
The database file (db.sqlite) must be created and populated with the initial schema and 175 sample flights.

Bash

python initialize_db.py
Step 4: Start the FastAPI Backend (Server)
Open your first terminal window, ensure the venv is active, and start the FastAPI application. This server handles all data and logic.

Bash

# Terminal 1: Start the Backend
python -m uvicorn main:app --reload
(The backend will run at http://127.0.0.1:8000)

Step 5: Start the Streamlit Frontend (Client)
Open a second terminal window, ensure the venv is active, and start the Streamlit UI.

Bash

# Terminal 2: Start the Frontend
streamlit run frontend.py
(The UI will open automatically in your browser, typically at http://localhost:8501)
