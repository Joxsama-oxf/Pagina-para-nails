from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Servicio, HistorialPrecio, CategoriaServicio
from rutas._helpers import obtener_hora_ecuador, requiere_permiso
from datetime import datetime, timedelta

admin_servicios_bp = Blueprint('admin_servicios', __name__)

@admin_servicios_bp.route('/admin/servicios', methods=['GET', 'POST'])
@login_required
@requiere_permiso('servicios.editar')
def index():
    ahora      = obtener_hora_ecuador()
    hoy        = ahora.date()
    negocio_id = current_user.negocio_id

    if request.method == 'POST':
        accion = request.form.get('accion')
        try:
            if accion == 'agregar_categoria':
                nombre = request.form.get('nombre_categoria', '').strip()
                if nombre:
                    db.session.add(CategoriaServicio(negocio_id=negocio_id, nombre=nombre, orden=0))
                    db.session.commit()
                    flash('Categoría agregada.', 'success')

            elif accion == 'eliminar_categoria':
                cat = CategoriaServicio.query.get_or_404(int(request.form.get('id')))
                if cat.negocio_id != negocio_id: abort(403)
                db.session.delete(cat)
                db.session.commit()
                flash('Categoría eliminada.', 'success')

            elif accion == 'agregar':
                cat_id = request.form.get('categoria_id') or None
                nuevo  = Servicio(negocio_id=negocio_id,
                                  categoria_id=int(cat_id) if cat_id else None,
                                  nombre=request.form.get('nombre','').strip(),
                                  duracion_min=int(request.form.get('duracion_min', 60)),
                                  activo=True)
                db.session.add(nuevo)
                db.session.flush()
                db.session.add(HistorialPrecio(
                    servicio_id=nuevo.id, precio=float(request.form.get('precio')),
                    es_promocion=False, fecha_inicio=hoy, motivo='Precio inicial'))
                db.session.commit()
                flash('Servicio agregado.', 'success')

            elif accion == 'editar':
                serv = Servicio.query.get_or_404(int(request.form.get('id')))
                if serv.negocio_id != negocio_id: abort(403)
                nuevo_precio = float(request.form.get('precio'))
                cat_id = request.form.get('categoria_id') or None
                serv.nombre       = request.form.get('nombre', serv.nombre).strip()
                serv.duracion_min = int(request.form.get('duracion_min', serv.duracion_min))
                serv.categoria_id = int(cat_id) if cat_id else None
                if nuevo_precio != serv.precio_actual:
                    db.session.add(HistorialPrecio(
                        servicio_id=serv.id, precio=nuevo_precio,
                        es_promocion=False, fecha_inicio=hoy, motivo='Actualización'))
                db.session.commit()
                flash('Servicio actualizado.', 'success')

            elif accion == 'promocion':
                serv = Servicio.query.get_or_404(int(request.form.get('id')))
                if serv.negocio_id != negocio_id: abort(403)
                fecha_fin = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
                db.session.add(HistorialPrecio(
                    servicio_id=serv.id, precio=float(request.form.get('precio_promocion')),
                    es_promocion=True, fecha_inicio=hoy, fecha_fin=fecha_fin, motivo='Promoción'))
                db.session.commit()
                flash('Promoción activada.', 'success')

            elif accion == 'quitar_promocion':
                serv = Servicio.query.get_or_404(int(request.form.get('id')))
                if serv.negocio_id != negocio_id: abort(403)
                promo = serv.promo_activa
                if promo:
                    promo.fecha_fin = hoy - timedelta(days=1)
                    db.session.commit()
                flash('Promoción retirada.', 'success')

            elif accion == 'eliminar':
                serv = Servicio.query.get_or_404(int(request.form.get('id')))
                if serv.negocio_id != negocio_id: abort(403)
                db.session.delete(serv)
                db.session.commit()
                flash('Servicio eliminado.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_servicios.index'))

    categorias = CategoriaServicio.query.filter_by(negocio_id=negocio_id).order_by(CategoriaServicio.orden).all()
    servicios  = Servicio.query.filter_by(negocio_id=negocio_id).order_by(Servicio.nombre).all()
    return render_template('admin_servicios.html', servicios=servicios, categorias=categorias, hoy=hoy)
