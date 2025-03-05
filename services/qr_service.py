# services/qr_service.py
import qrcode
import os

class QRService:
    def generate_qr_code(self, short_alias, url):
        if not os.path.exists('static/qr_codes'):
            os.makedirs('static/qr_codes')
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        qr_path = f'static/qr_codes/qr_{short_alias}.png'
        img.save(qr_path)
        return qr_path