from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .utils import tipo_usuario_aceptado, ultimas_cuotas
from .models import Permit, User, Cuotas
from . import db
from sqlalchemy import func
from datetime import datetime


# Estas son las vistas de la app general. 
views = Blueprint('views', __name__)

# Definir las URL de cada página
@views.route('/')
def home():
    return render_template("home.html", user=current_user)

# Definir las URL de cada página
@views.route('/maps_no_user')
def maps_no_user():
    return render_template("maps-no-user.html", user=current_user)

# Mapa para usuarios
@views.route('/maps_users',  methods=['GET', 'POST'])
@login_required
def maps_users():
    return render_template("maps_users.html", user=current_user)

@views.route('/dashboard')
@login_required
@tipo_usuario_aceptado({'user', 'admin'})
def dashboard():
    if current_user.is_authenticated:
        id = current_user.id
    
        permits = Permit.query.filter_by(user_id=id).first() #type: ignore
        cols = 0
        
        if permits:
            if permits.mapas == 'Si': #type: ignore
                cols += 1
            
            if permits.loteos == 'Si': #type: ignore
                cols += 1
            
            if permits.construccion == 'Si':#type: ignore
                cols += 1
        else: 
            cols = 3
            permits = {}
            permits['mapas'] = 'Si'
            permits['loteos'] = 'Si'
            permits['construccion'] = 'Si'
            
    return render_template('user_dashboard.html', user=current_user, permits=permits, cols=cols)

@views.route('/admindashboard')
@login_required
@tipo_usuario_aceptado('admin')
def admindashboard():
    return render_template('admin_dashboard.html', user=current_user)

@views.route('/admincuotas')
@login_required
@tipo_usuario_aceptado('admin')
def admincuotas():
    if current_user.is_authenticated:
        # Consulta para obtener los usuarios que tienen loteos = 'Si'
        usuarios_loteos = User.query.join(Permit).filter(Permit.loteos == 'Si').all()
        
        # Consulta para obtener los usuarios que tienen loteos = 'Si'
        #userLotes = Permit.query.filter_by(loteos = 'Si').all()
    
        cuotas_usuarios_loteos = Cuotas.query.all()
        
        for cuota in cuotas_usuarios_loteos:
            cuota.fecha = cuota.fecha.date()
        
    return render_template('admin_cuotas.html', user=current_user, usuarios_loteos=usuarios_loteos, cuotas_usuario=cuotas_usuarios_loteos)

@views.route('/admin_descargas', methods=['GET'])
@login_required
@tipo_usuario_aceptado('admin')
def admin_descargas():
    return render_template('admin_descargas.html', user=current_user)

@views.route('/admin_pagos', methods=['GET'])
@login_required
@tipo_usuario_aceptado('admin')
def admin_pagos():
    
    cuotas = Cuotas.query.all()
    usuarios = User.query.filter_by(tipo='user')
    
    for user in usuarios:
        # Obtener una lista de clientes únicos para el usuario actual
        clientes = db.session.query(Cuotas.clienteid).filter_by(user_id=user.id).distinct().all()
        
        # Lista para almacenar los resultados
        resultados = []

    # Iterar sobre cada cliente único
        for cliente in clientes:
            cliente = cliente[0]  # El resultado es una tupla, así que tomamos el primer elemento
            # Obtener la última cuota pagada para el cliente actual
            ultima_cuota_pagada = Cuotas.query.filter_by(clienteid=cliente, estadocuota='Pagado') \
                                            .order_by(Cuotas.fechacuota.desc()).first()
            # Obtener la siguiente cuota a pagar para el cliente actual
            siguiente_cuota_pagar = Cuotas.query.filter_by(clienteid=cliente, estadocuota='Pendiente') \
                                                .order_by(Cuotas.fechacuota).first()
                                                
            # Calcular el total de cuotas y el saldo pendiente
            total_cuotas_cliente = Cuotas.query.filter_by(clienteid=cliente).count()
            saldo_pendiente_cliente = db.session.query(func.sum(Cuotas.cuotadolar)) \
                                        .filter_by(clienteid=cliente, estadocuota='Pendiente').scalar()
                                                
            totalDeuda = total_cuotas_cliente * siguiente_cuota_pagar.cuotadolar #type:ignore
                            
            labelColor=""
            estado = ""
            if siguiente_cuota_pagar.fechacuota < datetime.now().date(): #type:ignore
                labelColor = 'danger'
                estado = 'Vencido'
            elif siguiente_cuota_pagar.fechacuota == datetime.now().date():  #type:ignore
                labelColor = 'warning'
                estado = 'Pronto'
            else: 
                labelColor='success'
                estado = 'A tiempo'

            # Agregar los resultados a la lista
            resultados.append({
                'user': user.nombre + ' ' + user.apellido,
                'cliente': cliente,
                'ultima_cuota_pagada': ultima_cuota_pagada,
                'siguiente_cuota_pagar': siguiente_cuota_pagar, 
                'saldo_pendiente_cliente': saldo_pendiente_cliente,
                'labelColor' : labelColor, 
                'estado':estado,
                'totalDeuda':totalDeuda,
            })
    print(resultados)
                                            
    return render_template('admin_pagos.html', user=current_user, cuotas=cuotas, usuarios=usuarios, 
                           ultima=resultados)

@views.route('/user_cuotas', methods=['GET'])
@login_required
@tipo_usuario_aceptado({'user', 'admin'})
def user_cuotas():
    if current_user.is_authenticated:
        cuotas = Cuotas.query.filter_by(user_id = current_user.id).all()
                
        next_cuotas = ultimas_cuotas(current_user.id)
    
        if cuotas:
            for cuota in cuotas:   
                cuota.fecha = cuota.fecha.date()
                
            # Realiza una consulta para obtener valores únicos de la columna "cliente"
            clientes_unicos = Cuotas.query.filter_by(user_id = current_user.id)\
                .with_entities(Cuotas.cliente, Cuotas.clienteid).distinct()\
                        .all()
            
            temp_dict = {}

            # Iterar sobre los datos originales
            for cliente, clienteid in clientes_unicos:
                # Si el cliente ya está en el diccionario, agregamos el clienteid a la lista existente
                if cliente in temp_dict:
                    temp_dict[cliente].append(clienteid)
                # Si el cliente no está en el diccionario, creamos una nueva lista con el clienteid
                else:
                    temp_dict[cliente] = [clienteid]

            # Convertir el diccionario en la lista de diccionarios deseada
            clientes_unicos = [{'cliente': cliente, 'cuentasid': tuple(ids)} for cliente, ids in temp_dict.items()]
        
    return render_template('user_cuotas.html', user=current_user, cuotas=cuotas, clientes=clientes_unicos, next_cuotas=next_cuotas)