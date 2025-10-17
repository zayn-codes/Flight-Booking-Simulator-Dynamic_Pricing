#!/bin/bash

# --- 1. Database Setup (Milestone 1) ---
echo "--- Initializing SQLite Database ---"
# Check if the DB exists. If not, run the initialization script.
if [ ! -f db.sqlite ]; then
    python initialize_db.py
else
    echo "Database db.sqlite already exists. Skipping initialization."
fi
echo "Database setup complete."

# --- 2. Start FastAPI Backend (MILESTONE 2/3 Server) ---
# Use the official Python module execution method for reliability.
# We run this in the background (&).
echo "--- Starting FastAPI Backend ---"
# Note: --host 0.0.0.0 is essential for cloud hosting environments
python -m uvicorn main:app --host 0.0.0.0 --port 8000 & 

# --- 3. Wait for FastAPI to Start (Optional but Recommended) ---
# Give the backend a few seconds to start up before the frontend tries to connect.
echo "Waiting for backend to launch on port 8000..."
sleep 5

# --- 4. Start Streamlit Frontend (Client) ---
# We launch Streamlit, and since this is the last command *not* run in the background, 
# it will become the main process monitored by the hosting platform.
echo "--- Starting Streamlit Frontend ---"
streamlit run frontend.py --server.port $PORT --server.enableCORS true --server.enableXsrfProtection false
