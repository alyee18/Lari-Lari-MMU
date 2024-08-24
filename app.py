from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

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
    return redirect(url_for('login'))

    #render the html template with the categories data
    return render_template("signup.html")

if __name__ == "__main__":
   app.run(debug=True)

######### login ##########
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login' , methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    user = user.get(username)

    if user and user['password'] == password:
        session['username'] = username
        session['role'] =user['role']

        if user['role'] =='seller':
            return redirect(url_for('seller_page'))
        elif user ['role'] =='runner':
            return redirect(url_for('runner_page'))
        elif user ['role'] =='buyer':
            return redirect(url_for('buyer_page'))
        elif user ['role'] =='admin':
            return redirect(url_for('admin_page'))
    else:
        return redirect(url_for('index',_external=True, category='danger'))
    
@app.route('/seller')
def seller_page():
    if 'username' not in session:
        return redirect(url_for('index', message='Please log in to access this page.'))
    elif session.get('role') != 'seller':
        return redirect(url_for('index', message='You do not have permission to access this page.'))
    return 'Welcome to the Seller Page!'

@app.route('/runner')
def runner_page():
    if 'username' not in session:
        return redirect(url_for('index', message='Please log in to access this page.'))
    elif session.get('role') != 'runner':
        return redirect(url_for('index', message='You do not have permission to access this page.'))
    return 'Welcome to the Runner Page!'

@app.route('/buyer')
def seller_page():
    if 'username' not in session:
        return redirect(url_for('index', message='Please log in to access this page.'))
    elif session.get('role') != 'buyer':
        return redirect(url_for('index', message='You do not have permission to access this page.'))
    return 'Welcome to the Buyer Page!'

@app.route('/admin')
def seller_page():
    if 'username' not in session:
        return redirect(url_for('index', message='Please log in to access this page.'))
    elif session.get('role') != 'admin':
        return redirect(url_for('index', message='You do not have permission to access this page.'))
    return 'Welcome to the Admin Page!'

if __name__ == "__main__":
   app.run(debug=True)





        