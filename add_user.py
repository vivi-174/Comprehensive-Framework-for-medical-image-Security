import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the database (creates users.db if it doesn't exist)
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK (role IN ('doctor', 'staff'))
    )
''')
conn.commit()

# Function to add a user
def add_user(username, password, role):
    try:
        hashed_password = generate_password_hash(password)  # Hash the password
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                       (username, hashed_password, role))
        conn.commit()
        print(f"User '{username}' added successfully as {role}.")
    except sqlite3.IntegrityError:
        print(f"Error: Username '{username}' already exists.")

# Example: Add users manually
add_user("Josh", "josh123", "doctor")  # Add doctor user
add_user("admin", "admin123", "staff")  # Add staff user

# Close the connection
conn.close()
