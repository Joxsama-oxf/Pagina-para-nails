from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Movimiento, Cita, Servicio
from datetime import datetime, timedelta
import json

facturacion_bp = Blueprint('facturacion', __name__)

def obtener_hora_ecuador():
    return datetime.utcnow() - timedelta(hours=5)

@facturacion_bp.route('/facturacion', methods=['GET', 'POST'])
@login_required
def index():
    ahora = obtener_hora_ecuador()
    hoy = ahora.date()
    
    if request.method == 'POST':
        try:
            total_venta = float(request.form.get('total_hidden'))
            descripcion_venta = request.form.get('descripcion_hidden')
            
            # Identificador de quién está cobrando
            if current_user.role == 'admin':
                cobrador = "Admin"
            else:
                # Extrae el usuario antes del @ en el correo para identificar a la manicurista
                cobrador = f"Manicurista {current_user.id} ({current_user.email.split('@')[0]})"
            
            if total_venta > 0:
                nuevo_ingreso = Movimiento(
                    tipo='Ingreso (+)',
                    monto=total_venta,
                    # Se inyecta la firma en la descripción para la contabilidad
                    descripcion=f"Venta: {descripcion_venta} | Cobrado por: {cobrador}",
                    fecha=ahora
                )
                db.session.add(nuevo_ingreso)
                db.session.commit()
                flash('Venta registrada y guardada en contabilidad', 'success')
            else:
                flash('El monto debe ser mayor a 0', 'error')
                
        except Exception as e:
            flash(f'Error al procesar venta: {str(e)}', 'error')
            
        return redirect(url_for('facturacion.index'))

    # Filtrado por usuario logueado
    if current_user.role == 'admin':
        citas_hoy = Cita.query.filter_by(date=hoy).order_by(Cita.time).all()
    else:
        citas_hoy = Cita.query.filter_by(date=hoy, stylist_id=current_user.id).order_by(Cita.time).all()

    servicios_bd = Servicio.query.all()
    mapa_precios = {s.nombre: s.precio_actual for s in servicios_bd}

    return render_template('facturacion.html', 
                           citas=citas_hoy, 
                           precios=json.dumps(mapa_precios),
                           es_admin=(current_user.role == 'admin'))