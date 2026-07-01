from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from models import db, Cliente, Cita
from rutas._helpers import requiere_permiso, tiene_permiso, obtener_hora_ecuador, validar_cedula_ecuatoriana
import requests as http_req
import re

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/clientes')
@login_required
@requiere_permiso('citas.ver')
def index():
    negocio_id = current_user.negocio_id
    q = request.args.get('q', '').strip()
    query = Cliente.query.filter_by(negocio_id=negocio_id)
    if q:
        query = query.filter(db.or_(
            Cliente.nombre.ilike(f'%{q}%'),
            Cliente.cedula.ilike(f'%{q}%'),
            Cliente.telefono.ilike(f'%{q}%')
        ))
    clientes = query.order_by(Cliente.nombre).all()
    return render_template('clientes.html', clientes=clientes, q=q)


@clientes_bp.route('/clientes/nuevo', methods=['POST'])
@login_required
@requiere_permiso('citas.ver')
def nuevo():
    negocio_id = current_user.negocio_id
    try:
        cedula   = request.form.get('cedula', '').strip() or None
        nombre   = request.form.get('nombre', '').strip()
        telefono = request.form.get('telefono', '').strip() or None
        email    = request.form.get('email', '').strip() or None
        notas    = request.form.get('notas', '').strip() or None

        if not nombre:
            flash('El nombre es obligatorio.', 'error')
            return redirect(url_for('clientes.index'))

        if cedula and not validar_cedula_ecuatoriana(cedula):
            flash('La cédula ingresada no es válida.', 'error')
            return redirect(url_for('clientes.index'))

        if cedula:
            existente = Cliente.query.filter_by(negocio_id=negocio_id, cedula=cedula).first()
            if existente:
                flash(f'La cédula {cedula} ya está registrada para "{existente.nombre}".', 'error')
                return redirect(url_for('clientes.index'))

        db.session.add(Cliente(negocio_id=negocio_id, cedula=cedula, nombre=nombre,
                               telefono=telefono, email=email, notas=notas,
                               fecha_registro=obtener_hora_ecuador()))
        db.session.commit()
        flash(f'Cliente "{nombre}" registrado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('clientes.index'))


@clientes_bp.route('/api/cedula/<cedula>')
@login_required
def buscar_cedula_sri(cedula):
    """Consulta opcional al SRI para autocompletar el nombre del titular.

    Es solo una AYUDA: si el SRI está caído o no tiene datos, el registro del
    cliente NO se bloquea. La respuesta incluye 'sri_disponible' para que el
    frontend muestre un mensaje adecuado y permita escribir el nombre a mano.
    """
    # Validación local (24/7, no depende de internet)
    if not validar_cedula_ecuatoriana(cedula):
        return jsonify({'encontrado': False, 'sri_disponible': True,
                        'error': 'La cédula no es válida'})

    ruc = cedula + '001'
    url = (f'https://srienlinea.sri.gob.ec/sri-catastro-sujeto-servicio-internet'
           f'/rest/ConsolidadoContribuyente/obtenerPorNumeroPrincipal?numeroRuc={ruc}')
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}

    # Hasta 2 intentos: el SRI suele fallar de forma intermitente.
    for intento in range(2):
        try:
            resp = http_req.get(url, timeout=6, headers=headers)
            data = resp.json()
            razon = (data.get('razonSocial', '') or '').strip()
            if razon:
                # SRI devuelve APELLIDOS NOMBRES en mayúsculas → Title Case
                return jsonify({'encontrado': True, 'sri_disponible': True,
                                'nombre': razon.title()})
            # SRI respondió, pero no hay datos para esa cédula
            return jsonify({'encontrado': False, 'sri_disponible': True,
                            'error': 'El SRI no tiene datos para esta cédula'})
        except Exception:
            if intento == 0:
                continue  # reintentar una vez
            # SRI caído tras reintentar: no es culpa del usuario, no bloquear
            return jsonify({'encontrado': False, 'sri_disponible': False,
                            'error': 'El SRI no está disponible en este momento'})


@clientes_bp.route('/clientes/<int:id>')
@login_required
@requiere_permiso('citas.ver')
def detalle(id):
    cliente = Cliente.query.get_or_404(id)
    if cliente.negocio_id != current_user.negocio_id:
        abort(403)
    citas = Cita.query.filter_by(cliente_id=id)\
                      .order_by(Cita.fecha.desc(), Cita.hora_inicio.desc()).all()
    return render_template('cliente_detalle.html', cliente=cliente, citas=citas)


@clientes_bp.route('/clientes/<int:id>/editar', methods=['POST'])
@login_required
@requiere_permiso('usuarios.gestionar')
def editar(id):
    cliente = Cliente.query.get_or_404(id)
    if cliente.negocio_id != current_user.negocio_id:
        abort(403)
    try:
        nueva_cedula = request.form.get('cedula', '').strip()
        if nueva_cedula and not validar_cedula_ecuatoriana(nueva_cedula):
            flash('La cédula ingresada no es válida.', 'error')
            return redirect(url_for('clientes.detalle', id=id))
        if nueva_cedula and nueva_cedula != (cliente.cedula or ''):
            existente = Cliente.query.filter_by(
                negocio_id=cliente.negocio_id, cedula=nueva_cedula).first()
            if existente and existente.id != cliente.id:
                flash('Esa cédula ya está registrada para otro cliente.', 'error')
                return redirect(url_for('clientes.detalle', id=id))
        cliente.cedula   = nueva_cedula or None
        cliente.nombre   = request.form.get('nombre', cliente.nombre).strip()
        cliente.telefono = request.form.get('telefono', '').strip() or None
        cliente.email    = request.form.get('email', '').strip() or None
        cliente.notas    = request.form.get('notas', '').strip() or None
        db.session.commit()
        flash('Cliente actualizado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('clientes.detalle', id=id))


@clientes_bp.route('/clientes/<int:id>/eliminar', methods=['POST'])
@login_required
@requiere_permiso('usuarios.gestionar')
def eliminar(id):
    cliente = Cliente.query.get_or_404(id)
    if cliente.negocio_id != current_user.negocio_id:
        abort(403)
    try:
        nombre = cliente.nombre
        Cita.query.filter_by(cliente_id=id).update({'cliente_id': None})
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Cliente "{nombre}" eliminado. Sus citas previas se conservaron.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('clientes.index'))
