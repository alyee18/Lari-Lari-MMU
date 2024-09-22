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
            email UNIQUE NOT NULL,
            username UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            phone_no UNIQUE NOT NULL
        )
        """
    ) 

    # Create restaurants table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            cuisine TEXT NOT NULL,
            price_range TEXT NOT NULL,
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
            category TEXT NOT NULL,
            estimated_time INTEGER NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
        )
        """
    )

    # Create the orders table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_username TEXT NOT NULL,
            restaurant_name TEXT NOT NULL,
            item_name TEXT NOT NULL,
            total_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            order_status TEXT DEFAULT 'available',
            status TEXT DEFAULT 'pending',
            runner_name TEXT,
            runner_lat REAL,
            runner_lng REAL,
            delivery_address TEXT,
            delivery_lat REAL,
            delivery_lng REAL
        )
        """
    )

    # Create trigger to adjust order_date to Malaysia time (UTC+8)
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS adjust_order_date
        AFTER INSERT ON orders
        FOR EACH ROW
        BEGIN
            UPDATE orders
            SET order_date = DATETIME(order_date, '+8 hours')
            WHERE id = NEW.id;
        END;
        """
    )

    # Create order_reviews table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS order_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            buyer_username TEXT NOT NULL,
            restaurant_name TEXT NOT NULL,
            item_name TEXT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            review TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )   
        """
    )

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()
       
if __name__ == "__main__":
    createtables()