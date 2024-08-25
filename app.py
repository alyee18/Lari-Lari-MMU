from flask import Flask, render_template, redirect, url_for, session, flash, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"


def get_db_connection():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con


######### home ##########
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        phone_no = request.form.get("phone_no")

        # Debug: Print received data
        print(
            f"Received signup data: {name}, {email}, {username}, {password}, {role}, {phone_no}"
        )

        # Check if all required fields are present
        if not all([name, email, username, password, role, phone_no]):
            flash("All fields are required!", "error")
            return render_template("signup.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if username already exists
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already exists!", "error")
                conn.close()
                return render_template("signup.html")

            # Hash the password before storing it
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

            # Save the user details to the database
            cursor.execute(
                """
                INSERT INTO users (name, email, username, password, role, phone_no)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, email, username, hashed_password, role, phone_no),
            )
            conn.commit()
            print("User added to the database.")  # Debug: Confirm data is being added

        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "error")
            print(f"SQLite error: {e}")  # Debug: Print SQLite error message

        finally:
            conn.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


######### login ##########
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the user by username
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["role"] = user["role"]
            flash("Login successful!", "success")
            return redirect(url_for(f'{user["role"]}_page'))
        else:
            flash("Invalid username or password.", "error")

    if "username" in session:
        return redirect(url_for(f'{session["role"]}_page'))

    return render_template("login.html")


######### Role-based pages ##########
@app.route("/restaurant_page")
def restaurant_page():
    if "role" not in session or session["role"] != "restaurant":
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("login"))
    return "Welcome to the Restaurant Page!"


@app.route("/buyer_page")
def buyer_page():
    if "role" not in session or session["role"] != "buyer":
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("login"))
    return "Welcome to the Buyer Page!"


@app.route("/runner_page")
def runner_page():
    if "role" not in session or session["role"] != "runner":
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("login"))
    return "Welcome to the Runner Page!"


@app.route("/admin_page")
def admin_page():
    if "role" not in session or session["role"] != "admin":
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for("login"))
    return "Welcome to the Admin Page!"


######### logout ##########
@app.route("/logout" , methods=["GET" , "POST"])
def logout():
    session.pop("username", None)
    session.pop("password", None)
    flash("You have been logged out successully.", "info")

    return render_template("logout.html")

######### Delete User ##########
@app.route("/delete_user/<username>", methods=["POST"])
def delete_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    flash(f"User {username} has been deleted.", "info")
    return redirect(url_for("admin_page"))

######### Admin Page ##########
@app.route("/admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template("admin.html", users=users)

######### Restaurant page ##########
@app.route("/restaurants")
def restaurants():
    return render_template("restaurants.html")

if __name__ == "__main__":
    app.run(debug=True)