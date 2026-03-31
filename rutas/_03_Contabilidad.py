from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import db, Movimiento
from datetime import datetime, date

contabilidad_bp = Blueprint('contabilidad', __name__)

@contabilidad_bp.route('/contabilidad', methods=['GET', 'POST'])
@login_required
def index():
    # REGISTRAR NUEVO MOVIMIENTO
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo')
            monto = float(request.form.get('monto'))
            descripcion = request.form.get('descripcion')
            
            nuevo_mov = Movimiento(tipo=tipo, monto=monto, descripcion=descripcion, fecha=datetime.now())
            db.session.add(nuevo_mov)
            db.session.commit()
            flash('Movimiento registrado', 'success')
        except Exception as e:
            flash(f'Error al registrar: {str(e)}', 'error')
            
        return redirect(url_for('contabilidad.index'))

    # EXTRACCIÓN Y SEGMENTACIÓN DE DATOS
    todos_movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).all()
    hoy = date.today()
    mes_actual = datetime.now().month
    ano_actual = datetime.now().year

    # Filtros de matrices
    movimientos_hoy = [m for m in todos_movimientos if m.fecha.date() == hoy]
    movimientos_mes = [m for m in todos_movimientos if m.fecha.month == mes_actual and m.fecha.year == ano_actual]

    # Cálculos Diarios
    ingresos_hoy = sum(m.monto for m in movimientos_hoy if 'Ingreso' in m.tipo)
    gastos_hoy = sum(m.monto for m in movimientos_hoy if 'Gasto' in m.tipo)
    utilidad_hoy = ingresos_hoy - gastos_hoy

    # Cálculos Mensuales
    ingresos_mes = sum(m.monto for m in movimientos_mes if 'Ingreso' in m.tipo)
    gastos_mes = sum(m.monto for m in movimientos_mes if 'Gasto' in m.tipo)
    utilidad_mes = ingresos_mes - gastos_mes

    return render_template('contabilidad.html', 
                           movimientos=movimientos_hoy, 
                           ingresos=ingresos_hoy, 
                           gastos=gastos_hoy, 
                           utilidad=utilidad_hoy,
                           ingresos_mes=ingresos_mes,
                           gastos_mes=gastos_mes,
                           utilidad_mes=utilidad_mes)

@contabilidad_bp.route('/contabilidad/cerrar_dia', methods=['POST'])
@login_required
def cerrar_dia():
    try:
        pago_manicuristas = float(request.form.get('pago_manicuristas', 0))
        if pago_manicuristas > 0:
            nuevo_mov = Movimiento(
                tipo='Gasto', 
                monto=pago_manicuristas, 
                descripcion='Cierre Diario: Pago a Manicuristas', 
                fecha=datetime.now()
            )
            db.session.add(nuevo_mov)
            db.session.commit()
            flash('Cierre diario ejecutado y comisiones descontadas', 'success')
    except Exception as e:
        flash(f'Error en cierre: {str(e)}', 'error')
        
    return redirect(url_for('contabilidad.index'))

@contabilidad_bp.route('/contabilidad/borrar/<int:id>')
@login_required
def borrar(id):
    movimiento = Movimiento.query.get_or_404(id)
    db.session.delete(movimiento)
    db.session.commit()
    flash('Movimiento eliminado correctamente', 'success')
    return redirect(url_for('contabilidad.index'))