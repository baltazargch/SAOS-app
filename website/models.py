from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, Date

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
    
class Cashflow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), default=func.now())
    cliente = db.Column(db.String(250))
    clienteid = db.Column(db.String(250))
    proyecto = db.Column(db.String(250))
    idmov = db.Column(db.Integer)
    movdolar = db.Column(db.Integer)
    movpesos = db.Column(db.Integer)
    fechamov = db.Column(Date)
    razonsocial = db.Column(db.String(250))
    responsable = db.Column(db.String(250))
    notas = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='cashflow')

class Cobranza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime(timezone=True), default=func.now())
    proyecto = db.Column(db.String(250))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='cobranza')