import streamlit as st
import requests
import pandas as pd
from typing import Optional
import time
import random

# --- Configuration ---
FASTAPI_URL = "https://flight-booking-simulator-dynamic-pricing.onrender.com" #"http://127.0.0.1:8000" 

# --- Helper Functions for API Communication ---

def api_request(endpoint: str, data: dict = None, method: str = 'POST'):
    """Generic function to send data to any API endpoint."""
    url = f"{FASTAPI_URL}/{endpoint}"
    
    try:
        if method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'DELETE':
            # DELETE requests often use the URL for the resource ID
            response = requests.delete(url, json=data)
        elif method == 'GET':
            # GET requests use the 'data' dictionary as query parameters ('params')
            response = requests.get(url, params=data) 
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get('detail', 'Unknown error')
        except requests.exceptions.JSONDecodeError:
            error_detail = f"Server returned status {response.status_code} with non-JSON content."
        st.error(f"Operation Failed ({method} {response.status_code}): {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during API call: {e}")
        return None

def fetch_flights(endpoint: str, params: dict = None):
    return api_request(endpoint, data=params, method='GET')

def fetch_airports():
    result = api_request("airports", method='GET')
    if result:
        airports = result.get("airports", [])
        airports.insert(0, "Select...")
        return airports
    return ["Select..."]

def display_flights_data(flights, header_text):
    """Enhanced display function with custom table styling."""
    if flights is None or not flights:
        st.info("No flights found matching your criteria.")
        return

    st.subheader(header_text)
    df = pd.DataFrame(flights)
    
    # CRITICAL FIX 1: Format currency and explicitly cast to string (object)
    df['Base Price'] = df['base_price'].apply(lambda x: f"${x:,.2f}").astype(str)
    
    # Renaming to display names, using the new city/country column keys
    df = df.rename(columns={
        'flight_number': 'Flight No.',
        'seats_remaining': 'Seats Left',
        'from_city_country': 'Origin',      
        'to_city_country': 'Destination',    
        'airline': 'Airline',
        'total_seats': 'Total Seats'
    })
    
    max_seats = int(df['Total Seats'].max()) if not df.empty else 1

    display_cols = ['Flight No.', 'Airline', 'Origin', 'Destination', 'Seats Left', 'Base Price']
    
    st.dataframe(
        df[display_cols], 
        width='stretch', 
        hide_index=True,
        column_config={
            "Price (Dynamic)": st.column_config.TextColumn(
                "Price (Dynamic)", 
                help="Price adjusted based on demand and availability",
            ),
            "Seats Left": st.column_config.ProgressColumn(
                "Seats Left",
                help="Remaining capacity",
                format="%d",
                min_value=0,
                max_value=max_seats,
                width="small"
            )
        }
    )


# --- Streamlit Session Initialization ---

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 1 
if 'airports' not in st.session_state:
    st.session_state['airports'] = fetch_airports() 
if 'page' not in st.session_state:
    st.session_state['page'] = 'Landing'
if 'pending_booking' not in st.session_state:
    st.session_state['pending_booking'] = None


# --- Custom CSS for Futuristic Theme ---
st.markdown("""
<style>
/* Dark background, high contrast, neon colors */
.main { background-color: #0A0A10; }
h1 { color: #00FFFF; text-shadow: 0 0 10px #00FFFF; font-family: 'Space Mono', monospace; }
h2, h3 { color: #FF00FF; }
/* Input boxes */
.stTextInput > div > div > input { color: #FFFFFF; border: 1px solid #00FFFF; background-color: #1A1A22; }
/* Selectbox dropdowns */
.stSelectbox div[role="listbox"] { background-color: #1A1A22; border: 1px solid #FF00FF; }
/* Buttons */
.stButton>button {
    color: white;
    background-image: linear-gradient(90deg, #00FFFF 0%, #FF00FF 100%);
    border: none; border-radius: 8px; transition: transform 0.2s;
}
.stButton>button:hover { transform: scale(1.05); }
/* Streamlit's default info/success boxes */
[data-testid="stStatusWidget"] { border-left: 5px solid #00FFFF; }
</style>
""", unsafe_allow_html=True)


# --- 1. Landing Page Module ---
def render_landing_page():
    st.title("SKYLINE RESERVATION SYSTEM 🚀")
    st.subheader("Your Fast Track to Booking: Simple Search, Smart Prices, Guaranteed Seat.")
    st.markdown("---")

    col_stats, col_text = st.columns([1, 2])
    
    with col_stats:
        st.metric(label="Total Flights Available", value=200, delta="New routes added weekly")
        
        price_change = random.randint(-5, 5)
        st.metric(
            label="Real-Time Price Index", 
            value=f"{random.uniform(0.9, 1.1):.3f}", 
            delta=f"{price_change}% since last cycle",
            delta_color="normal" if price_change >= 0 else "inverse"
        )
        
        st.metric(label="Seats Reserved Today", value=f"{random.randint(500, 1500)}+", delta="High Volume")

    with col_text:
        st.markdown(
            """
            This platform is a **modern flight booking simulator** built using Python (FastAPI and Streamlit).
            
            ### What makes our system smart?
            
            1.  **Dynamic Pricing:** Ticket prices change automatically based on how many seats are left and how high the current demand is. You always see the up-to-the-minute fare.
            2.  **Guaranteed Bookings:** Our system uses advanced **transactional logic** to ensure that when you book a seat, it's immediately confirmed and the flight inventory is updated, preventing any overselling errors.
            3.  **Easy Search:** Just start typing your city, and the system finds the destination instantly.
            
            **Ready to explore routes?** Use the sidebar to log in and access the flight search terminal.
            """
        )
        if st.button("Start Your Flight Search"):
            st.session_state['page'] = 'List All Flights'
            st.rerun()

    st.image("https://images.unsplash.com/photo-1634981239781-b313c21d100e?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1935", caption="Digital Horizon", width='stretch')


# --- 2. Main Application UI and Sidebar Logic ---
def render_main_app():
    
    # --- Authentication Sidebar ---
    st.sidebar.header("USER AUTH :: ACCESS KEY")

    if st.session_state['logged_in']:
        st.sidebar.success(f"ACCESS GRANTED: **{st.session_state['username']}** 🔑 (ID: {st.session_state['user_id']})")
        if st.sidebar.button("LOGOUT (Revoke Access)"):
            if api_request("logout", method='POST'):
                st.session_state['logged_in'] = False
                st.session_state['username'] = None
                st.session_state['user_id'] = 1 
                st.session_state['pending_booking'] = None
                st.toast("Access revoked.")
                st.rerun()
    else:
        auth_mode = st.sidebar.radio("AUTHENTICATION PROTOCOL", ["Login", "Register"])
        
        with st.sidebar.form(key=auth_mode.lower() + "_form"):
            auth_username = st.text_input("Username (UID)")
            auth_password = st.text_input("Password (KEY)", type="password")
            auth_submitted = st.form_submit_button(f"{auth_mode.upper()} :: CONFIRM")
            
            if auth_submitted:
                data = {"username": auth_username, "password": auth_password}
                
                if auth_mode == "Register":
                    result = api_request("register", data, method='POST')
                    if result: st.success("Registration complete. Please login.")
                
                elif auth_mode == "Login":
                    result = api_request("login", data, method='POST')
                    if result:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = result['username']
                        st.session_state['user_id'] = result['user_id']
                        st.success("Login successful. Data access enabled.")
                        st.rerun()

    st.sidebar.header("NAVIGATION :: TERMINAL ACCESS")
    
    app_mode = st.sidebar.radio(
        "SELECT MODULE", 
        ["List All Flights", "Flight Search", "Make a Booking", "Payment Gateway", "History/Cancel"],
        index=0 if st.session_state['page'] == 'Landing' else ["List All Flights", "Flight Search", "Make a Booking", "Payment Gateway", "History/Cancel"].index(st.session_state['page'])
    )
    st.session_state['page'] = app_mode


    # --- Main Content Sections ---

    if st.session_state['page'] == "List All Flights":
        st.header("ACCESSING ALL FLIGHT SCHEDULES (DATA STREAM)")
        st.markdown("---")
        flights = api_request("flights/all", method='GET')
        display_flights_data(flights, f"Total Flights Found: {len(flights) if flights else 0}")


    elif st.session_state['page'] == "Flight Search":
        st.header("FLIGHT SEARCH :: DYNAMIC FILTERING")
        st.markdown("---")
        
        airports = st.session_state['airports']
        
        col1, col2 = st.columns(2)
        
        with col1:
            origin_input = st.text_input("ORIGIN CITY CODE INPUT", key="search_origin_input").upper()
            if origin_input and origin_input != "SELECT...":
                filtered_origins = [a for a in airports if a != "Select..." and origin_input in a.upper()]
                origin_selected = st.selectbox("SELECT ORIGIN TERMINAL:", options=["Select..."] + filtered_origins, key="origin_selected_box")
            else:
                origin_selected = "Select..."
                st.empty() 

        with col2:
            destination_input = st.text_input("DESTINATION CITY CODE INPUT", key="search_dest_input").upper()
            if destination_input and destination_input != "SELECT...":
                filtered_destinations = [a for a in airports if a != "Select..." and destination_input in a.upper()]
                destination_selected = st.selectbox("SELECT DESTINATION TERMINAL:", options=["Select..."] + filtered_destinations, key="destination_selected_box")
            else:
                destination_selected = "Select..."
                st.empty() 
                
        col_sort, col_order = st.columns(2)
        with col_sort:
            sort_by = st.selectbox("SORT CRITERIA", ["price", "duration"], index=0)
        with col_order:
            sort_order = st.selectbox("SORT DIRECTION", ["asc", "desc"], index=0)

        final_origin = origin_selected if origin_selected != "Select..." else None
        final_destination = destination_selected if destination_selected != "Select..." else None

        if st.button("EXECUTE SEARCH PROTOCOL"):
            if not final_origin or not final_destination:
                st.warning("Input incomplete. Select valid Origin and Destination cities.")
            else:
                params = {
                    "origin": final_origin,
                    "destination": final_destination,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                }
                flights = api_request("flights", params, method='GET') 
                display_flights_data(flights, f"RESULTS :: {final_origin} to {final_destination}")


    elif st.session_state['page'] == "Make a Booking":
        st.header("RESERVATION MODULE :: SEAT HOLD")
        st.markdown("---")
        
        if not st.session_state['logged_in']:
            st.warning("ACCESS DENIED: Please log in to enable booking transactions.")
        else:
            st.info(f"TRANSACTION INITIATED for user: **{st.session_state['username']}**")
            
            with st.form("booking_form", clear_on_submit=True):
                st.subheader("FLIGHT & PASSENGER INPUT")

                col_flight, col_date = st.columns(2)
                with col_flight:
                    booking_flight_number = st.text_input("Flight ID (e.g., FL107)", key="book_flight_no").upper()
                with col_date:
                    booking_date = st.date_input("Travel Date (Future Index)")
                seat_preference = st.selectbox("Seat Preference", ['Any', 'Window', 'Aisle'])

                st.markdown("#### Passenger Identity")
                colA, colB = st.columns(2)
                with colA: first_name = st.text_input("First Name")
                with colB: last_name = st.text_input("Last Name")
                
                colC, colD = st.columns(2)
                with colC: age = st.number_input("Age", min_value=1, max_value=120, value=30)
                with colD: phone = st.text_input("Phone Number (10 digits)")

                submitted = st.form_submit_button("RESERVE SEAT (PENDING PAYMENT)")

                if submitted:
                    try:
                        phone_int = int(phone)
                        
                        current_user_id = st.session_state['user_id'] # Get logged-in ID
                        
                        booking_data = {
                            "flight_number": booking_flight_number,
                            "travel_date": str(booking_date),
                            "seat_preference": seat_preference,
                            "user_id": current_user_id, # PASS LOGGED-IN ID TO BACKEND
                            "passenger": {
                                "first_name": first_name, "last_name": last_name,
                                "age": age, "phone": phone_int
                            }
                        }
                        
                        result = api_request("bookings", booking_data, method='POST')
                        
                        if result and result['status'] == 'PENDING_PAYMENT':
                            st.session_state['pending_booking'] = result 
                            st.success(f"Reservation created! PNR {result['pnr']} is PENDING PAYMENT.")
                            st.session_state['page'] = 'Payment Gateway' 
                            st.rerun()
                        elif result:
                            st.error(f"Error creating reservation: {result.get('message', 'Unknown response')}")
                    except ValueError:
                        st.error("Input Error: Phone must be a valid number.")


    elif st.session_state['page'] == "Payment Gateway":
        st.header("TRANSACTION MODULE :: SECURE PAYMENT")
        st.markdown("---")
        
        pending = st.session_state.get('pending_booking')

        if not st.session_state['logged_in']:
            st.warning("Access denied. Please log in.")
        elif not pending:
            st.warning("No pending booking found. Please reserve a seat first.")
        else:
            st.subheader(f"Booking PNR: **{pending['pnr']}**")
            st.metric(label="Amount Due", value=f"${pending['price_due']:.2f}", delta="Seat reservation is temporary.")

            with st.form("payment_form"):
                st.markdown("#### Simulated Payment Details")
                st.caption("Using dummy card details for simulation.")
                card = st.text_input("Card Number", max_chars=16, value="1234567890123456")
                expiry = st.text_input("Expiry Date", max_chars=5, value="12/26")
                cvv = st.text_input("CVV", type='password', max_chars=3, value="123")
                
                pay_submitted = st.form_submit_button("PAY NOW AND CONFIRM SEAT")

                if pay_submitted:
                    if len(card) == 16:
                        st.toast("Processing payment...")
                        time.sleep(1) 
                        
                        pay_result = api_request(f"bookings/pay/{pending['pnr']}", method='POST')

                        if pay_result and pay_result['status'] == 'CONFIRMED':
                            st.success(pay_result['message'])
                            st.session_state['pending_booking'] = None 
                            st.session_state['page'] = 'History/Cancel'
                            st.rerun()
                        else:
                            st.error(pay_result.get('detail', "Payment Confirmation Failed. Seat may have been sold out."))
                    else:
                        st.error("Input Error: Please enter a valid card number.")


    elif st.session_state['page'] == "History/Cancel":
        st.header("BOOKING HISTORY & MANAGEMENT")
        st.markdown("---")

        if not st.session_state['logged_in']:
            st.warning("Please log in to view your history.")
            return

        user_id = st.session_state['user_id']
        
        # Fetch Confirmed History
        confirmed_data = api_request(f"bookings/history/{user_id}", method='GET')
        
        # Fetch Cancellation History
        cancelled_data = api_request(f"bookings/cancelled/{user_id}", method='GET')
        
        # Check if either history exists
        if (confirmed_data and confirmed_data.get('history')) or (cancelled_data and cancelled_data.get('history')):
            
            # --- Display Confirmed Bookings ---
            if confirmed_data and confirmed_data.get('history'):
                history_df = pd.DataFrame(confirmed_data['history'])
                st.subheader("Confirmed Bookings Stream")
                
                # Apply type fix and formatting
                history_df['Price Paid'] = history_df['price_paid'].apply(lambda x: f"${x:,.2f}").astype(str)
                
                history_df = history_df.rename(columns={
                    'pnr': 'PNR', 'price_paid': 'Price Paid', 'booking_date': 'Booking Date',
                    'flight_number': 'Flight', 'from_city_country': 'Origin', 'to_city_country': 'Destination',
                    'airline': 'Airline', 'username': 'Booked By' 
                })
                
                # History Grid Display
                st.markdown("#### Transactions")
                cols_header = st.columns([2, 2.75, 1.5, 2.25, 1.5]) 
                cols_header[0].markdown("**PNR**")
                cols_header[1].markdown("**Route**")
                cols_header[2].markdown("**Date**")
                cols_header[3].markdown("**Price**")
                cols_header[4].markdown("**Actions**")
                st.markdown("---")

                for index, row in history_df.iterrows():
                    pnr = row['PNR'].strip() 
                    cols = st.columns([2, 2.75, 1.5, 2.25, 1.5]) 
                    
                    cols[0].code(pnr)
                    cols[1].write(f"{row['Origin']} → {row['Destination']} ({row['Flight']})")
                    cols[2].write(row['Booking Date'].split(' ')[0])
                    cols[3].write(row['Price Paid'])
                    
                    # Create the download button/link in the Actions column
                    download_link = f"""
                    <a href="{FASTAPI_URL}/tickets/{pnr}" download="ticket_{pnr}.pdf">
                        <button style="background-color: #FF00FF; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">
                            Ticket ⬇️
                        </button>
                    </a>
                    """
                    
                    cols[4].markdown(download_link, unsafe_allow_html=True)
                
                st.markdown("---")


            # --- Display Cancellation History ---
            if cancelled_data and cancelled_data.get('history'):
                cancel_df = pd.DataFrame(cancelled_data['history'])
                st.subheader("Archived Cancellation Records")
                
                # Apply type fix and formatting
                cancel_df['Original Price'] = cancel_df['price_paid'].apply(lambda x: f"${x:,.2f}").astype(str)
                cancel_df['Refund Amount'] = cancel_df['refund_amount'].apply(lambda x: f"${x:,.2f}").astype(str)
                
                cancel_df = cancel_df.rename(columns={
                    'pnr': 'PNR',
                    'cancellation_date': 'Date Cancelled',
                    'passenger_full_name': 'Passenger',
                    'flight_number': 'Flight No.',
                })

                st.dataframe(
                    cancel_df[['PNR', 'Flight No.', 'Passenger', 'Original Price', 'Refund Amount', 'Date Cancelled']],
                    hide_index=True,
                    width='stretch'
                )
            
            st.markdown("<br>", unsafe_allow_html=True)

            # --- Cancellation Module ---
            st.markdown("#### Cancellation Module")
            with st.form("cancellation_form", clear_on_submit=True):
                col_pnr, col_cancel = st.columns([2, 1])
                pnr_to_cancel = col_pnr.text_input("Enter PNR to Cancel", key="cancel_pnr_input").upper()
                
                submit_cancel = st.form_submit_button("Cancel & Refund")

                if submit_cancel:
                    if len(pnr_to_cancel) > 5:
                        st.toast("Processing cancellation and refund...")
                        
                        # CRITICAL FIX: Use method='DELETE'
                        cancel_result = api_request(f"bookings/{pnr_to_cancel}", method='DELETE')

                        if cancel_result: 
                            if cancel_result['status'] == 'REFUND_PROCESSED':
                                st.success(f"Canceled PNR {pnr_to_cancel}.")
                                st.metric("Refund Amount", f"${cancel_result['refund_amount']:.2f}", delta=f"Cancelled from ${cancel_result['price_paid']:.2f}")
                                st.info(cancel_result['note'])
                                
                                # Show receipt download link after successful cancellation
                                st.markdown(
                                    f"""
                                    <a href="{FASTAPI_URL}/receipts/{pnr_to_cancel}" download="cancellation_receipt_{pnr_to_cancel}.pdf">
                                        <button style="background-color: #7393B3; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-size: 16px;">
                                            Download Cancellation Receipt 📄
                                        </button>
                                    </a>
                                    """, unsafe_allow_html=True
                                )
                                
                                time.sleep(100)
                                st.rerun()
                            else:
                                st.error(cancel_result.get('detail', "Cancellation failed or PNR not found."))
                        # If post_request returned None, the error was displayed by the helper.
                    else:
                        st.error("Please enter a valid PNR.")
        else:
            st.info("No confirmed booking history found.")


# --- Application Flow Control ---
if st.session_state['page'] == 'Landing':
    render_landing_page()
else:

    render_main_app()
