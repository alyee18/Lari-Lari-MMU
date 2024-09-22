from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
import os
import json
import sqlite3
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_socketio import SocketIO, emit
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static',
            template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY')
socketio = SocketIO(app)

def get_db_connection():
    con = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'database.db'))
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
        return {
            "home_content": "",
            "shop_name": "",
            "logo": ""
        }
    except json.JSONDecodeError:
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
        
        filename = ""
        if "logo" in request.files:
            file = request.files["logo"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        content = {
            "home_content": home_content,
            "shop_name": shop_name,
            "logo": filename
        }

        save_content(content)
        
        flash("Content updated successfully!")
        return redirect(url_for("page_editor"))
    
    return render_template("pageEditor.html")

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

    cursor.execute("SELECT COUNT(*) FROM orders")
    num_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT restaurant_name, 
               SUM(total_price) AS total_earnings, 
               COUNT(id) AS total_orders 
        FROM orders 
        GROUP BY restaurant_name
    """)
    financial_overview = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM orders")
    num_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT restaurant_name, 
               SUM(total_price) AS total_earnings, 
               COUNT(id) AS total_orders 
        FROM orders 
        GROUP BY restaurant_name
    """)
    financial_overview = cursor.fetchall()

    conn.close()

    financial_data = {
        restaurant['restaurant_name']: {
            'total_earnings': restaurant['total_earnings'],
            'total_orders': restaurant['total_orders']
        }
        for restaurant in financial_overview
    }

    return render_template(
        'admin.html',
        num_runners=num_runners,
        num_buyers=num_buyers,
        num_sellers=num_sellers,
        num_orders=num_orders,
        financial_data=financial_data
    )
    financial_data = {
        restaurant['restaurant_name']: {
            'total_earnings': restaurant['total_earnings'],
            'total_orders': restaurant['total_orders']
        }
        for restaurant in financial_overview
    }

    return render_template(
        'admin.html',
        num_runners=num_runners,
        num_buyers=num_buyers,
        num_sellers=num_sellers,
        num_orders=num_orders,
        financial_data=financial_data
    )
    
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

@app.route('/menucontrol', methods=['GET'])
def menucontrol():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, name, price, restaurant_id
        FROM menu_items
    """
    cursor.execute(query)
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('menucontrol.html', menu_items=menu_items)

@app.route('/admin/add_menu_item', methods=['GET', 'POST'])
def admin_add_menu_item():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        restaurant_name = request.form['restaurant_name']

        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO menu (name, price, restaurant_name)
            VALUES (?, ?, ?)
        """
        cursor.execute(query, (name, price, restaurant_name))
        conn.commit()
        conn.close()

        return redirect(url_for('menucontrol'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM restaurants")
    restaurants = cursor.fetchall()
    conn.close()

    return render_template('admin_add_menu_item.html', restaurants=restaurants)

@app.route('/admin/edit_menu_item/<int:item_id>', methods=['GET', 'POST'])
def edit_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        restaurant_name = request.form['restaurant_name']

        query = """
            UPDATE menu
            SET name = ?, price = ?, restaurant_name = ?
            WHERE id = ?
        """
        cursor.execute(query, (name, price, restaurant_name))
        conn.commit()
        conn.close()

        return redirect(url_for('menucontrol'))
    
    query = """
        SELECT id, name, price, restaurant_name
        FROM menu
        WHERE id = ?
    """
    cursor.execute(query)
    menu_item = cursor.fetchone()
    conn.close()

    return render_template('edit_menu_item.html', menu_item=menu_item)

@app.route('/admin/delete_menu_item/<int:menu_id>', methods=['GET'])
def admin_delete_menu_item(menu_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        DELETE FROM menu
        WHERE id = ?
    """
    cursor.execute(query, (menu_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('menu_control'))

@app.route('/ordercontrol', methods=['GET'])
def ordercontrol():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, buyer_username, restaurant_name, item_name, total_price, quantity, order_date, status
        FROM orders
    """
    cursor.execute(query)
    orders = cursor.fetchall()
    conn.close()

    return render_template('ordercontrol.html', orders=orders)

@app.route('/edit_order/<int:order_id>', methods=['GET'])
def edit_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, item_name, total_price, quantity, status
        FROM orders
        WHERE id = ?
    """
    cursor.execute(query, (order_id,))
    order = cursor.fetchone()
    conn.close()

    if order is None:
        return redirect(url_for('order_control'))

    return render_template('edit_order.html', order=order)


@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    item_name = request.form['item_name']
    total_price = float(request.form['total_price'])
    quantity = int(request.form['quantity'])
    status = request.form['status']

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        UPDATE orders
        SET item_name = ?, total_price = ?, quantity = ?, status = ?
        WHERE id = ?
    """
    cursor.execute(query, (item_name, total_price, quantity, status, order_id))
    conn.commit()
    conn.close()

    return redirect(url_for('ordercontrol'))

@app.route('/delete_order/<int:order_id>', methods=['GET'])
def delete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        DELETE FROM orders
        WHERE id = ?
    """
    cursor.execute(query, (order_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('ordercontrol'))

@app.route('/restaurantcontrol', methods=['GET'])
def restaurantcontrol():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, name, cuisine, price_range
        FROM restaurants
    """
    cursor.execute(query)
    restaurants = cursor.fetchall()
    conn.close()

    return render_template('restaurantcontrol.html', restaurants=restaurants)

@app.route('/admin/edit_restaurant/<int:restaurant_id>', methods=['GET', 'POST'])
def edit_restaurant(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        cuisine = request.form['cuisine']
        price_range = request.form['price_range']

        query = """
            UPDATE restaurants
            SET name = ?, cuisine = ?, price_range = ?
            WHERE id = ?
        """
        cursor.execute(query, (name, cuisine, price_range, restaurant_id))
        conn.commit()
        conn.close()

        return redirect(url_for('restaurantcontrol'))
    
    query = """
        SELECT id, name, cuisine, price_range
        FROM restaurants
        WHERE id = ?
    """
    cursor.execute(query, (restaurant_id,))
    restaurant = cursor.fetchone()
    conn.close()

    if restaurant is None:
        return redirect(url_for('restaurantcontrol'))

    return render_template('edit_restaurant.html', restaurant=restaurant)

@app.route('/delete_restaurant/<int:restaurant_id>', methods=['GET'])
def delete_restaurant(restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        DELETE FROM restaurants
        WHERE id = ?
    """
    cursor.execute(query, (restaurant_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('restaurantcontrol'))

######### home ##########
@app.route("/")
def index():
    content = load_content()
    return render_template("index.html", content=content)

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
    delivery_address = request.form['delivery_address']

    geolocator = Nominatim(user_agent="myApp")
    try:
        location = geolocator.geocode(delivery_address)
        if location:
            delivery_lat = location.latitude
            delivery_lng = location.longitude
        else:
            delivery_lat = None
            delivery_lng = None
            print(f"Failed to geocode address: {delivery_address}")
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Geocoding error: {e}")
        delivery_lat = None
        delivery_lng = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (buyer_username, restaurant_name, item_name, total_price, quantity, order_status, order_date, delivery_address, delivery_lat, delivery_lng)
        VALUES (?, ?, ?, ?, ?, 'available', ?, ?, ?, ?)
        """,
        (buyer_username, restaurant_name, item_name, total_price, quantity, order_date, delivery_address, delivery_lat, delivery_lng)
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

    # Determine the status to filter tasks
    if task_type == 'current':
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, delivery_address, status, order_status
            FROM orders
            WHERE order_status = 'current' AND (runner_name IS NULL OR runner_name = ?)
            """,
            (runner_name,)
        )
    else:
        cursor.execute(
            """
            SELECT id, item_name, restaurant_name, total_price, quantity, buyer_username, order_date, delivery_address, status, order_status
            FROM orders
            WHERE order_status = ? AND (runner_name IS NULL OR runner_name = ?)
            """,
            (task_type, runner_name)
        )

    tasks = cursor.fetchall()

    cursor.execute("SELECT username FROM users WHERE role = 'runner'")
    runners = cursor.fetchall()

    conn.close()

    return render_template('task_management.html', task_type=task_type, tasks=tasks, runners=runners)

@app.route('/update_status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT status, order_status FROM orders WHERE id = ?", (order_id,))
        result = cursor.fetchone()

        if result:
            current_status, order_status = result

            if order_status == 'current' and current_status == 'ready for pickup':
                cursor.execute(
                    "UPDATE orders SET status = 'picked up', runner_name = ? WHERE id = ?", 
                    (session['username'], order_id)
                )
                conn.commit()
                flash('Order successfully picked up.', 'success')
                return redirect(url_for('share_location', order_id=order_id))
            else:
                flash('Order cannot be picked up (incorrect status).', 'error')
        else:
            flash('Order not found.', 'error')

    except sqlite3.Error as e:
        print(f"Error updating order status: {e}")
        conn.rollback()
        flash('An unexpected error occurred while updating the order status.', 'error')

    finally:
        conn.close()

    return redirect(url_for('task_management', task_type='current'))

@app.route('/share_location/<int:order_id>')
def share_location(order_id):
    return render_template('share_location.html', order_id=order_id)

@socketio.on('share_location')
def handle_location(data):
    order_id = data['order_id']
    lat = data['lat']
    lng = data['lng']

    print(f"Order ID: {order_id}, Latitude: {lat}, Longitude: {lng}")

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders
                SET runner_lat = ?, runner_lng = ?
                WHERE id = ?
            ''', (lat, lng, order_id))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

    emit('location_received', {'status': 'success', 'order_id': order_id}, broadcast=True)

@app.route('/runner_location/<int:order_id>', methods=['GET'])
def runner_location(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT runner_lat, runner_lng, delivery_address_lat, delivery_address_lng
        FROM orders
        WHERE id = ?
    """
    cursor.execute(query, (order_id,))
    order = cursor.fetchone()
    conn.close()
    
    if order is None:
        return "Order not found", 404

    runner_lat = order['runner_lat']
    runner_lng = order['runner_lng']
    delivery_lat = order['delivery_address_lat']
    delivery_lng = order['delivery_address_lng']
    
    return render_template('runner_location.html', 
                           runner_lat=runner_lat, runner_lng=runner_lng,
                           delivery_lat=delivery_lat, delivery_lng=delivery_lng)

def geocode_address(address):
    geolocator = Nominatim(user_agent="myGeocoder")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

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

        if not all([name, cuisine, price_range]):
            return render_template("add_restaurant.html")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO restaurants (name, cuisine, price_range, owner_username)
                VALUES (?, ?, ?, ?)
                """,
                (name, cuisine, price_range, session["username"]),
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

def get_categories():
    return [
        {"name": "Main Course", "estimated_time": 30},
        {"name": "Desserts", "estimated_time": 10},
        {"name": "Beverages", "estimated_time": 5},
        {"name": "Snack", "estimated_time": 5},
        {"name": "Daily Necessities", "estimated_time": 5}
    ]

@app.route("/add_menu_item/<int:restaurant_id>", methods=["GET", "POST"])
@login_required(role='seller')
def add_menu_item(restaurant_id):
    if request.method == "POST":
        name = request.form.get("name")
        try:
            price = float(request.form.get("price", 0))
        except ValueError:
            flash("Invalid price entered. Please enter a valid number.", "error")
            return render_template("add_menu_item.html", restaurant_id=restaurant_id, categories=get_categories())

        category_name = request.form.get("category")

        if not name or price <= 0 or not category_name:
            flash("All fields are required, and price must be a positive number.", "error")
            return render_template("add_menu_item.html", restaurant_id=restaurant_id, categories=get_categories())

        categories = get_categories()
        estimated_time = next((category['estimated_time'] for category in categories if category['name'] == category_name), 5)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO menu_items (restaurant_id, name, price, category, estimated_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (restaurant_id, name, price, category_name, estimated_time),
            )
            conn.commit()
            flash("Menu item added successfully!", "success")
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "error")
            print(f"SQLite error: {e}")
        finally:
            conn.close()

        return redirect(url_for("restaurant_items", restaurant_id=restaurant_id))

    return render_template("add_menu_item.html", restaurant_id=restaurant_id, categories=get_categories())

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
    seller_username = session['username']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch all orders for the seller's restaurant
        cursor.execute("""
            SELECT o.id, o.buyer_username, o.restaurant_name, o.item_name, o.total_price, 
                   o.quantity, o.order_date, o.order_status, o.status
            FROM orders o
            JOIN restaurants r ON o.restaurant_name = r.name
            WHERE r.owner_username = ?
            ORDER BY o.order_date DESC
        """, (seller_username,))
        orders = cursor.fetchall()
        
        if not orders:
            print("No orders found for this seller's restaurant.")
        
    except sqlite3.Error as e:
        orders = []
        print(f"Database error: {e}")
    finally:
        conn.close()

    return render_template('seller_orders.html', orders=orders)

@app.route('/update_seller_order_status/<int:order_id>', methods=['POST'])
@login_required(role='seller')
def update_seller_order_status(order_id):
    new_status = request.form['status']

    if new_status not in ['preparing', 'ready for pickup']:
        flash('Invalid status selected.', 'error')
        return redirect(url_for('seller_orders'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT order_status FROM orders WHERE id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            flash('Order not found.', 'error')
            return redirect(url_for('seller_orders'))
        
        if order[0] == 'picked up':
            flash('Order has already been picked up. Status cannot be updated.', 'error')
            return redirect(url_for('seller_orders'))
        
        cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (new_status, order_id))
        conn.commit()

        flash('Order status updated successfully.', 'success')
    except sqlite3.Error as e:
        print(f"Error updating order status: {e}")
        flash('An error occurred while updating the order status.', 'error')
    finally:
        conn.close()

    return redirect(url_for('seller_orders'))

@app.route('/select_restaurant', methods=['POST'])
@login_required(role='seller')
def select_restaurant():
    restaurant_id = request.form.get('restaurant_id')
    if restaurant_id:
        session['restaurant_id'] = restaurant_id 
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
    delivery_address = session.get('delivery_address', 'Address not found')
    return render_template('order_confirmation.html', delivery_address=delivery_address, message="Your order has been confirmed!")
    
@app.route('/confirm_order', methods=['POST'])
@login_required(role='buyer')
def confirm_order():
    conn = None
    try:
        cart_items = session.get('cart', [])
        delivery_address = request.form.get('delivery_address')

        if not cart_items:
            flash("Cart is empty. Please add items before confirming the order.", "error")
            return redirect(url_for('view_cart'))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert each item as a separate order with its correct restaurant name
        for item in cart_items:
            restaurant_id = item.get("restaurant_id")
            item_name = item.get("item_name")
            quantity = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            item_total_price = price * quantity

            cursor.execute("SELECT name FROM restaurants WHERE id = ?", (restaurant_id,))
            restaurant_row = cursor.fetchone()

            if not restaurant_row:
                flash(f"Restaurant not found for item {item_name}.", "error")
                return redirect(url_for('view_cart'))

            restaurant_name = restaurant_row[0]

            # Insert the order with the correct restaurant name
            cursor.execute(
                """
                INSERT INTO orders (buyer_username, restaurant_name, item_name, total_price, quantity, delivery_address)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session["username"], restaurant_name, item_name, item_total_price, quantity, delivery_address)
            )

        conn.commit()
        session.pop('cart', None)  # Clear the cart after order confirmation
        session['delivery_address'] = delivery_address  # Save address to session

    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        flash(f"An error occurred: {e}", "error")
        print(f"SQLite error: {e}")

    finally:
        if conn:
            conn.close()

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
        item["restaurant_name"] = restaurants.get(item.get("restaurant_id"), "Unknown")

    order_id = 1

    return render_template("cart.html", cart_items=cart_items, total_price=total_price, order_id=order_id)

@app.route("/update_cart", methods=["POST"])
@login_required(role='buyer')
def update_cart():
    item_index = int(request.form.get('item_index'))
    new_quantity = int(request.form.get('quantity'))

    cart_items = session.get('cart', [])
    if item_index < len(cart_items):
        cart_items[item_index]['quantity'] = new_quantity
        session['cart'] = cart_items

    return redirect(url_for('view_cart'))

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
        # Fetch orders for the current buyer, including the restaurant name
        cursor.execute("""
            SELECT orders.id, orders.restaurant_name, orders.item_name, orders.total_price, orders.quantity, orders.order_status, orders.order_date, orders.delivery_address
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

@app.route('/buyer_order_details/<int:order_id>', methods=['GET'])
def buyer_order_details(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch order details
    query = """
        SELECT id, buyer_username, restaurant_name, item_name, total_price, quantity, order_date, delivery_address, delivery_lat, delivery_lng, runner_lat, runner_lng, runner_name, status, order_status
        FROM orders
        WHERE id = ?
    """
    cursor.execute(query, (order_id,))
    order = cursor.fetchone()

    if order is None:
        return redirect(url_for('buyer_orders'))

    # Fetch review details if they exist
    cursor.execute("""
        SELECT rating, review FROM order_reviews 
        WHERE order_id = ? AND buyer_username = ?
    """, (order_id, session.get('username')))
    submitted_review = cursor.fetchone()

    conn.close()

    return render_template('buyer_order_details.html', order=order, submitted_review=submitted_review)

@app.route('/submit_review/<int:order_id>', methods=['POST'])
def submit_review(order_id):
    rating = request.form['rating']
    review = request.form['review']
    buyer_username = session.get('username') 

    if not buyer_username:
        flash('You must be logged in to submit a review.', 'error')
        return redirect(url_for('buyer_order_details', order_id=order_id))

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Fetch the restaurant name and item name based on the order ID
            cursor.execute("SELECT restaurant_name, item_name FROM orders WHERE id = ?", (order_id,))
            order_details = cursor.fetchone()

            if order_details is None:
                flash('Order not found.', 'error')
                return redirect(url_for('buyer_order_details', order_id=order_id))

            restaurant_name, item_name = order_details  

            query = """
                INSERT INTO order_reviews (order_id, buyer_username, restaurant_name, item_name, rating, review)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (order_id, buyer_username, restaurant_name, item_name, rating, review))
            conn.commit()

            flash('Your review has been submitted!', 'success')
    except sqlite3.IntegrityError as e:
        flash(f'An integrity error occurred: {e}', 'error')
    except sqlite3.OperationalError as e:
        flash(f'An operational error occurred while accessing the database: {e}', 'error')
    except Exception as e:
        flash(f'An unexpected error occurred: {e}', 'error')

    return redirect(url_for('buyer_home', order_id=order_id))

if __name__ == "__main__":
    socketio.run(app, debug=True)