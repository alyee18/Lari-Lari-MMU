from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
import os
import json
import sqlite3
import logging
logging.basicConfig(level=logging.DEBUG)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime

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

######### Admin Page Editor##########
def load_content():
    """Load content from content.json."""
    try:
        with open("content.json", "r") as content_file:
            return json.load(content_file)
    except FileNotFoundError:
        # Return default values if the file does not exist
        return {
            "home_content": "",
            "shop_name": "",
            "logo": ""
        }
    except json.JSONDecodeError:
        # Handle JSON decoding errors
        return {
            "home_content": "",
            "shop_name": "",
            "logo": ""
        }

def save_content(content):
    """Save content to content.json."""
    try:
        with open("content.json", "w") as content_file:
            json.dump(content, content_file, indent=4)
    except IOError as e:
        print(f"Error saving content: {e}")

@app.route("/pageEditor", methods=["GET", "POST"])
def page_editor():
    if request.method == "POST":
        home_content = request.form.get("home_content")
        shop_name = request.form.get("shop_name")
        
        # Handle file upload
        filename = ""
        if "logo" in request.files:
            file = request.files["logo"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Update content (ensure 'content' is defined or retrieved appropriately)
        content = {
            "home_content": home_content,
            "shop_name": shop_name,
            "logo": filename
        }
        
        # Save content (define `save_content` function or method)
        save_content(content)
        
        flash("Content updated successfully!")
        return redirect(url_for("page_editor"))
    
    return render_template("pageEditor.html")

@app.route('/change_admin_credentials', methods=['POST'])
def change_admin_credentials():
    admin_current_email = request.form.get('admin_current_email')
    admin_new_email = request.form.get('admin_email')
    admin_current_password = request.form.get('admin_current_password')
    admin_new_password = request.form.get('admin_password')

    # Example admin credentials validation and update logic
    # Ensure that the admin credentials are stored securely and hashed properly
    if admin_current_email == admin_email and admin_current_password == admin_password:
        if admin_new_email:
            admin_email = admin_new_email
        if admin_new_password:
            admin_password = admin_new_password
        # Commit changes to the database here
        # Example: db.session.commit()
        
        flash("Email and/or password updated successfully!")
    else:
        flash("Invalid email or password!")

    admin_data = {"email": admin_email, "password": admin_password}
    with open("admin.json", "w") as admin_file:
        json.dump(admin_data, admin_file)
    
    return redirect(url_for("page_editor"))

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

    cursor.execute('SELECT * FROM orders')
    orders = cursor.fetchall()

    conn.close()

    return render_template('admin.html', num_runners=num_runners, num_buyers=num_buyers, num_sellers=num_sellers, orders=orders)
    
@app.route('/usercontrol')
def user_control():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('usercontrol.html', users=users)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user is None:
        flash('User not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        if '_method' in request.form and request.form['_method'] == 'DELETE':
            # Handle DELETE request
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()

            users = conn.execute('SELECT id FROM users ORDER BY id').fetchall()
            for new_id, user in enumerate(users, start=1):
                conn.execute('UPDATE users SET id = ? WHERE id = ?', (new_id, user[0]))
            
            conn.commit()
            conn.close()
            flash('User deleted and IDs renumbered successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            # Handle POST request (update user)
            username = request.form['username']
            email = request.form['email']
            phone_no = request.form['phone_no']

            print(f"Updating user {user_id} with username: {username}, email: {email}, and phone_no: {phone_no}")
            
            conn.execute('UPDATE users SET username = ?, email = ?, phone_no = ? WHERE id = ?',
                         (username, email, phone_no, user_id))
            conn.commit()
            conn.close()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
    
    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    
    # Renumber IDs
    users = conn.execute('SELECT id FROM users ORDER BY id').fetchall()
    for new_id, user in enumerate(users, start=1):
        conn.execute('UPDATE users SET id = ? WHERE id = ?', (new_id, user['id']))
    
    conn.commit()
    conn.close()

    flash('User deleted and IDs renumbered successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/menucontrol')
def menu_control():
    conn = get_db_connection()
    menu_items = conn.execute('SELECT * FROM menu_items').fetchall()
    conn.close()
    return render_template('menucontrol.html', menu_items=menu_items)

@app.route('/admin/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        conn.execute('UPDATE menu_items SET name = ?, price = ? WHERE id = ?', (name, price, item_id))
        conn.commit()
        conn.close()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    conn.close()
    return render_template('edit_menu_item.html', item=item)

@app.route('/ordercontrol')
def order_control():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM orders')
    orders = cursor.fetchall()

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
    print(restaurants)

    return render_template('restaurantcontrol.html', restaurants=restaurants)

@app.route('/admin/edit_restaurant/<int:restaurant_id>', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id):
    conn = get_db_connection()
    restaurant = conn.execute('SELECT * FROM restaurants WHERE id = ?', (restaurant_id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        cuisine = request.form['cuisine']
        price_range = request.form['price_range']
        
        conn.execute('UPDATE restaurants SET name = ?, cuisine = ?, price_range = ? WHERE id = ?',
                     (name, cuisine, price_range, restaurant_id))
        conn.commit()
        conn.close()
        flash('Restaurant updated successfully!', 'success')
        return redirect(url_for('restaurant_control'))
    
    conn.close()
    return render_template('edit_restaurant.html', restaurant=restaurant)


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

@app.route('/runner_tasks/<runner_name>/<task_type>')
def runner_tasks(runner_name, task_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    if task_type in ['available', 'current', 'completed']:
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, runner_name
            FROM orders
            WHERE order_status = ? AND (runner_name = ? OR runner_name IS NULL)
            """,
            (task_type, runner_name)
        )
    else:
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, runner_name
            FROM orders
            WHERE runner_name = ?
            """,
            (runner_name,)
        )

    tasks = cursor.fetchall()
    
    cursor.execute("SELECT username FROM users WHERE role = 'runner'")
    runners = cursor.fetchall()

    conn.close()
    return render_template('runner_tasks.html', task_type=task_type, tasks=tasks)

@app.route('/place_order', methods=['POST'])
def place_order():
    buyer_username = request.form['buyer_username']
    restaurant_name = request.form['restaurant_name']
    item_name = request.form['item_name']
    total_price = float(request.form['total_price'])
    quantity = int(request.form['quantity'])
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO orders (buyer_username, restaurant_name, item_name, total_price, quantity, order_status, order_date)
        VALUES (?, ?, ?, ?, ?, 'available', ?)
        """,
        (buyer_username, restaurant_name, item_name, total_price, quantity, order_date)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('order_confirmation'))


@app.route('/accept_order/<int:order_id>', methods=['POST'])
def accept_order(order_id):
    runner_name = request.form.get('runner_name')
    logging.debug(f"Attempting to accept order ID {order_id} for runner {runner_name}")

    if not runner_name:
        return "Runner name is required", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
    """
    UPDATE orders
    SET order_status = 'current', runner_name = ?
    WHERE id = ?
    """,
    (runner_name, order_id)
)

    conn.commit()
    conn.close()
    return redirect(url_for('task_management', task_type='current'))

@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
    """
    UPDATE orders
    SET order_status = 'completed'
    WHERE id = ?
    """,
    (order_id,)
)

    conn.commit()
    conn.close()
    return redirect(url_for('task_management', task_type='completed'))

@app.route('/task_management/<task_type>')
def task_management(task_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    runner_name = session.get('username')

    if task_type in ['available', 'current', 'completed']:
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, runner_name, order_status
            FROM orders
            WHERE order_status = ? AND (runner_name = ? OR runner_name IS NULL)
            """,
            (task_type, runner_name)
        )
    else:
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, runner_name, order_status
            FROM orders
            WHERE runner_name = ?
            """,
            (runner_name,)
        )

    tasks = cursor.fetchall()

    cursor.execute("SELECT username FROM users WHERE role = 'runner'")
    runners = cursor.fetchall()

    conn.close()

    return render_template('task_management.html', task_type=task_type, tasks=tasks, runners=runners)

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
@login_required(role='seller')
@login_required(role='seller')
def seller_home():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE owner_username = ?", (session['username'],))
    restaurants = cursor.fetchall()
    conn.close()

    if not restaurants:
        flash("No restaurants found. Please add a restaurant.", "info")
        return redirect(url_for('add_restaurant'))

    # Set the default restaurant_id if needed
    if not session.get('restaurant_id') and restaurants:
        session['restaurant_id'] = restaurants[0]['id']

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

        # Check if all required fields are present
        if not name or price <= 0:
            flash("All fields are required and price must be positive!", "error")
            return render_template("add_menu_item.html", restaurant_id=restaurant_id)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
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
            print(f"SQLite error: {e}")
        finally:
            conn.close()

        flash("Menu item added successfully!", "success")
        return redirect(url_for("seller_home"))

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
    finally:
        conn.close()

    flash('Menu item deleted successfully!', "success")
    return redirect(url_for('restaurant_items', restaurant_id=restaurant_id))

@app.route('/restaurant_items/<int:restaurant_id>')
@login_required(role='seller')
def restaurant_items(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE id = ? AND owner_username = ?", (restaurant_id, session['username']))
    restaurant = cursor.fetchone()

    if not restaurant:
        flash("Restaurant not found or you do not have permission to view it.", "error")
        return redirect(url_for('seller_home'))

    cursor.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant_id,))
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('restaurant_items.html', restaurant=restaurant, menu_items=menu_items)

@app.route('/seller_profile')
def seller_profile():
    if session.get('role') != 'seller':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('seller_profile.html', user=user)

@app.route('/update_seller_profile', methods=['POST'])
def update_seller_profile():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('login'))

    name = request.form.get('name')
    email = request.form.get('email')
    phone_no = request.form.get('phone_no')

    if not all([name, email, phone_no]):
        flash("All fields are required.", "error")
        return redirect(url_for('seller_profile'))

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
    return redirect(url_for('seller_profile'))

@app.route('/delete_seller_account', methods=['POST'])
def delete_seller_account():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (session['username'],))
    conn.commit()
    conn.close()

    session.pop('username', None)
    session.pop('role', None)

    flash("Account deleted successfully.", "success")
    return redirect(url_for('index'))

@app.route('/progress_tracking')
def seller_progress_tracking():
    return render_template('progress_tracking.html')

@app.route('/seller_orders')
@login_required(role='seller')
def seller_orders():
    restaurant_name = session.get('restaurant_name')

    if not restaurant_name:
        flash("Restaurant name is missing. Please select a restaurant.", "error")
        return redirect(url_for('seller_home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, buyer_username, item_name, total_price, quantity, order_date, order_status
            FROM orders
            WHERE restaurant_name = ?
            ORDER BY order_date DESC
        """, (restaurant_name,))
        orders = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"An error occurred while fetching orders: {e}", "error")
        orders = []

    conn.close()

    return render_template('seller_orders.html', orders=orders)


@app.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required(role='seller')
def update_order_status_handler(order_id):
    new_status = request.form.get('order_status')

    if new_status not in ['pending', 'completed', 'canceled']:
        flash("Invalid status.", "error")
        return redirect(url_for('seller_orders'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE orders
            SET order_status = ?
            WHERE id = ?
            """,
            (new_status, order_id)
        )
        conn.commit()
        flash("Order status updated successfully!", "success")
    except sqlite3.Error as e:
        flash(f"An error occurred: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('seller_orders'))

@app.route('/select_restaurant', methods=['POST'])
@login_required(role='seller')
def select_restaurant():
    restaurant_id = request.form.get('restaurant_id')
    if restaurant_id:
        session['restaurant_id'] = restaurant_id  # Store restaurant_id in the session
    return redirect(url_for('seller_orders'))

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

@app.route('/order_confirmation')
def order_confirmation():
    return render_template('order_confirmation.html', message="Your order has been confirmed!")
    
@app.route('/confirm_order', methods=['POST'])
@login_required(role='buyer')
def confirm_order():
    conn = None
    try:
        print("Confirm Order route accessed")
        cart_items = session.get('cart', [])
        print(f"Cart items: {cart_items}")

        if not cart_items:
            flash("Cart is empty. Please add items before confirming the order.", "error")
            return redirect(url_for('view_cart'))

        restaurant_id = cart_items[0].get("restaurant_id")
        total_price = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in cart_items)
        print(f"Total price: {total_price}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the restaurant name from the database using restaurant_id
        cursor.execute("SELECT name FROM restaurants WHERE id = ?", (restaurant_id,))
        restaurant_row = cursor.fetchone()

        if not restaurant_row:
            flash("Restaurant not found.", "error")
            return redirect(url_for('view_cart'))

        restaurant_name = restaurant_row[0]
        print(f"Restaurant name from DB: {restaurant_name}")

        # Insert the order into the orders table
        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO orders (buyer_username, restaurant_name, item_name, total_price, quantity)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session["username"], restaurant_name, item["item_name"], total_price, item["quantity"])
            )

        conn.commit()
        flash("Order confirmed successfully!", "success")
        session.pop('cart', None)

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred: {e}", "error")
        print(f"SQLite error: {e}")

    finally:
        if conn:
            conn.close()

    # Ensure 'order_confirmation' is a valid endpoint
    return redirect(url_for('order_confirmation'))


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
        return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))

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

@app.route('/buyer_profile')
def buyer_profile():
    if session.get('role') != 'buyer':
        flash("You do not have permission to access this page.", "error")
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (session['username'],))
    user = cursor.fetchone()
    conn.close()

    return render_template('buyer_profile.html', user=user)

@app.route('/update_buyer_profile', methods=['POST'])
def update_buyer_profile():
    if 'username' not in session:
        flash("You need to log in to access this page.", "error")
        return redirect(url_for('login'))
    
    name = request.form.get('name')
    email = request.form.get('email')
    phone_no = request.form.get('phone_no')

    if not all([name, email, phone_no]):
        flash("All fields are required.", "error")
        return redirect(url_for('buyer_profile'))

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
    return redirect(url_for('buyer_profile'))

@app.route('/delete_buyer_account', methods=['POST'])
def delete_buyer_account():
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

@app.route('/progress_tracking')
def buyer_progress_tracking():
    return render_template('progress_tracking.html')

@app.route('/buyer_orders')
@login_required(role='buyer')
def buyer_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch orders with correct schema
        cursor.execute("""
            SELECT orders.id, orders.restaurant_name, orders.item_name,orders.total_price,orders.order_status, orders.order_date
            FROM orders
            WHERE orders.buyer_username = ?
            ORDER BY orders.order_date DESC
        """, (session['username'],))

        orders = cursor.fetchall()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        flash(f"An error occurred: {e}", "error")
        orders = []

    finally:
        conn.close()

    return render_template('buyer_orders.html', orders=orders)

if __name__ == "__main__":
    app.run(debug=True)