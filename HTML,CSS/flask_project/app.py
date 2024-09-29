from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Display the login page
@app.route('/', methods=['GET'])
def display_login():
    return render_template('login.html')

# Handle the login form submission
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Capture the email from the form
        email = request.form['email']
        
        # Here, you can add your logic to check the email, authenticate, etc.
        if email == 'admin@example.com':
            flash('Login successful!', 'success')
            return redirect(url_for('display_login'))
        else:
            flash('Invalid email!', 'danger')
            return redirect(url_for('display_login'))
    
    # If it's a GET request, show the login page
    return render_template('login.html')

# Display the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Capture the user details from the form
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        country = request.form['country']
        
        # Here, you can add logic to save the user details to a database
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('display_login'))
    
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
