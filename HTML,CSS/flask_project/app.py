from flask import Flask, render_template, request, redirect, url_for, flash
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
            flash('Login successful!', 'success')
            # Redirect to another page after successful login
            return redirect(url_for('display_login'))  # Change this to your desired page
        else:
            flash('Invalid email or password!', 'danger')
        
        cursor.close()
        conn.close()

    return render_template('login.html')

# Display the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        
        # Logic to save user details to a database
        conn = get_db_connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO user_login (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('display_login'))
        except mysql.connector.Error as err:
            flash('Error creating account: {}'.format(err), 'danger')
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
