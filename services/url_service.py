# services/url_service.py
from models.url import URL
from app import db
import string, random

class URLService:
    def __init__(self):
        self.length = 6  # Length of short alias

    def generate_short_alias(self):
        characters = string.ascii_letters + string.digits
        while True:
            short_alias = ''.join(random.choice(characters) for _ in range(self.length))
            if not URL.query.filter_by(short_alias=short_alias).first():
                return short_alias

    def create_url(self, original_url, custom_alias=None, password=None, user_id=None):
        if not original_url or not original_url.startswith('http'):
            raise ValueError("Invalid URL. Must start with http:// or https://")
        
        short_alias = custom_alias if custom_alias else self.generate_short_alias()
        if URL.query.filter_by(short_alias=short_alias).first():
            raise ValueError("Alias already taken.")

        new_url = URL(
            original_url=original_url,
            short_alias=short_alias,
            password=password if password else None,
            user_id=user_id
        )
        db.session.add(new_url)
        db.session.commit()
        return new_url

    def get_url(self, short_alias):
        return URL.query.filter_by(short_alias=short_alias).first()

    def get_user_urls(self, user_id, page=1, per_page=10):
        return URL.query.filter_by(user_id=user_id).order_by(URL.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)