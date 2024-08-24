from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Necessary for session management

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/name/<name>")
def user(name):
    return f"Hello {name}!"

#---------------------------------------------------------Restaurants Listing---------------------------------------------------------------------------------
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

    # Initialize cart if not present
    if "cart" not in session:
        session["cart"] = []

    # Add item to cart
    session["cart"].append({"restaurant_id": restaurant_id, "item_name": item_name, "quantity": quantity})

    # Save the session
    session.modified = True

    return redirect(url_for("view_cart"))

@app.route("/cart")
def view_cart():
    cart_items = session.get("cart", [])
    print(cart_items)  # Debugging line
    return render_template("cart.html", cart_items=cart_items)

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
    {"id": 1, "name": "Haji Tapah", "cuisine": "Mamak", "price_range": "2-20", "delivery_time": 30, "rating": 3.7, "menu": ["Maggie Goreng", "Roti Canai", "Teh Tarik"]},
    {"id": 2, "name": "STC Deen Cafe(STAD)", "cuisine": "Mamak", "price_range": "1-20", "delivery_time": 30, "rating": 3.6, "menu": ["Maggie Goreng", "Roti Canai", "Teh Tarik"]},
    {"id": 3, "name": "7-Eleven", "cuisine": "Convenience", "price_range": "5-30", "delivery_time": 20, "rating": 5.0, "menu": ["Snacks", "Beverages", "Instant Noodles"]},
    {"id": 4, "name": "Starbee", "cuisine": "Food Court", "price_range": "1-20", "delivery_time": 40, "rating": 3.8, "menu": ["(haven't found yet)"]},
    {"id": 5, "name": "D' light bakery", "cuisine": "Bakery", "price_range": "3-20", "delivery_time": 20, "rating": 4.5, "menu": ["Bread", "Espresso", "White Coffee", "Black Coffee"]},
    {"id": 6, "name": "He & She Coffee", "cuisine": "Cafe", "price_range": "4-20", "delivery_time": 30, "rating": 5.0, "menu": ["Espresso", "White Coffee", "Black Coffee", "Cake", "Cookies", "Pasta"]},
]

if __name__ == "__main__":
    app.run(debug=True)
