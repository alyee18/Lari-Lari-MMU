from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/name/<name>")
def user(name):
    return f"Hello {name}!"

@app.route("/restaurants")
def restaurant_list():
    cuisine = request.args.get("cuisine")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    max_delivery_time = request.args.get("max_delivery_time", type=int)
    min_rating = request.args.get("min_rating", type=float)

    filtered_list = filter_restaurants(
        restaurants,
        cuisine=cuisine,
        min_price=min_price,
        max_price=max_price,
        max_delivery_time=max_delivery_time,
        min_rating=min_rating
    )

    return render_template("restaurants.html", restaurants=filtered_list)

@app.route("/restaurant/<int:restaurant_id>")
def restaurant_detail(restaurant_id):
    restaurant = next((r for r in restaurants if r["id"] == restaurant_id), None)
    if restaurant:
        return render_template("restaurant_detail.html", restaurant=restaurant)
    else:
        return "Restaurant not found", 404


def filter_restaurants(restaurants, cuisine=None, min_price=None, max_price=None, max_delivery_time=None, min_rating=None):
    filtered = []
    
    for restaurant in restaurants:
        if cuisine and restaurant['cuisine'] != cuisine:
            continue
        
        if min_price or max_price:
            price_range = restaurant['price_range'].split('-')
            price_min = int(price_range[0])
            price_max = int(price_range[1])
            if (min_price and price_max < min_price) or (max_price and price_min > max_price):
                continue
        
        if max_delivery_time and restaurant['delivery_time'] > max_delivery_time:
            continue
        
        if min_rating and restaurant['rating'] < min_rating:
            continue
        
        filtered.append(restaurant)
    
    return filtered

restaurants = [
    {"id": 1, "name": "Haji Tapah", "cuisine": "Mamak", "price_range": "2-20", "delivery_time": 30, "rating": 3.7, "menu": ["Maggie Goreng", "Roti Canai", "Teh Tarik"]},
    {"id": 2, "name": "STC Deen Cafe(STAD)", "cuisine": "Cafe", "price_range": "1-20", "delivery_time": 45, "rating": 3.6, "menu": ["Maggie Goreng", "Roti Canai", "Teh Tarik"]},
    {"id": 3, "name": "7-Eleven", "cuisine": "Convenience", "price_range": "5-30", "delivery_time": 15, "rating": 5.0, "menu": ["Snacks", "Beverages", "Instant Noodles"]},
    {"id": 4, "name": "Starbee", "cuisine": "Cafe", "price_range": "1-20", "delivery_time": 60, "rating": 3.8, "menu": ["(havent find yet)"]},
    {"id": 5, "name": "D' light bakery", "cuisine": "Bakery", "price_range": "3-20", "delivery_time": 20, "rating": 4.5, "menu": ["Bread", "Espresso", "White Coffee", "Black Coffee"]},
    {"id": 6, "name": "He & She Coffee", "cuisine": "Cafe", "price_range": "4-20", "delivery_time": 25, "rating": 5.0, "menu": ["Espresso", "White Coffee", "Black Coffee", "Cake", "Cookies", "Pasta"]},
]


if __name__ == "__main__":
    app.run(debug=True)
