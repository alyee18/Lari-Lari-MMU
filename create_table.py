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
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        phone_no TEXT NOT NULL 
        )"""
)

# Commit the transaction and close the connection
con.commit()
con.close()

print("Table created successfully.")

