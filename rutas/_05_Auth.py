from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, Negocio, Rol, Permiso, Servicio, HistorialPrecio, CategoriaServicio, db
from rutas._helpers import obtener_hora_ecuador

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inicio.home'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email, activo=True).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('inicio.home'))
        flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/configurar-sistema')
def configurar_sistema():
    """Ejecutar UNA SOLA VEZ. Crea negocio, roles, permisos, usuarios y servicios demo."""
    try:
        db.session.query(User).delete()
        db.session.query(HistorialPrecio).delete()
        db.session.query(Servicio).delete()
        db.session.query(CategoriaServicio).delete()
        db.session.query(Rol).delete()
        db.session.query(Permiso).delete()
        db.session.query(Negocio).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()

    ahora = obtener_hora_ecuador()
    hoy   = ahora.date()

    # 1. Negocio
    negocio = Negocio(nombre='Laura Nails Beauty Studio', tipo_negocio='salon_unas',
                      direccion='Dirección del local', telefono='0999999999',
                      email_contacto='lauranadmin@gmail.com', activo=True, fecha_registro=ahora)
    db.session.add(negocio)
    db.session.flush()

    # 2. Permisos
    codigos = [
        ('citas.ver',               'Ver agenda y citas'),
        ('citas.crear',             'Agendar nuevas citas'),
        ('citas.borrar',            'Eliminar citas'),
        ('facturacion.ver',         'Ver facturación'),
        ('facturacion.cobrar',      'Registrar cobros'),
        ('contabilidad.ver',        'Ver contabilidad'),
        ('contabilidad.registrar',  'Registrar movimientos'),
        ('contabilidad.cerrar_dia', 'Cerrar caja diaria'),
        ('servicios.ver',           'Ver catálogo'),
        ('servicios.editar',        'Editar servicios y precios'),
        ('redes.ver',               'Ver redes sociales'),
        ('usuarios.ver',            'Ver usuarios'),
        ('usuarios.gestionar',      'Gestionar usuarios'),
        ('inventario.ver',          'Ver inventario'),
        ('inventario.editar',       'Editar inventario'),
    ]
    permisos = {}
    for codigo, desc in codigos:
        p = Permiso(negocio_id=negocio.id, codigo=codigo, descripcion=desc)
        db.session.add(p)
        permisos[codigo] = p
    db.session.flush()

    # 3. Roles
    rol_admin = Rol(negocio_id=negocio.id, nombre='Admin', descripcion='Acceso total', activo=True)
    rol_admin.permisos = list(permisos.values())
    db.session.add(rol_admin)

    rol_mani = Rol(negocio_id=negocio.id, nombre='Manicurista', descripcion='Agenda y cobro', activo=True)
    rol_mani.permisos = [permisos['citas.ver'], permisos['citas.crear'],
                         permisos['facturacion.ver'], permisos['facturacion.cobrar'],
                         permisos['servicios.ver']]
    db.session.add(rol_mani)
    db.session.flush()

    # 4. Usuarios
    for u in [
        {'nombre': 'Admin Principal',  'email': 'lauranadmin@gmail.com',  'pass': 'Anabella03#.,', 'rol': rol_admin},
        {'nombre': 'Admin Secundario', 'email': 'lauranadmin2@gmail.com', 'pass': 'Anabella03#.,', 'rol': rol_admin},
        {'nombre': 'Manicurista 1',    'email': 'lauranails01@gmail.com', 'pass': 'Beauty01',      'rol': rol_mani},
        {'nombre': 'Manicurista 2',    'email': 'lauranails02@gmail.com', 'pass': 'Studio71',      'rol': rol_mani},
        {'nombre': 'Manicurista 3',    'email': 'lauranails03@gmail.com', 'pass': 'Nails2026',     'rol': rol_mani},
    ]:
        nuevo = User(negocio_id=negocio.id, nombre=u['nombre'], email=u['email'],
                     password=generate_password_hash(u['pass'], method='scrypt'),
                     es_superadmin=False, activo=True, fecha_registro=ahora)
        nuevo.roles = [u['rol']]
        db.session.add(nuevo)

    # 5. Categorías y servicios demo
    cat_manos = CategoriaServicio(negocio_id=negocio.id, nombre='Manos', orden=1)
    cat_pies  = CategoriaServicio(negocio_id=negocio.id, nombre='Pies',  orden=2)
    cat_extra = CategoriaServicio(negocio_id=negocio.id, nombre='Adicionales', orden=3)
    db.session.add_all([cat_manos, cat_pies, cat_extra])
    db.session.flush()

    servicios_demo = [
        ('Manicure Tradicional', 5.00,  cat_manos.id, 30),
        ('Semipermanente',       7.00,  cat_manos.id, 45),
        ('Rubber',              12.00,  cat_manos.id, 60),
        ('Softgel',             15.00,  cat_manos.id, 75),
        ('Esculpidas',          25.00,  cat_manos.id, 90),
        ('Poligel',             28.00,  cat_manos.id, 90),
        ('Baño Acrílico',       15.00,  cat_manos.id, 60),
        ('Pedicure Tradicional', 7.00,  cat_pies.id,  45),
        ('Pedicure Profunda',   12.00,  cat_pies.id,  60),
        ('Semipermanente Pies', 12.00,  cat_pies.id,  50),
        ('Retiro Manos',         5.00,  cat_pies.id,  20),
        ('Retiro Gel',           2.00,  cat_pies.id,  15),
        ('Ojo de Gato',          5.00,  cat_extra.id, 10),
        ('Efecto Espejo',        3.00,  cat_extra.id, 10),
        ('Flores 3D',            1.50,  cat_extra.id,  5),
        ('Encapsulado',          1.00,  cat_extra.id,  5),
    ]
    for nombre, precio, cat_id, duracion in servicios_demo:
        srv = Servicio(negocio_id=negocio.id, categoria_id=cat_id,
                       nombre=nombre, duracion_min=duracion, activo=True)
        db.session.add(srv)
        db.session.flush()
        db.session.add(HistorialPrecio(servicio_id=srv.id, precio=precio,
                                       es_promocion=False, fecha_inicio=hoy, motivo='Precio inicial'))

    db.session.commit()
    return """<div style='font-family:sans-serif;text-align:center;margin-top:50px;'>
        <h1 style='color:green;'>&#10003; Sistema configurado</h1>
        <p>Negocio, roles, permisos, usuarios y servicios demo creados.</p>
        <a href='/login' style='background:#d63384;color:white;padding:12px 28px;
           text-decoration:none;border-radius:8px;font-weight:bold;'>Ir al Login</a>
    </div>"""
