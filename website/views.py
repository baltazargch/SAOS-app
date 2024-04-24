from flask import Blueprint, render_template, redirect, send_file
from flask_login import login_required, current_user
from .utils import tipo_usuario_aceptado, ultimas_cuotas, convert_to_kml
from .models import *
from . import db
from sqlalchemy import func, and_
from datetime import datetime
import plotly.io as pio
import plotly.graph_objs as go
import os
import geojson
import json
from shapely import from_geojson
from . import type
import io


# Estas son las vistas de la app general. 
views = Blueprint('views', __name__)

# Mapa para admins
@views.route('/maps_admin',  methods=['GET', 'POST'])
@login_required
def maps_admin():
    mapdir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
    files = os.listdir(mapdir)
    
    def obtener_fecha(x):
        return datetime.strptime(x['properties']['fecha'], '%Y-%m-%d')
        
    centroides = []
    estados = []
    datos = []
    graphs = []
    for archivo in files:
        if type == 'testing':
            ruta= f'{mapdir}\\{archivo}'
        else:
            ruta= f'{mapdir}/{archivo}'
        with open(ruta) as f:
            data = geojson.load(f)
            geometria = from_geojson(geojson.dumps(data)) 
            centroides.append({"name": archivo, "coords": geometria.centroid.coords[:][0]})
            feat = data['features'][:]
            feat = json.loads(json.dumps(feat))
            disp = sum(1 for fe in feat if fe['properties']['estado'] == 'DISPONIBLE')
            rese = sum(1 for fe in feat if fe['properties']['estado'] == 'RESERVADO')
            vend = sum(1 for fe in feat if fe['properties']['estado'] == 'VENDIDO')
            
            estados.append({
                'name': archivo, 
                'disponibles': disp, 
                'reservados': rese, 
                'vendidos': vend, 
                'total': sum(1 for fe in feat)
            })
            
            graphs.append({
                'name': archivo, 
                'graph': pio.to_html(go.Figure(data=[go.Pie(labels=['Disponibles', 'Reservados', 'Vendidos'], 
                                                values=[disp, rese, vend])]).update_traces(hole=0.4), full_html=False)
            })
            
            # Seleccionar las primeras 10 características con fecha ordenadas
            feat_with_date = [fe for fe in feat if fe['properties'].get('fecha') is not None]
            feat_ordenadas = sorted(feat_with_date, key=obtener_fecha, reverse=True)[:10]

            # Agregar características ordenadas al diccionario de datos
            datos.append({
                archivo.replace('.geojson', ''): [fe.get('properties', {}) for fe in feat_ordenadas]
            })
            
    return render_template("admin_map.html", user=current_user, files=files, centroides=centroides, 
                           estados=estados, datos=datos, graphs=graphs)

# Mapa para usuarios
@views.route('/maps_users',  methods=['GET', 'POST'])
@login_required
def maps_users():
    mapdir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
    files = os.listdir(mapdir)
    
    mappermits_values = {}
    for permit in current_user.permits:
        mappermits_values = permit.mappermits
        
    def obtener_fecha(x):
        return datetime.strptime(x['properties']['fecha'], '%Y-%m-%d')
        
    files = [file for file in files if file.replace('.geojson', '') in mappermits_values]
    centroides = []
    estados = []
    datos = []
    graphs = []
    for archivo in files:
        if type == 'testing':
            ruta= f'{mapdir}\\{archivo}'
        else:
            ruta= f'{mapdir}/{archivo}'
        with open(ruta) as f:
            data = geojson.load(f)
            geometria = from_geojson(geojson.dumps(data)) 
            centroides.append({"name": archivo, "coords": geometria.centroid.coords[:][0]})
            feat = data['features'][:]
            feat = json.loads(json.dumps(feat))
            disp = sum(1 for fe in feat if fe['properties']['estado'] == 'DISPONIBLE')
            rese = sum(1 for fe in feat if fe['properties']['estado'] == 'RESERVADO')
            vend = sum(1 for fe in feat if fe['properties']['estado'] == 'VENDIDO')
            
            estados.append({
                'name': archivo, 
                'disponibles': disp, 
                'reservados': rese, 
                'vendidos': vend, 
                'total': sum(1 for fe in feat)
            })
            
            graphs.append({
                'name': archivo, 
                'graph': pio.to_html(go.Figure(data=[go.Pie(labels=['Disponibles', 'Reservados', 'Vendidos'], 
                                                values=[disp, rese, vend])]).update_traces(hole=0.4), full_html=False)
            })
            
            # Seleccionar las primeras 10 características con fecha ordenadas
            feat_with_date = [fe for fe in feat if fe['properties'].get('fecha') is not None]
            feat_ordenadas = sorted(feat_with_date, key=obtener_fecha, reverse=True)[:10]

            # Agregar características ordenadas al diccionario de datos
            datos.append({
                archivo.replace('.geojson', ''): [fe.get('properties', {}) for fe in feat_ordenadas]
            })
            
    return render_template("map_users.html", user=current_user, files=files, centroides=centroides, 
                           estados=estados, datos=datos, graphs=graphs)

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
            
        cobranzas = Cobranza.query.all()
        if not cobranzas:
            cobranzas = []
        
    return render_template('admin_cuotas.html', user=current_user, usuarios_loteos=usuarios_loteos, 
                           cuotas_usuario=cuotas_usuarios_loteos, cobranzas=cobranzas)

@views.route('/admin_descargas', methods=['GET'])
@login_required
@tipo_usuario_aceptado('admin')
def admin_descargas():
    mapdir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
    files = os.listdir(mapdir)
    
    return render_template('admin_descargas.html', user=current_user, files=files)

@views.route('/admin_pagos', methods=['GET'])
@login_required
@tipo_usuario_aceptado('admin')
def admin_pagos():
    
    cuotas = Cuotas.query.all()
    usuarios = User.query.filter_by(tipo='user')
    
    resultados = []
    for user in usuarios:
        userName = user.nombre + ' ' + user.apellido
        resultados = ultimas_cuotas(user.id, userName)
        
    return render_template('admin_pagos.html', user=current_user, cuotas=cuotas, usuarios=usuarios, 
                           ultima=resultados)

@views.route('/user_cuotas', methods=['GET'])
@login_required
@tipo_usuario_aceptado({'user', 'admin'})
def user_cuotas():
    if current_user.is_authenticated:
        cuotas = Cuotas.query.filter_by(user_id = current_user.id).all()
        
        if cuotas:        
            next_cuotas = ultimas_cuotas(current_user.id, current_user.nombre)
        
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
        else: 
            cuotas = None
    return render_template('user_cuotas.html', user=current_user, cuotas=cuotas)

@views.route('/cashflow', methods=['GET', 'POST'])
@login_required
@tipo_usuario_aceptado('admin')
def admin_cashflow():
    cashflow = Cuotas.query.all()
    if not cashflow: 
        cashflow = []
    usuarios = User.query.filter_by(tipo='user')
    if not usuarios: 
        usuarios = []
    rubros = Rubro.query.all()
    subrubros = Subrubro.query.all()
    
    return render_template('admin_cashflow.html', user=current_user, cashflow=cashflow, usuarios=usuarios, 
                           rubros=rubros, subrubros=subrubros)

@views.route('/maps_descargas/<map>')
@login_required
@tipo_usuario_aceptado('admin')
def maps_descargas(map):
    if map: 
        filemap = os.path.join(os.path.dirname(__file__), 'static', 'maps', map)
        
        kml_data = convert_to_kml(filemap)

        # Enviar el archivo KMZ al cliente
    return send_file(io.BytesIO(kml_data.encode()), mimetype='application/vnd.google-earth.kml+xml', 
                     as_attachment=True, download_name=str(datetime.now().date()) + '_' + map.replace('.geojson', '.kml'))