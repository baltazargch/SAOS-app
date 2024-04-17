from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, send_file
from .models import User, Permit, Cuotas, Cobranza
from . import db
from flask_login import login_required, current_user
from .utils import tipo_usuario_aceptado, crear_cuotas_usuario, generar_csv_cuotas
from datetime import datetime
import os
import json

# Esta es la vista de login. 
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
                    fecha_inicio=fechaini
                    )
            
    return redirect('/admincuotas')

@manager.route('/descargar_csv', methods=['POST'])
def descargar_csv_cuotas():
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    # Generamos el contenido del CSV de las cuotas
    contenido_csv_cuotas = generar_csv_cuotas()

    # Creamos una respuesta con el contenido del CSV
    response = Response(contenido_csv_cuotas, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={fecha_actual}_cuotas_SAOS.csv'  # Nombre del archivo a descargar

    return response

@manager.route('/registrar_pago/<clienteid>/<cuota>', methods=['POST']) #type: ignore
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


@manager.route('/add_cobranza', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def add_cobranza():
    if request.method == 'POST':
        newproyect = request.form.get('proyect')
        if newproyect:
            existe = Cuotas.query.filter_by(proyecto=newproyect.upper()).first()
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
    

@manager.route('/modify_map', methods=['POST']) # type: ignore
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
            
    return redirect(url_for('views.maps_users', loteo=loteo, clickloteo=clickloteo))


