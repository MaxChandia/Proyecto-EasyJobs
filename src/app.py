import os
import datetime
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from api.models import db, User, UserPublicacion
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from werkzeug.security import generate_password_hash, check_password_hash


ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../public/"
)
app = Flask(__name__)
CORS(app)
app.url_map.strict_slashes = False


db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = "postgresql://postgres:postgres@localhost:5432/dbp4g"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)


setup_admin(app)

setup_commands(app)

app.register_blueprint(api, url_prefix="/api")


app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
jwt = JWTManager(app)




@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route("/")
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, "index.html")


#Logica para registrarse


@app.route("/api/register", methods=["POST"])
def register():
    nombre = request.json.get("nombre")
    apellido = request.json.get("apellido")
    email = request.json.get("email")
    password = request.json.get("password")
    rut = request.json.get("rut")
    telefono = request.json.get("telefono")
    comuna = request.json.get("comuna")
    fecha_de_nacimiento = request.json.get("fecha_de_nacimiento")
    tipoUsuario = request.json.get("tipoUsuario")
    rubro = request.json.get("rubro")

    user_found = User.query.filter_by(email=email).first()

    if user_found:
        return jsonify({"message": "Email ya registrado"}), 400
    
    user_found = User.query.filter_by(telefono=telefono).first()

    if user_found:
        return jsonify({"error": "Telefono ya registrado"}), 400
    
    user_found = User.query.filter_by(rut=rut).first()

    if user_found:
        return jsonify({"error": "Rut ya registrado"}), 400

    new_user= User()

    new_user.email = email
    new_user.password = generate_password_hash(password)
    new_user.nombre = nombre
    new_user.apellido = apellido
    new_user.rut = rut
    new_user.telefono = telefono
    new_user.comuna = comuna
    new_user.tipoUsuario = tipoUsuario
    new_user.fecha_de_nacimiento = fecha_de_nacimiento

    if "rubro" in request.json:
          new_user.rubro = rubro

    db.session.add(new_user)
    db.session.commit()

    id = new_user.idUser if hasattr(new_user, "idUser") else None
    expires = datetime.timedelta(days=3)
    access_token = create_access_token(identity=id, expires_delta=expires)

    data = {"message": "Usuario registrado con éxito","access_token": access_token, "user": new_user.serialize()}

    return jsonify(data), 200


#Logica para logearse

@app.route("/api/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    if not email:
        return jsonify({"error": "Email es obligatorio"}), 400

    if not password:
        return jsonify({"error": "Contraseña es obligatoria"}), 400

    user_found = User.query.filter_by(email=email).first()

    print("User Found:", user_found)

    if not user_found:
        print("User not found")
        return jsonify({"error": "Email/contraseña son incorrectos"}), 401

    if not check_password_hash(user_found.password, password):
        print("Password incorrect")
        return jsonify({"error": "Email/contraseña son incorrectos"}), 401

    expires = datetime.timedelta(days=3)

    if isinstance(user_found, User):
        access_token = create_access_token(
            identity=str(user_found.idUser), expires_delta=expires
        )
    
    else:
        access_token = None

    if access_token:
        data = {"access_token": access_token, "user": user_found.serialize()}

        return jsonify(data), 200
    else:
        return jsonify({"error": "Tipo de usuario no válido"}), 400
    

#Lógica para ver los datos del usuario en el perfil
    

@app.route("/api/perfil_logeado", methods=["POST"])
def perfil_logeado():
    email = request.json.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 400

    publicaciones = UserPublicacion.query.filter_by(email=email).all()
    publicaciones_data = [publicacion.serialize() for publicacion in publicaciones]

    return jsonify({"usuario": user.serialize(), "publicaciones": publicaciones_data})




@app.route("/publicaciones", methods=["GET"])
def publicaciones():
    publicaciones = UserPublicacion.query.all()
    publicaciones = list(
        map(lambda publicacion: publicacion.serialize(), publicaciones)

    
    )
    return jsonify({"publicaciones": publicaciones}), 200

#Lógica para editar usuario

@app.route("/api/perfil", methods=["PUT"])
def actualizar_perfil():
   
    data = request.json

    try:
        user = User.query.filter_by(email=data["email"]).first()
        user.telefono = data.get("telefono", user.telefono)
        user.rubro = data.get("rubro", user.rubro)
        user.comuna = data.get("comuna", user.comuna)
        db.session.commit()
        return jsonify({"message": "Datos de perfil actualizados correctamente"})
    except Exception as e:   
        return jsonify({"error": str(e)}), 500
    

#Lógica para crear publicaciones
    

@app.route("/publicacionpost", methods=["POST"])
def enviar_datos_de_publicacionpost():
    try:
        body = request.get_json()
        publicacion = UserPublicacion()
        publicacion.idUsuario = body.get("idUser")
        publicacion.nombre = body.get("nombre")
        publicacion.apellido = body.get("apellido")
        publicacion.titulo = body.get("titulo")
        publicacion.email = body.get("email")
        publicacion.descripcion = body.get("descripcion")
        publicacion.comuna = body.get("comuna")
        publicacion.rubro = body.get("rubro")
        publicacion.fecha = body.get("fecha")

        db.session.add(publicacion)
        db.session.commit()
       
        required_fields = ["idUser", "nombre", "apellido", "titulo", "email", "descripcion", "comuna", "rubro", "fecha"]

        for field in required_fields:
            if field not in body:
             return jsonify({"error": f"Campo '{field}' faltante en la solicitud"}), 400

        return jsonify({"message": "Publicación exitosa"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


#Lógica para mostrar, editar y borrar publicaciones en perfil de usuario


@app.route("/publicacion/<int:id>", methods=["GET", "PUT", "DELETE"])
def publicacion(id):
    if request.method == "GET":
        data = request.json
    
        idPublicacion = data.get("idPublicacion")
        idUser = data.get("idUser")
        nombre = data.get("nombre")
        apellido = data.get("apellido")
        email = data.get("email")
        descripcion = data.get("descripcion")
        comuna = data.get("comuna")
        rubro = data.get("rubro")
        fecha = data.get("fecha")
        return (
                jsonify(
                    {
                        "idPublicacion": idPublicacion,
                        "idUser": idUser,
                        "nombre": nombre,
                        "apellido": apellido,
                        "email": email,
                        "descripcion": descripcion,
                        "comuna": comuna,
                        "rubro": rubro,
                        "fecha": fecha,
                    }
                ),
                200)

    if request.method == "PUT":
        data = request.json
        try:
            publicacion_edit = UserPublicacion.query.filter_by(id=data["idPublicacion"]).first()
            publicacion_edit.comuna = data.get("comuna",publicacion_edit.comuna)
            publicacion_edit.titulo = data.get("titulo",publicacion_edit.titulo)
            publicacion_edit.descripcion = data.get("descripcion",publicacion_edit.descripcion)
            db.session.commit()
            return jsonify({"message": "Publicación actualizada correctamente"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"No se pudo modificar la publicación: {str(e)}"}), 500
    if request.method == "DELETE":
        try:
            publicacion = UserPublicacion.query.get(id)
            if publicacion:
                db.session.delete(publicacion)
                db.session.commit()
                return jsonify({"message": f"Publicación con ID {id} eliminada correctamente"}), 200
            else:
                return jsonify({"error": f"No se encontró la publicación con ID {id}"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
        

#Lógica para mostrar perfiles de prestadores que ofrecen servicios en las publicaciones


@app.route("/api/perfil/<int:id>", methods=["GET"])
def obtener_perfil(id):
    user = User.query.get(id) 
    perfil_data = {
        "firstName": user.nombre,
        "lastName": user.apellido,
        "email": user.email,
        "comuna": user.comuna,
        "telefono": user.telefono,
        "birthDate": user.fecha_de_nacimiento,
        "rubro": user.rubro
    }

    return jsonify(perfil_data)



@app.route("/api/contactar", methods=[ "POST" ])
@jwt_required()
def contactar():
    id= get_jwt_identity()
    return jsonify({"msg": id}), 200
    


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3001))
    app.run(host="0.0.0.0", port=PORT, debug=True)
