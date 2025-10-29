import streamlit as st
import requests
import pandas as pd
from typing import Optional
import time
import random
from datetime import date # Needed for date input

# --- Configuration ---
FASTAPI_URL = "http://127.0.0.1:8000"

# --- Helper Functions for API Communication ---

def api_request(endpoint: str, data: dict = None, method: str = 'POST'):
    """Generic function to send data to any API endpoint."""
    url = f"{FASTAPI_URL}/{endpoint}"

    try:
        if method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, json=data)
        elif method == 'GET':
            response = requests.get(url, params=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        if response.status_code == 204: # No Content
             return {"status": "success", "message": "Operation successful, no content returned."}
        if not response.text:
             return {"status": "warning", "message": "Empty response from server."}
        return response.json()

    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get('detail', 'Unknown error')
        except requests.exceptions.JSONDecodeError:
            error_detail = f"Server returned status {response.status_code} with non-JSON content: {response.text[:100]}..."
        st.error(f"Operation Failed ({method} {response.status_code}): {error_detail}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return None
    except requests.exceptions.JSONDecodeError:
        st.error(f"Error decoding JSON response from backend. Response: {response.text[:100]}...")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during API call: {e}")
        return None


def fetch_airports():
    """Fetches the list of all unique city/country names from the backend."""
    result = api_request("airports", method='GET')
    if result:
        airports = result.get("airports", [])
        airports.insert(0, "Select...") # Keep "Select..." for dropdowns
        return airports
    return ["Select..."]

# --- HELPER: Handles setting state for redirection ---
def handle_booking_redirect(flight_id):
    """Sets the page and the flight ID for autofill via selection."""
    if flight_id: # Ensure we have a valid flight_id
        st.session_state['autofill_flight_id'] = flight_id
        st.session_state['page'] = 'Make a Booking'
        st.session_state['search_results'] = None # Clear search results after booking
        st.rerun()
    else:
        st.warning("Could not identify the selected flight. Please try again.")


def display_flights_data(flights, header_text, context_page):
    """Standard display function for search results."""
    if flights is None or not flights:
        st.info("No flights found matching your criteria.")
        return

    st.subheader(header_text)
    df = pd.DataFrame(flights)

    # Format currency and explicitly cast to string (object)
    df['Base Price'] = df['base_price'].apply(lambda x: f"${x:,.2f}").astype(str)

    # Renaming to display names
    df = df.rename(columns={
        'flight_number': 'Flight No.',
        'seats_remaining': 'Seats Left',
        'from_city_country': 'Origin',
        'to_city_country': 'Destination',
        'airline': 'Airline',
        'total_seats': 'Total Seats' # Keep original name for calculation
    })

    # Safely get max_seats, default to 1 if empty or error
    try:
        max_seats = int(df['Total Seats'].max()) if not df.empty else 1
    except:
        max_seats = 1

    display_cols = ['Flight No.', 'Airline', 'Origin', 'Destination', 'Seats Left', 'Base Price']

    # --- Standard DataFrame Rendering ---
    st.dataframe(
        df[display_cols],
        width='stretch', # Use recommended parameter
        hide_index=True,
        column_config={
             "Base Price": st.column_config.TextColumn(
                "Base Price",
                help="Base fare before adjustments",
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

    # --- Post-Table Selection Form (Only for Flight Search) ---
    if context_page == "Flight Search" and not df.empty:
        st.markdown("#### Select Flight for Booking")
        with st.form("flight_selection_form"):
            flight_options = ['-- Select ID --'] + df['Flight No.'].tolist()
            selected_flight = st.selectbox(
                "Choose Flight ID:",
                options=flight_options,
                key='flight_selector'
            )
            submit_book = st.form_submit_button("BOOK NOW")
            if submit_book:
                if selected_flight != '-- Select ID --':
                    handle_booking_redirect(selected_flight)
                else:
                    st.warning("Please select a valid Flight ID first.")


# --- Streamlit Session Initialization ---
st.set_page_config(layout="wide", page_title="SKYLINE RESERVATION SYSTEM")

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
if 'autofill_flight_id' not in st.session_state:
    st.session_state['autofill_flight_id'] = ''
if 'search_results' not in st.session_state:
    st.session_state['search_results'] = None
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- Custom CSS for Futuristic Theme ---
st.markdown("""
<style>
/* Dark background, high contrast, neon colors */
.main .block-container { padding-top: 1rem; padding-bottom: 5rem; padding-left: 2rem; padding-right: 2rem; }
body { background-color: #0A0A10; }
.stApp { background-color: #0A0A10; }
h1 { color: #00FFFF; text-shadow: 0 0 10px #00FFFF; font-family: 'Space Mono', monospace; text-align: center; margin-bottom: 0.5rem;}
h2, h3 { color: #FF00FF; }
/* Input boxes */
.stTextInput > div > div > input, .stDateInput > div > div > input { color: #FFFFFF; border: 1px solid #00FFFF; background-color: #1A1A22; }
/* Selectbox dropdowns */
.stSelectbox div[role="listbox"] { background-color: #1A1A22; border: 1px solid #FF00FF; }
/* Buttons */
.stButton>button {
    color: white;
    background-image: linear-gradient(90deg, #00FFFF 0%, #FF00FF 100%);
    border: none; border-radius: 8px; transition: transform 0.2s;
    padding: 10px 24px;
    font-size: 16px;
    display: block;
    margin: 10px auto;
}
.stButton>button:hover { transform: scale(1.05); }
/* Specific button styling for Home Button & Landing Page Login/Register */
button[kind="secondary"] {
    background-image: linear-gradient(90deg, #555 0%, #333 100%);
    font-size: 14px;
    padding: 5px 15px;
    margin: 5px 0;
    display: inline-block;
}
div[data-testid="stHorizontalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stButton"] > button[kind="secondary"] {
     background-image: linear-gradient(90deg, #444 0%, #222 100%);
     margin: 5px;
}

/* Streamlit's default info/success boxes */
[data-testid="stStatusWidget"] { border-left: 5px solid #00FFFF; }

/* Styling for Landing Page Search Form Container */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:has(div[data-testid="stForm"][key="landing_search_form"]) {
    background-color: rgba(26, 26, 34, 0.8);
    border-radius: 15px;
    padding: 25px;
    border: 1px solid #FF00FF;
    box-shadow: 0 0 15px #FF00FF;
    margin-bottom: 30px;
}

/* Style Popular Destination images */
.popular-dest img {
    border-radius: 10px;
    border: 2px solid #00FFFF;
    box-shadow: 0 0 8px #00FFFF;
    transition: transform 0.3s ease;
    width: 100%; /* Make image fill column width */
    height: 200px; /* Fixed height for consistency */
    object-fit: cover; /* Ensure image covers space */
}
.popular-dest img:hover {
    transform: scale(1.03);
}

/* Footer Styling */
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #1A1A22;
    color: #888;
    text-align: center;
    padding: 10px;
    font-size: 12px;
    border-top: 1px solid #FF00FF;
    z-index: 1000;
}

/* Adjust main content padding to prevent overlap with footer */
.main .block-container { padding-bottom: 5rem; }

/* Style for Offer Display */
.offer-box {
    background: linear-gradient(90deg, #1D1D1D 0%, #111 100%);
    color: #00FF00; /* Neon Green */
    border: 1px solid #00FF00;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    font-size: 20px;
    font-weight: bold;
    margin-top: 20px;
    margin-bottom: 20px;
    box-shadow: 0 0 15px #00FF00;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 10px #00FF00; }
    50% { box-shadow: 0 0 20px #00FF00; }
    100% { box-shadow: 0 0 10px #00FF00; }
}

/* Styling for "Why Book With Us" and Testimonials */
.feature-box, .testimonial-box {
    background-color: #1A1A22;
    padding: 0px;
    border-radius: 10px;
    border: 1px solid #555;
    height: 100%; /* Ensure columns are equal height */
}
.testimonial-box blockquote {
    font-style: italic;
    color: #ccc;
    border-left: 3px solid #FF00FF;
    padding-left: 10px;
}

/* NEW: Chatbot Popover Style (Placed at bottom right) */
/* Target the specific element that holds the popover content */
div[data-testid="stPopover"] div[data-testid="stVerticalBlock"] {
    position: fixed !important;
    bottom: 60px; /* Above the footer */
    right: 20px;
    z-index: 999;
    max-width: 350px;
    min-width: 300px;
    background-color: #1A1A22;
    border: 1px solid #00FFFF;
    border-radius: 15px;
    box-shadow: 0 0 20px #00FFFF;
}
/* Ensure chat history scrolls correctly */
div[data-testid="stChatMessageContainer"] {
    max-height: 250px; /* Limit history height */
    overflow-y: auto;
    display: flex;
    flex-direction: column-reverse; /* Display newest messages at bottom */
}
/* Ensure the popover button stays at the bottom */
div[data-testid="stPopover"] button {
    margin-bottom: 0px !important;
}


</style>
""", unsafe_allow_html=True)


# --- 1. Landing Page Module (REVAMPED) ---
def render_landing_page():
    
    # FIX: Center Banner Image & Use use_container_width=True
    img_col1, img_col2, img_col3 = st.columns([1, 3, 1])
    with img_col2:
        st.image(
            "flights.jpg",
            use_container_width=True
        )

    st.title("SKYLINE RESERVATION SYSTEM 🚀")
    st.subheader("Book Your Next Journey Through the Stars (Simulator)")
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Login/Register Buttons ---
    col_login, col_register = st.columns(2)
    with col_login:
        if st.button("Login / Access Account", key="landing_login_btn", type="secondary", use_container_width=True):
             st.session_state['page'] = 'List All Flights' # Go to main app
             st.rerun()
    with col_register:
        if st.button("Register New User", key="landing_register_btn", type="secondary", use_container_width=True):
             st.session_state['page'] = 'List All Flights' # Go to main app
             st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Prominent Search Form ---
    airports_list = st.session_state.get('airports', ["Select..."])

    with st.form("landing_search_form"):
        st.markdown("#### **Find Your Flight**")
        col1, col2 = st.columns(2)
        with col1:
            origin_selected = st.selectbox("Leaving From:", options=airports_list, key="landing_origin")
        with col2:
            destination_selected = st.selectbox("Going To:", options=airports_list, key="landing_destination")

        col_dep, col_ret = st.columns(2)
        with col_dep:
            departure_date = st.date_input("Departure Date", value=date.today())
        with col_ret:
             return_date = st.date_input("Return Date (Optional)", value=None)

        submitted_landing_search = st.form_submit_button("SEARCH FLIGHTS 🚀")

        if submitted_landing_search:
            if origin_selected == "Select..." or destination_selected == "Select...":
                st.warning("Please select both Origin and Destination.")
            else:
                params = { "origin": origin_selected, "destination": destination_selected, "sort_by": "price", "sort_order": "asc" }
                flights = api_request("flights", params, method='GET')
                if flights:
                    st.session_state['search_results'] = flights
                    st.session_state['page'] = 'Flight Search'
                    st.rerun()
                else:
                    pass # Error handled by api_request

    # --- Dynamic Offer Display ---
    st.markdown("---")
    st.header("⚡ Today's Flash Deals ⚡")
    offer_placeholder = st.empty() 

    offers = [
        "🚀 15% OFF flights to Tokyo! Book now!",
        "✨ Special Weekend Getaway: London from $450!",
        "🌴 Fly to Dubai - Exclusive fares starting $999!",
        "⏳ Limited Time: $50 OFF any flight booked today!",
        "🌌 Explore Paris: Round trips under $600!",
        "🎉 BONUS: Book 2 tickets, get complimentary seat selection!",
    ]
    current_offer = random.choice(offers)
    # Apply styling using the CSS class
    offer_placeholder.markdown(f"<div class='offer-box'>{current_offer}</div>", unsafe_allow_html=True)
    st.markdown("---")


    # --- Popular Destinations Section (UPDATED IMAGES) ---
    st.header("✨ Explore Popular Destinations ✨")
    dest_col1, dest_col2, dest_col3 = st.columns(3)
    popular_dests = {
        "Tokyo, Japan": "https://images.unsplash.com/photo-1710766320687-e1a169467c12?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1160",
        "Paris, France": "https://images.unsplash.com/photo-1663040552262-33b1c804089c?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1160",
        "New York, USA": "https://images.unsplash.com/photo-1701188377824-98a69d8dcdf5?ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&q=80&w=1160"
    }
    cols = [dest_col1, dest_col2, dest_col3]
    i = 0
    for city, img_url in popular_dests.items():
        with cols[i % 3]:
            st.markdown(f"<div class='popular-dest'>", unsafe_allow_html=True)
            # Use container_width to fill column, CSS handles fixed height
            st.image(img_url, caption=city, use_container_width=True) 
            st.markdown("</div>", unsafe_allow_html=True)
        i += 1
    st.markdown("---")

    # --- "Why Book With Us?" Section ---
    st.header("Why Book With Us?")
    why_col1, why_col2, why_col3 = st.columns(3)
    with why_col1:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.subheader("🛰️ Real-Time Pricing")
        st.write("Our dynamic pricing engine constantly updates fares based on seat availability and simulated demand. No surprises, just the real price.")
        st.markdown("</div>", unsafe_allow_html=True)
    with why_col2:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.subheader("🔒 Guaranteed Bookings")
        st.write("We use atomic transactions. When you book a seat, it's 100% yours. No overselling, no "
                 "'last-second' errors.")
        st.markdown("</div>", unsafe_allow_html=True)
    with why_col3:
        st.markdown("<div class='feature-box'>", unsafe_allow_html=True)
        st.subheader("⚡ Instant Confirmation")
        st.write("Receive your PNR and downloadable PDF ticket the moment your payment is confirmed. No waiting, just action.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    # --- "Testimonials" Section ---
    st.header("What Our Travelers Say")
    test_col1, test_col2, test_col3 = st.columns(3)
    with test_col1:
        st.markdown("<div class='testimonial-box'>", unsafe_allow_html=True)
        st.write("The dynamic pricing was fascinating! I watched the price shift just before I booked. Felt like a real stock market for flights.")
        st.caption("- Data Scientist")
        st.markdown("</div>", unsafe_allow_html=True)
    with test_col2:
        st.markdown("<div class='testimonial-box'>", unsafe_allow_html=True)
        st.write("Smooth from start to finish. The search was fast, the payment was instant, and the PDF ticket was clean. A-plus simulation.")
        st.caption("- QA Tester")
        st.markdown("</div>", unsafe_allow_html=True)
    with test_col3:
        st.markdown("<div class='testimonial-box'>", unsafe_allow_html=True)
        st.write("I tried to break the booking system by opening two windows to book the last seat. It correctly failed one. Impressive transactional safety.")
        st.caption("- Backend Developer")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")


    # --- Info and Metrics Section at the Bottom ---
    st.header("🚀 System Intelligence & Performance")
    col_info, col_metrics = st.columns([2, 1])
    with col_info:
        st.markdown("### What makes our system smart?")
        st.markdown( """
            * **Dynamic Pricing:** Ticket prices change automatically based on how many seats are left and how high the current demand is. You always see the up-to-the-minute fare.
            * **Guaranteed Bookings:** Our system uses advanced **transactional logic** to ensure that when you book a seat, it's immediately confirmed and the flight inventory is updated, preventing any overselling errors.
            * **Easy Search:** Just start typing your city, and the system finds the destination instantly.

            **Ready to explore routes?** Use the sidebar to log in and access the flight search terminal.
            """ )
    with col_metrics:
        st.markdown("#### Real-Time System Stats")
        st.metric(label="Total Flights Available", value=200, delta="New routes weekly")
        price_change = random.randint(-5, 5)
        st.metric(label="Real-Time Price Index", value=f"{random.uniform(0.9, 1.1):.3f}", delta=f"{price_change}% cycle change", delta_color="normal" if price_change >= 0 else "inverse")
        st.metric(label="Seats Reserved Today", value=f"{random.randint(500, 1500)}+", delta="High Volume")
    st.markdown("---")

    # --- Footer ---
    st.markdown('<div class="footer">Designed and Developed by Md Ali.</div>', unsafe_allow_html=True)


# --- 2. Main Application UI and Sidebar Logic ---
def render_main_app():

    # --- Home Button Logic ---
    col_home, _, _ = st.columns([1, 4, 1])
    with col_home:
        if st.session_state.get('page') != 'Landing':
            if st.button("🏠 Home", key="home_button_main", type="secondary"):
                st.session_state['page'] = 'Landing'
                st.session_state['search_results'] = None
                st.session_state['pending_booking'] = None
                st.session_state['autofill_flight_id'] = ''
                st.rerun()

    st.sidebar.header("USER AUTH :: ACCESS KEY")
    if st.session_state.get('logged_in'):
        st.sidebar.success(f"ACCESS GRANTED: **{st.session_state.get('username')}** 🔑 (ID: {st.session_state.get('user_id')})")
        if st.sidebar.button("LOGOUT (Revoke Access)"):
            if api_request("logout", method='POST'):
                st.session_state.clear()
                st.session_state['page'] = 'Landing'
                st.rerun()
    else:
        auth_mode = st.sidebar.radio("AUTHENTICATION PROTOCOL", ["Login", "Register"])
        with st.sidebar.form(key=auth_mode.lower() + "_form"):
            auth_username = st.text_input("Username (UID)")
            auth_password = st.text_input("Password (KEY)", type="password")
            
            # --- NEW Registration Fields ---
            if auth_mode == "Register":
                st.markdown("##### New User Details")
                reg_full_name = st.text_input("Full Name")
                reg_phone = st.text_input("Phone Number")
                reg_country = st.text_input("Country")
            
            auth_submitted = st.form_submit_button(f"{auth_mode.upper()} :: CONFIRM")
            
            if auth_submitted:
                if auth_mode == "Register":
                    data = {
                        "username": auth_username, 
                        "password": auth_password,
                        "full_name": reg_full_name,
                        "phone": reg_phone,
                        "country": reg_country
                    }
                    result = api_request("register", data, method='POST')
                    if result: st.success("Registration complete. Please login.")
                
                elif auth_mode == "Login":
                    data = {"username": auth_username, "password": auth_password}
                    result = api_request("login", data, method='POST')
                    if result:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = result['username']
                        st.session_state['user_id'] = result['user_id']
                        st.success("Login successful. Data access enabled.")
                        st.rerun()

    st.sidebar.header("NAVIGATION :: TERMINAL ACCESS")

    prev_page = st.session_state.get('page', 'Landing')

    app_mode = st.sidebar.radio(
        "SELECT MODULE",
        ["List All Flights", "Flight Search", "Make a Booking", "Payment Gateway", "History/Cancel"],
        index=0 if st.session_state.get('page', 'Landing') == 'Landing' else ["List All Flights", "Flight Search", "Make a Booking", "Payment Gateway", "History/Cancel"].index(st.session_state.get('page', 'List All Flights'))
    )

    if prev_page == 'Flight Search' and app_mode != 'Flight Search':
        st.session_state['search_results'] = None

    if st.session_state.get('page') != app_mode:
        st.session_state['page'] = app_mode
        st.rerun()


    # --- NEW: AI Chatbot Popover (Bottom Right) ---
    st.sidebar.markdown("---")
    
    # We must use a popover since fixed position is unreliable in native Streamlit
    with st.sidebar:
        with st.popover("🤖 AI Trip Planner", use_container_width=True):
            st.markdown("##### Skyline AI Assistant")
            st.caption("Ask me to plan a trip! e.g., 'Plan a 5-day trip to Paris from New York.'")
            
            # Display chat history (reverse order for visual appeal)
            # Use a container to make the history scrollable
            history_container = st.container(height=350)
            
            with history_container:
                # Display messages in reverse order (newest at bottom)
                for message in reversed(st.session_state.messages):
                    with st.chat_message(message["role"]):
                        st.markdown(message["parts"])
            
            # Chat input at the bottom of the popover
            if prompt := st.chat_input("How can I help you plan?", key="chat_input_box"):
                # Add user message to history
                st.session_state.messages.append({"role": "user", "parts": prompt})
                
                # Prepare data for backend
                chat_data = {
                    # Send all history including the new user message
                    "history": st.session_state.messages,
                    "prompt": prompt
                }

                # Call the backend /chat endpoint
                # Immediately show user message before response comes in
                st.rerun() 
            
            # This block runs after rerun, handles the API call and update
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                last_prompt = st.session_state.messages[-1]["parts"]
                
                # Prepare data for backend
                chat_data = {
                    "history": st.session_state.messages[:-1], # Send history before the last prompt
                    "prompt": last_prompt
                }
                
                # Use a placeholder to show thinking message
                with st.spinner("Thinking..."):
                    response = api_request("chat", data=chat_data, method='POST')
                    
                    if response:
                        response_text = response.get("parts", "Sorry, I encountered an error.")
                        # Add model response to history and rerun
                        st.session_state.messages.append({"role": "model", "parts": response_text})
                    else:
                        st.session_state.messages.append({"role": "model", "parts": "AI service is currently unavailable."})
                    
                    st.rerun()

    # --- Main Content Sections ---

    current_page = st.session_state.get('page')

    if current_page == "List All Flights":
        st.header("ACCESSING ALL FLIGHT SCHEDULES (DATA STREAM)")
        st.markdown("---")
        
        # --- Domestic/International Tabbed View ---
        flights = api_request("flights/all", method='GET')
        
        if flights:
            # Filter flights in Python
            domestic_flights = [f for f in flights if ', India' in f.get('from_city_country', '') and ', India' in f.get('to_city_country', '')]
            international_flights = [f for f in flights if not (', India' in f.get('from_city_country', '') and ', India' in f.get('to_city_country', ''))]

            tab_dom, tab_intl = st.tabs(["🇮🇳 Domestic Flights", "🌍 International Flights"])
            
            with tab_dom:
                display_flights_data(domestic_flights, f"Total Domestic Flights: {len(domestic_flights)}", "List All Flights")
            
            with tab_intl:
                display_flights_data(international_flights, f"Total International Flights: {len(international_flights)}", "List All Flights")
        else:
            st.info("No flights available at the moment.")


    elif current_page == "Flight Search":
        st.header("FLIGHT SEARCH :: DYNAMIC FILTERING")
        st.markdown("---")
        airports = st.session_state.get('airports', ["Select..."])

        with st.form("search_form"):
            col1, col2 = st.columns(2)
            with col1:
                origin_selected = st.selectbox("SELECT ORIGIN TERMINAL:", options=airports, key="origin_selected_box")
            with col2:
                destination_selected = st.selectbox("SELECT DESTINATION TERMINAL:", options=airports, key="destination_selected_box")

            col_sort, col_order = st.columns(2)
            with col_sort:
                sort_by = st.selectbox("SORT CRITERIA", ["price", "duration"], index=0)
            with col_order:
                sort_order = st.selectbox("SORT DIRECTION", ["asc", "desc"], index=0)

            submitted_search = st.form_submit_button("EXECUTE SEARCH PROTOCOL")

            if submitted_search:
                if origin_selected == "Select..." or destination_selected == "Select...":
                    st.warning("Input incomplete. Select valid Origin and Destination cities.")
                    st.session_state['search_results'] = None
                else:
                    params = { "origin": origin_selected, "destination": destination_selected, "sort_by": sort_by, "sort_order": sort_order }
                    flights = api_request("flights", params, method='GET')
                    st.session_state['search_results'] = flights
                    st.rerun()

        # Display results if they exist in the session state
        if st.session_state.get('search_results'):
            results = st.session_state['search_results']
            display_flights_data(results, f"RESULTS FOUND: {len(results) if (results and isinstance(results, list)) else 0}", "Flight Search")

    elif current_page == "Make a Booking":
        st.header("RESERVATION MODULE :: SEAT HOLD")
        st.markdown("---")

        autofill_id = st.session_state.get('autofill_flight_id', '')
        initial_flight_id_value = autofill_id if autofill_id else ""
        if 'autofill_processed' not in st.session_state:
             st.session_state.autofill_processed = False

        if initial_flight_id_value and not st.session_state.autofill_processed:
             st.session_state['autofill_flight_id'] = ''
             st.session_state.autofill_processed = True


        if not st.session_state.get('logged_in'):
            st.warning("ACCESS DENIED: Please log in to enable booking transactions.")
        else:
            st.info(f"TRANSACTION INITIATED for user: **{st.session_state.get('username')}**")
            with st.form("booking_form", clear_on_submit=True):
                st.subheader("FLIGHT & PASSENGER INPUT")
                col_flight, col_date = st.columns(2)
                with col_flight:
                    booking_flight_number = st.text_input("Flight ID (e.g., FL107)", key="book_flight_no", value=initial_flight_id_value)
                with col_date:
                    booking_date = st.date_input("Travel Date")
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
                    st.session_state.autofill_processed = False # Reset flag on new submission
                    try:
                        phone_int = int(phone)
                        submitted_flight_number = st.session_state.book_flight_no.upper() # Read value via key
                        booking_data = {
                            "flight_number": submitted_flight_number, "travel_date": str(booking_date),
                            "seat_preference": seat_preference, "user_id": st.session_state.get('user_id'),
                            "passenger": {"first_name": first_name, "last_name": last_name, "age": age, "phone": phone_int}
                        }
                        result = api_request("bookings", booking_data, method='POST')
                        if result and result.get('status') == 'PENDING_PAYMENT':
                            st.session_state['pending_booking'] = result
                            st.session_state['page'] = 'Payment Gateway'
                            st.rerun()
                        elif result:
                            st.error(f"Error: {result.get('message', 'Unknown response')}")
                    except ValueError:
                        st.error("Input Error: Phone must be a valid number.")
                    except AttributeError:
                         st.error("Error retrieving form data. Please try again.")


    elif current_page == "Payment Gateway":
        st.header("TRANSACTION MODULE :: SECURE PAYMENT")
        st.markdown("---")
        pending = st.session_state.get('pending_booking')
        if not st.session_state.get('logged_in'):
            st.warning("Access denied. Please log in.")
        elif not pending:
            st.warning("No pending booking found. Please reserve a seat first.")
        else:
            st.subheader(f"Booking PNR: **{pending['pnr']}**")
            st.metric(label="Amount Due", value=f"${pending['price_due']:.2f}", delta="Seat reservation is temporary.")
            with st.form("payment_form"):
                st.markdown("#### Simulated Payment Details")
                st.caption("Using dummy card details for simulation.")
                card = st.text_input("Card Number", "1234567890123456")
                expiry = st.text_input("Expiry Date", "12/26")
                cvv = st.text_input("CVV", "123", type='password')
                pay_submitted = st.form_submit_button("PAY NOW AND CONFIRM SEAT")
                if pay_submitted:
                    if len(card) == 16:
                        st.toast("Processing payment...")
                        time.sleep(5)
                        pay_result = api_request(f"bookings/pay/{pending['pnr']}", method='POST')
                        if pay_result and pay_result.get('status') == 'CONFIRMED':
                            st.success(pay_result['message'])
                            st.session_state['pending_booking'] = None
                            st.session_state['page'] = 'History/Cancel'
                            st.rerun()
                        else:
                            st.error(pay_result.get('detail', "Payment failed.") if pay_result else "Payment failed: No response")
                    else:
                        st.error("Input Error: Please enter a valid card number.")

    elif current_page == "History/Cancel":
        st.header("BOOKING HISTORY & MANAGEMENT")
        st.markdown("---")
        if not st.session_state.get('logged_in'):
            st.warning("Please log in to view your history.")
            return
        user_id = st.session_state.get('user_id')
        confirmed_data = api_request(f"bookings/history/{user_id}", method='GET')
        cancelled_data = api_request(f"bookings/cancelled/{user_id}", method='GET')

        tab_confirmed, tab_cancelled = st.tabs(["✅ Confirmed Bookings", "❌ Cancellation History"])
        with tab_confirmed:
            if confirmed_data and confirmed_data.get('history'):
                history_df = pd.DataFrame(confirmed_data['history'])
                history_df['Price Paid'] = history_df['price_paid'].apply(lambda x: f"${x:,.2f}").astype(str)
                history_df = history_df.rename(columns={'pnr': 'PNR', 'booking_date': 'Date', 'flight_number': 'Flight', 'passenger_full_name': 'Passenger', 'from_city_country': 'Origin', 'to_city_country': 'Destination'})

                st.markdown("#### Transactions")
                cols_header = st.columns([1.5, 3, 1.5, 1.5, 1.5])
                cols_header[0].markdown("**PNR**")
                cols_header[1].markdown("**Route**")
                cols_header[2].markdown("**Date**")
                cols_header[3].markdown("**Price**")
                cols_header[4].markdown("**Actions**")
                st.markdown("---")

                for index, row in history_df.iterrows():
                    pnr = row['PNR'].strip()
                    cols = st.columns([1.5, 3, 1.5, 1.5, 1.5])
                    cols[0].code(pnr)
                    cols[1].write(f"{row.get('Origin', 'N/A')} → {row.get('Destination', 'N/A')} ({row.get('Flight', 'N/A')})")
                    cols[2].write(row['Date'].split(' ')[0])
                    cols[3].write(row['Price Paid'])
                    download_link = f'<a href="{FASTAPI_URL}/tickets/{pnr}" download="ticket_{pnr}.pdf" target="_blank"><button style="background-color: #FF00FF; color: white; border: none; padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer;">Ticket ⬇️</button></a>'
                    cols[4].markdown(download_link, unsafe_allow_html=True)
                st.markdown("---")
            else:
                st.info("No confirmed bookings found.")

        with tab_cancelled:
            if cancelled_data and cancelled_data.get('history'):
                cancel_df = pd.DataFrame(cancelled_data['history'])
                cancel_df['Original Price'] = cancel_df['price_paid'].apply(lambda x: f"${x:,.2f}").astype(str)
                cancel_df['Refund Amount'] = cancel_df['refund_amount'].apply(lambda x: f"${x:,.2f}").astype(str)
                cancel_df = cancel_df.rename(columns={'pnr': 'PNR', 'cancellation_date': 'Date Cancelled', 'passenger_full_name': 'Passenger', 'flight_number': 'Flight No.'})
                st.dataframe(cancel_df[['PNR', 'Flight No.', 'Passenger', 'Original Price', 'Refund Amount', 'Date Cancelled']], width='stretch', hide_index=True)
            else:
                st.info("No cancellation history found.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Manage Bookings")

        col1, col2 = st.columns(2)
        with col1:
             # Combined Download Form
             with st.form("download_form"):
                 st.markdown("##### Download Ticket")
                 pnr_to_download = st.text_input("Enter PNR to Download").upper()
                 submitted_download = st.form_submit_button("Download Ticket ⬇️")
                 if submitted_download and pnr_to_download:
                     # Use markdown link for download as it's more reliable
                     st.markdown(f'<a href="{FASTAPI_URL}/tickets/{pnr_to_download}" target="_blank">Click here if download doesn\'t start automatically for {pnr_to_download}</a>', unsafe_allow_html=True)

        with col2:
            # Cancellation Form
            with st.form("cancellation_form", clear_on_submit=True):
                 st.markdown("##### Cancel Booking")
                 pnr_to_cancel = st.text_input("Enter PNR to Cancel").upper()
                 submit_cancel = st.form_submit_button("Cancel & Refund")
                 if submit_cancel and pnr_to_cancel:
                     st.toast("Processing cancellation...")
                     cancel_result = api_request(f"bookings/{pnr_to_cancel}", method='DELETE')
                     if cancel_result and cancel_result.get('status') == 'REFUND_PROCESSED':
                         st.success(f"Canceled PNR {pnr_to_cancel}.")
                         st.metric("Refund Amount", f"${cancel_result['refund_amount']:.2f}", delta=f"from ${cancel_result['price_paid']:.2f}")
                         st.markdown(f'<a href="{FASTAPI_URL}/receipts/{pnr_to_cancel}" target="_blank">Download Cancellation Receipt</a>', unsafe_allow_html=True)
                         time.sleep(120); st.rerun()
                     else:
                        st.error(cancel_result.get('detail', "Cancellation failed.") if cancel_result else "Cancellation failed: No response")

    # --- Footer for Main App Pages ---
    if current_page != 'Landing':
        st.markdown('<div class="footer">Designed and Developed by Md Ali.</div>', unsafe_allow_html=True)


# --- Application Flow Control ---
if st.session_state.get('page', 'Landing') == 'Landing':
    render_landing_page()
else:
    render_main_app()