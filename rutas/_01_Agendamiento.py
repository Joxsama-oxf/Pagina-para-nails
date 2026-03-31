from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Cita, Servicio
from datetime import datetime, timedelta
import json

agendamiento_bp = Blueprint('agendamiento', __name__)

def obtener_hora_ecuador():
    return datetime.utcnow() - timedelta(hours=5)

@agendamiento_bp.route('/agendamiento', methods=['GET', 'POST'])
@login_required
def index():
    ahora = obtener_hora_ecuador()
    hoy_date = ahora.date()
    
    fecha_min_str = hoy_date.strftime('%Y-%m-%d')
    fecha_max_str = (hoy_date + timedelta(days=30)).strftime('%Y-%m-%d')

    fecha_str = request.args.get('fecha')
    if fecha_str:
        try:
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_obj = hoy_date
            
        if fecha_obj < hoy_date or fecha_obj > (hoy_date + timedelta(days=30)):
            return redirect(url_for('agendamiento.index'))
    else:
        fecha_obj = hoy_date

    if request.method == 'POST':
        try:
            estilista = int(request.form.get('stylist_id'))
            cliente = request.form.get('client_name')
            
            servicios_lista = request.form.getlist('service')
            if not servicios_lista:
                flash('Error: Debe seleccionar al menos un servicio.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))
            
            hora_str = request.form.get('time')
            hora_fin_str = request.form.get('time_end')
            
            if not hora_str or not hora_fin_str:
                flash('Error: Rango de tiempo inválido.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            hora_obj = datetime.strptime(hora_str, '%H:%M').time()
            hora_fin_obj = datetime.strptime(hora_fin_str, '%H:%M').time()
            
            fecha_hora_inicio = datetime.combine(fecha_obj, hora_obj)
            fecha_hora_fin = datetime.combine(fecha_obj, hora_fin_obj)
            
            if fecha_hora_inicio < ahora:
                flash('Error: El horario seleccionado ya pasó.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))
                
            if fecha_hora_inicio >= fecha_hora_fin:
                flash('Error: La hora de fin debe ser posterior a la de inicio.', 'error')
                return redirect(url_for('agendamiento.index', fecha=fecha_obj))

            citas_dia = Cita.query.filter_by(stylist_id=estilista, date=fecha_obj).all()
            hay_conflicto = False
            
            for c in citas_dia:
                c_inicio = datetime.combine(fecha_obj, c.time)
                partes = c.service.split('|')
                c_fin_str = partes[1] if len(partes) > 1 else c.time.strftime('%H:%M')
                c_fin_obj = datetime.strptime(c_fin_str, '%H:%M').time()
                c_fin = datetime.combine(fecha_obj, c_fin_obj)
                
                # Condición de superposición de rangos
                if fecha_hora_inicio < c_fin and fecha_hora_fin > c_inicio:
                    hay_conflicto = True
                    break

            if hay_conflicto:
                flash('Error: El horario choca con una cita existente.', 'error')
            else:
                servicio_texto = ", ".join(servicios_lista) + f"|{hora_fin_str}"
                
                nueva_cita = Cita(
                    stylist_id=estilista,
                    client_name=cliente,
                    service=servicio_texto,
                    date=fecha_obj,
                    time=hora_obj
                )
                db.session.add(nueva_cita)
                db.session.commit()
                flash('Cita agendada correctamente', 'success')
                
        except Exception as e:
            flash(f'Error al agendar: {str(e)}', 'error')
        
        return redirect(url_for('agendamiento.index', fecha=fecha_obj))

    citas_1 = Cita.query.filter_by(date=fecha_obj, stylist_id=1).order_by(Cita.time).all()
    citas_2 = Cita.query.filter_by(date=fecha_obj, stylist_id=2).order_by(Cita.time).all()
    
    rangos_ocupados = {"1": [], "2": []}
    for c in citas_1:
        partes = c.service.split('|')
        fin = partes[1] if len(partes) > 1 else c.time.strftime('%H:%M')
        rangos_ocupados["1"].append({"start": c.time.strftime('%H:%M'), "end": fin})
        
    for c in citas_2:
        partes = c.service.split('|')
        fin = partes[1] if len(partes) > 1 else c.time.strftime('%H:%M')
        rangos_ocupados["2"].append({"start": c.time.strftime('%H:%M'), "end": fin})
    
    servicios_bd = Servicio.query.all() 

    return render_template('agendamiento.html', 
                           fecha=fecha_obj, 
                           citas_1=citas_1, 
                           citas_2=citas_2,
                           servicios=servicios_bd,
                           rangos_ocupados=json.dumps(rangos_ocupados),
                           fecha_min=fecha_min_str,
                           fecha_max=fecha_max_str)

@agendamiento_bp.route('/borrar/<int:id>')
@login_required
def borrar(id):
    cita = Cita.query.get_or_404(id)
    try:
        db.session.delete(cita)
        db.session.commit()
        flash('Registro eliminado correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar: {str(e)}', 'error')
    return redirect(request.referrer or url_for('agendamiento.index'))

@agendamiento_bp.route('/historial_citas')
@login_required
def historial():
    ahora = obtener_hora_ecuador()
    hoy_date = ahora.date()
    citas_pasadas = Cita.query.filter(Cita.date < hoy_date).order_by(Cita.date.desc(), Cita.time).all()
    return render_template('historial_citas.html', citas=citas_pasadas)