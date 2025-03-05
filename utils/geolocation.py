# utils/geolocation.py
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

def get_geolocation(ip_address):
    if ip_address in ['127.0.0.1', '::1']:
        return {'city': 'Localhost'}
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=3)
        logging.debug(f"Geolocation response for {ip_address}: Status={response.status_code}, Content={response.text}")
        return response.json()
    except Exception as e:
        logging.error(f"Geolocation failed for {ip_address}: {str(e)}")
        return {'city': 'Unknown'}