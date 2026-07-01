from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from datetime import datetime
from models import Cita, Movimiento, Cliente
from rutas._helpers import obtener_hora_ecuador, tiene_permiso

inicio_bp = Blueprint('inicio', __name__)

DIAS_ES  = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
MESES_ES = ['','enero','febrero','marzo','abril','mayo','junio',
            'julio','agosto','septiembre','octubre','noviembre','diciembre']

@inicio_bp.route('/')
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    ahora      = obtener_hora_ecuador()
    hoy        = ahora.date()
    negocio_id = current_user.negocio_id

    # Permisos que definen QUÉ ve cada quien en el panel
    ve_todo   = tiene_permiso('usuarios.ver')      # admin: todo el negocio
    ve_dinero = tiene_permiso('contabilidad.ver')  # admin: ingresos/utilidad

    # Saludo según la hora
    if ahora.hour < 12:
        saludo = 'Buenos días'
    elif ahora.hour < 19:
        saludo = 'Buenas tardes'
    else:
        saludo = 'Buenas noches'

    # --- Citas de hoy (todas si es admin, solo las propias si es manicurista) ---
    q_citas = Cita.query.filter_by(negocio_id=negocio_id, fecha=hoy)
    if not ve_todo:
        q_citas = q_citas.filter_by(empleado_id=current_user.id)
    citas_hoy = q_citas.order_by(Cita.hora_inicio).all()

    total_citas      = len(citas_hoy)
    citas_pendientes = sum(1 for c in citas_hoy if c.estado == 'pendiente')
    citas_pagadas    = sum(1 for c in citas_hoy if c.estado == 'pagada')

    # --- Próximas citas de hoy (desde la hora actual, aún no pagadas) ---
    hora_actual = ahora.time()
    proximas = [c for c in citas_hoy
                if c.hora_inicio >= hora_actual and c.estado != 'pagada'][:6]

    # --- Dinero del día (solo si tiene permiso de contabilidad) ---
    ingresos_hoy = gastos_hoy = utilidad_hoy = 0.0
    if ve_dinero:
        inicio_dia = datetime.combine(hoy, datetime.min.time())
        fin_dia    = datetime.combine(hoy, datetime.max.time())
        movs_hoy = Movimiento.query.filter(
            Movimiento.negocio_id == negocio_id,
            Movimiento.fecha >= inicio_dia,
            Movimiento.fecha <= fin_dia).all()
        ingresos_hoy = sum(m.monto for m in movs_hoy if m.tipo == 'ingreso')
        gastos_hoy   = sum(m.monto for m in movs_hoy if m.tipo == 'gasto')
        utilidad_hoy = ingresos_hoy - gastos_hoy

    # Total de clientes (solo admin)
    total_clientes = 0
    if ve_todo:
        total_clientes = Cliente.query.filter_by(negocio_id=negocio_id).count()

    fecha_label = f"{DIAS_ES[hoy.weekday()]} {hoy.day} de {MESES_ES[hoy.month]}"

    return render_template('index.html',
        saludo=saludo, ahora=ahora, fecha_label=fecha_label,
        ve_todo=ve_todo, ve_dinero=ve_dinero,
        total_citas=total_citas, citas_pendientes=citas_pendientes,
        citas_pagadas=citas_pagadas, proximas=proximas,
        ingresos_hoy=ingresos_hoy, gastos_hoy=gastos_hoy, utilidad_hoy=utilidad_hoy,
        total_clientes=total_clientes)
