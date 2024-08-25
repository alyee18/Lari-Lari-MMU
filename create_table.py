import sqlite3

DATABASE = 'database.db'

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # create  user table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            phone_no TEXT NOT NULL 
        )
    ''')

 # Commit the transaction and close the connection
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
    print("Tables created successfully!")


