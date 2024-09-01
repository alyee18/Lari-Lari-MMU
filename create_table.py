import sqlite3

DATABASE = "database.db"

def createtables():
    try:
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

        # Create menu_items table without a description column
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

        # Commit the transaction and close the connection
        conn.commit()
        print("Tables created successfully!")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    createtables()
