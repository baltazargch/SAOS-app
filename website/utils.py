from functools import wraps
from flask import abort, Flask
from flask_login import current_user
from .models import User, Permit, Cuotas
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from . import db
from datetime import timedelta, datetime
from io import StringIO
import csv
import calendar

def tipo_usuario_aceptado(tipo):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Usuario no autenticado
            if current_user.tipo not in tipo:
                abort(403)  # Usuario no tiene permiso
            return func(*args, **kwargs)
        return wrapper
    return decorator

def new_user_const(email, password, nombre, apellido, tipo, mapas, loteos, construccion):
    # Crea un nuevo usuario
    nuevo_usuario = User(email=email, password=password, nombre=nombre, apellido=apellido, tipo=tipo)# type: ignore
    db.session.add(nuevo_usuario)
    db.session.commit()

    # Crea un nuevo permiso asociado al usuario
    nuevo_permiso = Permit(mapas=mapas, loteos=loteos, construccion=construccion, user=nuevo_usuario)# type: ignore
    db.session.add(nuevo_permiso)
    db.session.commit()

    return nuevo_usuario

# Función para obtener el próximo día 10 del mes
def proximo_dia_10(fecha, dia):
    # Obtener el año y mes de la fecha proporcionada
    año = fecha.year
    mes = fecha.month

    # Obtener el día 10 del mes siguiente
    if mes == 12:
        mes_siguiente = 1
        año_siguiente = año + 1
    else:
        mes_siguiente = mes + 1
        año_siguiente = año

    # Obtener el día 10 del mes siguiente
    fecha_siguiente = datetime(año_siguiente, mes_siguiente, dia)

    # Ajustar al siguiente lunes si cae en sábado o domingo
    dia_semana = fecha_siguiente.weekday()
    if dia_semana == calendar.SATURDAY:
        fecha_siguiente += timedelta(days=2)  # Siguiente lunes
    elif dia_semana == calendar.SUNDAY:
        fecha_siguiente += timedelta(days=1)  # Siguiente lunes

    return fecha_siguiente

def crear_cuotas_usuario(cliente, proyecto, lote, usuario, 
                         num_cuotas, valor_cuota, fecha_inicio, pago_ini):
    
    # crear id único
    clienteid = "{}-{}-{}".format(cliente.replace(' ', '-'), proyecto, lote).lower()
    # Pago inicial (cuota id 0)
    cuota_ini = Cuotas(
        cliente=cliente,
        clienteid = clienteid,
        proyecto = proyecto,
        lote = lote, 
        numcuotas = num_cuotas,
        idcuota = 0,
        estadocuota = 'Pagado',
        cuotadolar = pago_ini,
        cuotapagadadolar = pago_ini,# Asignar el nombre del cliente (puedes cambiarlo según tus necesidades)
        fechacuota=fecha_inicio,  # Asignar la fecha de la cuota
        user=usuario  # Asignar el usuario correspondiente a la cuota
        ) # type: ignore
        
        # Agregar la nueva cuota a la sesión de la base de datos
    db.session.add(cuota_ini)
    
    # fecha de inicio para la primera cuota
    fecha_cuota = fecha_inicio
    
    # iniciar id de cuota
    id_cuota = 1
    # Crear cuotas para el usuario
    for _ in range(num_cuotas):
        # Crear una nueva cuota
        nueva_cuota = Cuotas(
            cliente=cliente,
            clienteid = clienteid,
            proyecto = proyecto,
            lote = lote, 
            numcuotas = num_cuotas,
            idcuota = id_cuota,
            estadocuota = 'Pendiente',
            cuotadolar = valor_cuota, # Asignar el nombre del cliente (puedes cambiarlo según tus necesidades)
            fechacuota=fecha_cuota,  # Asignar la fecha de la cuota
            user=usuario  # Asignar el usuario correspondiente a la cuota
        ) # type: ignore
        
        # Agregar la nueva cuota a la sesión de la base de datos
        db.session.add(nueva_cuota)
        
        # Avanzar la fecha de la cuota al próximo mes
        fecha_cuota = proximo_dia_10(fecha_cuota, fecha_inicio.day)
        id_cuota += 1
    
    # Confirmar los cambios en la base de datos
    db.session.commit()
    
def generar_csv_cuotas():
    # Obtiene todos los registros de la tabla Cuotas
    cuotas = Cuotas.query.all()

    # Creamos un objeto StringIO para almacenar los datos CSV
    output = StringIO()

    # Usamos DictWriter para escribir los datos en formato CSV
    csv_writer = csv.DictWriter(
        output, 
        fieldnames= ['ID', 'Fecha', 'Usuario', 'Cliente', 'Proyecto', 
                     'Lote', 'Numero_de_Cuotas', 
                     'Estado_de_Cuota', 'Id_Cuota',
                     'Fecha_Cuota', 'Fecha_Pago', 
                     'Cuota_Dólar', 
                     'Cuota_Pagada_Dólar', 
                     'Cuota_Pesos',
                     'Cuota_Pagada_Pesos'])
    csv_writer.writeheader()

    for cuota in cuotas:
        csv_writer.writerow({'ID': cuota.id, 
                             'Fecha': cuota.fecha, 
                             'Usuario': cuota.user.nombre + ' ' + cuota.user.apellido,
                             'Cliente': cuota.cliente, 
                             'Proyecto': cuota.proyecto, 
                             'Lote': cuota.lote, 
                             'Numero_de_Cuotas': cuota.numcuotas, 
                             'Estado_de_Cuota': cuota.estadocuota,
                             'Id_Cuota': cuota.idcuota,
                             'Fecha_Cuota': cuota.fechacuota, 
                             'Fecha_Pago': cuota.fechapago, 
                             'Cuota_Dólar': cuota.cuotadolar, 
                             'Cuota_Pagada_Dólar': cuota.cuotapagadadolar, 
                             'Cuota_Pesos': cuota.cuotapesos, 
                             'Cuota_Pagada_Pesos': cuota.cuotapagadapesos})

    # Regresamos el contenido del archivo CSV
    return output.getvalue()

def ultimas_cuotas(id):
    # Obtener una lista de clientes únicos para el usuario actual
    clientes = db.session.query(Cuotas.clienteid).filter_by(user_id=id).distinct().all()
    
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
            'cliente': cliente,
            'ultima_cuota_pagada': ultima_cuota_pagada,
            'siguiente_cuota_pagar': siguiente_cuota_pagar, 
            'saldo_pendiente_cliente': saldo_pendiente_cliente,
            'labelColor' : labelColor, 
            'estado':estado,
            'totalDeuda':totalDeuda,
        })

    return resultados