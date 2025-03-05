from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Custom Jinja2 filter to sum a list of dictionaries by attribute
@app.template_filter('sum')
def sum_filter(items, attribute):
    return sum(item[attribute] for item in items)

# Register blueprints
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.dashboard import dashboard_bp
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(dashboard_bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

# Initialize database
if not os.path.exists('instance'):
    os.makedirs('instance')

with app.app_context():
    db.create_all()
    try:
        open('usage_counter.txt', 'r').close()
    except FileNotFoundError:
        with open('usage_counter.txt', 'w') as f:
            f.write('0')

if __name__ == '__main__':
    app.run(debug=True)