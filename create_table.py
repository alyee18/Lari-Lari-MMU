import sqlite3

# Function to get database connection
def get_db_connection():
        con = sqlite3.connect("database.db")
        con.row_factory = sqlite3.Row
        return con

# Connect with db
con = sqlite3.connect("database.db")
cur = con.cursor()




cur.execute(
    """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        faculty TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        phone_number TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
        )"""
)