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
from models import db, User

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
    return jsonify(users=[user.serialize() for user in users])

app.register_blueprint(api)

with app.test_request_context():
    print(app.url_map)

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
