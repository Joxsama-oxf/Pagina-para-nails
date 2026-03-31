from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager 
from models import db, User # Solo necesitamos db y User para la configuración inicial
from rutas import register_blueprints

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_super_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lauranails.db'

db.init_app(app)

# --- CONFIGURACIÓN DEL LOGIN ---
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# -------------------------------

register_blueprints(app)

# Esto crea la base de datos si no existe
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)