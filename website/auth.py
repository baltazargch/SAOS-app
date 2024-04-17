from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User, Permit
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .utils import tipo_usuario_aceptado, new_user_const
from email_validator import validate_email, EmailNotValidError
import os
import json

# Esta es la vista de login. 
auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        if current_user.tipo == 'admin':
            return redirect(url_for('views.admindashboard'))
        else:
            return redirect(url_for('views.dashboard'))
            
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email = email).first()
        if user:
            if check_password_hash(user.password, password): # type: ignore
                flash('Acceso al sistema exitoso.', category='success')
                login_user(user, remember=True)
                if user.tipo == 'admin':
                    return redirect(url_for('views.admindashboard'))
                else:
                    return redirect(url_for('views.dashboard'))
            else:
                flash('Contraseña incorrecta. Intente de nuevo.', category='error')
        else: 
            flash('El email ingresado no se encuentra registrado.', category='error')
     
    return render_template('home.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sing_up', methods=['GET', 'POST'])
@tipo_usuario_aceptado('admin')
def sign_up():
    tablaUsers = User.query.all()
    
    areUser = User.query.filter_by(tipo='user').all()
    if areUser:
        permitsUser = Permit.query.all()
        mappermits = {}
        for user in permitsUser:
            mappermits_str = user.mappermits
            if mappermits_str:
                mappermits[user.id] = json.loads(mappermits_str)
            else:
                mappermits[user.id] = []
    else:
        permitsUser = ''
        mappermits = {}
        
    for user in tablaUsers:
        user.date = user.fecha.date() 
        
    mapdir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
    files = os.listdir(mapdir)
    
    return render_template('admin_permits.html', user=current_user, tablaUsers = tablaUsers, permitsUser=permitsUser, 
                           permitMapas=files, mappermits = mappermits)

@auth.route("/new_user", methods=['POST'])
@tipo_usuario_aceptado('admin')
def new_user():
    if request.method == 'POST':
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        tipo = request.form.get('rol')
        
        user = User.query.filter_by(email = email).first()
        
        try:
            emailTested = validate_email(str(email))
        except EmailNotValidError as erroremail:
            flash(str(erroremail),  category="error")
            
        if user:
            flash('El email ingresado ya se encuentra registrado.', category='error')
        elif len(str(nombre)) < 2: 
            flash("Nombre debe contener más de 2 caracteres.",  category="error")
        elif len(str(apellido)) < 2:
            flash("Apellido debe contener más de 2 caracteres.",  category="error")
        elif password1 != password2:
            flash("Las contraseñas no coinciden. Por favor revise e intente nuevamente.",  category="error")
        elif len(str(password1)) < 4:
            flash("La contraseña debe contener más de 4 caracteres.",  category="error")
        else:
            """ new_user = User(email=emailTested.normalized,
                        nombre=nombre,
                        apellido=apellido,
                        tipo=tipo,
                        password= generate_password_hash(password1,  method='pbkdf2')) # type: ignore """
            
            new_user_const(
                email=emailTested.normalized, 
                password=generate_password_hash(str(password1),  method='pbkdf2'), 
                nombre=nombre,
                apellido=apellido,
                tipo=tipo,
                mapas='No',
                loteos='No', 
                construccion='No')
            
            flash("¡Cuenta creada correctamente!",  category="success")
    return redirect('/sing_up')

@auth.route('/delete_user/<string:id>', methods=['GET','POST'])
@login_required
@tipo_usuario_aceptado('admin')
def delete_user(id):
    usuario = User.query.filter_by(id = id).first()
    if usuario:
        if usuario.tipo == 'admin':
            flash('No se puede eliminar un usuario admin directamente.', 'error')
        else:
            db.session.delete(usuario)
            db.session.commit()
            flash('Usuario eliminado correctamente.', 'success')
    return redirect('/sing_up')

@auth.route('/edit_user/<string:id>', methods=['GET', 'POST'])
@login_required
@tipo_usuario_aceptado('admin')
def edit_user(id):
    usuario = User.query.filter_by(id = id).first()
    
    return render_template('admin_edit_contact.html', usuario=usuario, user=current_user)

@auth.route('/update_user/<string:id>', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def update_user(id):
    if request.method == 'POST':
        usuario = User.query.get(id)
        if usuario: 
            usuario.email = request.form.get('email')
            usuario.nombre = request.form.get('nombre')
            usuario.apellido = request.form.get('apellido')
            usuario.tipo = request.form.get('rol')
            db.session.commit()
            
            flash('Clave correcta. Usuario modificado.', 'warning')
        else: 
            flash('Clave incorrecta.', 'error')
    return redirect('/sing_up')

@auth.route('/verificar_clave/<id>', methods=['GET', 'POST'])
@login_required
@tipo_usuario_aceptado('admin')
def verificar_clave(id):
    clave_correcta = request.form.get('clave') == 'saos1234'
    return jsonify({'success': clave_correcta})
        
@auth.route('/edit_permits', methods=['POST'])
@login_required
@tipo_usuario_aceptado('admin')
def edit_permits(): 
    if request.method == 'POST':
        id =  request.form.get('btnId')
        tomod = Permit.query.get(id)
        
        if tomod:  
            if request.form.get('mapsPermit'+str(id)) is not None: 
                tomod.mapas ='Si'
            else:
                tomod.mapas ='No'
            if request.form.get('lotsPermit'+str(id)) is not None:
                tomod.loteos = 'Si'
            else:
                tomod.loteos ='No'
            if request.form.get('consPermit'+str(id)) is not None:
                tomod.construccion = 'Si'
            else:
                tomod.construccion ='No'
            
            db.session.commit()
            flash("Permisos cambiados correctamente!",  category="success")
    return redirect('/sing_up?tab=permisos')

