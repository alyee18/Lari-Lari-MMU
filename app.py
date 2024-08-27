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

        #Clear session data to avoid unwanted redirects
        session.pop("username", None)
        session.pop("role", None)

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
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    if "username" in session:
        return redirect(url_for("index"))

    return render_template("login.html")


######### logout ##########
@app.route("/logout", methods=["GET", "POST"])
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


######### Buyer Page ##########
@app.route("/restaurants")
def restaurant_list():
    # Directly pass the full list of restaurants
    return render_template("restaurants.html", restaurants=restaurants)


@app.route("/restaurant/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)
    if restaurant:
        return render_template("restaurant_detail.html", restaurant=restaurant)
    else:
        return "Restaurant not found", 404


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    restaurant_id = int(request.form.get("restaurant_id"))
    item_name = request.form.get("item_name")
    quantity = int(request.form.get("quantity", 1))

    # Find the restaurant to get the item price
    restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)
    if restaurant is None:
        return "Restaurant not found", 404

    item_price = restaurant["menu"].get(item_name, 0)  # Default to 0 if item not found

    # Initialize cart if not present
    if "cart" not in session:
        session["cart"] = []

    # Add item to cart
    session["cart"].append(
        {
            "restaurant_id": restaurant_id,
            "item_name": item_name,
            "price": item_price,
            "quantity": quantity,
        }
    )

    # Save the session
    session.modified = True

    return redirect(url_for("view_cart"))


@app.route("/cart")
def view_cart():
    cart_items = session.get("cart", [])

    # Calculate total price and gather restaurant data
    total_price = 0
    for item in cart_items:
        restaurant_id = item["restaurant_id"]
        item_price = item["price"] * item["quantity"]
        total_price += item_price

    # Get restaurant names for the cart items
    restaurants_data = {r["id"]: r["name"] for r in restaurants}

    # Add restaurant names to cart items
    for item in cart_items:
        item["restaurant_name"] = restaurants_data.get(item["restaurant_id"], "Unknown")

    print("Session Cart Data:", session.get("cart"))  # Debugging line
    return render_template(
        "cart.html",
        cart_items=cart_items,
        total_price=total_price,
        restaurants=restaurants,
    )


@app.route("/update_cart", methods=["POST"])
def update_cart():
    item_index = int(request.form.get("item_index"))
    quantity = int(request.form.get("quantity"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"][item_index]["quantity"] = quantity
            session.modified = True  # Ensure the session is saved

    return redirect(url_for("view_cart"))


@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_index = int(request.form.get("item_index"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"].pop(item_index)
            session.modified = True  # Ensure the session is saved

    return redirect(url_for("view_cart"))


restaurants = [
    {
        "id": 1,
        "name": "Haji Tapah",
        "cuisine": "Mamak",
        "price_range": "2-20",
        "delivery_time": 30,
        "rating": 3.7,
        "menu": {
            "Maggie Goreng": 8,
            "Nasi Goreng": 10,
            "Roti Kosong": 3,
            "Roti Telur": 4,
            "Roti Planta": 5,
            "Roti Pisang": 6,
            "Teh Tarik": 4,
        },
    },
    {
        "id": 2,
        "name": "STC Deen Cafe(STAD)",
        "cuisine": "Mamak",
        "price_range": "1-20",
        "delivery_time": 30,
        "rating": 3.6,
        "menu": {
            "Maggie Goreng": 8,
            "Nasi Goreng": 10,
            "Roti Kosong": 3,
            "Roti Telur": 4,
            "Roti Planta": 5,
            "Roti Pisang": 6,
            "Teh Tarik": 4,
        },
    },
    {
        "id": 3,
        "name": "7-Eleven",
        "cuisine": "Convenience",
        "price_range": "5-30",
        "delivery_time": 20,
        "rating": 5.0,
        "menu": {
            "Snacks": 2,
            "100 Plus": 3,
            "Coca Cola": 3,
            "Pepsi": 3,
            "Juice": 4,
            "Ice cream": 5,
            "Bread": 2,
            "Instant Noodles": 3,
        },
    },
    {
        "id": 4,
        "name": "Starbee",
        "cuisine": "Food Court",
        "price_range": "1-20",
        "delivery_time": 40,
        "rating": 3.8,
        "menu": {
            "Shawarma": 12,
            "Noodle": 10,
            "Korea Fried Chicken Rice": 15,
            "Nasi Lemak": 8,
            "100 Plus": 3,
            "Coca Cola": 3,
            "Ice Lemon Tea": 4,
        },
    },
    {
        "id": 5,
        "name": "D' light bakery",
        "cuisine": "Bakery",
        "price_range": "3-20",
        "delivery_time": 20,
        "rating": 4.5,
        "menu": {
            "Bread": 3,
            "Espresso": 5,
            "White Coffee": 4,
            "Black Coffee": 4,
            "Smoothies": 6,
        },
    },
    {
        "id": 6,
        "name": "He & She Coffee",
        "cuisine": "Cafe",
        "price_range": "4-20",
        "delivery_time": 30,
        "rating": 5.0,
        "menu": {
            "Espresso": 5,
            "White Coffee": 4,
            "Black Coffee": 4,
            "Cake": 6,
            "Cookies": 3,
            "Pasta": 10,
        },
    },
]


@app.route("/confirm_order", methods=["POST"])
def confirm_order():
    cart_items = session.get("cart", [])
    if not cart_items:
        return redirect(url_for("view_cart"))

    session.pop("cart", None)  # Clear the cart
    return render_template(
        "order_confirmation.html", message="Your order has been placed successfully!"
    )


# ---------------------------------------------------------------Runner Page------------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)