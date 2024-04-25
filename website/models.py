from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, Date
import calendar
from datetime import datetime

# GENERAL DATA
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    nombre = db.Column(db.String(250))
    apellido = db.Column(db.String(250))
    tipo = db.Column(db.String(250))
    fecha = db.Column(db.DateTime(timezone=True), default=func.now())
    cuotas = db.relationship('Cuotas', back_populates='user', lazy=True, cascade="all, delete-orphan")
    cashflow = db.relationship('Cashflow', back_populates='user', lazy=True, cascade="all, delete-orphan")
    cobranza = db.relationship('Cobranza', back_populates='user', lazy=True, cascade="all, delete-orphan")
    permits = db.relationship('Permit', back_populates='user', lazy=True, cascade="all, delete-orphan")
    
class Permit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), default=func.now())
    mapas = db.Column(db.String(250))
    loteos = db.Column(db.String(250))
    construccion = db.Column(db.String(250))
    mappermits = db.Column(db.JSON) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='permits')

# COBRANZAS
class Cuotas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=False), default=func.now())
    cliente = db.Column(db.String(250))
    clienteid = db.Column(db.String(250))
    proyecto = db.Column(db.String(250))
    lote = db.Column(db.String(250))
    numcuotas = db.Column(db.Integer)
    estadocuota = db.Column(db.String(250))
    idcuota = db.Column(db.Integer)
    fechacuota = db.Column(Date)
    fechapago = db.Column(Date)
    cuotadolar = db.Column(db.Integer)
    cuotapagadadolar = db.Column(db.Integer)
    cuotapesos = db.Column(db.Integer)
    cuotapagadapesos = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='cuotas')
    
    __table_args__ = (
        CheckConstraint(estadocuota.in_(['Pagado', 'Pendiente', 'Vencido']), name='estadocuota_valido'),
    )

class Cobranza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), default=func.now())
    proyecto = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='cobranza')
    
# CASH FLOW
class Cashflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True))
    mesanio = db.Column(db.String(20))
    subrubro_id = db.Column(db.Integer, db.ForeignKey('subrubro.id'), nullable=False)
    montousd = db.Column(db.Float)
    montoarg = db.Column(db.Float)
    descripcion = db.Column(db.String(255))
    empresa = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='cashflow')

class Rubro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    subrubros = db.relationship('Subrubro', backref='rubro', lazy=True,  cascade="all, delete-orphan")

class Subrubro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    rubro_id = db.Column(db.Integer, db.ForeignKey('rubro.id'), nullable=False)