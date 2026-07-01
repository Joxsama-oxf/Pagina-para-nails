import re
from functools import wraps
from flask import abort
from flask_login import current_user
from datetime import datetime, timedelta, timezone

def validar_cedula_ecuatoriana(cedula: str) -> bool:
    """Valida una cédula ecuatoriana (mismo algoritmo que el JS del frontend).

    Reglas: 10 dígitos, código de provincia válido (01-24 ó 30) y dígito
    verificador correcto (algoritmo módulo 10). Devuelve True si es válida.
    """
    if not cedula or not re.match(r'^\d{10}$', cedula):
        return False
    provincia = int(cedula[:2])
    if provincia < 1 or (provincia > 24 and provincia != 30):
        return False
    digitos = [int(c) for c in cedula]
    suma = 0
    for i in range(9):
        valor = digitos[i]
        if i % 2 == 0:          # posiciones impares (índice par) se multiplican por 2
            valor *= 2
            if valor > 9:
                valor -= 9
        suma += valor
    verificador = (10 - (suma % 10)) % 10
    return verificador == digitos[9]

def tiene_permiso(codigo: str) -> bool:
    if not current_user.is_authenticated:
        return False
    if current_user.es_superadmin:
        return True
    for rol in current_user.roles:
        for permiso in rol.permisos:
            if permiso.codigo == codigo:
                return True
    return False

def requiere_permiso(codigo: str):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not tiene_permiso(codigo):
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

def obtener_hora_ecuador():
    # Hora local de Ecuador (UTC-5) como datetime naive, sin usar utcnow() (deprecado).
    return datetime.now(timezone(timedelta(hours=-5))).replace(tzinfo=None)

def formatear_telefono_ec(telefono: str):
    """Convierte un teléfono ecuatoriano al formato internacional para WhatsApp.

    Ej: '0999999999' -> '593999999999'.  Devuelve None si no es usable.
    Acepta números con espacios, guiones o el prefijo 593 ya puesto.
    """
    if not telefono:
        return None
    num = re.sub(r'\D', '', telefono)   # solo dígitos
    if not num:
        return None
    if num.startswith('593'):
        intl = num
    elif num.startswith('0'):
        intl = '593' + num[1:]
    else:
        intl = '593' + num
    # Validación mínima: 593 + 8 a 10 dígitos
    if not (11 <= len(intl) <= 13):
        return None
    return intl
