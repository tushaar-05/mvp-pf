from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_wtf import CSRFProtect
import mysql.connector
import re
import os
import uuid
from datetime import datetime
from collections import Counter
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
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

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

STATUS_CONFIG = {
    'new': {'label': 'New', 'badge_class': 'status-new'},
    'waiting': {'label': 'Waiting', 'badge_class': 'status-waiting'},
    'assigned': {'label': 'Assigned', 'badge_class': 'status-assigned'},
    'progress': {'label': 'In Progress', 'badge_class': 'status-progress'},
    'completed': {'label': 'Completed', 'badge_class': 'status-completed'},
    'cancelled': {'label': 'Cancelled', 'badge_class': 'status-cancelled'},
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
            
            # Professional profiles table (extends users table)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_profiles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL UNIQUE,
                    gender ENUM('male', 'female', 'other'),
                    street_address TEXT,
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pincode VARCHAR(10),
                    profile_photo VARCHAR(255),
                    work_radius_km INT DEFAULT 10,
                    bio TEXT,
                    experience_years ENUM('0-1', '2-5', '6-10', '10+'),
                    skill_level ENUM('beginner', 'intermediate', 'expert'),
                    hourly_rate DECIMAL(10,2),
                    is_verified BOOLEAN DEFAULT FALSE,
                    verification_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Professional services table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_services (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professional_id INT NOT NULL,
                    primary_service VARCHAR(100) NOT NULL,
                    sub_service VARCHAR(200) NOT NULL,
                    base_price DECIMAL(10,2),
                    price_type ENUM('fixed', 'hourly', 'square_feet') DEFAULT 'fixed',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professional_id) REFERENCES professional_profiles(id) ON DELETE CASCADE
                )
            ''')
            
            # Professional availability table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_availability (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professional_id INT NOT NULL,
                    day_of_week ENUM('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'),
                    start_time TIME,
                    end_time TIME,
                    is_available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professional_id) REFERENCES professional_profiles(id) ON DELETE CASCADE
                )
            ''')
            
            # Professional languages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_languages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professional_id INT NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professional_id) REFERENCES professional_profiles(id) ON DELETE CASCADE
                )
            ''')
            
            # Professional documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professional_id INT NOT NULL,
                    document_type ENUM('government_id_front', 'government_id_back', 'address_proof', 'pan_card', 'portfolio', 'police_verification'),
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    file_size INT,
                    mime_type VARCHAR(100),
                    is_verified BOOLEAN DEFAULT FALSE,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professional_id) REFERENCES professional_profiles(id) ON DELETE CASCADE
                )
            ''')
            
            # Professional portfolio table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS professional_portfolio (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    professional_id INT NOT NULL,
                    image_name VARCHAR(255) NOT NULL,
                    image_path VARCHAR(500) NOT NULL,
                    caption TEXT,
                    display_order INT DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (professional_id) REFERENCES professional_profiles(id) ON DELETE CASCADE
                )
            ''')

            # Customer gigs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_gigs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    address_line1 VARCHAR(255),
                    address_line2 VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pincode VARCHAR(12),
                    assigned_professional_id INT NULL,
                    accepted_at TIMESTAMP NULL,
                    status ENUM('new', 'waiting', 'assigned', 'progress', 'completed', 'cancelled') DEFAULT 'new',
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (assigned_professional_id) REFERENCES professional_profiles(id) ON DELETE SET NULL
                )
            ''')

            # Ensure legacy tables have address columns
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS address_line1 VARCHAR(255) AFTER category
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS address_line2 VARCHAR(255) AFTER address_line1
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS city VARCHAR(100) AFTER address_line2
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS state VARCHAR(100) AFTER city
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS pincode VARCHAR(12) AFTER state
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS assigned_professional_id INT NULL AFTER pincode
            ''')
            cursor.execute('''
                ALTER TABLE customer_gigs
                ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP NULL AFTER assigned_professional_id
            ''')

            # Gig activity timeline
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gig_activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    gig_id INT,
                    user_id INT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (gig_id) REFERENCES customer_gigs(id) ON DELETE SET NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Saved addresses
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_addresses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    label ENUM('home', 'work', 'other') DEFAULT 'home',
                    address_line1 VARCHAR(255),
                    address_line2 VARCHAR(255),
                    city VARCHAR(100),
                    state VARCHAR(100),
                    pincode VARCHAR(12),
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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


def normalize_address_label(label):
    """Normalize address label to allowed values"""
    allowed_labels = {'home', 'work', 'other'}
    normalized = (label or 'home').strip().lower()
    return normalized if normalized in allowed_labels else 'other'


def get_user_addresses(user_id, limit=None):
    """Return saved addresses for a user"""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, label, address_line1, address_line2, city, state, pincode, is_default, created_at
            FROM customer_addresses
            WHERE user_id = %s
            ORDER BY is_default DESC, created_at DESC
        """
        params = [user_id]
        if limit:
            query += " LIMIT %s"
            params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall() or []
        return rows
    except mysql.connector.Error as exc:
        print(f"Address fetch error: {exc}")
        return []
    finally:
        cursor.close()
        conn.close()


def allowed_file(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        
        # Create directory if it doesn't exist
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        return filename
    return None


def format_datetime_display(value, fmt='%b %d, %Y'):
    """Format datetime objects for display"""
    if not value:
        return ''
    if isinstance(value, datetime):
        return value.strftime(fmt)
    return str(value)


def format_relative_time(value):
    """Return human readable relative time"""
    if not value:
        return ''

    if isinstance(value, datetime):
        base = datetime.now(tz=value.tzinfo) if value.tzinfo else datetime.utcnow()
        delta = base - value
    else:
        return str(value)

    seconds = max(int(delta.total_seconds()), 0)
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    return value.strftime('%b %d, %Y')


def build_initials(first_name='', last_name='', fallback_name=''):
    """Create initials from provided name parts"""
    name_parts = []
    if first_name:
        name_parts.append(first_name.strip())
    if last_name:
        name_parts.append(last_name.strip())
    if not name_parts and fallback_name:
        name_parts = fallback_name.strip().split()
    initials = ''.join([part[0].upper() for part in name_parts if part][:2])
    return initials or 'U'


def get_customer_dashboard_data(user_id, session_user=None):
    """Fetch dashboard data for a customer"""
    fallback_full_name = session_user.get('full_name') if session_user else ''
    fallback_email = session_user.get('email') if session_user else ''

    data = {
        'user': {
            'id': user_id,
            'first_name': '',
            'last_name': '',
            'full_name': fallback_full_name,
            'email': fallback_email,
            'phone': '',
            'initials': build_initials(fallback_name=fallback_full_name)
        },
        'stats': {
            'active_gigs': 0,
            'in_progress_services': 0,
            'completed_gigs': 0,
            'pending_approvals': 0
        },
        'gigs': [],
        'activities': [],
        'addresses': [],
        'status_counts': {
            'all': 0,
            'new': 0,
            'in_progress': 0,
            'completed': 0
        }
    }

    conn = get_db_connection()
    if not conn:
        return data

    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch user profile
        cursor.execute(
            "SELECT id, first_name, last_name, email, phone FROM users WHERE id = %s",
            (user_id,)
        )
        user_row = cursor.fetchone()
        if user_row:
            full_name = f"{user_row.get('first_name', '').strip()} {user_row.get('last_name', '').strip()}".strip()
            user_row['full_name'] = full_name or fallback_full_name
            user_row['initials'] = build_initials(user_row.get('first_name'), user_row.get('last_name'), fallback_name=fallback_full_name)
            data['user'].update(user_row)

        # Stats
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN status IN ('new', 'waiting', 'assigned', 'progress') THEN 1 ELSE 0 END), 0) AS active_gigs,
                COALESCE(SUM(CASE WHEN status IN ('assigned', 'progress') THEN 1 ELSE 0 END), 0) AS in_progress_services,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_gigs,
                COALESCE(SUM(CASE WHEN status = 'waiting' THEN 1 ELSE 0 END), 0) AS pending_approvals
            FROM customer_gigs
            WHERE user_id = %s
        """, (user_id,))
        stats_row = cursor.fetchone()
        if stats_row:
            data['stats'].update({key: int(value or 0) for key, value in stats_row.items()})

        # Recent gigs
        cursor.execute("""
            SELECT id, title, description, category, status, posted_at, updated_at
            FROM customer_gigs
            WHERE user_id = %s
            ORDER BY posted_at DESC
            LIMIT 10
        """, (user_id,))
        gig_rows = cursor.fetchall() or []
        status_counter = Counter()
        for gig in gig_rows:
            status_key = gig.get('status', 'new')
            status_counter.update([status_key])
            gig['status_meta'] = STATUS_CONFIG.get(status_key, STATUS_CONFIG['new'])
            gig['posted_at_display'] = format_datetime_display(gig.get('posted_at'))
            gig['posted_at_relative'] = format_relative_time(gig.get('posted_at'))
            data['gigs'].append(gig)
        data['status_counts']['all'] = len(gig_rows)
        data['status_counts']['new'] = status_counter.get('new', 0)
        data['status_counts']['in_progress'] = status_counter.get('assigned', 0) + status_counter.get('progress', 0)
        data['status_counts']['completed'] = status_counter.get('completed', 0)

        # Recent activity
        cursor.execute("""
            SELECT gal.id, gal.message, gal.created_at, cg.title
            FROM gig_activity_logs gal
            LEFT JOIN customer_gigs cg ON cg.id = gal.gig_id
            WHERE gal.user_id = %s
            ORDER BY gal.created_at DESC
            LIMIT 5
        """, (user_id,))
        activity_rows = cursor.fetchall() or []
        for activity in activity_rows:
            activity['timestamp_display'] = format_relative_time(activity.get('created_at'))
            activity['created_at_display'] = format_datetime_display(activity.get('created_at'), '%b %d, %Y %I:%M %p')
            data['activities'].append(activity)

        # Saved addresses
        cursor.execute("""
            SELECT id, label, address_line1, address_line2, city, state, pincode, is_default, created_at
            FROM customer_addresses
            WHERE user_id = %s
            ORDER BY is_default DESC, created_at DESC
            LIMIT 3
        """, (user_id,))
        address_rows = cursor.fetchall() or []
        for address in address_rows:
            data['addresses'].append(address)

    except mysql.connector.Error as exc:
        print(f"Dashboard data fetch error: {exc}")
    finally:
        cursor.close()
        conn.close()

    if not data['user'].get('initials'):
        data['user']['initials'] = build_initials(
            data['user'].get('first_name'),
            data['user'].get('last_name'),
            fallback_name=data['user'].get('full_name', '')
        )

    return data


def get_user_settings_data(user_id, session_user=None):
    """Fetch data required for the user settings page"""
    fallback_full_name = session_user.get('full_name') if session_user else ''
    fallback_email = session_user.get('email') if session_user else ''

    data = {
        'user': {
            'id': user_id,
            'first_name': '',
            'last_name': '',
            'full_name': fallback_full_name,
            'email': fallback_email,
            'phone': '',
        },
        'addresses': []
    }

    conn = get_db_connection()
    if not conn:
        return data

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, first_name, last_name, email, phone, created_at FROM users WHERE id = %s",
            (user_id,)
        )
        user_row = cursor.fetchone()
        if user_row:
            full_name = f"{user_row.get('first_name', '').strip()} {user_row.get('last_name', '').strip()}".strip()
            user_row['full_name'] = full_name or fallback_full_name
            user_row['created_at_display'] = format_datetime_display(user_row.get('created_at'))
            data['user'].update(user_row)

        cursor.execute("""
            SELECT id, label, address_line1, address_line2, city, state, pincode, is_default, created_at
            FROM customer_addresses
            WHERE user_id = %s
            ORDER BY is_default DESC, created_at DESC
        """, (user_id,))
        data['addresses'] = cursor.fetchall() or []
    except mysql.connector.Error as exc:
        print(f"Settings data fetch error: {exc}")
    finally:
        cursor.close()
        conn.close()

    if not data['user'].get('full_name'):
        data['user']['full_name'] = fallback_full_name

    return data


def get_professional_dashboard_data(user_id, session_user=None):
    """Fetch dashboard data for a professional"""
    fallback_full_name = session_user.get('full_name') if session_user else ''
    fallback_email = session_user.get('email') if session_user else ''

    data = {
        'user': {
            'id': user_id,
            'first_name': '',
            'last_name': '',
            'full_name': fallback_full_name,
            'email': fallback_email,
            'phone': '',
        },
        'profile': {
            'city': '',
            'state': '',
            'pincode': '',
            'experience_years': '',
            'skill_level': '',
            'bio': '',
        },
        'stats': {
            'total_earnings': 0,
            'active_jobs': 0,
            'new_requests': 0,
            'rating': 0.0,
            'reviews_count': 0,
        },
        'services': [],
        'requests': [],
        'active_jobs_list': [],
        'completed_jobs': [],
        'schedule': [],
        'reviews': [],
    }

    conn = get_db_connection()
    if not conn:
        return data

    cursor = conn.cursor(dictionary=True)
    try:
        # Basic user info
        cursor.execute(
            "SELECT id, first_name, last_name, email, phone FROM users WHERE id = %s",
            (user_id,),
        )
        user_row = cursor.fetchone()
        if user_row:
            full_name = f"{user_row.get('first_name', '').strip()} {user_row.get('last_name', '').strip()}".strip()
            user_row['full_name'] = full_name or fallback_full_name
            data['user'].update(user_row)

        # Professional profile (use * to be tolerant to schema differences)
        cursor.execute(
            "SELECT * FROM professional_profiles WHERE user_id = %s",
            (user_id,),
        )
        prof_row = cursor.fetchone() or {}
        prof_id = prof_row.get('id')
        if prof_row:
            data['profile'].update({
                'city': prof_row.get('city', ''),
                'state': prof_row.get('state', ''),
                'pincode': prof_row.get('pincode', ''),
                'experience_years': prof_row.get('experience_years', ''),
                'skill_level': prof_row.get('skill_level', ''),
                'bio': prof_row.get('bio', ''),
            })

            if prof_id:
                cursor.execute(
                    """
                    SELECT primary_service, sub_service, base_price, price_type
                    FROM professional_services
                    WHERE professional_id = %s
                    """,
                    (prof_id,),
                )
                data['services'] = cursor.fetchall() or []

        if prof_id:
            # Stats derived from gigs
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN assigned_professional_id = %s AND status IN ('assigned', 'progress') THEN 1 ELSE 0 END), 0) AS active_jobs,
                    COALESCE(SUM(CASE WHEN status IN ('new', 'waiting') AND (assigned_professional_id IS NULL OR assigned_professional_id = 0) THEN 1 ELSE 0 END), 0) AS new_requests,
                    COALESCE(SUM(CASE WHEN assigned_professional_id = %s AND status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_jobs
                FROM customer_gigs
                """,
                (prof_id, prof_id),
            )
            stats_row = cursor.fetchone() or {}
            data['stats']['active_jobs'] = int(stats_row.get('active_jobs', 0) or 0)
            data['stats']['new_requests'] = int(stats_row.get('new_requests', 0) or 0)
            data['stats']['completed_jobs'] = int(stats_row.get('completed_jobs', 0) or 0)

            # Open requests (unassigned gigs)
            cursor.execute(
                """
                SELECT
                    cg.id,
                    cg.title,
                    cg.description,
                    cg.category,
                    cg.posted_at,
                    cg.address_line1,
                    cg.address_line2,
                    cg.city,
                    cg.state,
                    cg.pincode,
                    CONCAT(u.first_name, ' ', u.last_name) AS customer_name
                FROM customer_gigs cg
                JOIN users u ON u.id = cg.user_id
                WHERE cg.status IN ('new', 'waiting') AND (cg.assigned_professional_id IS NULL OR cg.assigned_professional_id = 0)
                ORDER BY cg.posted_at DESC
                LIMIT 10
                """
            )
            request_rows = cursor.fetchall() or []
            for req in request_rows:
                req['requested_at_display'] = format_datetime_display(req.get('posted_at'))
                req['requested_at_relative'] = format_relative_time(req.get('posted_at'))
            data['requests'] = request_rows

            # Active jobs for this professional
            cursor.execute(
                """
                SELECT
                    cg.id,
                    cg.title,
                    cg.description,
                    cg.category,
                    cg.status,
                    cg.updated_at,
                    cg.address_line1,
                    cg.city,
                    cg.state,
                    CONCAT(u.first_name, ' ', u.last_name) AS customer_name
                FROM customer_gigs cg
                JOIN users u ON u.id = cg.user_id
                WHERE cg.assigned_professional_id = %s AND cg.status IN ('assigned', 'progress')
                ORDER BY cg.updated_at DESC
                """,
                (prof_id,),
            )
            active_jobs = cursor.fetchall() or []
            for job in active_jobs:
                status_meta = STATUS_CONFIG.get(job.get('status', 'assigned'), STATUS_CONFIG['new'])
                job['status_label'] = status_meta.get('label', job.get('status', '').title())
                job['status_badge_class'] = status_meta.get('badge_class')
                job['scheduled_for_display'] = format_datetime_display(job.get('updated_at'))
            data['active_jobs_list'] = active_jobs

            # Completed jobs history
            cursor.execute(
                """
                SELECT
                    cg.id,
                    cg.title,
                    cg.category,
                    cg.updated_at,
                    CONCAT(u.first_name, ' ', u.last_name) AS customer_name
                FROM customer_gigs cg
                JOIN users u ON u.id = cg.user_id
                WHERE cg.assigned_professional_id = %s AND cg.status = 'completed'
                ORDER BY cg.updated_at DESC
                LIMIT 5
                """,
                (prof_id,),
            )
            data['completed_jobs'] = cursor.fetchall() or []

    except mysql.connector.Error as exc:
        print(f"Professional dashboard data fetch error: {exc}")
    finally:
        cursor.close()
        conn.close()

    return data
# ========== REGULAR USER ROUTES ==========

@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@app.route('/get-started')
def get_started():
    """Friendly alias used across the marketing site"""
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Customer signup page route"""
    if request.method == 'POST':
        return handle_signup()
    
    # GET request - serve the signup page
    return render_template('signup.html')

def handle_signup():
    """Handle customer signup form submission"""
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


@app.route('/professional/login', methods=['GET', 'POST'])
def professional_login():
    """Professional login page route"""
    if request.method == 'POST':
        return handle_login()

    return render_template('professional_login.html')

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
            
            # Redirect based on user type
            redirect_url = '/professional/dashboard' if user['user_type'] == 'professional' else '/dashboard'
            
            return jsonify({
                'success': True, 
                'message': 'Login successful! Redirecting...',
                'redirect': redirect_url
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid email or password'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during login'})

@app.route('/dashboard')
def dashboard():
    """Customer dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    session_user = {
        'full_name': session.get('user_name', ''),
        'email': session.get('user_email', '')
    }

    dashboard_data = get_customer_dashboard_data(session['user_id'], session_user=session_user)

    return render_template(
        'user_dashboard.html',
        user=dashboard_data['user'],
        stats=dashboard_data['stats'],
        gigs=dashboard_data['gigs'],
        activities=dashboard_data['activities'],
        addresses=dashboard_data['addresses'],
        status_counts=dashboard_data['status_counts'],
        status_config=STATUS_CONFIG
    )


@app.route('/settings')
def user_settings():
    """User settings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    session_user = {
        'full_name': session.get('user_name', ''),
        'email': session.get('user_email', '')
    }

    settings_data = get_user_settings_data(session['user_id'], session_user=session_user)

    return render_template(
        'user_settings.html',
        user=settings_data['user'],
        addresses=settings_data['addresses'],
        success_message=request.args.get('success'),
        error_message=request.args.get('error')
    )


@app.route('/settings/profile', methods=['POST'])
def update_user_profile():
    """Handle profile updates from settings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()

    if not all([first_name, last_name, email, phone]):
        return redirect(url_for('user_settings', error='All profile fields are required.'))

    # Basic validation
    if not re.match(r"^[a-zA-Z\s\-']+$", first_name):
        return redirect(url_for('user_settings', error='Please enter a valid first name.'))
    if not re.match(r"^[a-zA-Z\s\-']+$", last_name):
        return redirect(url_for('user_settings', error='Please enter a valid last name.'))
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return redirect(url_for('user_settings', error='Please enter a valid email address.'))

    phone_valid, phone_message = validate_phone(phone)
    if not phone_valid:
        return redirect(url_for('user_settings', error=phone_message))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('user_settings', error='Unable to update profile right now. Please try again later.'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM users WHERE email = %s AND id != %s",
            (email, session['user_id'])
        )
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', error='Another account already uses this email.'))

        cursor.execute("""
            UPDATE users
            SET first_name = %s,
                last_name = %s,
                email = %s,
                phone = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (first_name, last_name, email, phone, session['user_id']))

        conn.commit()
        cursor.close()
        conn.close()

        session['user_name'] = f"{first_name} {last_name}".strip()
        session['user_email'] = email

        return redirect(url_for('user_settings', success='Profile updated successfully.'))

    except mysql.connector.Error as exc:
        print(f"Profile update error: {exc}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return redirect(url_for('user_settings', error='Unable to save changes due to a database error.'))


@app.route('/settings/password', methods=['POST'])
def update_user_password():
    """Handle password updates from settings page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not all([current_password, new_password, confirm_password]):
        return redirect(url_for('user_settings', error='Please fill out all password fields.'))

    if new_password != confirm_password:
        return redirect(url_for('user_settings', error='New passwords do not match.'))

    valid_password, password_message = validate_password(new_password)
    if not valid_password:
        return redirect(url_for('user_settings', error=password_message))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('user_settings', error='Unable to update password right now. Please try again later.'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
        user_row = cursor.fetchone()

        if not user_row or not check_password_hash(user_row['password_hash'], current_password):
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', error='Current password is incorrect.'))

        new_password_hash = generate_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
            (new_password_hash, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('user_settings', success='Password updated successfully.'))

    except mysql.connector.Error as exc:
        print(f"Password update error: {exc}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return redirect(url_for('user_settings', error='Unable to change password due to a database error.'))


@app.route('/settings/address', methods=['POST'])
def create_customer_address():
    """Create a new saved address"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    label = normalize_address_label(request.form.get('label', 'home'))
    address_line1 = request.form.get('address_line1', '').strip()
    address_line2 = request.form.get('address_line2', '').strip()
    city = request.form.get('city', '').strip()
    state = request.form.get('state', '').strip()
    pincode = request.form.get('pincode', '').strip()
    is_default = request.form.get('is_default') == 'on'

    if not all([address_line1, city, state, pincode]):
        return redirect(url_for('user_settings', error='Please complete all required address fields.'))

    if len(pincode) < 4 or len(pincode) > 12:
        return redirect(url_for('user_settings', error='Please enter a valid postal code.'))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('user_settings', error='Unable to save address right now. Please try later.'))

    try:
        cursor = conn.cursor()
        if is_default:
            cursor.execute(
                "UPDATE customer_addresses SET is_default = FALSE WHERE user_id = %s",
                (session['user_id'],)
            )

        cursor.execute(
            """
            INSERT INTO customer_addresses (
                user_id, label, address_line1, address_line2, city, state, pincode, is_default
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session['user_id'],
                label,
                address_line1,
                address_line2,
                city,
                state,
                pincode,
                is_default
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('user_settings', success='Address added successfully.'))
    except mysql.connector.Error as exc:
        print(f"Address creation error: {exc}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return redirect(url_for('user_settings', error='Unable to add address due to a database error.'))


@app.route('/settings/address/<int:address_id>', methods=['POST'])
def update_customer_address(address_id):
    """Update, delete, or set default for an address"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    action = request.form.get('action', 'update')
    conn = get_db_connection()
    if not conn:
        return redirect(url_for('user_settings', error='Unable to update address right now. Please try later.'))

    try:
        cursor = conn.cursor(dictionary=True)

        if action == 'delete':
            cursor.execute(
                "DELETE FROM customer_addresses WHERE id = %s AND user_id = %s",
                (address_id, session['user_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', success='Address removed successfully.'))

        if action == 'default':
            cursor.execute(
                "SELECT id FROM customer_addresses WHERE id = %s AND user_id = %s",
                (address_id, session['user_id'])
            )
            address = cursor.fetchone()
            if not address:
                cursor.close()
                conn.close()
                return redirect(url_for('user_settings', error='Address not found.'))

            cursor.execute(
                "UPDATE customer_addresses SET is_default = FALSE WHERE user_id = %s",
                (session['user_id'],)
            )
            cursor.execute(
                "UPDATE customer_addresses SET is_default = TRUE WHERE id = %s AND user_id = %s",
                (address_id, session['user_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', success='Default address updated.'))

        # Update flow
        label = normalize_address_label(request.form.get('label', 'home'))
        address_line1 = request.form.get('address_line1', '').strip()
        address_line2 = request.form.get('address_line2', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        is_default = request.form.get('is_default') == 'on'

        if not all([address_line1, city, state, pincode]):
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', error='Please complete all required address fields.'))

        if len(pincode) < 4 or len(pincode) > 12:
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', error='Please enter a valid postal code.'))

        cursor.execute(
            "SELECT id FROM customer_addresses WHERE id = %s AND user_id = %s",
            (address_id, session['user_id'])
        )
        address = cursor.fetchone()
        if not address:
            cursor.close()
            conn.close()
            return redirect(url_for('user_settings', error='Address not found.'))

        if is_default:
            cursor.execute(
                "UPDATE customer_addresses SET is_default = FALSE WHERE user_id = %s",
                (session['user_id'],)
            )

        cursor.execute(
            """
            UPDATE customer_addresses
            SET label = %s,
                address_line1 = %s,
                address_line2 = %s,
                city = %s,
                state = %s,
                pincode = %s,
                is_default = %s,
                updated_at = NOW()
            WHERE id = %s AND user_id = %s
            """,
            (
                label,
                address_line1,
                address_line2,
                city,
                state,
                pincode,
                is_default,
                address_id,
                session['user_id']
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('user_settings', success='Address updated successfully.'))

    except mysql.connector.Error as exc:
        print(f"Address update error: {exc}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return redirect(url_for('user_settings', error='Unable to update address due to a database error.'))


@app.route('/gigs/new', methods=['GET', 'POST'])
def create_gig():
    """Create a new customer gig"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    addresses = get_user_addresses(user_id)
    session_user = {
        'full_name': session.get('user_name', ''),
        'email': session.get('user_email', '')
    }
    user_context = {
        'full_name': session_user['full_name'],
        'email': session_user['email'],
        'initials': build_initials(fallback_name=session_user['full_name'])
    }

    def pick_default_address_id():
        for addr in addresses:
            if addr.get('is_default'):
                return str(addr['id'])
        return str(addresses[0]['id']) if addresses else ''

    if request.method == 'GET':
        return render_template(
            'create_gig.html',
            addresses=addresses,
            selected_address_id=pick_default_address_id(),
            user=user_context
        )

    # POST: handle gig creation
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', '').strip()
    selected_address_id = request.form.get('address_id', '').strip()

    if not title or not category:
        error = 'Title and category are required.'
        return render_template(
            'create_gig.html',
            error=error,
            form=request.form,
            addresses=addresses,
            selected_address_id=selected_address_id or pick_default_address_id(),
            user=user_context
        )

    selected_address = None
    if selected_address_id:
        selected_address = next(
            (addr for addr in addresses if str(addr['id']) == selected_address_id),
            None
        )

    allow_new_address = len(addresses) == 0
    if not selected_address and not allow_new_address:
        error = 'Please select one of your saved service addresses.'
        return render_template(
            'create_gig.html',
            error=error,
            form=request.form,
            addresses=addresses,
            selected_address_id=selected_address_id or pick_default_address_id(),
            user=user_context
        )

    new_address_data = None
    if not selected_address:
        address_line1 = request.form.get('address_line1', '').strip()
        address_line2 = request.form.get('address_line2', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()

        if not all([address_line1, city, state, pincode]):
            error = 'Please add your service address details to continue.'
            return render_template(
                'create_gig.html',
                error=error,
                form=request.form,
                addresses=addresses,
                selected_address_id=selected_address_id,
                user=user_context
            )

        if len(pincode) < 4 or len(pincode) > 12:
            error = 'Please enter a valid postal code.'
            return render_template(
                'create_gig.html',
                error=error,
                form=request.form,
                addresses=addresses,
                selected_address_id=selected_address_id,
                user=user_context
            )

        new_address_data = {
            'label': 'home',
            'address_line1': address_line1,
            'address_line2': address_line2,
            'city': city,
            'state': state,
            'pincode': pincode,
            'is_default': True
        }

    conn = get_db_connection()
    if not conn:
        error = 'Database connection error. Please try again.'
        return render_template(
            'create_gig.html',
            error=error,
            form=request.form,
            addresses=addresses,
            selected_address_id=selected_address_id or pick_default_address_id(),
            user=user_context
        )

    try:
        cursor = conn.cursor()
        if new_address_data:
            cursor.execute(
                '''
                INSERT INTO customer_addresses (
                    user_id, label, address_line1, address_line2, city, state, pincode, is_default
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                (
                    user_id,
                    new_address_data['label'],
                    new_address_data['address_line1'],
                    new_address_data['address_line2'],
                    new_address_data['city'],
                    new_address_data['state'],
                    new_address_data['pincode'],
                    new_address_data['is_default']
                )
            )
            new_address_id = cursor.lastrowid
            selected_address = {
                'id': new_address_id,
                'address_line1': new_address_data['address_line1'],
                'address_line2': new_address_data['address_line2'],
                'city': new_address_data['city'],
                'state': new_address_data['state'],
                'pincode': new_address_data['pincode']
            }

        cursor.execute(
            '''
            INSERT INTO customer_gigs (
                user_id, title, description, category,
                address_line1, address_line2, city, state, pincode
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''',
            (
                user_id, title, description, category,
                selected_address['address_line1'],
                selected_address.get('address_line2'),
                selected_address['city'],
                selected_address['state'],
                selected_address['pincode']
            ),
        )
        gig_id = cursor.lastrowid

        # Optional: log activity
        cursor.execute(
            '''
            INSERT INTO gig_activity_logs (gig_id, user_id, message)
            VALUES (%s, %s, %s)
            ''',
            (gig_id, session['user_id'], f'Gig "{title}" created'),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('dashboard') + '#gigs')

    except mysql.connector.Error as e:
        print(f"Gig creation DB error: {e}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        error = 'Unable to create gig due to a database error.'
        return render_template(
            'create_gig.html',
            error=error,
            form=request.form,
            addresses=addresses,
            selected_address_id=selected_address_id or pick_default_address_id(),
            user=user_context
        )

@app.route('/professional/dashboard')
def professional_dashboard():
    """Professional dashboard"""
    if 'user_id' not in session or session.get('user_type') != 'professional':
        return redirect(url_for('login'))

    session_user = {
        'full_name': session.get('user_name', ''),
        'email': session.get('user_email', ''),
    }

    dashboard_data = get_professional_dashboard_data(session['user_id'], session_user=session_user)

    return render_template(
        'professional_dashboard.html',
        user=dashboard_data['user'],
        profile=dashboard_data['profile'],
        stats=dashboard_data['stats'],
        services=dashboard_data['services'],
        requests=dashboard_data['requests'],
        active_jobs=dashboard_data['active_jobs_list'],
        completed_jobs=dashboard_data['completed_jobs'],
        schedule=dashboard_data['schedule'],
        reviews=dashboard_data['reviews'],
    )


@app.route('/professional/gigs/<int:gig_id>/accept', methods=['POST'])
def accept_customer_gig(gig_id):
    """Allow a professional to accept an open customer gig"""
    if 'user_id' not in session or session.get('user_type') != 'professional':
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('professional_dashboard'))

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM professional_profiles WHERE user_id = %s",
            (session['user_id'],)
        )
        prof_row = cursor.fetchone()
        if not prof_row:
            cursor.close()
            conn.close()
            return redirect(url_for('professional_dashboard'))

        prof_id = prof_row['id']
        cursor.execute(
            """
            SELECT id, user_id, title, status, assigned_professional_id
            FROM customer_gigs
            WHERE id = %s
            """,
            (gig_id,)
        )
        gig_row = cursor.fetchone()
        if not gig_row:
            cursor.close()
            conn.close()
            return redirect(url_for('professional_dashboard'))

        cursor.execute(
            """
            UPDATE customer_gigs
            SET assigned_professional_id = %s,
                status = 'assigned',
                accepted_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
              AND status IN ('new', 'waiting')
              AND (assigned_professional_id IS NULL OR assigned_professional_id = 0)
            """,
            (prof_id, gig_id)
        )

        if cursor.rowcount == 0:
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('professional_dashboard'))

        cursor.execute(
            """
            INSERT INTO gig_activity_logs (gig_id, user_id, message)
            VALUES (%s, %s, %s)
            """,
            (gig_id, session['user_id'], f'Gig "{gig_row.get("title", "")}" accepted by professional')
        )

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('professional_dashboard') + '#active-jobs')

    except mysql.connector.Error as exc:
        print(f"Gig acceptance error: {exc}")
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
        return redirect(url_for('professional_dashboard'))

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

# ========== PROFESSIONAL SIGNUP ROUTES ==========

@app.route('/professional/signup', methods=['GET'])
def professional_signup():
    """Professional signup page"""
    return render_template('professional_signup.html')

@app.route('/api/professional/signup', methods=['POST'])
def api_professional_signup():
    """Handle professional signup form submission"""
    try:
        # Get form data
        data = request.form
        
        # Step 1: Personal Information
        if 'step' in data and data['step'] == '1':
            return handle_personal_info(data, request.files)
        
        # Step 2: Service Details
        elif 'step' in data and data['step'] == '2':
            return handle_service_details(data)
        
        # Step 3: Experience & Pricing
        elif 'step' in data and data['step'] == '3':
            return handle_experience_pricing(data)
        
        # Step 4: Documents Upload
        elif 'step' in data and data['step'] == '4':
            return handle_documents_upload(data, request.files)
        
        # Complete registration
        elif 'step' in data and data['step'] == 'complete':
            return complete_professional_registration(data)
        
        return jsonify({'success': False, 'message': 'Invalid step'})
        
    except Exception as e:
        print(f"Professional signup error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during registration'})

def handle_personal_info(data, files):
    """Handle step 1: Personal information"""
    # Validate required fields
    required_fields = ['fullName', 'gender', 'phone', 'email', 'password', 
                      'street', 'city', 'pincode', 'state']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'})
    
    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
        return jsonify({'success': False, 'message': 'Please enter a valid email address'})
    
    # Validate phone number
    if not re.match(r'^\d{10}$', data['phone']):
        return jsonify({'success': False, 'message': 'Phone number must be 10 digits'})
    
    # Validate pincode
    if not re.match(r'^\d{6}$', data['pincode']):
        return jsonify({'success': False, 'message': 'Pincode must be 6 digits'})
    
    # Validate password
    if len(data['password']) < 8 or not re.search(r'[A-Za-z]', data['password']) or not re.search(r'\d', data['password']):
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters with letters and numbers'})
    
    # Check if user already exists
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})
    
    cursor = conn.cursor()
    
    # Check for existing email
    cursor.execute("SELECT id FROM users WHERE email = %s", (data['email'],))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'An account with this email already exists'})
    
    # Check for existing phone
    cursor.execute("SELECT id FROM users WHERE phone = %s", (data['phone'],))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'An account with this phone number already exists'})
    
    # Store data in session for later steps
    session['professional_data'] = {
        'personal': {
            'full_name': data['fullName'],
            'gender': data['gender'],
            'phone': data['phone'],
            'email': data['email'],
            'password': data['password'],
            'street': data['street'],
            'city': data['city'],
            'pincode': data['pincode'],
            'state': data['state'],
            'work_radius': data.get('workRadius', 10)
        }
    }
    
    # Handle profile photo upload
    if 'profilePhoto' in files:
        profile_photo = files['profilePhoto']
        if profile_photo and allowed_file(profile_photo.filename):
            if profile_photo.content_length > MAX_FILE_SIZE:
                return jsonify({'success': False, 'message': 'Profile photo must be less than 4MB'})
            
            filename = save_uploaded_file(profile_photo, 'profiles')
            if filename:
                session['professional_data']['personal']['profile_photo'] = filename
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Personal information saved', 'next_step': 2})

def handle_service_details(data):
    """Handle step 2: Service details"""
    if 'professional_data' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
    
    # Validate required fields
    if not data.get('primaryService'):
        return jsonify({'success': False, 'message': 'Primary service is required'})
    
    sub_services = data.getlist('subServices[]')
    if not sub_services:
        return jsonify({'success': False, 'message': 'At least one sub-service is required'})
    
    if not data.get('skillLevel'):
        return jsonify({'success': False, 'message': 'Skill level is required'})
    
    languages = data.getlist('languages[]')
    if not languages:
        return jsonify({'success': False, 'message': 'At least one language is required'})
    
    # Store service data in session
    session['professional_data']['services'] = {
        'primary_service': data['primaryService'],
        'sub_services': sub_services,
        'skill_level': data['skillLevel'],
        'languages': languages
    }
    
    return jsonify({'success': True, 'message': 'Service details saved', 'next_step': 3})

def handle_experience_pricing(data):
    """Handle step 3: Experience and pricing"""
    if 'professional_data' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
    
    # Validate required fields
    if not data.get('experience'):
        return jsonify({'success': False, 'message': 'Years of experience is required'})
    
    if not data.get('about') or len(data['about']) < 40:
        return jsonify({'success': False, 'message': 'About me must be at least 40 characters'})
    
    # Store experience data in session
    session['professional_data']['experience'] = {
        'years': data['experience'],
        'about': data['about'],
        'pricing': {},
        'availability': {}
    }
    
    # Process pricing data
    for key, value in data.items():
        if key.startswith('pricing-') and not key.startswith('pricingType-'):
            service_name = key.replace('pricing-', '').replace('-', ' ')
            price_type = data.get(f'pricingType-{service_name.replace(" ", "-").lower()}', 'fixed')
            session['professional_data']['experience']['pricing'][service_name] = {
                'amount': value,
                'type': price_type
            }
    
    # Process availability data
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in days:
        if data.get(f'available-{day}') == 'on':
            session['professional_data']['experience']['availability'][day] = {
                'start': data.get(f'startTime-{day}', '09:00'),
                'end': data.get(f'endTime-{day}', '18:00')
            }
    
    return jsonify({'success': True, 'message': 'Experience and pricing saved', 'next_step': 4})

def handle_documents_upload(data, files):
    """Handle step 4: Documents upload"""
    if 'professional_data' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
    
    # Store documents data in session
    session['professional_data']['documents'] = {
        'pan_number': data.get('panNumber', '')
    }
    
    # Handle file uploads
    document_files = {}
    required_docs = ['idFront', 'idBack', 'addressProof']
    
    for doc_type in required_docs:
        if doc_type in files:
            file = files[doc_type]
            if file and allowed_file(file.filename):
                if file.content_length > MAX_FILE_SIZE:
                    return jsonify({'success': False, 'message': f'{doc_type} must be less than 4MB'})
                
                filename = save_uploaded_file(file, 'documents')
                if filename:
                    document_files[doc_type] = filename
    
    # Check if required documents are uploaded
    for doc_type in required_docs:
        if doc_type not in document_files:
            return jsonify({'success': False, 'message': f'{doc_type} is required'})
    
    session['professional_data']['documents']['files'] = document_files
    
    # Handle PAN card upload if provided
    if 'panCard' in files and files['panCard']:
        pan_file = files['panCard']
        if allowed_file(pan_file.filename):
            if pan_file.content_length > MAX_FILE_SIZE:
                return jsonify({'success': False, 'message': 'PAN card must be less than 4MB'})
            
            filename = save_uploaded_file(pan_file, 'documents')
            if filename:
                session['professional_data']['documents']['pan_card'] = filename
    
    # Handle portfolio images
    portfolio_files = []
    if 'portfolio' in files:
        portfolio_files_list = files.getlist('portfolio')
        for file in portfolio_files_list:
            if file and allowed_file(file.filename):
                if file.content_length > MAX_FILE_SIZE:
                    continue  # Skip files that are too large
                
                filename = save_uploaded_file(file, 'portfolio')
                if filename:
                    portfolio_files.append(filename)
    
    session['professional_data']['documents']['portfolio'] = portfolio_files
    
    return jsonify({'success': True, 'message': 'Documents uploaded successfully', 'next_step': 5})

def complete_professional_registration(data):
    """Complete professional registration"""
    if 'professional_data' not in session:
        return jsonify({'success': False, 'message': 'Session expired. Please start over.'})
    
    professional_data = session['professional_data']

    # Pull sections from session with safe defaults
    personal_data = professional_data.get('personal', {})
    services_data = professional_data.get('services', {})
    experience_data = professional_data.get('experience', {})
    # Documents are optional for now (verification disabled)
    documents_data = professional_data.get('documents', {})

    # We must at least have basic personal information to create the user
    if not personal_data.get('full_name') or not personal_data.get('email') or not personal_data.get('phone') or not personal_data.get('password'):
        return jsonify({
            'success': False,
            'message': 'Basic personal details are missing. Please fill the first step again.'
        })
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection error'})
    
    try:
        cursor = conn.cursor()
        
        # Start transaction
        conn.start_transaction()
        
        # 1. Create user account
        password_hash = generate_password_hash(personal_data['password'])
        
        # Split full name into first and last name
        name_parts = personal_data['full_name'].split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, phone, password_hash, user_type)
            VALUES (%s, %s, %s, %s, %s, 'professional')
        ''', (
            first_name,
            last_name,
            personal_data['email'],
            personal_data['phone'],
            password_hash
        ))
        
        user_id = cursor.lastrowid
        
        # 2. Create professional profile
        # Make this INSERT compatible with your actual DB schema by checking existing columns.
        cursor.execute("SHOW COLUMNS FROM professional_profiles")
        existing_columns = {row[0] for row in cursor.fetchall()}

        profile_data = {
            'user_id': user_id,
            'gender': personal_data.get('gender'),
            'street_address': personal_data.get('street'),
            'city': personal_data.get('city'),
            'state': personal_data.get('state'),
            'pincode': personal_data.get('pincode'),
            'profile_photo': personal_data.get('profile_photo'),
            'work_radius_km': personal_data.get('work_radius', 10),
            'bio': experience_data.get('about', ''),
            'experience_years': experience_data.get('years'),
            'skill_level': services_data.get('skill_level'),
            'is_verified': True,
            'verification_status': 'approved'
        }

        # Only keep keys that correspond to real columns
        insert_columns = [col for col in profile_data.keys() if col in existing_columns]
        insert_values = [profile_data[col] for col in insert_columns]

        if 'user_id' not in insert_columns:
            raise Exception("Database schema for professional_profiles is missing required column 'user_id'.")

        columns_sql = ', '.join(insert_columns)
        placeholders_sql = ', '.join(['%s'] * len(insert_columns))
        insert_sql = f"INSERT INTO professional_profiles ({columns_sql}) VALUES ({placeholders_sql})"

        cursor.execute(insert_sql, insert_values)
        
        professional_id = cursor.lastrowid
        
        # 3. Add services
        for sub_service in services_data.get('sub_services', []):
            pricing = experience_data.get('pricing', {}).get(sub_service, {})
            cursor.execute('''
                INSERT INTO professional_services 
                (professional_id, primary_service, sub_service, base_price, price_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', (
                professional_id,
                services_data['primary_service'],
                sub_service,
                pricing.get('amount'),
                pricing.get('type', 'fixed')
            ))
        
        # 4. Add languages
        for language in services_data.get('languages', []):
            cursor.execute('''
                INSERT INTO professional_languages (professional_id, language)
                VALUES (%s, %s)
            ''', (professional_id, language))
        
        # 5. Add availability
        availability_data = experience_data.get('availability', {})
        for day, times in availability_data.items():
            cursor.execute('''
                INSERT INTO professional_availability 
                (professional_id, day_of_week, start_time, end_time, is_available)
                VALUES (%s, %s, %s, %s, TRUE)
            ''', (professional_id, day, times['start'], times['end']))
        
        # 6. Add documents
        document_types = {
            'idFront': 'government_id_front',
            'idBack': 'government_id_back',
            'addressProof': 'address_proof',
            'panCard': 'pan_card'
        }
        
        for doc_key, doc_type in document_types.items():
            if doc_key in documents_data.get('files', {}):
                cursor.execute('''
                    INSERT INTO professional_documents 
                    (professional_id, document_type, file_name, file_path)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    professional_id,
                    doc_type,
                    documents_data['files'][doc_key],
                    f"documents/{documents_data['files'][doc_key]}"
                ))
        
        # 7. Add portfolio images
        for portfolio_image in documents_data.get('portfolio', []):
            cursor.execute('''
                INSERT INTO professional_portfolio 
                (professional_id, image_name, image_path)
                VALUES (%s, %s, %s)
            ''', (professional_id, portfolio_image, f"portfolio/{portfolio_image}"))
        
        # Commit transaction
        conn.commit()
        
        # Clear session data
        session.pop('professional_data', None)
        
        # Set user session
        session['user_id'] = user_id
        session['user_email'] = personal_data['email']
        session['user_name'] = personal_data['full_name']
        session['user_type'] = 'professional'
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Registration completed successfully! Redirecting to your dashboard.',
            'redirect': '/professional/dashboard'
        })
        
    except mysql.connector.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        error_message = f"Database error during registration: {str(e)}"
        print(error_message)
        return jsonify({'success': False, 'message': error_message})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        error_message = f"Unexpected error during registration: {str(e)}"
        print(error_message)
        return jsonify({'success': False, 'message': error_message})

# ========== API ENDPOINTS ==========

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
    # Create upload directories
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'profiles'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'documents'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'portfolio'), exist_ok=True)
    
    # Initialize database on startup
    init_database()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5001)