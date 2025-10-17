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

## 🚀 How to Run the Project Locally

Follow these steps to set up and run the simulator on your machine.

### Prerequisites

* Python 3.8+
* `git` (optional, for cloning the repo)

### Step 1: Clone the Repository and Set Up Environment

```bash
# Clone the repository
git clone [https://github.com/YourUsername/flight-booking-simulator.git](https://github.com/YourUsername/flight-booking-simulator.git)
cd flight-booking-simulator

# Create and activate a virtual environment
python -m venv venv
# On macOS/Linux
source venv/bin/activate
# On Windows PowerShell
.\venv\Scripts\activate
