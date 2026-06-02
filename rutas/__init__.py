#   --> |Aqui va el codigo de inicializacion del paquete rutas init| <--   #

# rutas/__init__.py

# Importamos los nuevos módulos de Laura Nails
# Nota: Deberás crear estas carpetas en el siguiente paso
from ._00_Inicio import inicio_bp
from ._01_Agendamiento import agendamiento_bp
from ._02_Facturacion import facturacion_bp
from ._03_Contabilidad import contabilidad_bp
from ._04_Redes import redes_bp
from ._05_Auth import auth_bp
from ._06_AdminServicios import admin_servicios_bp



#   --> |Aqui van las funciones para registrar los blueprints| <--   #
#--------------------------------------------------------------------------------------------------------------------------------------------#
def register_blueprints(app):
    # Registramos los blueprints en la aplicación principal
    app.register_blueprint(inicio_bp)
    app.register_blueprint(agendamiento_bp)
    app.register_blueprint(facturacion_bp)
    app.register_blueprint(contabilidad_bp)
    app.register_blueprint(redes_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_servicios_bp)
#--------------------------------------------------------------------------------------------------------------------------------------------#
