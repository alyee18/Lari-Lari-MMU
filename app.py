from flask import Flask, render_template, redirect, url_for, session, flash, request
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Necessary for session management

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/name/<name>")
def user(name):
    return f"Hello {name}!"

#--------------------------------------------------------------Buyer Page--------------------------------------------------------------------------------------
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
    session["cart"].append({"restaurant_id": restaurant_id, "item_name": item_name, "price": item_price, "quantity": quantity})

    # Save the session
    session.modified = True

    return redirect(url_for("view_cart"))

@app.route("/cart")
def view_cart():
    cart_items = session.get("cart", [])
    
    # Calculate total price and gather restaurant data
    total_price = 0
    for item in cart_items:
        restaurant_id = item['restaurant_id']
        item_price = item['price'] * item['quantity']
        total_price += item_price

    # Get restaurant names for the cart items
    restaurants_data = {r["id"]: r["name"] for r in restaurants}
    
    # Add restaurant names to cart items
    for item in cart_items:
        item['restaurant_name'] = restaurants_data.get(item['restaurant_id'], "Unknown")

    print("Session Cart Data:", session.get("cart"))  # Debugging line
    return render_template("cart.html", cart_items=cart_items, total_price=total_price, restaurants=restaurants)

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
    {"id": 1, "name": "Haji Tapah", "cuisine": "Mamak", "price_range": "2-20", "delivery_time": 30, "rating": 3.7, 
     "menu": {"Maggie Goreng": 8, "Nasi Goreng": 10, "Roti Kosong": 3, "Roti Telur": 4, "Roti Planta": 5, 
              "Roti Pisang": 6, "Teh Tarik": 4}},
    {"id": 2, "name": "STC Deen Cafe(STAD)", "cuisine": "Mamak", "price_range": "1-20", "delivery_time": 30, "rating": 3.6, 
     "menu": {"Maggie Goreng": 8, "Nasi Goreng": 10, "Roti Kosong": 3, "Roti Telur": 4, "Roti Planta": 5, 
              "Roti Pisang": 6, "Teh Tarik": 4}},
    {"id": 3, "name": "7-Eleven", "cuisine": "Convenience", "price_range": "5-30", "delivery_time": 20, "rating": 5.0, 
     "menu": {"Snacks": 2, "100 Plus": 3, "Coca Cola": 3, "Pepsi": 3, "Juice": 4, "Ice cream": 5, "Bread": 2, 
              "Instant Noodles": 3}},
    {"id": 4, "name": "Starbee", "cuisine": "Food Court", "price_range": "1-20", "delivery_time": 40, "rating": 3.8, 
     "menu": {"Shawarma": 12, "Noodle": 10, "Korea Fried Chicken Rice": 15, "Nasi Lemak": 8, "100 Plus": 3, 
              "Coca Cola": 3, "Ice Lemon Tea": 4}},
    {"id": 5, "name": "D' light bakery", "cuisine": "Bakery", "price_range": "3-20", "delivery_time": 20, "rating": 4.5, 
     "menu": {"Bread": 3, "Espresso": 5, "White Coffee": 4, "Black Coffee": 4, "Smoothies": 6}},
    {"id": 6, "name": "He & She Coffee", "cuisine": "Cafe", "price_range": "4-20", "delivery_time": 30, "rating": 5.0, 
     "menu": {"Espresso": 5, "White Coffee": 4, "Black Coffee": 4, "Cake": 6, "Cookies": 3, "Pasta": 10}},
]

@app.route("/confirm_order", methods=["POST"])
def confirm_order():
    cart_items = session.get("cart", [])
    if not cart_items:
        return redirect(url_for("view_cart"))
    
    session.pop("cart", None)  # Clear the cart
    return render_template("order_confirmation.html", message="Your order has been placed successfully!")

# ---------------------------------------------------------------Runner Page------------------------------------------------------------------------------------


if __name__ == "__main__":
    app.run(debug=True)
