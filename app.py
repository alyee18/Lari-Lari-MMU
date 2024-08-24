from flask import Flask, render_template, redirect, url_for, session, flash, request

app = Flask(__name__)
app.secret_key = 'your_secret_key'

######### signup ##########
@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        phone_no = request.form['phone_no']
   
    #redirect a success template after processing
    flash('Signup successful! Please log in.', 'success')
    return redirect(url_for('login'))

    #render the html template with the categories data
    return render_template("signup.html")

######### login ##########
@app.route('/login' , methods=['POST'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = user.get(username)

        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect(url_for(f'{user["role"]}_page'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/seller')
def seller_page():
    if 'role' not in session or session['role'] != 'seller':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('login'))
    return 'Welcome to the Seller Page!'

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

if __name__ == "__main__":
    app.run(debug=True)




        