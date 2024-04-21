from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_manager, LoginManager
from werkzeug.security import generate_password_hash
from sqlalchemy import select

type = 'testing'

db = SQLAlchemy()

if type == 'testing':
    DB_NAME = 'database.db'
elif type=='production':
    DB_NAME = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="baltazargch",
    password="rhapsody-999",
    hostname="baltazargch.mysql.pythonanywhere-services.com",
    databasename="baltazargch$saosdata",
    )

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'asdasdasdasdsaos12341025715'
    # Databse inside app  
    if type == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    elif type == 'production':
        app.config['SQLALCHEMY_DATABASE_URI'] = DB_NAME
    
    db.init_app(app)

    from .views import views
    from .auth import auth
    from .manager import manager
    
    # Aquí se registran las vistas y las url (notar que / es el prefijo para que queden donde se asignaron en sus debidos archivos)
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(manager, url_prefix='/')
    
    from .models import User

    if type == 'testing':
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
    else: 
        with app.app_context():
            try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
                db.session.scalar(select(1))
            except db.exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
                if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
                    db.session.scalar(select(1))
                else:
                    raise
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login' #type: ignore
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) 
    
    return app

