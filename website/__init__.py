from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import login_manager, LoginManager
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
DB_NAME = 'database.db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apoiqweasdh777asdj__%&'
    # Databse inside app  
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .manager import manager
    
    # Aquí se registran las vistas y las url (notar que / es el prefijo para que queden donde se asignaron en sus debidos archivos)
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(manager, url_prefix='/')
    
    from .models import User

    with app.app_context():
        db.create_all()
        
        # Check if the admin user already exists
        admin_user = User.query.filter_by(email='saos@saos.com').first()
        
        if not admin_user:
            new_user = User(email='saos@saos.com',
                        nombre='saos',
                        apellido='saos',
                        tipo="admin",
                        password = generate_password_hash('1234',  method='pbkdf2')) # type: ignore
            
            db.session.add(new_user)
            db.session.commit()
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' #type: ignore
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) 
    
    return app

