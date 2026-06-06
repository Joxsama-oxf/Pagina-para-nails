from functools import wraps
from flask import abort
from flask_login import current_user
from datetime import datetime, timedelta

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
    return datetime.utcnow() - timedelta(hours=5)
