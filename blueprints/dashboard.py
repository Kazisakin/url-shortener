# blueprints/dashboard.py (updated)
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, send_file
from flask_login import login_required, current_user
from services.url_service import URLService
from services.analytics_service import AnalyticsService
from services.qr_service import QRService
from utils.export import export_urls_to_csv
from utils.geolocation import get_geolocation  # Add this import
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    url_service = URLService()
    analytics_service = AnalyticsService()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = url_service.get_user_urls(current_user.id, page, per_page)
    user_urls = pagination.items
    metrics = analytics_service.get_summary_metrics(user_urls)
    return render_template('dashboard.html', urls=user_urls, pagination=pagination, **metrics)

@dashboard_bp.route('/generate_qr/<short_alias>')
@login_required
def generate_qr(short_alias):
    url_service = URLService()
    qr_service = QRService()
    url = url_service.get_url(short_alias)
    if not url or url.user_id != current_user.id:
        flash('URL not found.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    qr_path = qr_service.generate_qr_code(short_alias, f"{request.host_url}{short_alias}")
    return send_file(qr_path, as_attachment=True, download_name=f"qr_{short_alias}.png")

@dashboard_bp.route('/analytics/<short_alias>')
@login_required
def analytics(short_alias):
    url_service = URLService()
    analytics_service = AnalyticsService()
    url = url_service.get_url(short_alias)
    if not url or url.user_id != current_user.id:
        flash('URL not found.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    try:
        daily_clicks = analytics_service.get_click_trends(url.id)
        device_data = analytics_service.get_device_breakdown(url.id)
        geo_data = analytics_service.get_geolocation_data(url.id)

        clicks = analytics_service.click_service.get_clicks(url.id)
        csv_data = ['Date,Clicks,IP Address,User Agent,City']
        for click in clicks:
            location = get_geolocation(click.ip_address) if click.ip_address else {'city': 'Unknown'}
            csv_data.append(f"{click.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{1},{click.ip_address},{click.user_agent},{location.get('city', 'Unknown')}")
        csv_string = '\n'.join(csv_data)

        return render_template('analytics.html', url=url, daily_clicks=json.dumps(daily_clicks),
                              device_data=json.dumps(device_data), geo_data=json.dumps(geo_data), csv_data=csv_string)
    except Exception as e:
        flash(f"Error loading analytics: {str(e)}", 'error')
        return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/export_urls')
@login_required
def export_urls():
    url_service = URLService()
    user_urls = URL.query.filter_by(user_id=current_user.id).all()
    return export_urls_to_csv(user_urls)

@dashboard_bp.route('/export_analytics/<short_alias>')
@login_required
def export_analytics(short_alias):
    url_service = URLService()
    analytics_service = AnalyticsService()
    url = url_service.get_url(short_alias)
    if not url or url.user_id != current_user.id:
        flash('URL not found.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    clicks = analytics_service.click_service.get_clicks(url.id)
    csv_data = ['Date,Clicks,IP Address,User Agent,City']
    for click in clicks:
        location = get_geolocation(click.ip_address) if click.ip_address else {'city': 'Unknown'}
        csv_data.append(f"{click.timestamp.strftime('%Y-%m-%d %H:%M:%S')},{1},{click.ip_address},{click.user_agent},{location.get('city', 'Unknown')}")
    
    return Response(
        '\n'.join(csv_data),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=analytics_{short_alias}.csv'}
    )