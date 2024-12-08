from flask import Flask, render_template, request, redirect, url_for, flash, session , jsonify
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
            flash('Successfully logged in!', 'success')
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

    user_number = session['user_number']  # Get the logged-in user's number

    # Get the count of books from the database
    conn = get_db_connect()
    cursor = conn.cursor()

    # Count the total number of books
    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]

    # Count the number of borrowed books for the logged-in user (where returned = 0)
    cursor.execute(
        "SELECT COUNT(*) FROM borrowed_books WHERE user_number = %s AND returned = 0",
        (user_number,)
    )
    borrowed_count = cursor.fetchone()[0]

    # Count the number of returned books for the logged-in user (where returned = 1)
    cursor.execute(
        "SELECT COUNT(*) FROM borrowed_books WHERE user_number = %s AND returned = 1",
        (user_number,)
    )
    returned_count = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    return render_template('home.html', book_count=book_count, borrowed_count=borrowed_count, returned_count=returned_count)




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

# Hardcoded admin credentials
ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123'

@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email and password match the admin credentials
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True  # Store admin login state in the session
            flash('Successfully logged in as admin!', 'success')
            return redirect(url_for('admin_dashboard'))  # Redirect to the admin dashboard
        else:
            flash('Invalid admin email or password!', 'danger')

    return render_template('admin_login.html')

# Admin dashboard route (after login)
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):  # Check if the admin is logged in
        flash('You need to log in as an admin first!', 'danger')
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

#display the search page

@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in
    
    conn = get_db_connect()
    cursor = conn.cursor(dictionary=True)

    books = []  # Initialize books list

    # If it's a POST request (searching or resetting)
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()  # Get the search term and strip spaces
        
        if request.form.get('reset'):  # If the reset button was pressed
            # Reset the search (clear search term)
            return redirect(url_for('search'))  # Redirect to GET request to show all books
        
        # If there’s a search term, perform the search
        if search_term:
            cursor.execute("""
                SELECT * FROM books
                WHERE book_name LIKE %s
            """, ('%' + search_term + '%',))  # Use LIKE for partial match
            books = cursor.fetchall()  # Fetch the matching books
            if not books:
                flash('No books found matching your search.', 'info')  # No results found
        else:
            flash('Please enter a search term.', 'warning')  # Flash message if no search term is entered
    else:
        cursor.execute("SELECT * FROM books")  # For GET request, get all books
        books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('search.html', books=books)  # Render the search page with the books

# Route to handle book borrowing via AJAX
@app.route('/borrow_book', methods=['POST'])
def borrow_book():
    if 'user_number' not in session:  # Check if the user is logged in
        return jsonify({'success': False, 'message': 'You need to log in first!'})

    data = request.get_json()  # Get the JSON data from the request
    book_id = data.get('book_id')
    user_number = session['user_number']  # Get the logged-in user's ID

    if not book_id:
        return jsonify({'success': False, 'message': 'No book selected!'})

    # Insert the borrowed book into the borrowed_books table
    conn = get_db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO borrowed_books (user_number, book_id, returned)
        VALUES (%s, %s, %s)
    """, (user_number, book_id, 0))  # Default returned value is 0 (not returned yet)
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'success': True})

@app.route('/return_book', methods=['POST'])
def return_book():
    if request.method == 'POST':
        borrow_id = request.form.get('borrow_id')
        if borrow_id:
            try:
                conn = get_db_connect()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE borrowed_books
                    SET returned = 1
                    WHERE borrow_id = %s AND returned = 0
                """, (borrow_id,))
                conn.commit()
                cursor.close()
                conn.close()
                return jsonify({"status": "success"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Invalid request"})




# Display the book transaction page
@app.route('/book_transaction')
def book_transaction():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in
    
    conn = get_db_connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT borrowed_books.borrow_id, books.book_name, books.authors, books.publisher, borrowed_books.returned
        FROM borrowed_books
        JOIN books ON borrowed_books.book_id = books.book_id
        WHERE borrowed_books.user_number = %s
    """, (session['user_number'],))  # Get the books borrowed by the logged-in user

    borrowed_books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('book_transaction.html', borrowed_books=borrowed_books)





# Display the about page
@app.route('/about', methods=['GET'])
def about():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in
    return render_template('about.html')  # Render about.html


# Admin logout route
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)  # Remove admin session
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_number', None)  # Remove user_number from session
    flash('You have been logged out!', 'success')
    return redirect(url_for('display_login'))  # Redirect to login page after logout

if __name__ == '__main__':
    app.run(debug=True)
