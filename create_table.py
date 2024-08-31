import sqlite3

DATABASE = "database.db"


def createtables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create user table
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
    
    # Create restaurants table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            price_range TEXT NOT NULL,
            delivery_time INTEGER NOT NULL,
            owner_username TEXT NOT NULL,
            FOREIGN KEY (owner_username) REFERENCES users(username)
        )
    """
    )

    # Create menu_items table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
    """
    )
    # Commit the transaction and close the connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    createtables()
    print("Tables created successfully!")
