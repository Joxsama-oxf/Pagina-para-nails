from ._00_Inicio         import inicio_bp
from ._01_Agendamiento   import agendamiento_bp
from ._02_Facturacion    import facturacion_bp
from ._03_Contabilidad   import contabilidad_bp
from ._04_Redes          import redes_bp
from ._05_Auth           import auth_bp
from ._06_AdminServicios import admin_servicios_bp
from ._07_Usuarios       import usuarios_bp

def register_blueprints(app):
    app.register_blueprint(inicio_bp)
    app.register_blueprint(agendamiento_bp)
    app.register_blueprint(facturacion_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(redes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_servicios_bp)
    app.register_blueprint(usuarios_bp)
