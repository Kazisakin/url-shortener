import os
import io
import qrcode
import random
import string
from datetime import datetime
from urllib.parse import urlparse
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, session, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect, generate_csrf

# ----------------------------
# App Initialization & Config
# ----------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_value')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# For development ONLY: Uncomment the next line to disable CSRF protection
# app.config['WTF_CSRF_ENABLED'] = False

# Build an absolute path for the database directory and file
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, 'database')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
db_path = os.path.join(db_dir, 'urlshortener.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
limiter = Limiter(app, key_func=get_remote_address)
csrf = CSRFProtect(app)

# ----------------------------
# Context Processor for CSRF Token
# ----------------------------
@app.context_processor
def inject_csrf_token():
    # This ensures that the function csrf_token() is available in templates.
    return dict(csrf_token=generate_csrf)

# ----------------------------
# Models
# ----------------------------
class URL(db.Model):
    """Model for storing shortened URL data."""
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_id = db.Column(db.String(10), unique=True, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

class User(db.Model):
    """Model for storing user data."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    urls = db.relationship('URL', backref='owner', lazy=True)

class ClickLog(db.Model):
    """Model for logging clicks on shortened URLs."""
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    referrer = db.Column(db.String(2048))
    user_agent = db.Column(db.String(256))

# ----------------------------
# Helper Functions
# ----------------------------
def generate_short_id(num_chars=6):
    """Generate a random string of letters and digits for the short URL."""
    characters = string.ascii_letters + string.digits
    while True:
        short_id = ''.join(random.choice(characters) for _ in range(num_chars))
        if not URL.query.filter_by(short_id=short_id).first():
            return short_id

def is_valid_url(url):
    """Check if the URL has a valid scheme and network location."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

# A simple blacklist for suspicious domains
BLACKLISTED_DOMAINS = ['phishing.com', 'spam.com']

def is_blacklisted(url):
    """Return True if the URL's domain is blacklisted."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    return any(black in domain for black in BLACKLISTED_DOMAINS)

def login_required(f):
    """Decorator to require a logged-in user for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------------------
# Routes
# ----------------------------
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def index():
    """Home page for URL shortening."""
    if request.method == 'POST':
        original_url = request.form.get('original_url')
        custom_alias = request.form.get('custom_alias')
        expiration = request.form.get('expiration')
        password = request.form.get('password')
        bulk_urls = request.form.get('bulk_urls')

        # --- Bulk URL Shortening ---
        if bulk_urls:
            bulk_results = []
            new_urls = []
            urls = bulk_urls.splitlines()
            for url in urls:
                url = url.strip()
                if not url:
                    continue
                if not is_valid_url(url):
                    bulk_results.append({'url': url, 'error': 'Invalid URL'})
                    continue
                if is_blacklisted(url):
                    bulk_results.append({'url': url, 'error': 'URL is blacklisted'})
                    continue
                short_id = generate_short_id()
                new_url = URL(original_url=url, short_id=short_id)
                new_urls.append(new_url)
                bulk_results.append({'url': url, 'short_url': request.host_url + short_id})
            if new_urls:
                db.session.add_all(new_urls)
                db.session.commit()
            return render_template('index.html', bulk_results=bulk_results)

        # --- Single URL Shortening ---
        if not original_url or not is_valid_url(original_url):
            flash("Please enter a valid URL.", "danger")
            return redirect(url_for('index'))
        if is_blacklisted(original_url):
            flash("The URL is blacklisted.", "danger")
            return redirect(url_for('index'))

        if custom_alias:
            if URL.query.filter_by(short_id=custom_alias).first():
                flash("Custom alias already taken.", "danger")
                return redirect(url_for('index'))
            short_id = custom_alias
        else:
            short_id = generate_short_id()

        exp_date = None
        if expiration:
            try:
                exp_date = datetime.strptime(expiration, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid expiration date format.", "danger")
                return redirect(url_for('index'))

        password_hash = generate_password_hash(password) if password else None
        user_id = session.get('user_id')

        new_url = URL(
            original_url=original_url,
            short_id=short_id,
            expiration_date=exp_date,
            password_hash=password_hash,
            user_id=user_id
        )
        db.session.add(new_url)
        db.session.commit()

        flash("URL shortened successfully!", "success")
        return render_template('index.html',
                               short_url=request.host_url + short_id,
                               qr_url=url_for('qr_code', short_id=short_id))
    return render_template('index.html')

@app.route('/<short_id>', methods=['GET', 'POST'])
def redirect_short_url(short_id):
    """Redirect to the original URL, handling expiration and password protection."""
    url_entry = URL.query.filter_by(short_id=short_id).first_or_404()
    if url_entry.expiration_date and datetime.utcnow() > url_entry.expiration_date:
        flash("This link has expired.", "danger")
        return render_template('index.html')
    if url_entry.password_hash:
        if request.method == 'POST':
            password_input = request.form.get('password')
            if not check_password_hash(url_entry.password_hash, password_input):
                flash("Incorrect password.", "danger")
                return render_template('password_prompt.html', short_id=short_id)
        else:
            return render_template('password_prompt.html', short_id=short_id)
    url_entry.click_count += 1
    click = ClickLog(
        url_id=url_entry.id,
        ip_address=request.remote_addr,
        referrer=request.referrer,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(click)
    db.session.commit()
    return redirect(url_entry.original_url)

@app.route('/qr/<short_id>')
def qr_code(short_id):
    """Generate and return a QR code image for the given short URL."""
    url_entry = URL.query.filter_by(short_id=short_id).first_or_404()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(request.host_url + short_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ----------------------------
# REST API Endpoints
# ----------------------------
@app.route('/api/shorten', methods=['POST'])
@limiter.limit("20 per minute")
def api_shorten():
    """API endpoint to shorten a URL programmatically."""
    data = request.get_json()
    if not data or 'original_url' not in data:
        return jsonify({'error': 'No URL provided'}), 400

    original_url = data.get('original_url')
    custom_alias = data.get('custom_alias')
    expiration = data.get('expiration')
    password = data.get('password')

    if not is_valid_url(original_url):
        return jsonify({'error': 'Invalid URL'}), 400
    if is_blacklisted(original_url):
        return jsonify({'error': 'URL is blacklisted'}), 400

    if custom_alias:
        if URL.query.filter_by(short_id=custom_alias).first():
            return jsonify({'error': 'Custom alias already taken'}), 400
        short_id = custom_alias
    else:
        short_id = generate_short_id()

    exp_date = None
    if expiration:
        try:
            exp_date = datetime.strptime(expiration, "%Y-%m-%dT%H:%M")
        except ValueError:
            return jsonify({'error': 'Invalid expiration date format'}), 400

    password_hash = generate_password_hash(password) if password else None
    new_url = URL(
        original_url=original_url,
        short_id=short_id,
        expiration_date=exp_date,
        password_hash=password_hash
    )
    db.session.add(new_url)
    db.session.commit()

    return jsonify({'short_url': request.host_url + short_id}), 201

@app.route('/api/info/<short_id>', methods=['GET'])
def api_info(short_id):
    """API endpoint to retrieve information about a short URL."""
    url_entry = URL.query.filter_by(short_id=short_id).first_or_404()
    info = {
        'original_url': url_entry.original_url,
        'short_url': request.host_url + url_entry.short_id,
        'click_count': url_entry.click_count,
        'created_at': url_entry.created_at.isoformat(),
        'expiration_date': url_entry.expiration_date.isoformat() if url_entry.expiration_date else None
    }
    return jsonify(info)

# ----------------------------
# Authentication Routes
# ----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        if not username or not password:
            flash("Both username and password are required.", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('register'))
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for('login'))
        session['user_id'] = user.id
        session['username'] = user.username
        flash("Logged in successfully.", "success")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout route."""
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Logged out.", "success")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard for the logged-in user to manage their URLs."""
    user_id = session.get('user_id')
    urls = URL.query.filter_by(user_id=user_id).order_by(URL.created_at.desc()).all()
    return render_template('dashboard.html', urls=urls)

# ----------------------------
# Run the App
# ----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False)
