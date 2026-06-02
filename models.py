from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

# ==============================================================================
# TABLAS INTERMEDIAS PARA RBAC
# ==============================================================================
rol_permiso = db.Table('rol_permiso',
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id', ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    db.Column('permiso_id', db.Integer, db.ForeignKey('permiso.id', ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
)

user_rol = db.Table('user_rol',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id', ondelete="CASCADE", onupdate="CASCADE"), primary_key=True),
    db.Column('asignado_en', db.DateTime, default=datetime.utcnow)
)

# ==============================================================================
# CAPA 1: NEGOCIO (Multi-tenant)
# ==============================================================================

class Negocio(db.Model):
    __tablename__ = 'negocio'

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(100), nullable=False)
    tipo_negocio    = db.Column(db.String(50), nullable=False)
    direccion       = db.Column(db.String(200))
    telefono        = db.Column(db.String(20))
    email_contacto  = db.Column(db.String(100))
    logo_url        = db.Column(db.String(300))
    activo          = db.Column(db.Boolean, default=True)
    fecha_registro  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuarios        = db.relationship('User',        backref='negocio_rel', lazy=True)
    roles           = db.relationship('Rol',         backref='negocio_rel', lazy=True, cascade='all, delete-orphan')
    permisos        = db.relationship('Permiso',     backref='negocio_rel', lazy=True, cascade='all, delete-orphan')
    servicios       = db.relationship('Servicio',    backref='negocio_rel', lazy=True)
    citas           = db.relationship('Cita',        backref='negocio_rel', lazy=True)
    movimientos     = db.relationship('Movimiento',  backref='negocio_rel', lazy=True)
    productos       = db.relationship('Producto',    backref='negocio_rel', lazy=True)
    proveedores     = db.relationship('Proveedor',   backref='negocio_rel', lazy=True)

    def __repr__(self):
        return f'<Negocio {self.nombre}>'

# ==============================================================================
# CAPA 2: USUARIOS
# ==============================================================================

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    nombre          = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(100), unique=True, nullable=False)
    password        = db.Column(db.String(200), nullable=False)
    es_superadmin   = db.Column(db.Boolean, default=False, nullable=False)
    activo          = db.Column(db.Boolean, default=True)
    fecha_registro  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    roles           = db.relationship('Rol', secondary=user_rol, lazy='subquery',
                                      backref=db.backref('usuarios_asignados', lazy=True))
    citas_asignadas = db.relationship('Cita', backref='empleado_rel', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

# ==============================================================================
# CAPA 3: RBAC (Role-Based Access Control)
# ==============================================================================

class Rol(db.Model):
    __tablename__ = 'rol'
    __table_args__ = (db.UniqueConstraint('negocio_id', 'nombre', name='uq_rol_negocio_nombre'),)

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    nombre          = db.Column(db.String(100), nullable=False)
    descripcion     = db.Column(db.String(300))
    activo          = db.Column(db.Boolean, default=True)

    # Relaciones
    permisos        = db.relationship('Permiso', secondary=rol_permiso, lazy='subquery',
                                      backref=db.backref('roles_asignados', lazy=True))

    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Permiso(db.Model):
    __tablename__ = 'permiso'
    __table_args__ = (db.UniqueConstraint('negocio_id', 'codigo', name='uq_permiso_negocio_codigo'),)

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    codigo          = db.Column(db.String(100), nullable=False)
    descripcion     = db.Column(db.String(300))

    def __repr__(self):
        return f'<Permiso {self.codigo}>'

# ==============================================================================
# CAPA 4: CATÁLOGO DE SERVICIOS + HISTORIAL DE PRECIOS
# ==============================================================================

class CategoriaServicio(db.Model):
    __tablename__ = 'categoria_servicio'

    id          = db.Column(db.Integer, primary_key=True)
    negocio_id  = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    nombre      = db.Column(db.String(100), nullable=False)
    orden       = db.Column(db.Integer, default=0)

    servicios   = db.relationship('Servicio', backref='categoria_rel', lazy=True)

    def __repr__(self):
        return f'<CategoriaServicio {self.nombre}>'

class Servicio(db.Model):
    __tablename__ = 'servicio'

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    categoria_id    = db.Column(db.Integer, db.ForeignKey('categoria_servicio.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    nombre          = db.Column(db.String(100), nullable=False)
    descripcion     = db.Column(db.String(300))
    duracion_min    = db.Column(db.Integer, default=60, nullable=False)
    activo          = db.Column(db.Boolean, default=True)

    # Relaciones
    historial_precios = db.relationship('HistorialPrecio', backref='servicio_rel', lazy=True,
                                        order_by='HistorialPrecio.fecha_inicio.desc()')
    items_cita        = db.relationship('CitaServicio', backref='servicio_rel', lazy=True)

    @property
    def precio_actual(self):
        hoy = (datetime.utcnow() - timedelta(hours=5)).date()
        promo = HistorialPrecio.query.filter_by(servicio_id=self.id, es_promocion=True)\
                    .filter(HistorialPrecio.fecha_inicio <= hoy)\
                    .filter((HistorialPrecio.fecha_fin == None) | (HistorialPrecio.fecha_fin >= hoy))\
                    .order_by(HistorialPrecio.fecha_inicio.desc()).first()
        if promo:
            return promo.precio
        
        base = HistorialPrecio.query.filter_by(servicio_id=self.id, es_promocion=False)\
                   .filter(HistorialPrecio.fecha_inicio <= hoy)\
                   .order_by(HistorialPrecio.fecha_inicio.desc()).first()
        return base.precio if base else 0.0

    def __repr__(self):
        return f'<Servicio {self.nombre}>'

class HistorialPrecio(db.Model):
    __tablename__ = 'historial_precio'

    id              = db.Column(db.Integer, primary_key=True)
    servicio_id     = db.Column(db.Integer, db.ForeignKey('servicio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    precio          = db.Column(db.Float, nullable=False)
    es_promocion    = db.Column(db.Boolean, default=False, nullable=False)
    fecha_inicio    = db.Column(db.Date, nullable=False)
    fecha_fin       = db.Column(db.Date, nullable=True)
    motivo          = db.Column(db.String(200))

    def __repr__(self):
        return f'<HistorialPrecio servicio={self.servicio_id} precio={self.precio}>'

# ==============================================================================
# CAPA 5: AGENDAMIENTO
# ==============================================================================

class Cita(db.Model):
    __tablename__ = 'cita'

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    empleado_id     = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    nombre_cliente  = db.Column(db.String(100), nullable=False)
    telefono_cliente= db.Column(db.String(20))
    fecha           = db.Column(db.Date, nullable=False)
    hora_inicio     = db.Column(db.Time, nullable=False)
    hora_fin        = db.Column(db.Time, nullable=False)
    estado          = db.Column(db.String(20), default='pendiente', nullable=False)
    notas           = db.Column(db.String(300))
    fecha_registro  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    servicios_cita  = db.relationship('CitaServicio', backref='cita_rel', lazy=True, cascade='all, delete-orphan')
    movimiento      = db.relationship('Movimiento', backref='cita_rel', lazy=True, uselist=False)

    @property
    def total(self):
        return sum(item.precio_cobrado for item in self.servicios_cita)

    def __repr__(self):
        return f'<Cita {self.nombre_cliente} {self.fecha} {self.hora_inicio}>'

class CitaServicio(db.Model):
    __tablename__ = 'cita_servicio'

    id              = db.Column(db.Integer, primary_key=True)
    cita_id         = db.Column(db.Integer, db.ForeignKey('cita.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    servicio_id     = db.Column(db.Integer, db.ForeignKey('servicio.id', ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    precio_cobrado  = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<CitaServicio cita={self.cita_id} servicio={self.servicio_id}>'

# ==============================================================================
# CAPA 6: CONTABILIDAD
# ==============================================================================

class Movimiento(db.Model):
    __tablename__ = 'movimiento'

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    cita_id         = db.Column(db.Integer, db.ForeignKey('cita.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    registrado_por  = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    tipo            = db.Column(db.String(10), nullable=False)
    monto           = db.Column(db.Float, nullable=False)
    descripcion     = db.Column(db.String(300))
    metodo_pago     = db.Column(db.String(30))
    fecha           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Movimiento {self.tipo} ${self.monto}>'

# ==============================================================================
# CAPA 7: INVENTARIO
# ==============================================================================

class Proveedor(db.Model):
    __tablename__ = 'proveedor'

    id              = db.Column(db.Integer, primary_key=True)
    negocio_id      = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    nombre          = db.Column(db.String(100), nullable=False)
    contacto        = db.Column(db.String(100))
    telefono        = db.Column(db.String(20))
    email           = db.Column(db.String(100))
    notas           = db.Column(db.String(300))
    activo          = db.Column(db.Boolean, default=True)

    productos       = db.relationship('Producto', backref='proveedor_rel', lazy=True)

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'

class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'

    id          = db.Column(db.Integer, primary_key=True)
    negocio_id  = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    nombre      = db.Column(db.String(100), nullable=False)

    productos   = db.relationship('Producto', backref='categoria_rel', lazy=True)

    def __repr__(self):
        return f'<CategoriaProducto {self.nombre}>'

class Producto(db.Model):
    __tablename__ = 'producto'

    id                  = db.Column(db.Integer, primary_key=True)
    negocio_id          = db.Column(db.Integer, db.ForeignKey('negocio.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    proveedor_id        = db.Column(db.Integer, db.ForeignKey('proveedor.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    categoria_id        = db.Column(db.Integer, db.ForeignKey('categoria_producto.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    nombre              = db.Column(db.String(150), nullable=False)
    descripcion         = db.Column(db.String(300))
    unidad_medida       = db.Column(db.String(30))
    costo_unitario      = db.Column(db.Float, default=0.0, nullable=False)
    stock_actual        = db.Column(db.Float, default=0.0, nullable=False)
    stock_minimo        = db.Column(db.Float, default=0.0, nullable=False)
    activo              = db.Column(db.Boolean, default=True)
    fecha_registro      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    movimientos_inv     = db.relationship('MovimientoInventario', backref='producto_rel', lazy=True)

    @property
    def alerta_reposicion(self):
        return self.stock_actual <= self.stock_minimo

    def __repr__(self):
        return f'<Producto {self.nombre} stock={self.stock_actual}>'

class MovimientoInventario(db.Model):
    __tablename__ = 'movimiento_inventario'

    id              = db.Column(db.Integer, primary_key=True)
    producto_id     = db.Column(db.Integer, db.ForeignKey('producto.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    registrado_por  = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    tipo            = db.Column(db.String(20), nullable=False)
    cantidad        = db.Column(db.Float, nullable=False)
    costo_unitario  = db.Column(db.Float)
    motivo          = db.Column(db.String(200))
    cita_id         = db.Column(db.Integer, db.ForeignKey('cita.id', ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    fecha           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<MovimientoInventario {self.tipo} {self.cantidad} x producto={self.producto_id}>'