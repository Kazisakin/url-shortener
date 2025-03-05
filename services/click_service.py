# services/click_service.py
from models.click import Click
from app import db

class ClickService:
    def record_click(self, url_id, ip_address, user_agent):
        try:
            click = Click(url_id=url_id, ip_address=ip_address, user_agent=user_agent)
            db.session.add(click)
            db.session.commit()
            return click
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to record click: {str(e)}")

    def get_clicks(self, url_id):
        return Click.query.filter_by(url_id=url_id).all()