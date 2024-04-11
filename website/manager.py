from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, send_file
from .models import User, Permit, Cuotas
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