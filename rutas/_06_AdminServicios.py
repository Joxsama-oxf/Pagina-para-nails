from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Servicio
from datetime import datetime, timedelta
from sqlalchemy import text

admin_servicios_bp = Blueprint('admin_servicios', __name__)

def obtener_hora_ecuador():
    return datetime.utcnow() - timedelta(hours=5)

@admin_servicios_bp.route('/admin/servicios', methods=['GET', 'POST'])
@login_required
def index():
    try:
        db.session.execute(text("ALTER TABLE servicio ADD COLUMN precio_promocion FLOAT"))
        db.session.execute(text("ALTER TABLE servicio ADD COLUMN fecha_fin_promocion DATE"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    ahora = obtener_hora_ecuador()
    hoy = ahora.date()

    if request.method == 'POST':
        try:
            accion = request.form.get('accion')
            
            if accion == 'agregar':
                nombre = request.form.get('nombre')
                precio = float(request.form.get('precio'))
                nuevo_servicio = Servicio(nombre=nombre, precio=precio)
                db.session.add(nuevo_servicio)
                db.session.commit()
                flash('Servicio agregado', 'success')
                
            elif accion == 'editar':
                id_servicio = int(request.form.get('id'))
                servicio = Servicio.query.get(id_servicio)
                if servicio:
                    servicio.nombre = request.form.get('nombre')
                    servicio.precio = float(request.form.get('precio'))
                    db.session.commit()
                    flash('Precio base actualizado', 'success')

            elif accion == 'promocion':
                id_servicio = int(request.form.get('id'))
                servicio = Servicio.query.get(id_servicio)
                if servicio:
                    servicio.precio_promocion = float(request.form.get('precio_promocion'))
                    servicio.fecha_fin_promocion = datetime.strptime(request.form.get('fecha_fin'), '%Y-%m-%d').date()
                    db.session.commit()
                    flash('Promoción activada', 'success')
                    
            elif accion == 'quitar_promocion':
                id_servicio = int(request.form.get('id'))
                servicio = Servicio.query.get(id_servicio)
                if servicio:
                    servicio.precio_promocion = None
                    servicio.fecha_fin_promocion = None
                    db.session.commit()
                    flash('Promoción retirada', 'success')
                    
            elif accion == 'eliminar':
                id_servicio = int(request.form.get('id'))
                servicio = Servicio.query.get(id_servicio)
                if servicio:
                    db.session.delete(servicio)
                    db.session.commit()
                    flash('Registro eliminado', 'success')
                    
        except Exception as e:
            flash(f'Error en la operación: {str(e)}', 'error')

        return redirect(url_for('admin_servicios.index'))

    servicios_db = Servicio.query.order_by(Servicio.nombre).all()
    return render_template('admin_servicios.html', servicios=servicios_db, hoy=hoy)