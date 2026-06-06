from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Movimiento, Cita, Servicio, CategoriaServicio
from rutas._helpers import obtener_hora_ecuador, requiere_permiso, tiene_permiso
from datetime import datetime, timedelta
import json

facturacion_bp = Blueprint('facturacion', __name__)

@facturacion_bp.route('/facturacion', methods=['GET', 'POST'])
@login_required
@requiere_permiso('facturacion.ver')
def index():
    ahora      = obtener_hora_ecuador()
    hoy        = ahora.date()
    negocio_id = current_user.negocio_id

    if request.method == 'POST':
        if not tiene_permiso('facturacion.cobrar'):
            flash('Sin permiso para cobrar.', 'error')
            return redirect(url_for('facturacion.index'))
        try:
            total        = float(request.form.get('total_hidden', 0))
            descripcion  = request.form.get('descripcion_hidden', '')
            metodo_pago  = request.form.get('metodo_pago', 'efectivo')
            cita_id_str  = request.form.get('cita_id', '')
            cita_id      = int(cita_id_str) if cita_id_str.isdigit() else None

            if total <= 0:
                flash('El monto debe ser mayor a 0.', 'error')
                return redirect(url_for('facturacion.index'))

            if cita_id:
                cita = Cita.query.filter_by(id=cita_id, negocio_id=negocio_id).first()
                if cita:
                    cita.estado = 'pagada'

            db.session.add(Movimiento(
                negocio_id=negocio_id, cita_id=cita_id,
                registrado_por=current_user.id, tipo='ingreso',
                monto=total, descripcion=f"Venta: {descripcion}",
                metodo_pago=metodo_pago, fecha=ahora))
            db.session.commit()
            flash('Venta registrada.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('facturacion.index'))

    # GET
    if tiene_permiso('usuarios.ver'):
        citas_hoy = Cita.query.filter_by(negocio_id=negocio_id, fecha=hoy).order_by(Cita.hora_inicio).all()
    else:
        citas_hoy = Cita.query.filter_by(negocio_id=negocio_id, fecha=hoy,
                                          empleado_id=current_user.id).order_by(Cita.hora_inicio).all()

    categorias   = CategoriaServicio.query.filter_by(negocio_id=negocio_id).order_by(CategoriaServicio.orden).all()
    servicios_bd = Servicio.query.filter_by(negocio_id=negocio_id, activo=True).all()
    mapa_precios = {s.nombre: s.precio_actual for s in servicios_bd}

    return render_template('facturacion.html',
        citas=citas_hoy, categorias=categorias,
        servicios=servicios_bd, precios=json.dumps(mapa_precios))
