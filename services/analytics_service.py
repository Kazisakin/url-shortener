# services/analytics_service.py
# services/analytics_service.py
from services.click_service import ClickService
from utils.geolocation import get_geolocation
import json

class AnalyticsService:
    def __init__(self):
        self.click_service = ClickService()

    def get_click_trends(self, url_id):
        clicks = self.click_service.get_clicks(url_id)
        daily_clicks = {}
        for click in clicks:
            date = click.timestamp.strftime('%Y-%m-%d')
            daily_clicks[date] = daily_clicks.get(date, 0) + 1
        return [{'date': k, 'clicks': v} for k, v in daily_clicks.items()]

    def get_device_breakdown(self, url_id):
        clicks = self.click_service.get_clicks(url_id)
        device_types = {'Desktop': 0, 'Mobile': 0, 'Tablet': 0}
        for click in clicks:
            ua = click.user_agent.lower() if click.user_agent else ''
            if 'mobile' in ua:
                device_types['Mobile'] += 1
            elif 'tablet' in ua:
                device_types['Tablet'] += 1
            else:
                device_types['Desktop'] += 1
        return [{'device': k, 'count': v} for k, v in device_types.items()]

    def get_geolocation_data(self, url_id):
        clicks = self.click_service.get_clicks(url_id)
        geo_data = {}
        for click in clicks:
            if click.ip_address:
                location = get_geolocation(click.ip_address)
                city = location.get('city', 'Unknown')
                geo_data[city] = geo_data.get(city, 0) + 1
        return [{'city': k, 'count': v} for k, v in geo_data.items()]

    def get_summary_metrics(self, user_urls):
        total_clicks = sum(len(url.clicks) for url in user_urls)
        unique_ips = len(set(click.ip_address for url in user_urls for click in url.clicks))
        most_clicked = max(user_urls, key=lambda url: len(url.clicks), default=None)
        return {
            'total_clicks': total_clicks,
            'unique_ips': unique_ips,
            'most_clicked': most_clicked
        }