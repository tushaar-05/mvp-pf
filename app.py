from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_wtf import CSRFProtect
import mysql.connector
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
csrf = CSRFProtect(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'blue_collar_marketplace',
    'port': 3306
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database and create tables if they don't exist"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS blue_collar_marketplace")
            cursor.execute("USE blue_collar_marketplace")
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    user_type ENUM('customer', 'professional') DEFAULT 'customer',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Database initialized successfully")
    except mysql.connector.Error as e:
        print(f"Database initialization error: {e}")

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def validate_phone(phone):
    """Validate phone number format"""
    # Remove any non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Basic validation for international format
    if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned_phone):
        return False, "Please enter a valid phone number"
    
    return True, "Phone number is valid"

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page route"""
    if request.method == 'POST':
        return handle_signup()
    
    # GET request - serve the signup page
    return render_template('signup.html')

def handle_signup():
    """Handle signup form submission"""
    try:
        # Get form data
        first_name = request.form.get('firstName', '').strip()
        last_name = request.form.get('lastName', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')
        terms = request.form.get('terms')
        
        # Basic validation
        if not all([first_name, last_name, email, phone, password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if not terms:
            return jsonify({'success': False, 'message': 'You must agree to the terms and conditions'})
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'message': 'Please enter a valid email address'})
        
        # Validate phone number
        phone_valid, phone_message = validate_phone(phone)
        if not phone_valid:
            return jsonify({'success': False, 'message': phone_message})
        
        # Validate password
        password_valid, password_message = validate_password(password)
        if not password_valid:
            return jsonify({'success': False, 'message': password_message})
        
        # Check if passwords match
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'})
        
        # Check if user already exists
        try:
            conn = get_db_connection()
            if not conn:
                print("Failed to get database connection")
                return jsonify({'success': False, 'message': 'Database connection error'})
            
            cursor = conn.cursor(dictionary=True)
            
            # Check for existing email
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                print(f"User with email {email} already exists")
                return jsonify({'success': False, 'message': 'An account with this email already exists'})
            
            # Check for existing phone number
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                print(f"User with phone {phone} already exists")
                return jsonify({'success': False, 'message': 'An account with this phone number already exists'})
                
        except mysql.connector.Error as e:
            print(f"Database error during user check: {e}")
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': 'Error checking user existence. Please try again.'})
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Insert new user
        try:
            conn = get_db_connection()
            if not conn:
                print("Failed to get database connection")
                return jsonify({'success': False, 'message': 'Database connection error'})
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (first_name, last_name, email, phone, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            ''', (first_name, last_name, email, phone, password_hash))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            # Store user ID in session
            session['user_id'] = user_id
            session['user_email'] = email
            session['user_name'] = f"{first_name} {last_name}"
            
            return jsonify({
                'success': True, 
                'message': 'Account created successfully! Please log in with your credentials.',
                'redirect': '/login'
            })
            
        except mysql.connector.Error as e:
            print(f"Database error during user creation: {e}")
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': 'Error creating user account. Please try again.'})
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        return jsonify({'success': False, 'message': 'Database error occurred'})
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    if request.method == 'POST':
        return handle_login()
    
    return render_template('login.html')

def handle_login():
    """Handle login form submission"""
    try:
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'})
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection error'})
        
        cursor = conn.cursor(dictionary=True)
        
        # Find user by email
        cursor.execute('''
            SELECT id, first_name, last_name, email, password_hash, user_type 
            FROM users 
            WHERE email = %s AND is_active = TRUE
        ''', (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            # Login successful
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_name'] = f"{user['first_name']} {user['last_name']}"
            session['user_type'] = user['user_type']
            
            return jsonify({
                'success': True, 
                'message': 'Login successful! Redirecting...',
                'redirect': '/dashboard'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during login'})

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return f"Welcome to your dashboard, {session['user_name']}!"

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

# API endpoint for AJAX signup (if you want to use AJAX instead of form submission)
@app.route('/api/signup', methods=['POST'])
def api_signup():
    """API endpoint for AJAX signup"""
    return handle_signup()

# API endpoint for AJAX login
@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for AJAX login"""
    return handle_login()

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)