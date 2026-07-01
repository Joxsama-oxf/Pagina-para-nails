import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from models import db, User
from rutas import register_blueprints
from rutas._helpers import tiene_permiso, formatear_telefono_ec

# Carga .env solo si existe, pero NO sobreescribe variables ya definidas (Docker las define)
dotenv_path = Path(__file__).resolve().parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path, override=False)

app = Flask(__name__)

# SECRET_KEY: Docker ya la puso en el entorno, o usa default
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-por-defecto-docker-2026-laura-nails')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lauranails.db'

db.init_app(app)

csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_helpers():
    return dict(tiene_permiso=tiene_permiso,
                formatear_telefono_ec=formatear_telefono_ec)

register_blueprints(app)

with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass
    
    try:
        db.session.execute(text("ALTER TABLE cliente ADD COLUMN cedula VARCHAR(10)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug)