from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, Cita, CitaServicio, Servicio, User, Cliente
from rutas._helpers import obtener_hora_ecuador, requiere_permiso, tiene_permiso, validar_cedula_ecuatoriana
from datetime import datetime, timedelta
import json

agendamiento_bp = Blueprint('agendamiento', __name__)

DIAS_ES  = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
MESES_ES = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio',
            'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

def _es_staff(user):
    tiene_citas = tiene_cont = False
    for rol in user.roles:
        for p in rol.permisos:
            if p.codigo == 'citas.ver':        tiene_citas = True
            if p.codigo == 'contabilidad.ver': tiene_cont  = True
    return tiene_citas and not tiene_cont


@agendamiento_bp.route('/agendamiento', methods=['GET', 'POST'])
@login_required
@requiere_permiso('citas.ver')
def index():
    ahora      = obtener_hora_ecuador()
    hoy_date   = ahora.date()
    negocio_id = current_user.negocio_id

    fecha_min_str = hoy_date.strftime('%Y-%m-%d')
    fecha_max_str = (hoy_date + timedelta(days=30)).strftime('%Y-%m-%d')

    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_obj = hoy_date
        if fecha_obj < hoy_date or fecha_obj > hoy_date + timedelta(days=30):
            return redirect(url_for('agendamiento.index'))
    else:
        fecha_obj = hoy_date

    if request.method == 'POST':
        if not tiene_permiso('citas.crear'):
            flash('Sin permiso para agendar.', 'error')
            return redirect(url_for('agendamiento.index', fecha=fecha_obj))
        try:
            empleado_id      = int(request.form.get('empleado_id'))
            cedula           = request.form.get('cedula', '').strip()
            nombre_cliente   = request.form.get('nombre_cliente', '').strip()
            telefono_cliente = request.form.get('telefono_cliente', '').strip()
            servicio_ids     = request.form.getlist('servicio_id')
            hora_ini_str     = request.form.get('hora_inicio')
            hora_fin_str     = request.form.get('hora_fin')

            if not nombre_cliente or not servicio_ids or not hora_ini_str or not hora_fin_str:
                flash('Completa todos los campos obligatorios.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            if cedula and not validar_cedula_ecuatoriana(cedula):
                flash('La cédula ingresada no es válida.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            hora_ini_obj = datetime.strptime(hora_ini_str, '%H:%M').time()
            hora_fin_obj = datetime.strptime(hora_fin_str, '%H:%M').time()
            dt_inicio    = datetime.combine(fecha_obj, hora_ini_obj)
            dt_fin       = datetime.combine(fecha_obj, hora_fin_obj)

            if dt_inicio < ahora:
                flash('Ese horario ya pasó.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))
            if dt_inicio >= dt_fin:
                flash('La hora de fin debe ser posterior al inicio.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            citas_dia = Cita.query.filter_by(
                negocio_id=negocio_id, empleado_id=empleado_id, fecha=fecha_obj).all()
            if any(dt_inicio < datetime.combine(fecha_obj, c.hora_fin) and
                   dt_fin    > datetime.combine(fecha_obj, c.hora_inicio) for c in citas_dia):
                flash('El horario choca con una cita existente.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            # Buscar cliente: primero por cédula, luego por nombre (ilike)
            cliente_obj = None
            if cedula:
                cliente_obj = Cliente.query.filter_by(
                    negocio_id=negocio_id, cedula=cedula).first()
            if not cliente_obj:
                cliente_obj = Cliente.query.filter(
                    Cliente.negocio_id == negocio_id,
                    Cliente.nombre.ilike(nombre_cliente)
                ).first()

            if cliente_obj:
                # Actualizar datos si el cliente existe pero le faltaba info
                if cedula and not cliente_obj.cedula:
                    cliente_obj.cedula = cedula
                if telefono_cliente and not cliente_obj.telefono:
                    cliente_obj.telefono = telefono_cliente
            else:
                # Crear nuevo cliente
                cliente_obj = Cliente(
                    negocio_id=negocio_id,
                    cedula=cedula or None,
                    nombre=nombre_cliente,
                    telefono=telefono_cliente or None
                )
                db.session.add(cliente_obj)
                db.session.flush()

            nueva = Cita(
                negocio_id=negocio_id, empleado_id=empleado_id,
                cliente_id=cliente_obj.id,
                nombre_cliente=cliente_obj.nombre,
                telefono_cliente=telefono_cliente or cliente_obj.telefono,
                fecha=fecha_obj, hora_inicio=hora_ini_obj, hora_fin=hora_fin_obj,
                estado='pendiente', notas=request.form.get('notas', '')
            )
            db.session.add(nueva)
            db.session.flush()

            for sid in servicio_ids:
                serv = Servicio.query.get(int(sid))
                if serv:
                    db.session.add(CitaServicio(
                        cita_id=nueva.id, servicio_id=serv.id,
                        precio_cobrado=serv.precio_actual))

            db.session.commit()
            flash(f'Cita agendada para {cliente_obj.nombre}.', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('agendamiento.index', fecha=fecha_obj))

    # GET
    todos_activos      = User.query.filter_by(negocio_id=negocio_id, activo=True).all()
    staff_agenda       = [u for u in todos_activos if _es_staff(u)]
    empleados_visibles = staff_agenda if tiene_permiso('usuarios.ver') else \
                         ([current_user] if _es_staff(current_user) else [])

    citas_por_empleado = {
        emp.id: Cita.query.filter_by(negocio_id=negocio_id, empleado_id=emp.id, fecha=fecha_obj)
                          .order_by(Cita.hora_inicio).all()
        for emp in empleados_visibles
    }
    rangos_ocupados = {
        str(emp.id): [
            {"start": c.hora_inicio.strftime('%H:%M'), "end": c.hora_fin.strftime('%H:%M')}
            for c in Cita.query.filter_by(negocio_id=negocio_id,
                                          empleado_id=emp.id, fecha=fecha_obj).all()
        ]
        for emp in staff_agenda
    }

    servicios_bd = Servicio.query.filter_by(negocio_id=negocio_id, activo=True).all()

    # Datos de clientes para búsqueda en JS (por cédula y por nombre)
    todos_clientes = Cliente.query.filter_by(negocio_id=negocio_id).all()
    clientes_por_cedula = {
        c.cedula: {'nombre': c.nombre, 'telefono': c.telefono or ''}
        for c in todos_clientes if c.cedula
    }
    clientes_por_nombre = {
        c.nombre.lower(): {'nombre': c.nombre, 'telefono': c.telefono or '', 'cedula': c.cedula or ''}
        for c in todos_clientes
    }

    fecha_prev  = fecha_obj - timedelta(days=1)
    fecha_next  = fecha_obj + timedelta(days=1)
    fecha_label = f"{DIAS_ES[fecha_obj.weekday()]} {fecha_obj.day} de {MESES_ES[fecha_obj.month]}"

    return render_template('agendamiento.html',
        fecha=fecha_obj, fecha_prev=fecha_prev, fecha_next=fecha_next,
        fecha_label=fecha_label, empleados_visibles=empleados_visibles,
        todos_empleados=staff_agenda, citas_por_empleado=citas_por_empleado,
        servicios=servicios_bd, rangos_ocupados=json.dumps(rangos_ocupados),
        fecha_min=fecha_min_str, fecha_max=fecha_max_str,
        clientes_por_cedula=json.dumps(clientes_por_cedula),
        clientes_por_nombre=json.dumps(clientes_por_nombre))


@agendamiento_bp.route('/borrar/<int:id>', methods=['POST'])
@login_required
@requiere_permiso('citas.borrar')
def borrar(id):
    cita = Cita.query.get_or_404(id)
    if cita.negocio_id != current_user.negocio_id:
        abort(403)
    db.session.delete(cita)
    db.session.commit()
    flash('Cita eliminada.', 'success')
    return redirect(request.referrer or url_for('agendamiento.index'))


@agendamiento_bp.route('/historial_citas')
@login_required
@requiere_permiso('citas.ver')
def historial():
    ahora = obtener_hora_ecuador()
    q = Cita.query.filter(Cita.negocio_id == current_user.negocio_id,
                          Cita.fecha < ahora.date())
    if not tiene_permiso('usuarios.ver'):
        q = q.filter(Cita.empleado_id == current_user.id)
    citas = q.order_by(Cita.fecha.desc(), Cita.hora_inicio).all()
    return render_template('historial_citas.html', citas=citas)
