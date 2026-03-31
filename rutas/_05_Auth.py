from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db

auth_bp = Blueprint('auth', __name__)

# --- RUTA DE LOGIN ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Buscamos al usuario en la base de datos
        user = User.query.filter_by(email=email).first()
        
        # Verificamos si existe y si la contraseña coincide
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Redirigir según el rol
            if user.role == 'admin':
                return redirect(url_for('inicio.home')) # Va al Dashboard nuevo
            else:
                return redirect(url_for('inicio.home')) # Va al Dashboard (limitado)
        else:
            flash('Correo o contraseña incorrectos. Verifica tus credenciales.', 'error')
            
    return render_template('auth/login.html')

# --- RUTA DE LOGOUT ---
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('auth.login'))

# --- RUTA DE CONFIGURACIÓN DE USUARIOS (Ejecutar una sola vez) ---
@auth_bp.route('/configurar-usuarios')
def configurar_usuarios():
    # 1. Limpiamos la tabla de usuarios existente para evitar duplicados
    try:
        db.session.query(User).delete()
        db.session.commit()
    except:
        db.session.rollback()

    # 2. Lista de usuarios solicitada
    usuarios_a_crear = [
        # ADMINS (Clave: Anabella03#.,)
        {'email': 'lauranadmin@gmail.com',  'pass': 'Anabella03#.,', 'role': 'admin'},
        {'email': 'lauranadmin2@gmail.com', 'pass': 'Anabella03#.,', 'role': 'admin'},
        
        # MANICURISTAS
        {'email': 'lauranails01@gmail.com', 'pass': 'Beauty01',   'role': 'empleada'}, # Manicurista 1
        {'email': 'lauranails02@gmail.com', 'pass': 'Studio71',   'role': 'empleada'}, # Manicurista 2
        {'email': 'lauranails03@gmail.com', 'pass': 'Nails2026',  'role': 'empleada'}  # Manicurista 3
    ]

    # 3. Generamos los usuarios en la Base de Datos
    for u in usuarios_a_crear:
        # Encriptamos la contraseña antes de guardarla
        hashed_pw = generate_password_hash(u['pass'], method='scrypt')
        nuevo_usuario = User(email=u['email'], password=hashed_pw, role=u['role'])
        db.session.add(nuevo_usuario)
    
    db.session.commit()
    
    return """
    <div style='font-family: sans-serif; text-align: center; margin-top: 50px;'>
        <h1 style='color: green;'>✅ Usuarios Creados Correctamente</h1>
        <p>Se han configurado los 2 admins y las 3 manicuristas.</p>
        <a href='/login' style='background: #d63384; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;'>Ir al Login</a>
    </div>
    """