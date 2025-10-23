-- 1. SCHEMA DESIGN WITH CONSTRAINTS

-- Drop existing tables to ensure a clean start with the new schema
DROP TABLE IF EXISTS booking;
DROP TABLE IF EXISTS flight;
DROP TABLE IF EXISTS user;

-- User table with a primary key and unique constraint
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    profile_data VARCHAR(256)
);

-- Airport Lookup Table (Optional but provides a centralized place for names/codes)
-- We will use this list to generate the city/country names for the FLIGHT table below.
CREATE TABLE airport_lookup (
    code VARCHAR(10) PRIMARY KEY,
    city_country VARCHAR(100) NOT NULL
);

-- Flight table REVISED to use City/Country Names instead of short codes
CREATE TABLE flight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number VARCHAR(50) NOT NULL UNIQUE,
    airline VARCHAR(50) NOT NULL,
    -- REVISED COLUMNS: Using full city, country name
    from_city_country VARCHAR(100) NOT NULL, 
    to_city_country VARCHAR(100) NOT NULL,
    base_price REAL NOT NULL,
    total_seats INTEGER NOT NULL,
    seats_remaining INTEGER NOT NULL,
    demand_factor REAL DEFAULT 1.0, 
    -- Check constraint to ensure seats remaining is not negative
    CHECK(seats_remaining >= 0 AND seats_remaining <= total_seats)
);

-- Booking table with foreign keys linking to user and flight tables
-- REVISED SCHEMA FOR MILESTONE 3: BOOKING TABLE

CREATE TABLE booking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    flight_id INTEGER NOT NULL,
    pnr VARCHAR(10) NOT NULL UNIQUE,
    price_paid REAL NOT NULL,
    booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- NEW FIELD: Tracks the state of the booking transaction
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING_PAYMENT', 
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (flight_id) REFERENCES flight (id)
);


-- 2. POPULATING WITH SAMPLE DATA

-- Inserting data into the airport lookup table
INSERT INTO airport_lookup (code, city_country) VALUES
('JFK', 'New York, USA'), ('LHR', 'London, UK'),
('LAX', 'Los Angeles, USA'), ('DXB', 'Dubai, UAE'),
('CDG', 'Paris, France'), ('NRT', 'Tokyo, Japan'),
('SYD', 'Sydney, Australia'), ('SIN', 'Singapore, Singapore'),
('HKG', 'Hong Kong, China'), ('FRA', 'Frankfurt, Germany'),
('MUC', 'Munich, Germany'), ('BKK', 'Bangkok, Thailand'),
('SGN', 'Ho Chi Minh City, Vietnam'), ('ORD', 'Chicago, USA'),
('MIA', 'Miami, USA'), ('AMS', 'Amsterdam, Netherlands'),
('CPH', 'Copenhagen, Denmark'), ('DEL', 'New Delhi, India'),
('BOM', 'Mumbai, India'), ('PEK', 'Beijing, China'),
('PVG', 'Shanghai, China'), ('KUL', 'Kuala Lumpur, Malaysia'),
('MEX', 'Mexico City, Mexico'), ('CUN', 'Cancun, Mexico');


-- Inserting sample data into the user table (No Change)
INSERT INTO user (username, password_hash, profile_data) VALUES
('UserA', 'hash123abcde', 'Profile A'), ('UserB', 'hash456fghij', 'Profile B'),
('UserC', 'hash789gHI', 'Profile C'), ('UserD', 'hash111jKL', 'Profile D'),
('UserE', 'hash222MNO', 'Profile E'), ('UserF', 'hash333PQR', 'Profile F'),
('UserG', 'hash444STU', 'Profile G'), ('UserH', 'hash555VWX', 'Profile H'),
('UserI', 'hash666YZA', 'Profile I'), ('UserJ', 'hash777BCD', 'Profile J'),
('UserK', 'hash888EFG', 'Profile K'), ('UserL', 'hash999HIJ', 'Profile L'),
('UserM', 'hash000KLM', 'Profile M'), ('UserN', 'hash121NOP', 'Profile N'),
('UserO', 'hash232QRS', 'Profile O'), ('UserP', 'hash343TUV', 'Profile P'),
('UserQ', 'hash454WXY', 'Profile Q'), ('UserR', 'hash565ZAB', 'Profile R'),
('UserS', 'hash676CDE', 'Profile S'), ('UserT', 'hash787FGH', 'Profile T'),
('UserU', 'hash898IJK', 'Profile U'), ('UserV', 'hash909LMN', 'Profile V'),
('UserW', 'hash101OPQ', 'Profile W'), ('UserX', 'hash202RST', 'Profile X'),
('UserY', 'hash303UVW', 'Profile Y');


-- Inserting sample data into the flight table using City, Country names
INSERT INTO flight (flight_number, airline, from_city_country, to_city_country, base_price, total_seats, seats_remaining) VALUES
('FL101', 'AirlineA', 'New York, USA', 'London, UK', 550.00, 200, 150), 
('FL102', 'AirlineB', 'Los Angeles, USA', 'Dubai, UAE', 1200.50, 300, 280),
('FL103', 'AirlineC', 'Paris, France', 'Tokyo, Japan', 980.25, 250, 220), 
('FL104', 'AirlineA', 'London, UK', 'New York, USA', 600.00, 200, 180),
('FL105', 'AirlineD', 'Dubai, UAE', 'Sydney, Australia', 1500.75, 400, 350), 
('FL106', 'AirlineB', 'Tokyo, Japan', 'Paris, France', 950.00, 250, 200),
('FL107', 'AirlineE', 'New York, USA', 'Paris, France', 450.00, 180, 100), 
('FL108', 'AirlineA', 'Sydney, Australia', 'Los Angeles, USA', 1300.00, 400, 390),
('FL109', 'AirlineF', 'Singapore, Singapore', 'Hong Kong, China', 250.00, 150, 140), 
('FL110', 'AirlineC', 'Hong Kong, China', 'Singapore, Singapore', 280.00, 150, 120),
('FL111', 'AirlineG', 'Frankfurt, Germany', 'Munich, Germany', 150.00, 100, 80), 
('FL112', 'AirlineD', 'Bangkok, Thailand', 'Ho Chi Minh City, Vietnam', 320.00, 120, 110),
('FL113', 'AirlineH', 'Ho Chi Minh City, Vietnam', 'Bangkok, Thailand', 300.00, 120, 90), 
('FL114', 'AirlineA', 'Chicago, USA', 'Miami, USA', 350.00, 220, 200),
('FL115', 'AirlineI', 'Miami, USA', 'Chicago, USA', 380.00, 220, 190), 
('FL116', 'AirlineJ', 'Amsterdam, Netherlands', 'Copenhagen, Denmark', 200.00, 110, 50),
('FL117', 'AirlineK', 'Copenhagen, Denmark', 'Amsterdam, Netherlands', 210.00, 110, 60), 
('FL118', 'AirlineL', 'New Delhi, India', 'Mumbai, India', 120.00, 160, 150),
('FL119', 'AirlineM', 'Mumbai, India', 'New Delhi, India', 130.00, 160, 140), 
('FL120', 'AirlineN', 'Beijing, China', 'Shanghai, China', 180.00, 280, 250),
('FL121', 'AirlineO', 'Shanghai, China', 'Beijing, China', 190.00, 280, 240), 
('FL122', 'AirlineP', 'Dubai, UAE', 'Kuala Lumpur, Malaysia', 800.00, 320, 310),
('FL123', 'AirlineQ', 'Kuala Lumpur, Malaysia', 'Dubai, UAE', 850.00, 320, 300), 
('FL124', 'AirlineR', 'Mexico City, Mexico', 'Cancun, Mexico', 250.00, 180, 170),
('FL125', 'AirlineS', 'Cancun, Mexico', 'Mexico City, Mexico', 270.00, 180, 160);

-- Inserting sample data into the booking table (No Change needed as flight_id is intact)
INSERT INTO booking (user_id, flight_id, pnr, price_paid) VALUES
(1, 1, 'PNR123ABC', 550.00), (2, 2, 'PNR456DEF', 1200.50),
(3, 3, 'PNR789GHI', 980.25), (4, 4, 'PNR111JKL', 600.00),
(5, 5, 'PNR222MNO', 1500.75), (6, 6, 'PNR333PQR', 950.00),
(7, 7, 'PNR444STU', 450.00), (8, 8, 'PNR555VWX', 1300.00),
(9, 9, 'PNR666YZA', 250.00), (10, 10, 'PNR777BCD', 280.00),
(11, 11, 'PNR888EFG', 150.00), (12, 12, 'PNR999HIJ', 320.00),
(13, 13, 'PNR000KLM', 300.00), (14, 14, 'PNR121NOP', 350.00),
(15, 15, 'PNR232QRS', 380.00), (16, 16, 'PNR343TUV', 200.00),
(17, 17, 'PNR454WXY', 210.00), (18, 18, 'PNR565ZAB', 120.00),
(19, 19, 'PNR676CDE', 130.00), (20, 20, 'PNR787FGH', 180.00),
(21, 21, 'PNR898IJK', 190.00), (22, 22, 'PNR909LMN', 800.00),
(23, 23, 'PNR101OPQ', 850.00), (24, 24, 'PNR202RST', 250.00),
(25, 25, 'PNR303UVW', 270.00);


-- 1. Update Airline Names in the 'flight' Table

-- Change AirlineA (e.g., used for New York, USA <=> London, UK routes)
UPDATE flight SET airline = 'United Airlines' WHERE airline = 'AirlineA';

-- Change AirlineB (e.g., used for Los Angeles, USA <=> Dubai, UAE routes)
UPDATE flight SET airline = 'Emirates' WHERE airline = 'AirlineB';

-- Change AirlineC (e.g., used for Paris, France <=> Tokyo, Japan routes)
UPDATE flight SET airline = 'Air France' WHERE airline = 'AirlineC';

-- Change AirlineD (e.g., used for Dubai, UAE <=> Sydney, Australia routes)
UPDATE flight SET airline = 'Qantas' WHERE airline = 'AirlineD';

-- Change AirlineE (e.g., used for New York, USA <=> Paris, France routes)
UPDATE flight SET airline = 'Delta Airlines' WHERE airline = 'AirlineE';

-- Change AirlineF (e.g., used for Singapore, Singapore <=> Hong Kong, China routes)
UPDATE flight SET airline = 'Singapore Airlines' WHERE airline = 'AirlineF';

-- Change AirlineG (e.g., used for Frankfurt, Germany <=> Munich, Germany routes)
UPDATE flight SET airline = 'Lufthansa' WHERE airline = 'AirlineG';

-- Change AirlineH (e.g., used for Ho Chi Minh City, Vietnam <=> Bangkok, Thailand routes)
UPDATE flight SET airline = 'Thai Airways' WHERE airline = 'AirlineH';

-- Change AirlineI (e.g., used for Miami, USA <=> Chicago, USA routes)
UPDATE flight SET airline = 'American Airlines' WHERE airline = 'AirlineI';

-- Change AirlineJ (e.g., used for Amsterdam, Netherlands <=> Copenhagen, Denmark routes)
UPDATE flight SET airline = 'KLM' WHERE airline = 'AirlineJ';

-- Change AirlineK (e.g., used for Copenhagen, Denmark <=> Amsterdam, Netherlands routes)
UPDATE flight SET airline = 'SAS' WHERE airline = 'AirlineK';

-- Change AirlineL (e.g., used for New Delhi, India <=> Mumbai, India routes)
UPDATE flight SET airline = 'IndiGo' WHERE airline = 'AirlineL';

-- Change AirlineM (e.g., used for Mumbai, India <=> New Delhi, India routes)
UPDATE flight SET airline = 'Air India' WHERE airline = 'AirlineM';

-- Change AirlineN (e.g., used for Beijing, China <=> Shanghai, China routes)
UPDATE flight SET airline = 'Air China' WHERE airline = 'AirlineN';

-- Change AirlineO (e.g., used for Shanghai, China <=> Beijing, China routes)
UPDATE flight SET airline = 'China Eastern' WHERE airline = 'AirlineO';

-- Change AirlineP (e.g., used for Dubai, UAE <=> Kuala Lumpur, Malaysia routes)
UPDATE flight SET airline = 'Malaysian Airlines' WHERE airline = 'AirlineP';

-- Change AirlineQ (e.g., used for Kuala Lumpur, Malaysia <=> Dubai, UAE routes)
UPDATE flight SET airline = 'Qatar Airways' WHERE airline = 'AirlineQ';

-- Change AirlineR (e.g., used for Mexico City, Mexico <=> Cancun, Mexico routes)
UPDATE flight SET airline = 'Aeroméxico' WHERE airline = 'AirlineR';

-- Change AirlineS (e.g., used for Cancun, Mexico <=> Mexico City, Mexico routes)
UPDATE flight SET airline = 'Viva Aerobus' WHERE airline = 'AirlineS';


-- Verification (Optional: run this after execution to check changes)
-- SELECT flight_number, airline, from_city_country, to_city_country FROM flight;

-- 3. ADDING 50 NEW FLIGHTS (FL126 to FL175)

-- Introducing new City/Country pairs for variety:
-- Dublin, Ireland (DUB)
-- Istanbul, Turkey (IST)
-- Rio de Janeiro, Brazil (GIG)
-- Johannesburg, South Africa (JNB)
-- Vancouver, Canada (YVR)
-- Seoul, South Korea (ICN)
-- Dubai, UAE (DXB)

INSERT INTO flight (flight_number, airline, from_city_country, to_city_country, base_price, total_seats, seats_remaining) VALUES
('FL126', 'United Airlines', 'New York, USA', 'Dublin, Ireland', 480.00, 190, 140),
('FL127', 'Lufthansa', 'Frankfurt, Germany', 'Istanbul, Turkey', 350.00, 160, 120),
('FL128', 'Emirates', 'Dubai, UAE', 'Rio de Janeiro, Brazil', 1450.00, 350, 300),
('FL129', 'Qantas', 'Sydney, Australia', 'Johannesburg, South Africa', 1100.00, 280, 250),
('FL130', 'Air Canada', 'Vancouver, Canada', 'Tokyo, Japan', 850.00, 220, 170),
('FL131', 'Singapore Airlines', 'Singapore, Singapore', 'Seoul, South Korea', 580.00, 240, 200),
('FL132', 'Emirates', 'Rio de Janeiro, Brazil', 'Dubai, UAE', 1500.00, 350, 310),
('FL133', 'KLM', 'Amsterdam, Netherlands', 'New York, USA', 520.00, 210, 160),
('FL134', 'Air France', 'Paris, France', 'Rio de Janeiro, Brazil', 1150.00, 300, 280),
('FL135', 'Lufthansa', 'Munich, Germany', 'London, UK', 180.00, 120, 90),
('FL136', 'United Airlines', 'Chicago, USA', 'New York, USA', 220.00, 250, 210),
('FL137', 'IndiGo', 'Mumbai, India', 'Bangkok, Thailand', 280.00, 180, 150),
('FL138', 'Thai Airways', 'Bangkok, Thailand', 'Mumbai, India', 290.00, 180, 160),
('FL139', 'American Airlines', 'New York, USA', 'Los Angeles, USA', 390.00, 320, 300),
('FL140', 'Delta Airlines', 'Los Angeles, USA', 'New York, USA', 410.00, 320, 290),
('FL141', 'Singapore Airlines', 'Seoul, South Korea', 'Singapore, Singapore', 600.00, 240, 210),
('FL142', 'Qantas', 'Johannesburg, South Africa', 'Sydney, Australia', 1120.00, 280, 260),
('FL143', 'Air India', 'New Delhi, India', 'Dubai, UAE', 350.00, 200, 180),
('FL144', 'Emirates', 'Dubai, UAE', 'New Delhi, India', 370.00, 200, 170),
('FL145', 'Lufthansa', 'Istanbul, Turkey', 'Frankfurt, Germany', 360.00, 160, 130),
('FL146', 'United Airlines', 'Dublin, Ireland', 'New York, USA', 500.00, 190, 150),
('FL147', 'Air France', 'Paris, France', 'New York, USA', 550.00, 200, 160),
('FL148', 'Delta Airlines', 'New York, USA', 'Paris, France', 530.00, 200, 170),
('FL149', 'KLM', 'Copenhagen, Denmark', 'Amsterdam, Netherlands', 220.00, 110, 70),
('FL150', 'SAS', 'Amsterdam, Netherlands', 'Copenhagen, Denmark', 230.00, 110, 80),
('FL151', 'Air China', 'Shanghai, China', 'Hong Kong, China', 150.00, 260, 230),
('FL152', 'China Eastern', 'Hong Kong, China', 'Shanghai, China', 160.00, 260, 240),
('FL153', 'Qantas', 'Sydney, Australia', 'Tokyo, Japan', 780.00, 280, 250),
('FL154', 'Thai Airways', 'Bangkok, Thailand', 'Seoul, South Korea', 450.00, 210, 190),
('FL155', 'Singapore Airlines', 'Tokyo, Japan', 'Singapore, Singapore', 620.00, 250, 220),
('FL156', 'Aeroméxico', 'Cancun, Mexico', 'Miami, USA', 200.00, 150, 130),
('FL157', 'Viva Aerobus', 'Miami, USA', 'Cancun, Mexico', 210.00, 150, 120),
('FL158', 'Emirates', 'Dubai, UAE', 'London, UK', 650.00, 400, 350),
('FL159', 'British Airways', 'London, UK', 'Dubai, UAE', 670.00, 400, 360), -- Assuming British Airways is used for this new route
('FL160', 'Lufthansa', 'Frankfurt, Germany', 'New York, USA', 580.00, 280, 240),
('FL161', 'United Airlines', 'New York, USA', 'Frankfurt, Germany', 560.00, 280, 230),
('FL162', 'Air India', 'Mumbai, India', 'Dubai, UAE', 300.00, 220, 200),
('FL163', 'Emirates', 'Dubai, UAE', 'Mumbai, India', 320.00, 220, 190),
('FL164', 'Qantas', 'Sydney, Australia', 'Vancouver, Canada', 950.00, 270, 240),
('FL165', 'Air Canada', 'Vancouver, Canada', 'Sydney, Australia', 980.00, 270, 250),
('FL166', 'SAS', 'Copenhagen, Denmark', 'Istanbul, Turkey', 380.00, 150, 130),
('FL167', 'Turkish Airlines', 'Istanbul, Turkey', 'Copenhagen, Denmark', 390.00, 150, 140), -- Assuming Turkish Airlines is used for this new route
('FL168', 'Delta Airlines', 'Chicago, USA', 'Los Angeles, USA', 250.00, 300, 280),
('FL169', 'American Airlines', 'Los Angeles, USA', 'Chicago, USA', 260.00, 300, 270),
('FL170', 'Air France', 'Paris, France', 'Tokyo, Japan', 900.00, 250, 230),
('FL171', 'Japan Airlines', 'Tokyo, Japan', 'Paris, France', 920.00, 250, 240), -- Assuming Japan Airlines is used for this new route
('FL172', 'Lufthansa', 'Munich, Germany', 'Paris, France', 160.00, 140, 110),
('FL173', 'KLM', 'Amsterdam, Netherlands', 'London, UK', 130.00, 110, 90),
('FL174', 'British Airways', 'London, UK', 'Amsterdam, Netherlands', 140.00, 110, 80),
('FL175', 'Singapore Airlines', 'Singapore, Singapore', 'Dubai, UAE', 750.00, 350, 320);

-- 4. ADDING 25 MORE NEW FLIGHTS (FL176 to FL200)

INSERT INTO flight (flight_number, airline, from_city_country, to_city_country, base_price, total_seats, seats_remaining) VALUES
('FL176', 'Emirates', 'Dubai, UAE', 'Los Angeles, USA', 1550.00, 380, 350),
('FL177', 'United Airlines', 'Los Angeles, USA', 'Dubai, UAE', 1500.00, 380, 330),
('FL178', 'Air France', 'Paris, France', 'Johannesburg, South Africa', 1250.00, 310, 280),
('FL179', 'Lufthansa', 'Frankfurt, Germany', 'New York, USA', 610.00, 250, 210),
('FL180', 'Delta Airlines', 'New York, USA', 'Frankfurt, Germany', 590.00, 250, 220),
('FL181', 'Singapore Airlines', 'Singapore, Singapore', 'Sydney, Australia', 800.00, 300, 270),
('FL182', 'Qantas', 'Sydney, Australia', 'Singapore, Singapore', 790.00, 300, 260),
('FL183', 'Thai Airways', 'Bangkok, Thailand', 'Tokyo, Japan', 520.00, 200, 180),
('FL184', 'KLM', 'Amsterdam, Netherlands', 'Istanbul, Turkey', 350.00, 160, 140),
('FL185', 'Turkish Airlines', 'Istanbul, Turkey', 'Amsterdam, Netherlands', 360.00, 160, 130),
('FL186', 'IndiGo', 'New Delhi, India', 'Mumbai, India', 110.00, 170, 155),
('FL187', 'Air India', 'Mumbai, India', 'New Delhi, India', 120.00, 170, 150),
('FL188', 'American Airlines', 'Chicago, USA', 'Miami, USA', 230.00, 240, 210),
('FL189', 'Delta Airlines', 'Miami, USA', 'Chicago, USA', 240.00, 240, 200),
('FL190', 'Lufthansa', 'Munich, Germany', 'Frankfurt, Germany', 140.00, 130, 110),
('FL191', 'KLM', 'Amsterdam, Netherlands', 'Paris, France', 100.00, 120, 95),
('FL192', 'Air France', 'Paris, France', 'Amsterdam, Netherlands', 110.00, 120, 105),
('FL193', 'Air China', 'Beijing, China', 'Hong Kong, China', 190.00, 280, 250),
('FL194', 'China Eastern', 'Hong Kong, China', 'Beijing, China', 200.00, 280, 260),
('FL195', 'Aeroméxico', 'Mexico City, Mexico', 'Los Angeles, USA', 450.00, 200, 180),
('FL196', 'Japan Airlines', 'Tokyo, Japan', 'Los Angeles, USA', 950.00, 300, 270),
('FL197', 'SAS', 'Copenhagen, Denmark', 'New York, USA', 540.00, 210, 190),
('FL198', 'British Airways', 'London, UK', 'New York, USA', 580.00, 220, 180),
('FL199', 'United Airlines', 'New York, USA', 'London, UK', 570.00, 220, 170),
('FL200', 'Emirates', 'Dubai, UAE', 'Seoul, South Korea', 700.00, 350, 310);



-- ALTER TABLE command to add passenger name storage
ALTER TABLE booking ADD COLUMN passenger_full_name VARCHAR(100);

CREATE TABLE cancelled_booking (
    archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pnr VARCHAR(10),
    user_id INTEGER,
    flight_id INTEGER,
    price_paid REAL,
    refund_amount REAL,
    cancellation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    passenger_full_name VARCHAR(100)
);