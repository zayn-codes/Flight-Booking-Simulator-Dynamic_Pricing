import streamlit as st
import requests
import pandas as pd
from typing import Optional

# --- Configuration ---
FASTAPI_URL = "https://flight-booking-simulator-dynamic-pricing.onrender.com"  # Change this to 'http://127.0.0.1:8000" when working locally

# --- Helper Functions for API Communication ---

def fetch_flights(endpoint: str, params: dict = None):
    """General function to fetch data from a GET endpoint."""
    try:
        url = f"{FASTAPI_URL}/{endpoint}"
        response = requests.get(url, params=params if params else {})
        response.raise_for_status() 
        
        if not response.text:
            st.error(f"Backend responded with status {response.status_code} but an empty body.")
            return None
        
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get('detail', 'Unknown error')
        except requests.exceptions.JSONDecodeError:
            error_detail = f"Server returned status {response.status_code} with non-JSON content."
            
        st.error(f"HTTP Error: {response.status_code} - {error_detail}")
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: Is the FastAPI server running at {FASTAPI_URL}? ({e})")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error(f"Error decoding JSON response from backend. Response: {response.text[:100]}...")
        return None 

def post_request(endpoint: str, data: dict):
    """General function to send data to a POST endpoint (login, register, booking)."""
    try:
        url = f"{FASTAPI_URL}/{endpoint}"
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_detail = response.json().get('detail', 'Unknown error')
        st.error(f"Operation Failed: {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None

def fetch_airports():
    """Fetches the list of all unique city/country names from the backend."""
    try:
        url = f"{FASTAPI_URL}/airports"
        response = requests.get(url)
        response.raise_for_status()
        airports = response.json().get("airports", [])
        airports.insert(0, "Select...")
        return airports
    except Exception as e:
        return ["Select..."]

# --- Streamlit Session Initialization ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'airports' not in st.session_state:
    st.session_state['airports'] = fetch_airports() 


# --- Streamlit Application Layout ---
st.set_page_config(page_title="Flight Booking Simulator", layout="wide")
st.title("✈️ Flight Booking Simulator")
st.caption("Includes Authentication, Dynamic Pricing, and Transactional Booking.")


# --- Authentication Sidebar ---
st.sidebar.header("User Authentication")

if st.session_state['logged_in']:
    st.sidebar.success(f"Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        if post_request("logout", {}):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.toast("Logged out successfully!")
            st.rerun()
else:
    auth_mode = st.sidebar.radio("Select Mode", ["Login", "Register"])
    
    with st.sidebar.form(key=auth_mode.lower() + "_form"):
        auth_username = st.text_input("Username")
        auth_password = st.text_input("Password", type="password")
        auth_submitted = st.form_submit_button(auth_mode)
        
        if auth_submitted:
            data = {"username": auth_username, "password": auth_password}
            
            if auth_mode == "Register":
                result = post_request("register", data)
                if result:
                    st.success(result['message'] + ". Please log in now.")
            
            elif auth_mode == "Login":
                result = post_request("login", data)
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = result['username']
                    st.success(result['message'])
                    st.rerun()

st.sidebar.header("Navigation")
app_mode = st.sidebar.radio("Go to", ["List All Flights", "Flight Search", "Make a Booking"])


# --- Helper for Displaying Flight Data ---
def display_flights_data(flights, header_text):
    if flights is None or not flights:
        st.info("No flights found matching your criteria.")
        return

    st.subheader(header_text)
    df = pd.DataFrame(flights)
    
    # Formatting and renaming columns for presentation
    df['final_price'] = df['final_price'].apply(lambda x: f"${x:,.2f}")
    df['base_price'] = df['base_price'].apply(lambda x: f"${x:,.2f}")
    
    # Renaming to display names, using the new city/country column keys
    df = df.rename(columns={
        'flight_number': 'Flight No.',
        'seats_remaining': 'Seats Left',
        'base_price': 'Base Fare',
        'from_city_country': 'Origin',      
        'to_city_country': 'Destination',    
        'airline': 'Airline'
    })
    
    display_cols = ['Flight No.', 'Airline', 'Origin', 'Destination', 'Seats Left','Base Fare']
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)


# --- 1. List All Flights Section ---
if app_mode == "List All Flights":
    st.header("All Available Flight Schedules")
    
    flights = fetch_flights("flights/all")
    display_flights_data(flights, f"Total Flights Found: {len(flights) if flights else 0}")


# --- 2. Flight Search Section (Autocomplete Simulation) ---
elif app_mode == "Flight Search":
    st.header("Search Flights (Autocomplete Simulation)")
    
    airports = st.session_state['airports']
    
    col1, col2, col3, col4 = st.columns([1, 1, 0.5, 0.5])
    
    with col1:
        # Text input for typing
        origin_input = st.text_input("Origin City (e.g., New York)", key="search_origin_input").upper()
        
        # Dynamic Selectbox based on input
        if origin_input and origin_input != "SELECT...":
            filtered_origins = [a for a in airports if a != "Select..." and origin_input in a.upper()]
            origin_selected = st.selectbox(
                "Select Origin:",
                options=["Select..."] + filtered_origins,
                key="origin_selected_box"
            )
        else:
            origin_selected = "Select..."
            st.empty() 

    with col2:
        # Text input for typing
        destination_input = st.text_input("Destination City (e.g., London)", key="search_dest_input").upper()
        
        # Dynamic Selectbox based on input
        if destination_input and destination_input != "SELECT...":
            filtered_destinations = [a for a in airports if a != "Select..." and destination_input in a.upper()]
            destination_selected = st.selectbox(
                "Select Destination:",
                options=["Select..."] + filtered_destinations,
                key="destination_selected_box"
            )
        else:
            destination_selected = "Select..."
            st.empty() 
            
    with col3:
        sort_by = st.selectbox("Sort By", ["price", "duration"], index=0)
    with col4:
        sort_order = st.selectbox("Order", ["asc", "desc"], index=0)

    # Determine which city name to use for the API call
    final_origin = origin_selected if origin_selected != "Select..." else None
    final_destination = destination_selected if destination_selected != "Select..." else None

    if st.button("Search Flights"):
        if not final_origin or not final_destination:
            st.warning("Please select valid Origin and Destination cities from the dropdowns.")
        else:
            params = {
                "origin": final_origin,
                "destination": final_destination,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
            flights = fetch_flights("flights", params) 
            display_flights_data(flights, f"Results: {final_origin} to {final_destination}")


# --- 3. Make a Booking Section ---
elif app_mode == "Make a Booking":
    st.header("New Flight Booking (Transactional)")
    
    if not st.session_state['logged_in']:
        st.warning("Please **log in** to make a booking.")
    else:
        st.info(f"Booking will be processed for user: **{st.session_state['username']}**")
        
        with st.form("booking_form"):
            st.subheader("Flight Details")
            booking_flight_number = st.text_input("Flight Number (e.g., FL107)", key="book_flight_no").upper()
            booking_date = st.date_input("Travel Date")
            seat_preference = st.selectbox("Seat Preference", ['Any', 'Window', 'Aisle'])

            st.subheader("Passenger Details")
            colA, colB = st.columns(2)
            with colA: first_name = st.text_input("First Name")
            with colB: last_name = st.text_input("Last Name")
            
            colC, colD = st.columns(2)
            with colC: age = st.number_input("Age", min_value=1, max_value=120, value=30)
            with colD: phone = st.text_input("Phone Number (e.g., 9876543210)")

            submitted = st.form_submit_button("Confirm Booking")

            if submitted:
                try:
                    phone_int = int(phone)
                    
                    booking_data = {
                        "flight_number": booking_flight_number,
                        "travel_date": str(booking_date),
                        "seat_preference": seat_preference,
                        "passenger": {
                            "first_name": first_name, "last_name": last_name,
                            "age": age, "phone": phone_int
                        }
                    }
                    
                    result = post_request("bookings", booking_data)
                    
                    if result:
                        pnr_to_download = result.get('pnr')
                        
                        st.success(f"✅ Booking Successful! PNR: {pnr_to_download}")
                        st.json(result)
                        st.balloons()
                        
                        # Markdown link for PDF download
                        if pnr_to_download:
                            st.markdown(
                                f"""
                                <a href="{FASTAPI_URL}/tickets/{pnr_to_download}" download="flight_ticket_{pnr_to_download}.pdf">
                                    <button style="
                                        background-color: #007bff; color: white; border: none; padding: 10px 20px; 
                                        text-align: center; text-decoration: none; display: inline-block; font-size: 16px; 
                                        margin: 4px 2px; cursor: pointer; border-radius: 8px;">
                                        Download Ticket PDF ⬇️
                                    </button>
                                </a>
                                """,
                                unsafe_allow_html=True
                            )
                except ValueError:

                    st.error("Please enter a valid number for Phone.")
