from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta, timezone

db = SQLAlchemy()

# Zona horaria de Ecuador (UTC-5, sin horario de verano).
_TZ_ECUADOR = timezone(timedelta(hours=-5))

def hora_ecuador():
    """Hora local de Ecuador como datetime naive (sin tzinfo).

    Reemplaza a datetime.utcnow(), deprecado desde Python 3.12, y además
    corrige el desfase: antes las fechas de registro se guardaban en UTC
    (5 horas adelantadas respecto al resto del sistema).
    """
    return datetime.now(_TZ_ECUADOR).replace(tzinfo=None)

user_rol = db.Table('user_rol',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('rol_id',  db.Integer, db.ForeignKey('rol.id'),  primary_key=True)
)
rol_permiso = db.Table('rol_permiso',
    db.Column('rol_id',     db.Integer, db.ForeignKey('rol.id'),     primary_key=True),
    db.Column('permiso_id', db.Integer, db.ForeignKey('permiso.id'), primary_key=True)
)

class Negocio(db.Model):
    __tablename__ = 'negocio'
    id             = db.Column(db.Integer,     primary_key=True)
    nombre         = db.Column(db.String(100), nullable=False)
    tipo_negocio   = db.Column(db.String(50),  nullable=False)
    direccion      = db.Column(db.String(200))
    telefono       = db.Column(db.String(20))
    email_contacto = db.Column(db.String(100))
    logo_url       = db.Column(db.String(300))
    activo         = db.Column(db.Boolean,     default=True)
    fecha_registro = db.Column(db.DateTime,    default=hora_ecuador)

class Rol(db.Model):
    __tablename__ = 'rol'
    id          = db.Column(db.Integer,     primary_key=True)
    negocio_id  = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    nombre      = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300))
    activo      = db.Column(db.Boolean,     default=True)
    permisos    = db.relationship('Permiso', secondary=rol_permiso, lazy='select',
                                  backref=db.backref('roles', lazy='select'))

class Permiso(db.Model):
    __tablename__ = 'permiso'
    id          = db.Column(db.Integer,     primary_key=True)
    negocio_id  = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    codigo      = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300))

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id              = db.Column(db.Integer,     primary_key=True)
    negocio_id      = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=True)
    nombre          = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(100), unique=True, nullable=False)
    password        = db.Column(db.String(200), nullable=False)
    es_superadmin   = db.Column(db.Boolean,     default=False)
    activo          = db.Column(db.Boolean,     default=True)
    fecha_registro  = db.Column(db.DateTime,    default=hora_ecuador)
    roles           = db.relationship('Rol', secondary=user_rol, lazy='select',
                                      backref=db.backref('users', lazy='select'))
    citas_asignadas = db.relationship('Cita', backref='empleado', lazy='select')

class CategoriaServicio(db.Model):
    __tablename__ = 'categoria_servicio'
    id         = db.Column(db.Integer,     primary_key=True)
    negocio_id = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    orden      = db.Column(db.Integer,     default=0)
    servicios  = db.relationship('Servicio', backref='categoria', lazy='select')

class Servicio(db.Model):
    __tablename__ = 'servicio'
    id           = db.Column(db.Integer,     primary_key=True)
    negocio_id   = db.Column(db.Integer,     db.ForeignKey('negocio.id'),            nullable=False)
    categoria_id = db.Column(db.Integer,     db.ForeignKey('categoria_servicio.id'), nullable=True)
    nombre       = db.Column(db.String(100), nullable=False)
    descripcion  = db.Column(db.String(300))
    duracion_min = db.Column(db.Integer,     default=60)
    activo       = db.Column(db.Boolean,     default=True)
    historial_precios = db.relationship('HistorialPrecio', backref='servicio', lazy='select',
                                        order_by='HistorialPrecio.fecha_inicio.desc()')
    items_cita   = db.relationship('CitaServicio', backref='servicio_rel', lazy='select')

    def _hoy(self):
        return hora_ecuador().date()

    @property
    def promo_activa(self):
        hoy = self._hoy()
        for h in self.historial_precios:
            if h.es_promocion and h.fecha_inicio <= hoy and (h.fecha_fin is None or h.fecha_fin >= hoy):
                return h
        return None

    @property
    def precio_base(self):
        hoy = self._hoy()
        for h in self.historial_precios:
            if not h.es_promocion and h.fecha_inicio <= hoy:
                return h.precio
        return 0.0

    @property
    def precio_actual(self):
        promo = self.promo_activa
        return promo.precio if promo else self.precio_base

class HistorialPrecio(db.Model):
    __tablename__ = 'historial_precio'
    id           = db.Column(db.Integer, primary_key=True)
    servicio_id  = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    precio       = db.Column(db.Float,   nullable=False)
    es_promocion = db.Column(db.Boolean, default=False)
    fecha_inicio = db.Column(db.Date,    nullable=False)
    fecha_fin    = db.Column(db.Date,    nullable=True)
    motivo       = db.Column(db.String(200))

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id             = db.Column(db.Integer,     primary_key=True)
    negocio_id     = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    cedula         = db.Column(db.String(10),  nullable=True)   # ← NUEVO: cédula ecuatoriana
    nombre         = db.Column(db.String(100), nullable=False)
    telefono       = db.Column(db.String(20))
    email          = db.Column(db.String(100))
    notas          = db.Column(db.String(500))
    fecha_registro = db.Column(db.DateTime,    default=hora_ecuador)
    citas          = db.relationship('Cita', backref='cliente', lazy='select')

    @property
    def total_visitas(self):
        return len(self.citas)

    @property
    def ultima_visita(self):
        fechas = [c.fecha for c in self.citas]
        return max(fechas) if fechas else None

    @property
    def total_gastado(self):
        return sum(c.total for c in self.citas if c.estado == 'pagada')

    @property
    def servicio_favorito(self):
        conteo = {}
        for cita in self.citas:
            for item in cita.servicios_cita:
                nombre = item.servicio_rel.nombre
                conteo[nombre] = conteo.get(nombre, 0) + 1
        return max(conteo, key=conteo.get) if conteo else None

class Cita(db.Model):
    __tablename__ = 'cita'
    id               = db.Column(db.Integer,     primary_key=True)
    negocio_id       = db.Column(db.Integer,     db.ForeignKey('negocio.id'),  nullable=False)
    empleado_id      = db.Column(db.Integer,     db.ForeignKey('user.id'),     nullable=False)
    cliente_id       = db.Column(db.Integer,     db.ForeignKey('cliente.id'),  nullable=True)
    nombre_cliente   = db.Column(db.String(100), nullable=False)
    telefono_cliente = db.Column(db.String(20))
    fecha            = db.Column(db.Date,        nullable=False)
    hora_inicio      = db.Column(db.Time,        nullable=False)
    hora_fin         = db.Column(db.Time,        nullable=False)
    estado           = db.Column(db.String(20),  default='pendiente')
    notas            = db.Column(db.String(300))
    fecha_registro   = db.Column(db.DateTime,    default=hora_ecuador)
    servicios_cita   = db.relationship('CitaServicio', backref='cita_ref', lazy='select',
                                       cascade='all, delete-orphan')

    @property
    def total(self):
        return sum(item.precio_cobrado for item in self.servicios_cita)

class CitaServicio(db.Model):
    __tablename__ = 'cita_servicio'
    id             = db.Column(db.Integer, primary_key=True)
    cita_id        = db.Column(db.Integer, db.ForeignKey('cita.id'),     nullable=False)
    servicio_id    = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    precio_cobrado = db.Column(db.Float,   nullable=False)

class Movimiento(db.Model):
    __tablename__ = 'movimiento'
    id             = db.Column(db.Integer,     primary_key=True)
    negocio_id     = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    cita_id        = db.Column(db.Integer,     db.ForeignKey('cita.id'),    nullable=True)
    registrado_por = db.Column(db.Integer,     db.ForeignKey('user.id'),    nullable=True)
    tipo           = db.Column(db.String(10),  nullable=False)
    monto          = db.Column(db.Float,       nullable=False)
    descripcion    = db.Column(db.String(300))
    metodo_pago    = db.Column(db.String(30))
    fecha          = db.Column(db.DateTime,    nullable=False, default=hora_ecuador)

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id         = db.Column(db.Integer,     primary_key=True)
    negocio_id = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    contacto   = db.Column(db.String(100))
    telefono   = db.Column(db.String(20))
    email      = db.Column(db.String(100))
    notas      = db.Column(db.String(300))
    activo     = db.Column(db.Boolean,     default=True)
    productos  = db.relationship('Producto', backref='proveedor', lazy='select')

class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'
    id         = db.Column(db.Integer,     primary_key=True)
    negocio_id = db.Column(db.Integer,     db.ForeignKey('negocio.id'), nullable=False)
    nombre     = db.Column(db.String(100), nullable=False)
    productos  = db.relationship('Producto', backref='categoria', lazy='select')

class Producto(db.Model):
    __tablename__ = 'producto'
    id             = db.Column(db.Integer,     primary_key=True)
    negocio_id     = db.Column(db.Integer,     db.ForeignKey('negocio.id'),            nullable=False)
    proveedor_id   = db.Column(db.Integer,     db.ForeignKey('proveedor.id'),          nullable=True)
    categoria_id   = db.Column(db.Integer,     db.ForeignKey('categoria_producto.id'), nullable=True)
    nombre         = db.Column(db.String(150), nullable=False)
    descripcion    = db.Column(db.String(300))
    unidad_medida  = db.Column(db.String(30))
    costo_unitario = db.Column(db.Float,       default=0.0)
    stock_actual   = db.Column(db.Float,       default=0.0)
    stock_minimo   = db.Column(db.Float,       default=0.0)
    activo         = db.Column(db.Boolean,     default=True)
    fecha_registro = db.Column(db.DateTime,    default=hora_ecuador)
    movimientos_inv = db.relationship('MovimientoInventario', backref='producto', lazy='select')

    @property
    def alerta_reposicion(self):
        return self.stock_actual <= self.stock_minimo

class MovimientoInventario(db.Model):
    __tablename__ = 'movimiento_inventario'
    id             = db.Column(db.Integer,    primary_key=True)
    producto_id    = db.Column(db.Integer,    db.ForeignKey('producto.id'), nullable=False)
    registrado_por = db.Column(db.Integer,    db.ForeignKey('user.id'),     nullable=True)
    tipo           = db.Column(db.String(20), nullable=False)
    cantidad       = db.Column(db.Float,      nullable=False)
    costo_unitario = db.Column(db.Float)
    motivo         = db.Column(db.String(200))
    cita_id        = db.Column(db.Integer,    db.ForeignKey('cita.id'), nullable=True)
    fecha          = db.Column(db.DateTime,   nullable=False, default=hora_ecuador)
