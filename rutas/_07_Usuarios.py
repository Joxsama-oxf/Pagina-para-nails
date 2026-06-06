from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Rol
from rutas._helpers import requiere_permiso, obtener_hora_ecuador

usuarios_bp = Blueprint('usuarios', __name__)

@usuarios_bp.route('/admin/usuarios', methods=['GET', 'POST'])
@login_required
@requiere_permiso('usuarios.gestionar')
def index():
    negocio_id = current_user.negocio_id
    ahora      = obtener_hora_ecuador()

    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'agregar':
                nombre   = request.form.get('nombre', '').strip()
                email    = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                rol_id   = int(request.form.get('rol_id'))

                if User.query.filter_by(email=email).first():
                    flash('Ese correo ya está registrado.', 'error')
                    return redirect(url_for('usuarios.index'))

                rol = Rol.query.get_or_404(rol_id)
                if rol.negocio_id != negocio_id:
                    abort(403)

                nuevo = User(negocio_id=negocio_id, nombre=nombre, email=email,
                             password=generate_password_hash(password, method='scrypt'),
                             es_superadmin=False, activo=True, fecha_registro=ahora)
                nuevo.roles = [rol]
                db.session.add(nuevo)
                db.session.commit()
                flash(f'Usuario "{nombre}" creado correctamente.', 'success')

            elif accion == 'editar':
                uid  = int(request.form.get('user_id'))
                user = User.query.get_or_404(uid)
                if user.negocio_id != negocio_id:
                    abort(403)
                user.nombre = request.form.get('nombre', user.nombre).strip()
                nueva_pass  = request.form.get('password', '').strip()
                if nueva_pass:
                    user.password = generate_password_hash(nueva_pass, method='scrypt')
                rol_id = request.form.get('rol_id')
                if rol_id:
                    rol = Rol.query.get(int(rol_id))
                    if rol and rol.negocio_id == negocio_id:
                        user.roles = [rol]
                db.session.commit()
                flash('Usuario actualizado.', 'success')

            elif accion == 'desactivar':
                user = User.query.get_or_404(int(request.form.get('user_id')))
                if user.negocio_id != negocio_id or user.id == current_user.id:
                    abort(403)
                user.activo = False
                db.session.commit()
                flash('Usuario desactivado.', 'success')

            elif accion == 'activar':
                user = User.query.get_or_404(int(request.form.get('user_id')))
                if user.negocio_id != negocio_id:
                    abort(403)
                user.activo = True
                db.session.commit()
                flash('Usuario activado.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('usuarios.index'))

    usuarios = User.query.filter_by(negocio_id=negocio_id).order_by(User.activo.desc(), User.nombre).all()
    roles    = Rol.query.filter_by(negocio_id=negocio_id, activo=True).all()
    return render_template('usuarios.html', usuarios=usuarios, roles=roles)
