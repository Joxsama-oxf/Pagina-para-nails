from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from models import db, Movimiento
from datetime import datetime, date, timedelta
import re

contabilidad_bp = Blueprint('contabilidad', __name__)

def obtener_hora_ecuador():
    return datetime.utcnow() - timedelta(hours=5)

@contabilidad_bp.route('/contabilidad', methods=['GET', 'POST'])
@login_required
def index():
    ahora = obtener_hora_ecuador()
    # REGISTRAR NUEVO MOVIMIENTO
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo')
            monto = float(request.form.get('monto'))
            descripcion = request.form.get('descripcion')
            
            nuevo_mov = Movimiento(tipo=tipo, monto=monto, descripcion=descripcion, fecha=ahora)
            db.session.add(nuevo_mov)
            db.session.commit()
            flash('Movimiento registrado', 'success')
        except Exception as e:
            flash(f'Error al registrar: {str(e)}', 'error')
            
        return redirect(url_for('contabilidad.index'))

    # EXTRACCIÓN Y SEGMENTACIÓN DE DATOS
    todos_movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).all()
    hoy = ahora.date()
    mes_actual = ahora.month
    ano_actual = ahora.year

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

    # Lógica de desglose de ventas por manicurista para el cierre de caja
    ventas_por_manicurista = {}
    
    for m in movimientos_hoy:
        if 'Ingreso' in m.tipo and 'Cobrado por:' in m.descripcion:
            # Extraer el nombre/ID después de "Cobrado por: " usando expresiones regulares
            match = re.search(r'Cobrado por:\s*(.+)$', m.descripcion)
            if match:
                cobrador = match.group(1).strip()
                if cobrador in ventas_por_manicurista:
                    ventas_por_manicurista[cobrador] += m.monto
                else:
                    ventas_por_manicurista[cobrador] = m.monto

    return render_template('contabilidad.html', 
                           movimientos=movimientos_hoy, 
                           ingresos=ingresos_hoy, 
                           gastos=gastos_hoy, 
                           utilidad=utilidad_hoy,
                           ingresos_mes=ingresos_mes,
                           gastos_mes=gastos_mes,
                           utilidad_mes=utilidad_mes,
                           ventas_por_manicurista=ventas_por_manicurista)

@contabilidad_bp.route('/contabilidad/cerrar_dia', methods=['POST'])
@login_required
def cerrar_dia():
    ahora = obtener_hora_ecuador()
    try:
        pago_manicuristas = float(request.form.get('pago_manicuristas', 0))
        # Extraer pagos individuales si se mandan del form (Opcional, si quieres registrar desglosado)
        if pago_manicuristas > 0:
            nuevo_mov = Movimiento(
                tipo='Gasto', 
                monto=pago_manicuristas, 
                descripcion='Cierre Diario: Pago de comisiones consolidado', 
                fecha=ahora
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