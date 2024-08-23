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
    return redirect(url_for('signup'))

    #render the html template with the categories data
    return render_template("signup.html")

if __name__ == "__main__":
   app.run(debug=True)




        