import sqlite3

DATABASE_NAME = "db.sqlite"

def initialize_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    try:
        with open('db.sql', 'r') as f:
            sql_script = f.read()
        
        # Execute the full script
        cursor.executescript(sql_script)
        
        conn.commit()
        print(f"Database '{DATABASE_NAME}' created and populated successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()