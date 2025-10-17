import sqlite3
import uuid
import hashlib
import secrets
import random
import atexit
from datetime import datetime, timedelta
import os

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
from typing import List, Optional
from apscheduler.schedulers.background import BackgroundScheduler

# --- Configuration ---
DATABASE_NAME = "db.sqlite"
app = FastAPI()

# --- Database Dependency/Connection Utility ---
def get_db_connection():
    """Returns a connection object to the SQLite database with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def get_db():
    """Provides a database connection and ensures it is closed after the request."""
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models for Data Validation and Schema (MILESTONE 2, Task 2 & MILESTONE 3) ---

class UserAuth(BaseModel):
    """Schema for user registration and login credentials."""
    username: str
    password: str 

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

class FlightDisplay(BaseModel):
    """Schema for displaying flight information (MILESTONE 2, Task 1)."""
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

# --- Utilities and Dynamic Pricing Logic (MILESTONE 2, Task 4) ---

def hash_password(password: str):
    """Simple SHA-256 hash for demonstration."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def calculate_dynamic_price(base_price: float, seats_remaining: int, total_seats: int, demand_factor: float) -> float:
    """Calculates the final ticket price based on multiple factors."""
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

    # 2. Time Until Departure Factor (Simplified factor used due to lack of departure datetime column)
    time_factor = 0.05 

    # 3. Final Calculation
    final_price = base_price * (1 + seat_factor + time_factor) * demand_factor
    
    return round(final_price, 2)

def generate_ticket_pdf(pnr: str, booking_details: dict) -> str:
    """Generates a PDF ticket structured like a boarding pass."""
    
    file_path = f"ticket_{pnr}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BarcodeData', fontSize=14, fontName='Helvetica-Bold', alignment=1))
    
    story = []

    # Simulated data for ticket realism
    simulated_seat = f"{random.randint(1, 30)}{random.choice(['A', 'B', 'C', 'D', 'E', 'F'])}"
    simulated_gate = f"G{random.randint(10, 50)}"
    simulated_time = (datetime.now() + timedelta(hours=2)).strftime("%I:%M %p") 
    
    # Header and PNR
    story.append(Paragraph("✈️ **E-TICKET / BOARDING PASS**", styles['Title']))
    story.append(Paragraph(f"**Booking Reference (PNR):** {pnr}", styles['h2']))
    story.append(Spacer(1, 0.2 * inch))

    # Main Details Table
    main_table_data = [
        [
            # Column 1: Passenger and Flight Number
            [
                Paragraph("PASSENGER NAME:", styles['h4']),
                Paragraph(f"**{booking_details['passenger_name'].upper()}**", styles['Heading2']),
                Spacer(1, 0.1 * inch),
                Paragraph("FLIGHT:", styles['h4']),
                Paragraph(f"**{booking_details['flight_number']} ({booking_details['airline']})**", styles['h3']),
            ],
            # Column 2: Route and Date
            [
                Paragraph("ROUTE:", styles['h4']),
                Paragraph(f"{booking_details['from_city_country']} ➡️ {booking_details['to_city_country']}", styles['h3']),
                Spacer(1, 0.1 * inch),
                Paragraph("DATE:", styles['h4']),
                Paragraph(f"**{booking_details['booking_date'].split(' ')[0]}**", styles['h3']),
            ],
            # Column 3: Seat and Gate (Simulated)
            [
                Paragraph("GATE:", styles['h4']),
                Paragraph(f"**{simulated_gate}**", styles['Heading2']),
                Spacer(1, 0.1 * inch),
                Paragraph("SEAT:", styles['h4']),
                Paragraph(f"**{simulated_seat}**", styles['Heading2']),
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

    # Barcode Simulation Section
    story.append(Paragraph("BOARDING TIME:", styles['h4']))
    story.append(Paragraph(f"**{simulated_time}**", styles['h1']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("BARCODE DATA (Unique PNR):", styles['h4']))
    story.append(Paragraph(f"***{pnr}*** - F{booking_details['flight_number']}", styles['BarcodeData']))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("PLEASE PRESENT THIS TICKET AND PHOTO ID AT THE GATE. THANK YOU FOR FLYING.", styles['Italic']))

    doc.build(story)
    
    return file_path


# --- Background Task for Demand Simulation (MILESTONE 2, Task 6) ---

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
    """Registers a new user."""
    cursor = db.cursor()
    
    cursor.execute("SELECT id FROM user WHERE username = ?", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        
    hashed_password = hash_password(user.password)
    
    try:
        cursor.execute(
            "INSERT INTO user (username, password_hash) VALUES (?, ?)", 
            (user.username, hashed_password)
        )
        db.commit()
        return {"message": "User registered successfully", "username": user.username}
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {e}")

@app.post("/login")
def login_user(user: UserAuth, db: sqlite3.Connection = Depends(get_db)):
    """Authenticates a user and returns a simulated session token."""
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


# --- Flight Search and Data Endpoints (MILESTONE 2, Task 1, 3, 5) ---

@app.get("/airports")
def get_all_airports(db: sqlite3.Connection = Depends(get_db)):
    """Retrieves a list of all unique city/country names for dropdowns."""
    cursor = db.cursor()
    
    # Simulates external API for fetching airport data
    cursor.execute("""
        SELECT DISTINCT from_city_country FROM flight
        UNION
        SELECT DISTINCT to_city_country FROM flight
        ORDER BY 1
    """)
    
    airports = [row[0] for row in cursor.fetchall()]
    
    return {"airports": airports}


def apply_dynamic_pricing_and_sort(flights_data: list, sort_by: str, sort_order: str) -> List[dict]:
    """Helper to apply pricing and sorting logic (MILESTONE 2, Task 2, 5)."""
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
        
    # Sorting (MILESTONE 2, Task 2)
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
    """Searches for flights based on city/country."""
    cursor = db.cursor()
    query = "SELECT * FROM flight WHERE 1=1"
    params = []

    # Filtering uses input validation (MILESTONE 2, Task 2)
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


# --- Booking and PDF Endpoints (MILESTONE 3) ---

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(request: BookingRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Creates a new flight booking using a database transaction 
    (MILESTONE 3: Concurrency safety, PNR assignment).
    """
    cursor = db.cursor()
    USER_ID = 1 # Placeholder ID
    
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
        
        # 2. Check seat availability
        if seats_remaining <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No seats available.")

        # 3. Calculate final price
        final_price = calculate_dynamic_price(
            base_price=flight_data['base_price'],
            seats_remaining=seats_remaining,
            total_seats=flight_data['total_seats'],
            demand_factor=flight_data['demand_factor']
        )
        
        # 4. Decrease seats_remaining (part of the transaction)
        cursor.execute("UPDATE flight SET seats_remaining = seats_remaining - 1 WHERE id = ?", (flight_id,))
        
        # 5. Insert the new booking record
        PNR = "PNR" + str(uuid.uuid4().hex[:7]).upper() # Generate unique PNR
        
        cursor.execute("""
            INSERT INTO booking (user_id, flight_id, pnr, price_paid, booking_date) 
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (USER_ID, flight_id, PNR, final_price))
        
        # 6. Commit the transaction
        db.commit()
        
        return {
            "status": "success",
            "message": "Booking created and confirmed",
            "pnr": PNR,
            "price_paid": final_price,
            "flight_number": request.flight_number,
            "passenger": f"{request.passenger.first_name} {request.passenger.last_name}"
        }

    except HTTPException:
        db.rollback()
        raise
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Booking failed due to database error: {e}")


@app.get("/tickets/{pnr}")
def get_ticket_pdf(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Retrieves booking details and generates/returns the PDF ticket."""
    cursor = db.cursor()
    
    cursor.execute("""
        SELECT 
            b.price_paid, b.pnr, b.booking_date,
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

    details = {
        "pnr": booking_data['pnr'],
        "price_paid": booking_data['price_paid'],
        "booking_date": booking_data['booking_date'],
        "flight_number": booking_data['flight_number'],
        "airline": booking_data['airline'],
        "from_city_country": booking_data['from_city_country'], 
        "to_city_country": booking_data['to_city_country'],       
        "passenger_name": booking_data['username'], 
        "seat_preference": "Any" 
    }

    try:
        pdf_path = generate_ticket_pdf(pnr, details)
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate PDF ticket.")

    # Return as FileResponse for download (No cleanup argument for stability)
    return FileResponse(
        path=pdf_path,
        media_type='application/pdf',
        filename=f"flight_ticket_{pnr}.pdf"
    )


@app.delete("/bookings/{pnr}")
def cancel_booking(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    """Cancels a booking and restores the seat availability (MILESTONE 3)."""
    cursor = db.cursor()
    
    try:
        # 1. Find the booking
        cursor.execute("SELECT id, flight_id FROM booking WHERE pnr = ?", (pnr.upper(),))
        booking = cursor.fetchone()
        
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking with PNR {pnr} not found.")
            
        booking_id = booking['id']
        flight_id = booking['flight_id']

        # 2. Delete the booking record
        cursor.execute("DELETE FROM booking WHERE id = ?", (booking_id,))
        
        # 3. Restore the seat count
        cursor.execute("UPDATE flight SET seats_remaining = seats_remaining + 1 WHERE id = ?", (flight_id,))
        
        db.commit()
        return {
            "message": f"Booking {pnr} cancelled successfully.",
            "status": "Seat restored."
        }
        
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Cancellation failed: {e}")