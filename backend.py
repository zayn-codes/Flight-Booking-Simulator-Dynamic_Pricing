import sqlite3
import uuid
import hashlib
import secrets
import random
import atexit
from datetime import datetime, timedelta
import os

# --- NEW: Imports for Gemini Chatbot ---
import google.generativeai as genai
from pydantic import BaseModel as PydanticBaseModel # Use alias to avoid conflict
from typing import List, Optional

# Imports for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

# --- Configuration ---
DATABASE_NAME = "db.sqlite"
app = FastAPI()

# --- Gemini API Configuration (CRITICAL for Chatbot Fix) ---
try:
    # CRITICAL: This attempts to load the key from the environment
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    print("Gemini API configured successfully.")
except KeyError:
    print("="*50)
    print("WARNING: GEMINI_API_KEY environment variable not set.")
    print("Chatbot functionality will be disabled.")
    print("="*50)
    gemini_model = None # Set model to None if key is missing

# --- Database Dependency/Connection Utility ---
def get_db_connection():
    """Returns a connection object to the SQLite database with row_factory set to sqlite3.Row."""
    # Note: connect_args={"check_same_thread": False} is needed for SQLite with FastAPI/APScheduler
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_db():
    """Provides a database connection and ensures it is closed after the request."""
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models for Data Validation and Schema ---

class UserAuth(BaseModel):
    """Schema for user registration and login credentials. UPDATED for registration."""
    username: str
    password: str 
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None

class Passenger(BaseModel):
    """Schema for passenger information."""
    first_name: str
    last_name: str
    age: int
    phone: int

class BookingRequest(BaseModel):
    """Schema for creating a new booking."""
    flight_number: str
    passenger: Passenger
    travel_date: str 
    seat_preference: Optional[str] = 'Any'
    user_id: int # User ID passed from frontend

class FlightDisplay(BaseModel):
    """Schema for displaying flight information, using city/country names."""
    id: int
    flight_number: str
    airline: str
    from_city_country: str
    to_city_country: str
    base_price: float
    total_seats: int
    seats_remaining: int
    final_price: float
    demand_factor: float

# --- NEW: Pydantic Model for Chatbot ---
class ChatMessage(PydanticBaseModel):
    role: str
    parts: str

class ChatRequest(PydanticBaseModel):
    history: List[ChatMessage]
    prompt: str

# --- Utilities and Dynamic Pricing Logic ---

def hash_password(password: str):
    """Simple SHA-256 hash for demonstration."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def calculate_dynamic_price(base_price: float, seats_remaining: int, total_seats: int, demand_factor: float) -> float:
    """Calculates the final ticket price based on seat availability, a time factor, and external demand."""
    remaining_percentage = seats_remaining / total_seats

    # 1. Seat Availability Factor
    if remaining_percentage > 0.75:
        seat_factor = -0.05
    elif remaining_percentage > 0.5:
        seat_factor = 0.0
    elif remaining_percentage > 0.25:
        seat_factor = 0.15
    else:
        seat_factor = 0.30

    # 2. Time Until Departure Factor (Simplified)
    time_factor = 0.05

    # 3. Final Calculation
    final_price = base_price * (1 + seat_factor + time_factor) * demand_factor

    return round(final_price, 2)

def generate_ticket_pdf(pnr: str, booking_details: dict) -> str:
    """
    Generates a PDF ticket structured like a boarding pass.
    """

    file_path = f"ticket_{pnr}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='BarcodeData', fontSize=14, fontName='Helvetica-Bold', alignment=1))

    story = []

    # --- Simulated Real-World Data ---
    simulated_seat = f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
    simulated_gate = f"G{random.randint(10, 50)}"
    simulated_time = (datetime.now() + timedelta(hours=2)).strftime("%I:%M %p")

    # --- 1. Header Section ---
    story.append(Paragraph("✈️ E-TICKET / BOARDING PASS", styles['Title']))
    story.append(Paragraph(f"Booking Reference (PNR): {pnr}", styles['h2']))
    story.append(Spacer(1, 0.2 * inch))

    # --- 2. Main Flight Details Table (Boarding Pass Layout) ---
    main_table_data = [
        [
            # Column 1: Passenger and Flight Number
            [
                Paragraph("PASSENGER NAME:", styles['h4']),
                Paragraph(f"{booking_details['passenger_name'].upper()}", styles['Heading2']),
                Spacer(1, 0.1 * inch),
                Paragraph("FLIGHT:", styles['h4']),
                Paragraph(f"{booking_details['flight_number']} ({booking_details['airline']})", styles['h3']),
            ],
            # Column 2: Route and Date
            [
                Paragraph("ROUTE:", styles['h4']),
                Paragraph(f"{booking_details['from_city_country']} -> {booking_details['to_city_country']}", styles['h3']),
                Spacer(1, 0.1 * inch),
                Paragraph("DATE:", styles['h4']),
                Paragraph(f"{booking_details['booking_date'].split(' ')[0]}", styles['h3']),
            ],
            # Column 3: Seat and Gate (Simulated)
            [
                Paragraph("GATE:", styles['h4']),
                Paragraph(f"{simulated_gate}", styles['Heading2']),
                Spacer(1, 0.1 * inch),
                Paragraph("SEAT:", styles['h4']),
                Paragraph(f"{simulated_seat}", styles['Heading2']),
            ]
        ]
    ]

    table_data_flat = [
        [main_table_data[0][0], main_table_data[0][1], main_table_data[0][2]]
    ]

    flight_table = Table(table_data_flat, colWidths=[2.5*inch, 3*inch, 1.5*inch])

    flight_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.9, 0.9, 1)),
    ]))

    story.append(flight_table)
    story.append(Spacer(1, 0.5 * inch))

    # --- 3. Barcode Simulation Section ---
    story.append(Paragraph("BOARDING TIME:", styles['h4']))
    story.append(Paragraph(f"{simulated_time}", styles['h1']))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("BARCODE DATA (Unique PNR):", styles['h4']))

    story.append(Paragraph(f"{pnr} - F{booking_details['flight_number']}", styles['BarcodeData']))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("PLEASE PRESENT THIS TICKET AND PHOTO ID AT THE GATE. THANK YOU FOR FLYING.", styles['Italic']))

    doc.build(story)

    return file_path

def generate_cancellation_receipt(pnr: str, details: dict) -> str:
    """Generates a PDF receipt for a cancelled booking."""

    file_path = f"receipt_{pnr}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("❌ CANCELLATION & REFUND RECEIPT", styles['Title']))
    story.append(Spacer(1, 0.3 * inch))

    # PNR and Date
    story.append(Paragraph(f"Booking PNR: {pnr}", styles['h3']))
    story.append(Paragraph(f"Cancellation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['h4']))
    story.append(Spacer(1, 0.5 * inch))

    # Refund Details Table
    table_data = [
        ["DESCRIPTION", "AMOUNT"],
        [f"Original Price Paid ({details['flight_number']})", f"${details['price_paid']:.2f}"],
        ["Cancellation Fee (20%)", f"${details['price_paid'] * 0.20:.2f}"],
        [f"Refund Amount ({details['note']})", f"${details['refund_amount']:.2f}"],
    ]

    table_style = TableStyle([
        ('GRID', (0, 0), (-1, 2), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(1, 0.8, 0.8)), # Light red header
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'), # Bold the refund row
    ])
    
    t = Table(table_data, colWidths=[3.5*inch, 2*inch])
    t.setStyle(table_style)
    story.append(Paragraph(f"User: {details['username']}", styles['h4']))
    story.append(Paragraph(f"Passenger: {details['passenger_full_name']}", styles['h4']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(t)
    story.append(Spacer(1, 0.5 * inch))

    story.append(Paragraph("Note: Seat inventory has been restored. Funds will be returned to the original payment method within 5-7 business days.", styles['Italic']))

    doc.build(story)
    return file_path


# --- Background Task for Demand Simulation ---

def update_demand_factor():
    """Periodically updates the demand factor for all flights to simulate market shifts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM flight")
    flight_ids = [row[0] for row in cursor.fetchall()]

    for flight_id in flight_ids:
        new_demand_factor = round(random.uniform(0.9, 1.1), 2)
        cursor.execute("UPDATE flight SET demand_factor = ? WHERE id = ?", (new_demand_factor, flight_id))

    conn.commit()
    conn.close()
    print(f"Background process: Demand factors updated at {datetime.now().strftime('%H:%M:%S')}")

# Initialize and Start Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_demand_factor, trigger="interval", minutes=5)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


# --- Authentication Endpoints ---

@app.get("/")
def read_root():
    """Health check and welcome message."""
    return {"message" : "Welcome to the flight booking simulator API"}

@app.post("/register")
def register_user(user: UserAuth, db: sqlite3.Connection = Depends(get_db)):
    """Registers a new user with full name, phone, and country."""
    cursor = db.cursor()

    cursor.execute("SELECT id FROM user WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = hash_password(user.password)

    try:
        # UPDATED SQL INSERT to include new fields
        cursor.execute(
            "INSERT INTO user (username, password_hash, full_name, phone, country) VALUES (?, ?, ?, ?, ?)",
            (user.username, hashed_password, user.full_name, user.phone, user.country)
        )
        db.commit()
        return {"message": "User registered successfully", "username": user.username}
    except sqlite3.Error as e:
        db.rollback()
        if "no such column" in str(e):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Error: User table schema is outdated. Please add full_name, phone, and country columns.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

@app.post("/login")
def login_user(user: UserAuth, db: sqlite3.Connection = Depends(get_db)):
    """Authenticates a user and returns user ID and simulated session token."""
    cursor = db.cursor()

    cursor.execute("SELECT id, password_hash FROM user WHERE username = ?", (user.username,))
    user_data = cursor.fetchone()

    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    hashed_input = hash_password(user.password)
    if hashed_input != user_data['password_hash']:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(16)
    return {"message": "Login successful", "username": user.username, "user_id": user_data['id'], "token": session_token}

@app.post("/logout")
def logout_user():
    """Clears the session on the client side (simulated)."""
    return {"message": "Logout successful"}


# --- NEW: Chatbot Endpoint ---
@app.post("/chat")
def chat_with_gemini(request: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    """Handles chat prompts and generates responses using the Gemini API."""
    if not gemini_model:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gemini API key not configured on server.")

    # 1. Fetch available airports (cities) from our DB
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT from_city_country FROM flight")
    cities = [row[0] for row in cursor.fetchall()]
    city_list = ", ".join(cities)

    # 2. Engineer the system prompt
    system_prompt = f"""
    You are 'Skyline AI', a helpful assistant for the SKYLINE RESERVATION SYSTEM.
    Your goal is to help users plan their trip by suggesting destinations or helping them find flights.

    RULES:
    - Be friendly, concise, and professional.
    - If the user asks for flight availability or prices, you MUST state that you cannot check live prices or book flights.
    - You CAN suggest trip ideas based on their input (origin, destination, days).
    - The available cities we currently fly to/from are: {city_list}.
    - If a user asks for a city not in this list, gently inform them we don't fly there and suggest an alternative from the list.
    - If the user asks about origin, destination, and days, provide a helpful trip suggestion.

    User Prompt: {request.prompt}
    """

    # 3. Format history for Gemini
    gemini_history = []
    for msg in request.history:
        gemini_history.append({
            "role": msg.role,
            "parts": [msg.parts]
        })

    try:
        # Start a new chat session with the history
        chat = gemini_model.start_chat(history=gemini_history)
        # Send the new prompt (with system instructions)
        response = chat.send_message(system_prompt)

        return {"role": "model", "parts": response.text}

    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return a 500 error if the API fails, including the detail for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error communicating with AI: {e}")


# --- Flight Search and Data Endpoints ---

@app.get("/airports")
def get_all_airports(db: sqlite3.Connection = Depends(get_db)):
    """Retrieves a list of all unique city/country names for dropdowns."""
    cursor = db.cursor()

    cursor.execute("""
        SELECT DISTINCT from_city_country FROM flight
        UNION
        SELECT DISTINCT to_city_country FROM flight
        ORDER BY 1
    """)

    airports = [row[0] for row in cursor.fetchall()]

    return {"airports": airports}


def apply_dynamic_pricing_and_sort(flights_data: list, sort_by: str, sort_order: str) -> List[dict]:
    """Helper to apply pricing and sorting logic."""
    flights_with_pricing = []
    for row in flights_data:
        flight_dict = dict(row)

        final_price = calculate_dynamic_price(
            base_price=flight_dict['base_price'],
            seats_remaining=flight_dict['seats_remaining'],
            total_seats=flight_dict['total_seats'],
            demand_factor=flight_dict['demand_factor']
        )
        flight_dict['final_price'] = final_price
        flights_with_pricing.append(flight_dict)

    if sort_by == 'price':
        reverse_sort = sort_order.lower() == 'desc'
        flights_with_pricing.sort(key=lambda f: f['final_price'], reverse=reverse_sort)

    return flights_with_pricing

@app.get("/flights/all", response_model=List[FlightDisplay])
def list_all_flights(db: sqlite3.Connection = Depends(get_db)):
    """Retrieves all flights with dynamic pricing applied."""
    cursor = db.cursor()
    cursor.execute("SELECT * FROM flight")
    flights_data = cursor.fetchall()

    if not flights_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No flights found.")

    return apply_dynamic_pricing_and_sort(flights_data, sort_by='price', sort_order='asc')


@app.get("/flights", response_model=List[FlightDisplay])
def search_flights(
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    sort_by: str = Query("price"),
    sort_order: str = Query("asc"),
    db: sqlite3.Connection = Depends(get_db)
):
    """Searches for flights based on city/country, applying dynamic pricing."""
    cursor = db.cursor()
    query = "SELECT * FROM flight WHERE 1=1"
    params = []

    if origin:
        query += " AND from_city_country = ?"
        params.append(origin.strip())
    
    if destination:
        query += " AND to_city_country = ?"
        params.append(destination.strip())

    flights_data = cursor.execute(query, params).fetchall()

    if not flights_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No flights found for the given criteria.")

    return apply_dynamic_pricing_and_sort(flights_data, sort_by, sort_order)


# --- Booking and Payment Endpoints ---

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(request: BookingRequest, db: sqlite3.Connection = Depends(get_db)):
    """Creates a booking record with PENDING_PAYMENT status, using the actual logged-in user_id."""
    cursor = db.cursor()
    
    # Concatenate first name and last name for storage
    passenger_full_name = f"{request.passenger.first_name} {request.passenger.last_name}"

    try:
        # 1. Fetch flight data
        cursor.execute("""
            SELECT id, base_price, seats_remaining, total_seats, demand_factor
            FROM flight
            WHERE flight_number = ?
        """, (request.flight_number,))

        flight_data = cursor.fetchone()

        if not flight_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flight {request.flight_number} not found.")

        flight_id = flight_data['id']
        seats_remaining = flight_data['seats_remaining']

        if seats_remaining <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No seats available for reservation.")

        # 2. Calculate final price
        final_price = calculate_dynamic_price(
            base_price=flight_data['base_price'],
            seats_remaining=seats_remaining,
            total_seats=flight_data['total_seats'],
            demand_factor=flight_data['demand_factor']
        )

        # 3. Insert the PENDING booking record
        PNR = "PNR" + str(uuid.uuid4().hex[:7]).upper()

        # Using request.user_id (received from frontend) AND passenger_full_name
        cursor.execute("""
            INSERT INTO booking (user_id, flight_id, pnr, price_paid, booking_date, passenger_full_name)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (request.user_id, flight_id, PNR, final_price, passenger_full_name))

        db.commit()

        return {
            "status": "PENDING_PAYMENT",
            "message": "Booking created. Proceed to payment.",
            "pnr": PNR,
            "price_due": final_price,
            "flight_number": request.flight_number,
            "passenger": passenger_full_name
        }

    except sqlite3.Error as e:
        db.rollback()
        if "no such column: passenger_full_name" in str(e):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Error: Missing 'passenger_full_name' column. Did you run ALTER TABLE?")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Booking creation failed: {e}")

@app.post("/bookings/pay/{pnr}")
def simulate_payment_and_confirm(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Simulates payment, performs transactional seat decrement, and confirms booking."""
    cursor = db.cursor()

    try:
        # 1. Fetch booking to get flight ID
        cursor.execute("SELECT id, flight_id FROM booking WHERE pnr = ?", (pnr,))
        booking = cursor.fetchone()

        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending booking not found.")

        flight_id = booking['flight_id']

        # 2. Check seat availability and decrement seats (Atomic Transaction)
        cursor.execute("SELECT seats_remaining FROM flight WHERE id = ?", (flight_id,))
        flight_data = cursor.fetchone()

        if flight_data['seats_remaining'] <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment failed: Seat sold out during delay.")

        # A. Decrement seat count (Transactional step)
        cursor.execute("UPDATE flight SET seats_remaining = seats_remaining - 1 WHERE id = ?", (flight_id,))

        # B. Update booking status to CONFIRMED
        cursor.execute(
            "UPDATE booking SET status = 'CONFIRMED' WHERE pnr = ?",
            (pnr,)
        )

        # 3. Commit the transaction
        db.commit()

        return {
            "status": "CONFIRMED",
            "message": f"Payment successful. Seat reserved and PNR {pnr} confirmed.",
            "pnr": pnr,
        }

    except HTTPException:
        db.rollback()
        raise
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Payment/Confirmation failed: {e}")


@app.get("/bookings/history/{user_id}")
def get_user_booking_history(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Fetches recent confirmed tickets and transaction history for a logged-in user, including username."""
    cursor = db.cursor()

    cursor.execute("""
        SELECT
            b.pnr, b.price_paid, b.booking_date, b.status, b.passenger_full_name,
            f.flight_number, f.airline, f.from_city_country, f.to_city_country,
            u.username
        FROM booking b
        JOIN flight f ON b.flight_id = f.id
        JOIN user u ON b.user_id = u.id
        WHERE b.user_id = ? AND UPPER(b.status) LIKE '%CONFIRMED%'
        ORDER BY b.booking_date DESC
    """, (user_id,))

    history = cursor.fetchall()

    if not history:
        return {"user_id": user_id, "history": [], "message": "No confirmed bookings found for this user."}

    formatted_history = [dict(row) for row in history]

    return {"user_id": user_id, "history": formatted_history, "total_bookings": len(formatted_history)}


@app.get("/bookings/cancelled/{user_id}")
def get_cancellation_history(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """Fetches the cancellation and refund history from the audit log."""
    cursor = db.cursor()

    try:
        # CRITICAL: Join flight and user tables to retrieve display data
        cursor.execute("""
            SELECT
                ca.pnr, ca.price_paid, ca.refund_amount, ca.cancellation_date,
                ca.passenger_full_name, f.flight_number, f.airline, u.username
            FROM cancelled_booking ca
            JOIN flight f ON ca.flight_id = f.id
            JOIN user u ON ca.user_id = u.id
            WHERE ca.user_id = ?
            ORDER BY ca.cancellation_date DESC
        """, (user_id,))

        history = cursor.fetchall()

        if not history:
            return {"user_id": user_id, "history": [], "message": "No cancellation history found for this user."}

        formatted_history = [dict(row) for row in history]

        return {"user_id": user_id, "history": formatted_history, "total": len(formatted_history)}

    except sqlite3.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving cancellation history. Ensure 'cancelled_booking' table exists: {e}"
        )


@app.get("/tickets/{pnr}")
def get_ticket_pdf(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Retrieves booking details and generates/returns the PDF ticket."""
    cursor = db.cursor()

    # 1. Fetch comprehensive booking and flight details, including passenger_full_name
    cursor.execute("""
        SELECT
            b.price_paid, b.pnr, b.booking_date, b.passenger_full_name,
            f.flight_number, f.airline,
            f.from_city_country, f.to_city_country,
            u.username
        FROM booking b
        JOIN flight f ON b.flight_id = f.id
        JOIN user u ON b.user_id = u.id
        WHERE b.pnr = ?
    """, (pnr,))

    booking_data = cursor.fetchone()

    if not booking_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    # 2. Prepare data for the PDF generator
    details = {
        "pnr": booking_data['pnr'],
        "price_paid": booking_data['price_paid'],
        "booking_date": booking_data['booking_date'],
        "flight_number": booking_data['flight_number'],
        "airline": booking_data['airline'],
        "from_city_country": booking_data['from_city_country'],
        "to_city_country": booking_data['to_city_country'],
        "passenger_name": booking_data['passenger_full_name'],
        "seat_preference": "Any"
    }

    # 3. Generate PDF
    try:
        pdf_path = generate_ticket_pdf(pnr, details)
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate PDF ticket.")

    # 4. Return as FileResponse for download (Simplified for stability)
    return FileResponse(
        path=pdf_path,
        media_type='application/pdf',
        filename=f"flight_ticket_{pnr}.pdf"
    )

@app.get("/receipts/{pnr}")
def get_cancellation_receipt_pdf(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Retrieves cancellation data and generates/returns the PDF receipt."""
    cursor = db.cursor()

    # 1. Fetch the necessary data for the receipt from the ARCHIVED table
    cursor.execute("""
        SELECT
            ca.price_paid, ca.refund_amount, ca.pnr, ca.cancellation_date, ca.passenger_full_name,
            f.flight_number, f.airline, u.username
        FROM cancelled_booking ca
        JOIN flight f ON ca.flight_id = f.id
        JOIN user u ON ca.user_id = u.id
        WHERE ca.pnr = ?
    """, (pnr,))

    cancellation_data = cursor.fetchone()

    if not cancellation_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cancellation record not found.")

    # 2. Prepare data for the PDF receipt
    details = {
        "pnr": cancellation_data['pnr'],
        "flight_number": cancellation_data['flight_number'],
        "airline": cancellation_data['airline'],
        "price_paid": cancellation_data['price_paid'],
        "refund_amount": cancellation_data['refund_amount'],
        "note": f"80% Refund",
        "username": cancellation_data['username'],
        "passenger_full_name": cancellation_data['passenger_full_name']
    }

    try:
        receipt_path = generate_cancellation_receipt(pnr, details)
    except Exception as e:
        print(f"Receipt generation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate receipt PDF.")

    return FileResponse(
        path=receipt_path,
        media_type='application/pdf',
        filename=f"cancellation_receipt_{pnr}.pdf"
    )


@app.delete("/bookings/{pnr}")
def cancel_booking(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Cancels booking, archives the record, restores seat, and simulates a partial refund (80%)."""
    cursor = db.cursor()

    try:
        # 1. Find ALL necessary data BEFORE deletion
        cursor.execute("""
            SELECT
                b.id, b.flight_id, b.price_paid, b.user_id, b.passenger_full_name
            FROM booking b
            WHERE b.pnr = ? AND UPPER(b.status) = 'CONFIRMED'
        """, (pnr.upper(),))
        booking = cursor.fetchone()

        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with PNR {pnr} not found or not confirmed.")

        booking_id = booking['id']
        flight_id = booking['flight_id']
        price_paid = booking['price_paid']

        # 2. Simulate Refund Calculation
        REFUND_RATE = 0.80
        refund_amount = round(price_paid * REFUND_RATE, 2)
        refund_note = f"{REFUND_RATE*100:.0f}% Refund"

        # 3. ARCHIVE THE RECORD (Transactional Step A)
        cursor.execute("""
            INSERT INTO cancelled_booking
            (pnr, user_id, flight_id, price_paid, refund_amount, passenger_full_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pnr.upper(), booking['user_id'], flight_id, price_paid, refund_amount, booking['passenger_full_name']
        ))

        # 4. Delete the booking record (Transactional Step B)
        cursor.execute("DELETE FROM booking WHERE id = ?", (booking_id,))

        # 5. Restore the seat count (Transactional Step C)
        cursor.execute("UPDATE flight SET seats_remaining = seats_remaining + 1 WHERE id = ?", (flight_id,))

        db.commit()

        # 6. Return data for frontend confirmation
        return {
            "message": f"Booking {pnr} cancelled successfully.",
            "status": "REFUND_PROCESSED",
            "refund_amount": refund_amount,
            "price_paid": price_paid,
            "note": refund_note,
        }

    except sqlite3.Error as e:
        db.rollback()
        if "no such table: cancelled_booking" in str(e):
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="DB Error: Missing 'cancelled_booking' audit table. Please create it.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Cancellation failed: {e}")