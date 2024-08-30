import sqlite3

# Connect to the database
connection = sqlite3.connect('your_database.db')
cursor = connection.cursor()

# Delete the users table if it exists
cursor.execute("DROP TABLE IF EXISTS users;")

# Create the users table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        phone_no TEXT NOT NULL
    )
    """
)

# Commit the changes and close the connection
connection.commit()
connection.close()
