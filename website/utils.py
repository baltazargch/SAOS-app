from functools import wraps
from flask import abort, Flask
from flask_login import current_user
from .models import User, Permit, Cuotas
from flask_sqlalchemy import SQLAlchemy
from . import db
from datetime import timedelta
from io import StringIO
import csv

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

def crear_cuotas_usuario(cliente, proyecto, lote, usuario, num_cuotas, valor_cuota, fecha_inicio):
    # Calcular la fecha de inicio para la primera cuota
    fecha_cuota = fecha_inicio
    
    # Calcular el intervalo de tiempo entre cuotas (1 mes)
    intervalo_cuotas = timedelta(days=31)
    id_cuota = 1
    # Crear cuotas para el usuario
    for _ in range(num_cuotas):
        # Crear una nueva cuota
        nueva_cuota = Cuotas(
            cliente=cliente,
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
        fecha_cuota += intervalo_cuotas
        id_cuota += 1
    
    # Confirmar los cambios en la base de datos
    db.session.commit()
    
# Función para crear un archivo CSV a partir de los datos de la tabla Cuotas
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