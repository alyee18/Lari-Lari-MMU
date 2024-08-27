from flask import Flask, render_template, redirect, url_for, session, request, flash
import sqlite3
import create_table  # Import the module for database operations

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with your actual secret key

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(create_table.DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# Home Page for Buyers
@app.route("/")
def index():
    return render_template("index.html")

# Home Page for Sellers
@app.route("/seller")
def index_restaurant():
    return render_template("index_restaurant.html")

# Route to create a new restaurant (Seller page)
@app.route("/add_restaurant", methods=["GET", "POST"])
def add_restaurant():
    if request.method == "POST":
        name = request.form["name"]
        cuisine = request.form["cuisine"]
        price_range = request.form["price_range"]
        delivery_time = request.form["delivery_time"]
        rating = request.form["rating"]
        owner_id = request.form["owner_id"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO restaurants (name, cuisine, price_range, delivery_time, rating, owner_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, cuisine, price_range, delivery_time, rating, owner_id)
        )
        conn.commit()
        conn.close()

        flash("Restaurant added successfully!")
        return redirect(url_for("index_restaurant"))

    return render_template("add_restaurant.html")

# Route to create a new menu item for a specific restaurant (Seller page)
@app.route("/add_menu_item", methods=["GET", "POST"])
def add_menu_item():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        restaurant_id = request.form["restaurant_id"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO menu_items (name, price, restaurant_id)
            VALUES (?, ?, ?)
            """,
            (name, price, restaurant_id)
        )
        conn.commit()
        conn.close()

        flash("Menu item added successfully!")
        return redirect(url_for("index_restaurant"))

    # Fetch the list of restaurants to populate the dropdown menu
    conn = get_db_connection()
    restaurants = conn.execute("SELECT id, name FROM restaurants").fetchall()
    conn.close()

    return render_template("add_menu_item.html", restaurants=restaurants)

# Buyer Pages
@app.route("/restaurants")
def restaurant_list():
    conn = get_db_connection()
    restaurants = conn.execute("SELECT * FROM restaurants").fetchall()
    conn.close()
    return render_template("restaurants.html", restaurants=restaurants)

@app.route("/restaurant/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    conn = get_db_connection()
    restaurant = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
    menu_items = conn.execute("SELECT * FROM menu_items WHERE restaurant_id = ?", (restaurant_id,)).fetchall()
    conn.close()
    
    if restaurant:
        return render_template("restaurant_detail.html", restaurant=restaurant, menu_items=menu_items)
    else:
        return "Restaurant not found", 404

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    restaurant_id = int(request.form.get("restaurant_id"))
    item_name = request.form.get("item_name")
    quantity = int(request.form.get("quantity", 1))

    conn = get_db_connection()
    item = conn.execute("SELECT * FROM menu_items WHERE name = ? AND restaurant_id = ?", 
                        (item_name, restaurant_id)).fetchone()
    conn.close()

    if item is None:
        return "Item not found", 404

    item_price = item["price"]

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append({"restaurant_id": restaurant_id, "item_name": item_name, "price": item_price, "quantity": quantity})
    session.modified = True

    return redirect(url_for("view_cart"))

@app.route("/cart")
def view_cart():
    cart_items = session.get("cart", [])
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    conn = get_db_connection()
    restaurants = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM restaurants").fetchall()}
    conn.close()

    for item in cart_items:
        item['restaurant_name'] = restaurants.get(item['restaurant_id'], "Unknown")

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/update_cart", methods=["POST"])
def update_cart():
    item_index = int(request.form.get("item_index"))
    quantity = int(request.form.get("quantity"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"][item_index]["quantity"] = quantity
            session.modified = True

    return redirect(url_for("view_cart"))

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    item_index = int(request.form.get("item_index"))

    if "cart" in session:
        if 0 <= item_index < len(session["cart"]):
            session["cart"].pop(item_index)
            session.modified = True

    return redirect(url_for("view_cart"))

@app.route("/confirm_order", methods=["POST"])
def confirm_order():
    cart_items = session.get("cart", [])
    if not cart_items:
        return redirect(url_for("view_cart"))
    
    session.pop("cart", None)
    return render_template("order_confirmation.html", message="Your order has been placed successfully!")

# Functions to add data to the database
def add_restaurant(name, cuisine, price_range, delivery_time, rating, owner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO restaurants (name, cuisine, price_range, delivery_time, rating, owner_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, cuisine, price_range, delivery_time, rating, owner_id)
    )
    conn.commit()
    conn.close()

def add_menu_item(name, price, restaurant_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO menu_items (name, price, restaurant_id)
        VALUES (?, ?, ?)
        """,
        (name, price, restaurant_id)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Ensure the tables are created before running the app
    create_table.create_tables()
    
    # Example usage: Uncomment to add a restaurant and its menu items
    # add_restaurant("Haji Tapah", "Mamak", "2-20", 30, 3.7, owner_id=1)
    # add_menu_item("Maggie Goreng", 8, restaurant_id=1)
    # add_menu_item("Nasi Goreng", 10, restaurant_id=1)
    
    app.run(debug=True)
