from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

# Tabla de Usuarios (Para el Login: Admin vs Empleada)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin' o 'empleada'

# Tabla para Agendamiento
class Cita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stylist_id = db.Column(db.Integer, nullable=False) # 1 o 2
    client_name = db.Column(db.String(100), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='pendiente')

# Tabla para Contabilidad (Ingresos y Egresos)
class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False) # 'ingreso' o 'egreso'
    monto = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Tabla para Lista de Precios (Facturación)
class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    precio_promocion = db.Column(db.Float, nullable=True)
    fecha_fin_promocion = db.Column(db.Date, nullable=True)

    @property
    def precio_actual(self):
        from datetime import datetime, timedelta
        hoy = (datetime.utcnow() - timedelta(hours=5)).date()
        if self.precio_promocion and self.fecha_fin_promocion and self.fecha_fin_promocion >= hoy:
            return self.precio_promocion
        return self.precio