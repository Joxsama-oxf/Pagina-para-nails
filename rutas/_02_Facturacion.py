from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
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
            
            if total_venta > 0:
                nuevo_ingreso = Movimiento(
                    tipo='Ingreso (+)',
                    monto=total_venta,
                    descripcion=f"Venta: {descripcion_venta}",
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

    citas_hoy = Cita.query.filter_by(date=hoy).order_by(Cita.time).all()
    servicios_bd = Servicio.query.all()
    mapa_precios = {s.nombre: s.precio_actual for s in servicios_bd}

    return render_template('facturacion.html', citas=citas_hoy, precios=json.dumps(mapa_precios))