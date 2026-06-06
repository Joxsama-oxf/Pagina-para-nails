from flask import Flask
from flask_login import LoginManager
from models import db, User
from rutas import register_blueprints
from rutas._helpers import tiene_permiso

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_super_segura'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lauranails.db'

db.init_app(app)

# --- LOGIN ---
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- RBAC en templates ---
# Hace que tiene_permiso() esté disponible en TODOS los templates
# Uso: {% if tiene_permiso('citas.borrar') %}
@app.context_processor
def inject_helpers():
    return dict(tiene_permiso=tiene_permiso)

register_blueprints(app)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
