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


#USER

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



# Logout route
@app.route('/logout')
def logout():
    session.pop('user_number', None)  # Remove user_number from session
    flash('You have been logged out!', 'success')
    return redirect(url_for('display_login'))  # Redirect to login page after logout

#ADMIN


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



# Route to display the Add New Books page
@app.route('/add_books', methods=['GET', 'POST'])
def add_books():
    if request.method == 'POST':
        # Get form data
        book_name = request.form['book_name']
        author = request.form['author']
        publisher = request.form['publisher']
        
        # Connect to the database
        conn = get_db_connect()
        cursor = conn.cursor()

        try:
            # Insert book details into the books table
            cursor.execute("""
                INSERT INTO books (book_name, authors, publisher) 
                VALUES (%s, %s, %s)
            """, (book_name, author, publisher))
            conn.commit()

            

        except mysql.connector.Error as err:
            flash(f'Error adding book: {err}', 'danger')
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

    return render_template('add_books.html')

# Route to display the User Details page
@app.route('/user_details', methods=['GET'])
def user_details():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in
    
    user_number = session['user_number']  # Get the logged-in user's number

    # Fetch user details from both user_details and user_login tables
    conn = get_db_connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.user_number, u.first_name, u.last_name, u.country, l.Email
        FROM user_details u
        JOIN user_login l ON u.user_number = l.user_number
        """)

    user_details = cursor.fetchall()  # Use fetchall() to retrieve all matching users
    
    print(f"Fetched user details: {user_details}")  # Check the fetched data

    cursor.close()
    conn.close()

    return render_template('user_details.html', user_details=user_details)


# Route to display the Transaction page
@app.route('/transaction', methods=['GET'])
def book_records():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in

    # Fetch book records from borrowed_books, books, and user_login tables
    conn = get_db_connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT bb.user_number, ul.Email, bb.book_id, b.book_name, bb.returned
        FROM borrowed_books bb
        JOIN books b ON bb.book_id = b.book_id
        JOIN user_login ul ON bb.user_number = ul.user_number
    """)

    book_records = cursor.fetchall()  # Fetch all records matching the query

    cursor.close()
    conn.close()

    return render_template('transaction.html', book_records=book_records)

# Route to display the Book Details page
@app.route('/book_details', methods=['GET'])
def book_details():
    if 'user_number' not in session:  # Check if the user is logged in
        flash('You need to log in first!', 'danger')
        return redirect(url_for('display_login'))  # Redirect to login if not logged in

    # Fetch book records from the books table
    conn = get_db_connect()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT book_id, book_name, authors, publisher
        FROM books
    """)

    book_records = cursor.fetchall()  # Fetch all records from the books table

    cursor.close()
    conn.close()

    return render_template('book_details.html', book_records=book_records)

#Logout Admin
@app.route('/admin_logout', methods=['GET'])
def admin_logout():
    session.pop('admin_logged_in', None)  # Remove the session key for admin login
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))  # Redirect to the admin login page


if __name__ == '__main__':
    app.run(debug=True)


