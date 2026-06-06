from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models import db, Movimiento, User
from rutas._helpers import obtener_hora_ecuador, requiere_permiso, tiene_permiso
from datetime import datetime, date

contabilidad_bp = Blueprint('contabilidad', __name__)

@contabilidad_bp.route('/contabilidad', methods=['GET', 'POST'])
@login_required
@requiere_permiso('contabilidad.ver')
def index():
    ahora      = obtener_hora_ecuador()
    negocio_id = current_user.negocio_id

    if request.method == 'POST':
        if not tiene_permiso('contabilidad.registrar'):
            flash('Sin permiso.', 'error')
            return redirect(url_for('contabilidad.index'))
        try:
            db.session.add(Movimiento(
                negocio_id=negocio_id, registrado_por=current_user.id,
                tipo=request.form.get('tipo'),
                monto=float(request.form.get('monto')),
                descripcion=request.form.get('descripcion', ''),
                metodo_pago=request.form.get('metodo_pago', ''),
                fecha=ahora))
            db.session.commit()
            flash('Movimiento registrado.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('contabilidad.index'))

    hoy  = ahora.date()
    todos = Movimiento.query.filter_by(negocio_id=negocio_id).order_by(Movimiento.fecha.desc()).all()
    mov_hoy = [m for m in todos if m.fecha.date() == hoy]
    mov_mes = [m for m in todos if m.fecha.month == ahora.month and m.fecha.year == ahora.year]

    ingresos_hoy = sum(m.monto for m in mov_hoy if m.tipo == 'ingreso')
    gastos_hoy   = sum(m.monto for m in mov_hoy if m.tipo == 'gasto')
    ingresos_mes = sum(m.monto for m in mov_mes if m.tipo == 'ingreso')
    gastos_mes   = sum(m.monto for m in mov_mes if m.tipo == 'gasto')

    ventas_por_empleado = {}
    for m in mov_hoy:
        if m.tipo == 'ingreso' and m.registrado_por:
            u = User.query.get(m.registrado_por)
            nombre = u.nombre if u else f'Usuario #{m.registrado_por}'
            ventas_por_empleado[nombre] = ventas_por_empleado.get(nombre, 0) + m.monto

    return render_template('contabilidad.html',
        movimientos=mov_hoy,
        ingresos=ingresos_hoy, gastos=gastos_hoy, utilidad=ingresos_hoy - gastos_hoy,
        ingresos_mes=ingresos_mes, gastos_mes=gastos_mes, utilidad_mes=ingresos_mes - gastos_mes,
        ventas_por_empleado=ventas_por_empleado)


@contabilidad_bp.route('/contabilidad/cerrar_dia', methods=['POST'])
@login_required
@requiere_permiso('contabilidad.cerrar_dia')
def cerrar_dia():
    ahora = obtener_hora_ecuador()
    try:
        pago = float(request.form.get('pago_manicuristas', 0))
        if pago > 0:
            db.session.add(Movimiento(
                negocio_id=current_user.negocio_id, registrado_por=current_user.id,
                tipo='gasto', monto=pago,
                descripcion='Cierre Diario: Pago de comisiones', fecha=ahora))
            db.session.commit()
            flash('Cierre registrado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('contabilidad.index'))


@contabilidad_bp.route('/contabilidad/borrar/<int:id>')
@login_required
@requiere_permiso('contabilidad.registrar')
def borrar(id):
    mov = Movimiento.query.get_or_404(id)
    if mov.negocio_id != current_user.negocio_id:
        abort(403)
    db.session.delete(mov)
    db.session.commit()
    flash('Movimiento eliminado.', 'success')
    return redirect(url_for('contabilidad.index'))


@contabilidad_bp.route('/contabilidad/historial')
@login_required
@requiere_permiso('contabilidad.ver')
def historial():
    negocio_id  = current_user.negocio_id
    ahora       = obtener_hora_ecuador()

    # Filtros GET
    fecha_desde_str = request.args.get('fecha_desde', '')
    fecha_hasta_str = request.args.get('fecha_hasta', '')
    tipo_filtro     = request.args.get('tipo', 'todos')

    try:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d').date() if fecha_desde_str else date(ahora.year, ahora.month, 1)
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d').date() if fecha_hasta_str else ahora.date()
    except ValueError:
        fecha_desde = date(ahora.year, ahora.month, 1)
        fecha_hasta = ahora.date()

    query = Movimiento.query.filter(
        Movimiento.negocio_id == negocio_id,
        Movimiento.fecha >= datetime.combine(fecha_desde, datetime.min.time()),
        Movimiento.fecha <= datetime.combine(fecha_hasta, datetime.max.time())
    )
    if tipo_filtro in ('ingreso', 'gasto'):
        query = query.filter(Movimiento.tipo == tipo_filtro)

    movimientos = query.order_by(Movimiento.fecha.desc()).all()

    total_ingresos = sum(m.monto for m in movimientos if m.tipo == 'ingreso')
    total_gastos   = sum(m.monto for m in movimientos if m.tipo == 'gasto')

    return render_template('historial_ventas.html',
        movimientos=movimientos,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        utilidad=total_ingresos - total_gastos,
        fecha_desde=fecha_desde.strftime('%Y-%m-%d'),
        fecha_hasta=fecha_hasta.strftime('%Y-%m-%d'),
        tipo_filtro=tipo_filtro)
