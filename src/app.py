"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, Blueprint
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Favorite, Post
from sqlalchemy.orm.exc import NoResultFound


app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

api = Blueprint('api', __name__, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# ----------------- users api routes ------------------- #
@api.route('/users', methods=["POST"])
def create_user():
    """
    payload:
    {
        "username": "someusername",
        "email": "some@email.com",
        "password": "password"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No request payload found"}), 400
    
    if not 'username' in data:
        return jsonify({"error": "Bad request, missing username."}), 400
    
    if not 'email' in data:
        return jsonify({"error": "Bad request, missing email."}), 400
    
    if not 'password' in data:
        return jsonify({"error": "Bad request, missing password."}), 400
    
    user: User | None = User.query.filter_by(username=data.get('username')).first()
    
    if user:
        return jsonify({"error": f"Username {data.get('username')} alerady exists."}), 400

    user = User(username=data.get('username'), email=data.get('email'), password=data.get('password'))
    db.session().add(user)
    db.session.commit()
    db.session.refresh(user)

    return jsonify(user.serialize()), 201    

@api.route('/users', methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify(users=[user.serialize() for user in users]), 200

@api.route('/users/<string:username>', methods=["GET"])
def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(user.serialize()), 200
    return jsonify({"error": f"user {username} does not exist"}), 404

# ----------------- planet api routes ------------------- #
@api.route('/planets', methods=["POST"])
def create_planet():
    """
    payload:
    {
        "name": "planet name",
        "description": "planet description",
        "image_url": "url"
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No request payload found"}), 400

    if not 'name' in data:
        return jsonify({"error": "Bad request, missing name."}), 400
    
    if not 'description' in data:
        return jsonify({"error": "Bad request, missing description."}), 400
    
    if not 'image_url' in data:
        return jsonify({"error": "Bad request, missing image_url."}), 400
    
    planet: Planet | None = Planet.query.filter_by(name=data.get('name')).first()
    
    if planet:
        return jsonify({"error": f"Name {data.get('name')} alerady exists."}), 400
    
    planet = Planet(name=data.get("name"), description=data.get("description"), image_url=data.get("image_url"))

    db.session().add(planet)
    db.session.commit()
    db.session.refresh(planet)

    return jsonify(planet.serialize()), 201

@api.route('/planets', methods=["GET"])
def get_planets():
    planets = Planet.query.all()
    return jsonify(planets=[planet.serialize() for planet in planets])

@api.route('/planets/<string:name>', methods=["GET"])
def get_planet_by_name(name):
    planet = Planet.query.filter_by(name=name).first()
    if planet:
        return jsonify(planet.serialize()), 200
    return jsonify({"error": f"planet {name} does not exist"}), 404

# ----------------- people api routes ------------------- #
@api.route('/people', methods=["GET"])
def get_people():
    people = Character.query.all()
    return jsonify(people=[person.serialize() for person in people])

@api.route('/people', methods=["POST"])
def create_person():
    """
        payload:
        {
            "name": "person name",
            "description": "person description",
            "image_url": "url",
            "planet_id": "planet_id"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No request payload found"}), 400

    if not 'name' in data:
        return jsonify({"error": "Bad request, missing name."}), 400
    
    if not 'description' in data:
        return jsonify({"error": "Bad request, missing description."}), 400
    
    if not 'image_url' in data:
        return jsonify({"error": "Bad request, missing image_url."}), 400
    
    if not 'planet_id' in data:
        return jsonify({"error": "Bad request, missing image_url."}), 400
    
    person: Character | None = Character.query.filter_by(name=data.get('name')).first()
    
    if person:
        return jsonify({"error": f"Name {data.get('name')} alerady exists."}), 400
    
    planet: Planet | None = Planet.query.filter_by(id=data.get('planet_id')).first()

    if not planet:
        return jsonify({
            "error": f"No such planet id: {data.get('planet_id')}.",
            "planets": [planet.serialize_slim() for planet in Planet.query.all()]
            }), 400
    
    person = Character(
        name=data.get("name"), 
        description=data.get("description"), 
        image_url=data.get("image_url"), 
        planet_id=data.get("planet_id")
    )

    db.session().add(person)
    db.session.commit()
    db.session.refresh(person)

    return jsonify(person.serialize()), 201

@api.route('/people/<string:name>', methods=["GET"])
def get_person_by_name(name):
    person: Character | None = Character.query.filter_by(name=name).first()
    if person:
        return jsonify(person.serialize()), 200
    return jsonify({"error": f"person with name '{name}' does not exist"}), 404

# ----------------- fav api routes ------------------- #
@api.route('users/<int:user_id>/favorite/planet/<int:planet_id>', methods=["POST"])
def add_favorite_planet(user_id, planet_id):
    
    user = User.query.filter_by(id=user_id).first()
    planet = Planet.query.filter_by(id=planet_id).first()
    
    if not user :
        return jsonify({"error": f"user_id {user_id} not found"}), 404
    
    if not planet:
        return jsonify({"error": f"planet_id {planet_id} not found"}), 404

    existing_favorite = Favorite.query.filter_by(user_id=user.id, planet_id=planet.id).first()
    if existing_favorite:
        return jsonify({"error": f"planet_id {planet_id} is already assciated with user_id {user_id} "}), 400

    favorite = Favorite(user=user, planet=planet)
    db.session().add(favorite)
    db.session.commit()

    return jsonify(user.serialize())

@api.route('users/<int:user_id>/favorite/people/<int:character_id>', methods=["POST"])
def add_favorite_character(user_id, character_id):
   
    user = User.query.filter_by(id=user_id).first()
    character = Character.query.filter_by(id=character_id).first()

    if not user :
        return jsonify({"error": f"user_id {user_id} not found"}), 404
    
    if not character:
        return jsonify({"error": f"character_id {character_id} not found"}), 404

    existing_favorite = Favorite.query.filter_by(user_id=user.id, character_id=character.id).first()
    if existing_favorite:
        return jsonify({"error": f"character_id {character_id} is already added to favorites of user_id {user_id} "}), 400

    favorite = Favorite(user=user, character=character)
    db.session().add(favorite)
    db.session.commit()

    return jsonify(user.serialize())

@api.route('users/<int:user_id>/favorite/people/<int:character_id>', methods=["DELETE"])
def delete_favorite_character(user_id, character_id):
   
    user = User.query.filter_by(id=user_id).first()
    character = Character.query.filter_by(id=character_id).first()

    if not user :
        return jsonify({"error": f"user_id {user_id} not found"}), 404
    
    if not character:
        return jsonify({"error": f"character_id {character_id} not found"}), 404

    existing_favorite = Favorite.query.filter_by(user_id=user.id, character_id=character.id).first()
    if not existing_favorite:
        return jsonify({"error": f"character_id {character_id} is not added to favorites of user_id {user_id} "}), 400

    db.session().delete(existing_favorite)
    db.session.commit()

    return jsonify({"message": f"Character {character_id} removed from favorites of user {user_id}", "user": user.serialize()})

@api.route('users/<int:user_id>/favorite/planet/<int:planet_id>', methods=["DELETE"])
def delete_favorite_planet(user_id, planet_id):
    
    user = User.query.filter_by(id=user_id).first()
    planet = Planet.query.filter_by(id=planet_id).first()
    
    if not user :
        return jsonify({"error": f"user_id {user_id} not found"}), 404
    
    if not planet:
        return jsonify({"error": f"planet_id {planet_id} not found"}), 404

    existing_favorite = Favorite.query.filter_by(user_id=user.id, planet_id=planet.id).first()
    if not existing_favorite:
        return jsonify({"error": f"planet_id {planet_id} is already assciated with user_id {user_id} "}), 400
    
    db.session().delete(existing_favorite)
    db.session.commit()

    return jsonify({"message": f"Planet {planet_id} removed from favorites of user {user_id}", "user": user.serialize()}), 200

# ----------------- post api routes ------------------- #

@api.route('/posts/<int:user_id>', methods=["GET"])
def get_posts(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "not found"}), 404
    
    return jsonify({
        "username": user.username,
        "user_id": user.id,
        "posts": user.posts
    }), 200  

@api.route('/posts/<int:user_id>', methods=["POST"])
def create_post(user_id):
    
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "not found"}), 404
    
    data = request.json

    if not data:
        return jsonify({"error": "No request payload found"}), 400
    
    if not 'title' in data:
        return jsonify({"error": "Bad request, missing title."}), 400
    
    if not 'content' in data:
        return jsonify({"error": "Bad request, missing content."}), 400
    
    new_post = Post(
        title=data.get('title'),
        content = data.get('content'),
        user_id = user.id
    )

    user.posts.append(new_post)
    db.session().add(new_post)
    db.session().commit()

    return jsonify({
        "message": "Post created successfully",
        "user": {
            "username": user.username,
            "user_id": user.id,
            "posts": [post.serialize() for post in user.posts]
        }
    }), 201 

app.register_blueprint(api)

with app.test_request_context():
    print(app.url_map)

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
