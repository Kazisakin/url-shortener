# blueprints/main.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_limiter import Limiter
from flask_login import current_user
from services.url_service import URLService
from services.click_service import ClickService
from services.qr_service import QRService

main_bp = Blueprint('main', __name__)  # Define the Blueprint object

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    url_service = URLService()
    qr_service = QRService()
    usage_count = int(open('usage_counter.txt', 'r').read() or 0)
    if request.method == 'POST':
        original_url = request.form.get('original_url')
        custom_alias = request.form.get('custom_alias')
        password = request.form.get('password')
        bulk_urls = request.form.get('bulk_urls')

        try:
            if bulk_urls:
                urls = bulk_urls.splitlines()
                shortened_urls = []
                for url in urls:
                    url = url.strip()
                    if not url or not url.startswith('http'):
                        continue
                    new_url = url_service.create_url(url, user_id=current_user.id if current_user.is_authenticated else None)
                    shortened_urls.append(f"{request.host_url}{new_url.short_alias}")
                update_usage_counter()
                flash('Shortened URLs:\n' + '\n'.join(shortened_urls), 'success')
                return render_template('index.html', usage_count=usage_count)

            new_url = url_service.create_url(original_url, custom_alias, password, user_id=current_user.id if current_user.is_authenticated else None)
            shortened_url = f"{request.host_url}{new_url.short_alias}"
            qr_service.generate_qr_code(new_url.short_alias, shortened_url)
            update_usage_counter()
            return render_template('index.html', usage_count=usage_count, shortened_url=shortened_url)
        except ValueError as e:
            flash(str(e), 'error')

    return render_template('index.html', usage_count=usage_count)

@main_bp.route('/<short_alias>')
def redirect_to_url(short_alias):
    url_service = URLService()
    click_service = ClickService()
    url = url_service.get_url(short_alias)
    if not url:
        flash('Invalid URL.', 'error')
        return render_template('index.html')
    click = click_service.record_click(url.id, request.remote_addr, request.headers.get('User-Agent'))
    print(f"Recorded click for URL {url.short_alias}: ID={click.id}, IP={click.ip_address}, User-Agent={click.user_agent}, Timestamp={click.timestamp}")
    if url.password:
        return redirect(url_for('main.password_prompt', short_alias=short_alias))
    return redirect(url.original_url)

@main_bp.route('/password/<short_alias>', methods=['GET', 'POST'])
def password_prompt(short_alias):
    url_service = URLService()
    url = url_service.get_url(short_alias)
    if not url:
        flash('Invalid URL.', 'error')
        return render_template('index.html')
    if request.method == 'POST':
        password = request.form.get('password')
        if password == url.password:
            return redirect(url.original_url)
        flash('Incorrect password.', 'error')
    return render_template('password_prompt.html', short_alias=short_alias)

@main_bp.route('/favicon.ico')
def favicon():
    return '', 404

def update_usage_counter():
    try:
        with open('usage_counter.txt', 'r+') as f:
            count = int(f.read() or 0)
            count += 1
            f.seek(0)
            f.write(str(count))
            return count
    except FileNotFoundError:
        with open('usage_counter.txt', 'w') as f:
            f.write('1')
        return 1