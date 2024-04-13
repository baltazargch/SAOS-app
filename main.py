from website import create_app
from flask import Flask, jsonify, request, redirect, url_for
from flask_login import current_user
import os
import json

app = create_app()

@app.route('/get_files')
def get_files():
    # Obtener la lista de nombres de archivos en la carpeta static/maps
    files = str(app.static_folder) + '\\maps'
    files = os.listdir(files)
    return jsonify(files)

@app.route('/modify_map', methods=['POST']) # type: ignore
def modify_map():  
    if request.method == 'POST':
        usuario = current_user.email
      
        loteo = request.form.get('loteo')
        parcela =request.form.get('parcela')
        nuevo_estado = request.form['estado']
       
        # Determinar qué archivo GeoJSON leer según la información del modal
        nombre_archivo = loteo + '.geojson'  # type: ignore
        ruta_archivo = os.path.join(app.static_folder, 'maps', nombre_archivo) # type: ignore

         # Leer el contenido del archivo GeoJSON
        with open(ruta_archivo, 'r') as f:
            contenido_geojson = json.load(f)

        # Iterar sobre las características (features) del archivo GeoJSON
        for feature in contenido_geojson['features']:
            # Verificar si la propiedad "Parcela" es igual a "Parcela 1"
            if feature['properties']['nombrecompleto'] == parcela:
                if not feature['properties']['estado'] == nuevo_estado.upper():
                    # Actualizar la propiedad "Estado" solo para la característica que cumpla con la condición
                    feature['properties']['estado'] = nuevo_estado.upper()

        # Guardar los cambios en el archivo GeoJSON modificado
        with open(ruta_archivo, 'w') as f:
            json.dump(contenido_geojson, f)
            
    return redirect(url_for('views.maps_users', loteo=loteo, clickloteo=True))

if __name__ == '__main__':
    app.run(debug=True)