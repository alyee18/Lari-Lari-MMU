from flask import Flask, render_template, redirect, url_for, session, flash, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

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

@app.route('/runner_home')
def runner_home():
    if session.get('role') != 'runner':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    return render_template('runner_home.html')

@app.route('/seller_home')
def seller_home():
    if session.get('role') != 'seller':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    
    # Fetch the seller's restaurants
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE owner_username = ?", (session['username'],))
    restaurants = cursor.fetchall()
    conn.close()

    # Pass the restaurants to the template
    return render_template('seller_home.html', restaurants=restaurants)


@app.route('/buyer_home')
def buyer_home():
    if session.get('role') != 'buyer':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    return render_template('buyer_home.html')

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                flash("You need to log in to access this page.", "error")
                return redirect(url_for('login'))

            if role and session.get('role') != role:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

######### signup ##########
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
            
            # Redirect based on the user's role
            if user["role"] == "seller":
                return redirect(url_for("seller_home"))
            elif user["role"] == "runner":
                return redirect(url_for("runner_home"))
            elif user["role"] == "buyer":
                return redirect(url_for("buyer_home"))
            else:
                return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "error")

    if "username" in session:
        role = session.get("role")
        if role == "seller":
            return redirect(url_for("seller_home"))
        elif role == "runner":
            return redirect(url_for("runner_home"))
        elif role == "buyer":
            return redirect(url_for("buyer_home"))
        else:
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
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM restaurants")
    restaurants = cursor.fetchall()
    conn.close()

    return render_template("restaurants.html", restaurants=restaurants)

@app.route("/confirm_order", methods=["POST"])
@login_required(role='buyer')
def confirm_order():
    cart_items = session.get("cart", [])

    if not cart_items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("view_cart"))

    session.pop("cart", None)

    flash("Your order has been confirmed!", "success")
    return redirect(url_for("index"))

@app.route("/restaurant/<int:restaurant_id>")
@login_required(role='buyer')
def restaurant_detail(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the restaurant details
        cursor.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,))
        restaurant = cursor.fetchone()

        if not restaurant:
            return "Restaurant not found", 404

        # Fetch the menu items for the restaurant
        cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant_id,))
        menu_items = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return "An error occurred", 500

    finally:
        conn.close()

    return render_template("restaurant_detail.html", restaurant=restaurant, menu_items=menu_items)

@app.route("/add_to_cart", methods=["POST"])
@login_required(role='buyer')
def add_to_cart():
    restaurant_id = request.form.get("restaurant_id")
    item_name = request.form.get("item_name")
    quantity = request.form.get("quantity")

    if not restaurant_id or not item_name or not quantity:
        flash("Missing data. Please check your form.", "error")
        return redirect(url_for("restaurant_list"))

    restaurant_id = int(restaurant_id)
    quantity = int(quantity)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ? AND name = ?", (restaurant_id, item_name))
    menu_item = cursor.fetchone()
    conn.close()

    if menu_item:
        item_price = menu_item["price"]

        if "cart" not in session:
            session["cart"] = []

        session["cart"].append(
            {
                "restaurant_id": restaurant_id,
                "item_name": item_name,
                "price": item_price,
                "quantity": quantity,
            }
        )

        session.modified = True
        return redirect(url_for("view_cart"))
    else:
        flash("Item not found", "error")
        return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))

@app.route("/cart")
@login_required(role='buyer')
def view_cart():
    cart_items = session.get("cart", [])
    total_price = sum(item["price"] * item["quantity"] for item in cart_items)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all restaurants to be used in the template
    cursor.execute("SELECT id, name FROM restaurants")
    restaurants = {row["id"]: row["name"] for row in cursor.fetchall()}

    conn.close()

    # Add restaurant names to cart items
    for item in cart_items:
        item["restaurant_name"] = restaurants.get(item["restaurant_id"], "Unknown")

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/update_cart", methods=["POST"])
@login_required(role='buyer')
def update_cart():
    item_index = int(request.form.get("item_index"))
    quantity = int(request.form.get("quantity"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"][item_index]["quantity"] = quantity
            session.modified = True

    return redirect(url_for("view_cart"))


@app.route("/remove_from_cart", methods=["POST"])
@login_required(role='buyer')
def remove_from_cart():
    item_index = int(request.form.get("item_index"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"].pop(item_index)
            session.modified = True

    return redirect(url_for("view_cart"))


######### Seller Page ##########

@app.route("/add_restaurant", methods=["GET", "POST"])
@login_required(role='seller')
def add_restaurant():
    if request.method == "POST":
        name = request.form.get("name")
        cuisine = request.form.get("cuisine")
        price_range = request.form.get("price_range")
        delivery_time = int(request.form.get("delivery_time", 0))

        if not all([name, cuisine, price_range]) or delivery_time <= 0:
            flash("All fields are required and delivery time must be positive!", "error")
            return render_template("add_restaurant.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO restaurants (name, cuisine, price_range, delivery_time, owner_username)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, cuisine, price_range, delivery_time, session["username"]),
            )
            conn.commit()
            restaurant_id = cursor.lastrowid

        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "error")
            print(f"SQLite error: {e}")

        finally:
            conn.close()

        flash("Restaurant added successfully! You can now add menu items.", "success")
        return redirect(url_for("add_menu_item", restaurant_id=restaurant_id))

    return render_template("add_restaurant.html")

@app.route("/add_menu_item/<int:restaurant_id>", methods=["GET", "POST"])
@login_required(role='seller')
def add_menu_item(restaurant_id):
    if request.method == "POST":
        name = request.form.get("name")
        price = float(request.form.get("price", 0))

        # Debug: Print received data
        print(f"Received menu item data: {name}, {price}, {restaurant_id}")

        # Check if all required fields are present
        if not name or price <= 0:
            flash("All fields are required and price must be positive!", "error")
            return render_template("add_menu_item.html", restaurant_id=restaurant_id)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Save the menu item details to the database
            cursor.execute(
                """
                INSERT INTO menu_items (restaurant_id, name, price)
                VALUES (?, ?, ?)
                """,
                (restaurant_id, name, price),
            )
            conn.commit()

        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "error")
            print(f"SQLite error: {e}")  # Debug: Print SQLite error message

        finally:
            conn.close()

        flash("Menu item added successfully!", "success")
        return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))

    return render_template("add_menu_item.html", restaurant_id=restaurant_id)

@app.route('/restaurant_items/<int:restaurant_id>')
@login_required(role='seller')
def restaurant_items(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the restaurant details
    cursor.execute("SELECT * FROM restaurants WHERE id = ? AND owner_username = ?", (restaurant_id, session['username']))
    restaurant = cursor.fetchone()

    if not restaurant:
        flash("Restaurant not found or you do not have permission to view it.", "error")
        return redirect(url_for('seller_home'))

    # Fetch the menu items for the restaurant
    cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant_id,))
    menu_items = cursor.fetchall()

    conn.close()

    return render_template('restaurant_items.html', restaurant=restaurant, menu_items=menu_items)

if __name__ == "__main__":
    app.run(debug=True)