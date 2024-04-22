from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from .models import User, Permit, Cuotas, Cobranza
from . import db
from flask_login import login_required, current_user
from .utils import tipo_usuario_aceptado, crear_cuotas_usuario, generar_csv_cuotas
from datetime import datetime
import os
import json
import plotly.graph_objs as go
from sqlalchemy import func

# Este arhivo contiene todas las funciones que modifican las bases de datos
# PARA USUARIOS ADMIN
manager = Blueprint('manager', __name__)

@manager.route('/nuevo_cliente', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def nuevo_cliente():
    if request.method == 'POST':
        id = request.form.get('userLotes')
        user_to_add = User.query.get(id)
    
        if user_to_add:
            cliente = request.form.get('cliente')
            proyecto = request.form.get('proyecto')
            lote = request.form.get('lote')
            cuotas = request.form.get('cuotas')
            fechaini = request.form.get('fechaini')
            valorcuotas = request.form.get('valorcuotas')
            pago_ini = request.form.get('cuotaini')
            fechaini = datetime.strptime(fechaini, '%Y-%m-%d').date() # type: ignore
        
            clienteid = "{}-{}-{}".format(cliente.replace(' ', '-'), proyecto, lote).lower() #type: ignore
            existe = Cuotas.query.filter_by(clienteid=clienteid).first()
            if existe: 
                flash('El plan de pagos a crear {}, ya existe'.format(clienteid), 'error')
            else:
                crear_cuotas_usuario(
                    cliente=cliente,
                    proyecto=proyecto, 
                    lote = lote, 
                    usuario=user_to_add, 
                    num_cuotas=int(cuotas), # type: ignore
                    valor_cuota=valorcuotas, 
                    fecha_inicio=fechaini, 
                    pago_ini=pago_ini
                    )
                flash('Plan de pagos creado exitosamente.', 'success')
            
    return redirect('/admincuotas')

@manager.route('/descargar_csv', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def descargar_csv_cuotas():
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    # Generamos el contenido del CSV de las cuotas
    contenido_csv_cuotas = generar_csv_cuotas()

    # Creamos una respuesta con el contenido del CSV
    response = Response(contenido_csv_cuotas, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={fecha_actual}_cuotas_SAOS.csv'  # Nombre del archivo a descargar

    return response

@manager.route('/registrar_pago/<clienteid>/<cuota>', methods=['POST']) #type: ignore
@login_required
@tipo_usuario_aceptado('admin')
def registrar_pago(clienteid, cuota):
    if request.method == 'POST':
        pagado = request.form.get('pagodolares')
        cuota = Cuotas.query.filter_by(clienteid = clienteid, idcuota = cuota).first()
        
        cuota.estadocuota = 'Pagado' #type: ignore
        cuota.fechapago = datetime.now().date() #type: ignore
        cuota.cuotapagadadolar = pagado #type: ignore
        
        db.session.commit()
        return redirect('/admin_pagos')

@manager.route('/set_maps_permits/<id>', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def set_maps_permits(id):
    if request.method == 'POST':
        userDb = Permit.query.get(id)
        mapdir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
        files = os.listdir(mapdir)
        maps_data = {}
        
        for f in files:
            map_name = f.replace('.geojson', '')
            value = request.form.get(f + userDb.user.nombre) #type: ignore
            maps_data[map_name] = value
            
        si_permissions = [mapa for mapa, valor in maps_data.items() if valor == "Si"]
        maps_json = json.dumps(si_permissions)
        
        userDb.mappermits = maps_json #type: ignore
        db.session.commit()
    return redirect('/sing_up?tab=mappermits')

# Elimina proyectos de cobranzas (no altera table de cobranzas)
@manager.route('/delete_cobranza/<string:id>', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def delete_cobranza(id):
    proyecto = Cobranza.query.filter_by(id = id).first()
    if proyecto:
        db.session.delete(proyecto)
        db.session.commit()
        flash('Proyecto eliminado correctamente.', 'success')
    return redirect('/admincuotas')

# Esta función sirve para agregar proyectos de cobranzas y poder asignar plan de cuotas a los usuarios
@manager.route('/add_cobranza', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def add_cobranza():
    if request.method == 'POST':
        newproyect = request.form.get('proyect')
        if newproyect:
            existe = Cobranza.query.filter_by(proyecto=newproyect.upper()).first()
            if existe: 
                flash('El proyecto a crear {}, ya existe'.format(newproyect.upper()), 'error')
            else:
                newCobranza = Cobranza(
                    fecha=datetime.now().date(), 
                    proyecto=newproyect.upper(), 
                    user_id=current_user.id, 
                    user=current_user)# type: ignore
                db.session.add(newCobranza)
                db.session.commit()
                flash('¡Nuevo proyecto creado!', 'sucess')
              
    return redirect('/admincuotas')
        
@manager.route('/imprimir_pago/<id>', methods=['GET'])
@login_required
@tipo_usuario_aceptado('admin')
def imprimir_pago(id):
    cuotas_cliente = Cuotas.query.filter_by(clienteid=id).all()
    icliente =  Cuotas.query.filter_by(clienteid=id).first()
    if icliente:
        cliente = icliente.cliente
        idcliente = icliente.clienteid
    # Contar las cuotas pagadas y pendientes
    cuotas_pagadas = sum(1 for cuota in cuotas_cliente if cuota.estadocuota == 'Pagado') - 1
    cuotas_pendientes = sum(1 for cuota in cuotas_cliente if cuota.estadocuota == 'Pendiente')
    
    # Lista para almacenar los resultados
    resultados = []
    ultima_cuota_pagada = Cuotas.query.filter(
        Cuotas.clienteid==idcliente, 
        Cuotas.estadocuota=='Pagado', 
        Cuotas.idcuota>0) \
            .order_by(Cuotas.fechacuota.desc()).first()
            # Obtener la siguiente cuota a pagar para el cliente actual
    siguiente_cuota_pagar = Cuotas.query.filter_by(clienteid=idcliente, estadocuota='Pendiente') \
                                                .order_by(Cuotas.fechacuota).first()
    
    cuota_posterior = Cuotas.query.filter(
        Cuotas.clienteid == idcliente,
        Cuotas.estadocuota == 'Pendiente',
        Cuotas.fechacuota > siguiente_cuota_pagar.fechacuota).order_by(Cuotas.fechacuota).first()    #type: ignore 
                                    
    # Calcular el total de cuotas y el saldo pendiente
    total_cuotas_cliente = Cuotas.query.filter_by(clienteid=idcliente).count() - 1
    
    saldo_abonado = Cuotas.query.filter(
        Cuotas.clienteid==idcliente, 
        Cuotas.estadocuota=='Pagado', 
        Cuotas.idcuota > 0)\
            .with_entities(func.sum(Cuotas.cuotapagadadolar)) \
                .scalar()
                                                
    totalDeuda = total_cuotas_cliente * siguiente_cuota_pagar.cuotadolar #type:ignore
    saldo_pendiente_cliente  = totalDeuda - saldo_abonado   
    
    fechas_cuotas = [cuota.fechacuota for cuota in cuotas_cliente]

    # Calcula la fecha máxima y mínima
    fecha_maxima = max(fechas_cuotas)
    fecha_minima = min(fechas_cuotas)

    # Agregar los resultados a la lista
    resultados.append({
                'cliente': cliente,
                'ultima_cuota_pagada': ultima_cuota_pagada,
                'siguiente_cuota_pagar': siguiente_cuota_pagar, 
                'saldo_pendiente_cliente': saldo_pendiente_cliente,
                'cuota_posterior':cuota_posterior,
                'saldo_abonado': saldo_abonado,
                'totalDeuda':totalDeuda,
                'fecha_maxima': fecha_maxima,
                'fecha_minima': fecha_minima, 
                'total_cuotas': total_cuotas_cliente
            })
    today = datetime.now().date()
    
    return render_template('imprimir_pago.html', cliente=cuotas_cliente, 
                           dataCliente = resultados, today=today, icliente=icliente)

# PARA USUARIOS USERS
# Función para modificar el mapa en cuanto se cambia un estado de lote
@manager.route('/modify_map', methods=['POST']) # type: ignore
@login_required
def modify_map():  
    if request.method == 'POST':
        usuario = current_user.nombre
      
        loteo = request.form.get('loteo')
        parcela =request.form.get('parcela')
        comprador =request.form.get('comprador')
        nuevo_estado = request.form['estado']
       
        # Determinar qué archivo GeoJSON leer según la información del modal
        nombre_archivo = loteo + '.geojson'  # type: ignore
        ruta_archivo = os.path.join(os.path.dirname(__file__), 'static', 'maps', nombre_archivo) # type: ignore
        
         # Leer el contenido del archivo GeoJSON
        with open(ruta_archivo, 'r') as f:
            contenido_geojson = json.load(f)

        # Iterar sobre las características (features) del archivo GeoJSON
        for feature in contenido_geojson['features']:
             # Si el lote está vendido o reservado, verifica el usuario, si no tiene permisos -> error
            if feature['properties']['nombrecompleto'] == parcela:
                if feature['properties']['estado'] in ['RESERVADO','VENDIDO']:
                    if not feature['properties']['usuario'] == usuario:
                        clickloteo=False
                        break
                    else:
                    # Verificar si la propiedad "Parcela" es igual a "Parcela 1"
                        if not feature['properties']['estado'] == nuevo_estado.upper():
                            # Actualizar la propiedad "Estado" solo para la característica que cumpla con la condición
                            feature['properties']['estado'] = nuevo_estado.upper()
                            feature['properties']['fecha'] = str(datetime.now().date())
                            feature['properties']['comprador'] = comprador
                            feature['properties']['usuario'] = usuario
                            clickloteo = True
                # Si el lote está disponible, no verifica el usuario y realiza la operación
                elif feature['properties']['estado'] == 'DISPONIBLE':
                    # Verificar si la propiedad "Parcela" es igual a "Parcela 1"
                    if not feature['properties']['estado'] == nuevo_estado.upper():
                        # Actualizar la propiedad "Estado" solo para la característica que cumpla con la condición
                        feature['properties']['estado'] = nuevo_estado.upper()
                        feature['properties']['fecha'] = str(datetime.now().date())
                        feature['properties']['comprador'] = comprador
                        feature['properties']['usuario'] = usuario
                        clickloteo = True

        # Guardar los cambios en el archivo GeoJSON modificado
        with open(ruta_archivo, 'w') as f:
            json.dump(contenido_geojson, f)
    #TODO
    if current_user.tipo == 'admin':
        to = 'views.maps_admin'
    else: 
        to = 'views.maps_users'
    #print(request.referrer)
            
    return redirect(url_for(to, loteo=loteo, clickloteo=clickloteo))

@manager.route('/imprimir_cobranzas/<id>', methods=['GET'])
@login_required
def print_cobranzas(id):
    cuotas_cliente = Cuotas.query.filter_by(clienteid=id).all()
    icliente =  Cuotas.query.filter_by(clienteid=id).first()
    if icliente:
        cliente = icliente.cliente
        idcliente = icliente.clienteid
    # Contar las cuotas pagadas y pendientes
    cuotas_pagadas = sum(1 for cuota in cuotas_cliente if cuota.estadocuota == 'Pagado') - 1
    cuotas_pendientes = sum(1 for cuota in cuotas_cliente if cuota.estadocuota == 'Pendiente')

    # Crear los datos de la gráfica
    labels = ['Pagadas', 'Pendientes']
    valores = [cuotas_pagadas, cuotas_pendientes]

   # Crea el gráfico circular utilizando Plotly
    fig = go.Figure(data=[go.Pie(labels=labels, values=valores)])
    grafica = fig.to_html(full_html=False)
    
    # Lista para almacenar los resultados
    resultados = []
    ultima_cuota_pagada = Cuotas.query.filter(
        Cuotas.clienteid==idcliente, 
        Cuotas.estadocuota=='Pagado', 
        Cuotas.idcuota>0) \
            .order_by(Cuotas.fechacuota.desc()).first()
            # Obtener la siguiente cuota a pagar para el cliente actual
    siguiente_cuota_pagar = Cuotas.query.filter_by(clienteid=idcliente, estadocuota='Pendiente') \
                                                .order_by(Cuotas.fechacuota).first()
    
    cuota_posterior = Cuotas.query.filter(
        Cuotas.clienteid == idcliente,
        Cuotas.estadocuota == 'Pendiente',
        Cuotas.fechacuota > siguiente_cuota_pagar.fechacuota).order_by(Cuotas.fechacuota).first()    #type: ignore 
                                    
    # Calcular el total de cuotas y el saldo pendiente
    total_cuotas_cliente = Cuotas.query.filter_by(clienteid=idcliente).count() - 1
    
    saldo_abonado = Cuotas.query.filter(
        Cuotas.clienteid==idcliente, 
        Cuotas.estadocuota=='Pagado', 
        Cuotas.idcuota > 0)\
            .with_entities(func.sum(Cuotas.cuotapagadadolar)) \
                .scalar()
                                                
    totalDeuda = total_cuotas_cliente * siguiente_cuota_pagar.cuotadolar #type:ignore
    saldo_pendiente_cliente  = totalDeuda - saldo_abonado   
    
    fechas_cuotas = [cuota.fechacuota for cuota in cuotas_cliente]

    # Calcula la fecha máxima y mínima
    fecha_maxima = max(fechas_cuotas)
    fecha_minima = min(fechas_cuotas)

    # Agregar los resultados a la lista
    resultados.append({
                'cliente': cliente,
                'ultima_cuota_pagada': ultima_cuota_pagada,
                'siguiente_cuota_pagar': siguiente_cuota_pagar, 
                'saldo_pendiente_cliente': saldo_pendiente_cliente,
                'cuota_posterior':cuota_posterior,
                'saldo_abonado': saldo_abonado,
                'totalDeuda':totalDeuda,
                'fecha_maxima': fecha_maxima,
                'fecha_minima': fecha_minima, 
                'total_cuotas': total_cuotas_cliente
            })
    today = datetime.now().date()
    
    
    return render_template('imprimir_cobranza.html', cliente=cuotas_cliente, grafica=grafica, 
                           dataCliente = resultados, today=today, icliente=icliente)

