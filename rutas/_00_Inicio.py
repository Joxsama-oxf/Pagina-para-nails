from flask import Blueprint, render_template
from flask_login import login_required, current_user

inicio_bp = Blueprint('inicio', __name__)

@inicio_bp.route('/')
def home():
    return render_template('index.html') # Asegúrate que index.html exista

@inicio_bp.route('/dashboard-admin')
@login_required
def dashboard_admin():
    return "<h1>Bienvenida Administradora</h1><p>Panel de Control Total</p>"

@inicio_bp.route('/dashboard-empleada')
@login_required
def dashboard_empleada():
    return "<h1>Bienvenida Empleada</h1><p>Panel Limitado</p>"