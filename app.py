from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
   return "Hello! this is the main page <h1>HELLO<h1>"

@app.route("/name>")
def user(name):
   return f"Hello {name}!"

@app.route("signin")
    def signin(name)

#----------------------------------------------------------- Restruant Listing----------------------------------------------------------------------------------

def filter_restaurants(restaurants, cuisine=None, min_price=None, max_price=None, max_delivery_time=None, min_rating=None):
    filtered = []
    
    for restaurant in restaurants:
        # Check cuisine type
        if cuisine and restaurant['cuisine'] != cuisine:
            continue
        
        # Check price range
        if min_price or max_price:
            price_range = restaurant['price_range'].split('-')
            price_min = int(price_range[0])
            price_max = int(price_range[1])
            if (min_price and price_max < min_price) or (max_price and price_min > max_price):
                continue
        
        # Check delivery time
        if max_delivery_time and restaurant['delivery_time'] > max_delivery_time:
            continue
        
        # Check rating
        if min_rating and restaurant['rating'] < min_rating:
            continue
        
        filtered.append(restaurant)
    
    return filtered
# type of restaurants
restaurants = [
    {"name": "Haji Tapah", "cuisine": "Mamak", "price_range": "2-20", "delivery_time": 30, "rating": 3.7 },
    {"name": "STC Deen Cafe(STAD)", "cuisine": "Cafe", "price_range": "1-20", "delivery_time": 45, "rating": 3.6},
    {"name": "7-Eleven", "cuisine": "Convenience", "price_range": "5-30", "delivery_time": 15, "rating": 5.0},
    {"name": "Starbee", "cuisine": "Cafe", "price_range": "1-20", "delivery_time": 60, "rating": 3.8},
    {"name": "D' light bakery", "cuisine": "Bakery", "price_range": "3-20", "delivery_time": 20, "rating": 4.5},
    {"name": "He & She Coffee", "cuisine": "Cafe", "price_range": "4-20", "delivery_time": 25, "rating": 5.0},
]

# Filter example
filtered_list = filter_restaurants(
    restaurants,
    cuisine="Cafe",
    min_price=1,
    max_price=20,
    max_delivery_time=30,
    min_rating=4.0
)

for r in filtered_list:
    print(r)



if __name__ == "__main__":
   app.run()
