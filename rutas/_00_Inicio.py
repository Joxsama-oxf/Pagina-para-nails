from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

inicio_bp = Blueprint('inicio', __name__)

@inicio_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('index.html')
