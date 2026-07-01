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

# Carga el .env que está JUNTO a este archivo. Así funciona igual al correr
# 'python app.py' en tu PC y al importarse desde el WSGI de PythonAnywhere,
# sin depender de cuál sea la carpeta de trabajo.
load_dotenv(Path(__file__).resolve().parent / '.env')

app = Flask(__name__)

# La clave secreta se lee del entorno. Si falta, la app no arranca:
# así evitamos dejar una clave por defecto insegura en producción.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise RuntimeError(
        "Falta SECRET_KEY. Crea un archivo .env con SECRET_KEY=... "
        "(revisa el archivo .env.example)."
    )

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lauranails.db'

db.init_app(app)

# Protección CSRF: rechaza cualquier POST que no traiga un token válido.
# Cada formulario ya incluye <input name="csrf_token" value="{{ csrf_token() }}">.
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
    db.create_all()
    # Migración segura: agrega columna cedula si la tabla cliente ya existe
    try:
        db.session.execute(text("ALTER TABLE cliente ADD COLUMN cedula VARCHAR(10)"))
        db.session.commit()
    except Exception:
        db.session.rollback()

if __name__ == '__main__':
    # debug se activa solo si FLASK_DEBUG=1 en el .env.
    # NUNCA dejar debug activo en un servidor público.
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug)
