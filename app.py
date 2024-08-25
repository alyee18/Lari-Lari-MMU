from flask import Flask, render_template, redirect, url_for, session, flash, request
import sqlite3

# Import the function to create tables
from create_table import create_tables
app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'site.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


######### home ##########
@app.route('/')
def index():
    return render_template('index.html')

######### signup ##########
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        phone_no = request.form.get('phone_no')

        # Check if all required fields are present
        if not all([name, email, username, password, role, phone_no]):
            flash('All fields are required!', 'error')
            return render_template('signup.html')
        # Check if username already exists
        if username in username:
            flash('Username already exists!', 'error')
            return render_template('signup.html')
        
        # Save the user details to your database or data structure
        # For example, add the user to a dictionary (replace this with real database code)
        username[username] = {'password': password, 'role': role}
        
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

######### login##########
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = user.get(username)

        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for(f'{user["role"]}_page'))
        else:
            flash('Invalid username or password.', 'error')

    if 'username' in session:
        return redirect(url_for(f'{session["role"]}_page'))

    return render_template('login.html')

@app.route('/restaurant')
def restaurant_page():
    if 'role' not in session or session['role'] != 'restaurant':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return 'Welcome to the Restaurant Page!'

@app.route('/buyer')
def buyer_page():
    if 'role' not in session or session['role'] != 'buyer':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return 'Welcome to the Buyer Page!'

@app.route('/runner')
def runner_page():
    if 'role' not in session or session['role'] != 'runner':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return 'Welcome to the Runner Page!'

@app.route('/admin')
def admin_page():
    if 'role' not in session or session['role'] != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return 'Welcome to the Admin Page!'

######### logout ##########
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

######### Restaurant ##########
@app.route('/restaurant')
def restaurant():

    return render_template('restaurant.html')

if __name__ == "__main__":
    app.run(debug=True)
