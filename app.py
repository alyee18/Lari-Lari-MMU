from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
import json
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"

def get_db_connection():
    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row
    return con

def get_tasks(task_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE task_type = ?", (task_type,))
    tasks = cursor.fetchall()

    conn.close()
    return tasks

######### Admin ##########
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid username or password.')

    return render_template('admin_login.html')

@app.route('/api/dashboard_data')
def dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM orders')
    num_orders = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "runner"')
    num_runners = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "buyer"')
    num_buyers = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "seller"')
    num_sellers = cursor.fetchone()[0]

    conn.close()

    data = {
        'num_orders': num_orders,
        'num_runners': num_runners,
        'num_buyers': num_buyers,
        'num_sellers': num_sellers
    }

    return jsonify(data)

@app.route('/admin')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'runner'")
    num_runners = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'buyer'")
    num_buyers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'seller'")
    num_sellers = cursor.fetchone()[0]

    cursor.execute("SELECT id, buyer, seller, item_name, quantity, total_price, status FROM orders")
    orders = cursor.fetchall()

    conn.close()

    return render_template('admin.html', num_runners=num_runners, num_buyers=num_buyers, num_sellers=num_sellers, orders=orders)
    
@app.route('/usercontrol')
def user_control():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('usercontrol.html', users=users)

@app.route('/menucontrol')
def menu_control():
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM menu_items').fetchall()
    conn.close()
    return render_template('menucontrol.html', menu_items=menu_items)

@app.route('/ordercontrol')
def order_control():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('ordercontrol.html', orders=orders)

@app.route('/updateorderstatus/<int:order_id>', methods=('GET', 'POST'))
def update_order_status(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    
    if request.method == 'POST':
        status = request.form['status']
        conn.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
        conn.commit()
        conn.close()
        return redirect('/ordercontrol')
    
    conn.close()
    return render_template('update_order_status.html', order=order)

@app.route('/restaurantcontrol')
def restaurant_control():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, cuisine, price_range FROM restaurants")
    restaurants = cursor.fetchall()
    conn.close()

    return render_template('restaurantcontrol.html', restaurants=restaurants)

######### home ##########
@app.route("/")
def index():
    return render_template("index.html")

######### Runner ##########
@app.route('/runner_home')
def runner_home():
    if session.get('role') != 'runner':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    return render_template('runner_home.html')

@app.route('/task_management/<task_type>')
def task_management(task_type):
    task_list = get_tasks(task_type)

    task_list = [{'id': task['id'], 'description': task['description']} for task in task_list]

    return render_template('task_management.html', tasks=task_list, task_type=task_type)

@app.route('/progress_tracking')
def progress_tracking():
    return render_template('progress_tracking.html')

@app.route('/runner_profile')
def runner_profile():
    if session.get('role') != 'runner':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('runner_profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone_no = request.form.get('phone_no')

    if not all([name, email, phone_no]):
        flash("All fields are required.", "error")
        return redirect(url_for('runner_profile'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET name = ?, email = ?, phone_no = ?
        WHERE username = ?
        """,
        (name, email, phone_no, session['username'])
    )
    conn.commit()
    conn.close()

    flash("Profile updated successfully.", "success")
    return redirect(url_for('runner_profile'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE username = ?",
        (session['username'],)
    )
    conn.commit()
    conn.close()

    session.pop('username', None)
    session.pop('role', None)

    flash("Account deleted successfully.", "success")
    return redirect(url_for('index'))

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
                return render_template("signup.html")
            
            cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash('Email already registered.')
                return redirect(url_for('signup'))
        
            cursor.execute("SELECT 1 FROM users WHERE phone_no = ?", (phone_no,))
            if cursor.fetchone():
                flash('Phone number already registered.')
                return redirect(url_for('signup'))

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

            print(f"Logged in as: {username}")
            print(f"User role: {session['role']}")
            
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
            print("Invalid credentials")

    if "username" in session:
        role = session.get("role")
        print(f"Redirecting based on role: {role}")
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
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            conn = get_db_connection()  
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user[0], password):
                # Clear session data
                session.pop("username", None)
                session.pop("role", None)

                flash("You have been logged out successfully.", "info")
                return redirect(url_for("index"))
            else:
                flash("Invalid username or password.", "error")
        else:
            flash("Both username and password are required.", "error")

    return render_template("logout.html")

######### SellerPage ##########
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
        return redirect(url_for("seller_home"))  # Redirect to seller's home page

    return render_template("add_menu_item.html", restaurant_id=restaurant_id)

@app.route('/restaurant/<int:restaurant_id>/menu/update/<int:item_id>', methods=['POST'])
@login_required(role='seller')
def update_menu_item(restaurant_id, item_id):
    name = request.form['name']
    price = request.form['price']

    try:
        price = float(price)
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError as ve:
        flash(f"Invalid price: {ve}", "error")
        return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

    if not name:
        flash("Item name is required!", "error")
        return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE menu_items
            SET name = ?, price = ?
            WHERE id = ? AND restaurant_id = ?
            """,
            (name, price, item_id, restaurant_id),
        )
        conn.commit()

    except sqlite3.Error as e:
        flash(f"An error occurred: {e}", "error")
        print(f"SQLite error: {e}")
        return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

    finally:
        conn.close()

    flash('Menu item updated successfully!', "success")
    return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

@app.route('/restaurant/<int:restaurant_id>/menu/delete/<int:item_id>', methods=['POST'])
@login_required(role='seller')
def delete_menu_item(restaurant_id, item_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM menu_items WHERE id = ? AND restaurant_id = ?",
            (item_id, restaurant_id)
        )
        conn.commit()

    except sqlite3.Error as e:
        flash(f"An error occurred: {e}", "error")
        print(f"SQLite error: {e}")
        return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

    finally:
        conn.close()

    flash('Menu item deleted successfully!', "success")
    return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

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

######### Buyer Page ##########
@app.route('/buyer_home')
@login_required(role='buyer')
def buyer_home():
    if session.get('role') != 'buyer':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    return render_template('buyer_home.html')

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

if __name__ == "__main__":
    app.run(debug=True)