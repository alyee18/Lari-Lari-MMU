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

        # Create menu_items table with a description column
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

        # Create tasks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL
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
                total_price REAL NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (restaurant_name) REFERENCES restaurants (name)
            )
            """
        )

    # Create the order_items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                buyer_name TEXT NOT NULL,
                restaurant_name TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (rowid),
                FOREIGN KEY (restaurant_name) REFERENCES restaurants (name)
            )
            """
        )

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()
       
if __name__ == "__main__":
    createtables()