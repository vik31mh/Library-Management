from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'vikas',
    'host': 'localhost',
    'database': 'library_management'
}

# Connect to MySQL
def get_db_connect():
    conn = mysql.connector.connect(**db_config)
    return conn

# Display the login page
@app.route('/', methods=['GET'])
def display_login():
    return render_template('login.html')

# Handle the login form submission
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check credentials in the database
        conn = get_db_connect()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch user from database
        cursor.execute("SELECT * FROM user_login WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        # Check if user exists and verify password
        if user and user['password'] == password:
            session['user_number'] = user['user_number']  # Store user_number in session
            return redirect(url_for('home'))  # Redirect to home page
        else:
            flash('Invalid email or password!', 'danger')  # Flash only danger messages
        
        cursor.close()
        conn.close()

    return render_template('login.html')

# Display the home page
@app.route('/home', methods=['GET'])
def home():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in
    return render_template('home.html')  # Render home.html

# Display the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        country = request.form['country']
        
        # Connect to the database
        conn = get_db_connect()
        cursor = conn.cursor()

        try:
            # Check if the email already exists in user_login
            cursor.execute("SELECT * FROM user_login WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('Account already exists with this email!', 'danger')
            else:
                # Insert email and password into user_login
                cursor.execute("INSERT INTO user_login (email, password) VALUES (%s, %s)", (email, password))
                user_id = cursor.lastrowid  # Get the ID of the inserted user
                
                # Insert first name, last name, and country into user_details
                cursor.execute("INSERT INTO user_details (first_name, last_name, country, user_number_login) VALUES (%s, %s, %s, %s)", 
                               (first_name, last_name, country, user_id))
                
                conn.commit()
                flash('Account created successfully!', 'success')
                return redirect(url_for('display_login'))
        
        except mysql.connector.Error as err:
            flash(f'Error creating account: {err}', 'danger')
            conn.rollback()
        
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_number', None)  # Remove user_number from session
    flash('You have been logged out!', 'success')
    return redirect(url_for('display_login'))

if __name__ == '__main__':
    app.run(debug=True)
