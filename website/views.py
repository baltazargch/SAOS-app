from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .utils import tipo_usuario_aceptado, ultimas_cuotas
from .models import Permit, User, Cuotas


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
            clientes_unicos = Cuotas.query.filter_by(user_id = current_user.id).with_entities(Cuotas.cliente).distinct().all()
    
            # Extrae los valores únicos de la consulta y conviértelos en una lista
            clientes_unicos = [cliente[0] for cliente in clientes_unicos]
        
    return render_template('user_cuotas.html', user=current_user, cuotas=cuotas, 
                           clientes=clientes_unicos, next_cuotas=next_cuotas)