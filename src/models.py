from datetime import timezone, datetime
from flask_sqlalchemy import SQLAlchemy
from collections import OrderedDict

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users' 

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    posts = db.relationship("Post", back_populates="user")
    favorites = db.relationship("Favorite", back_populates="user")
    
    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "created_at": self.created_at, 
            "is_active": self.is_active,
            "favorites": {
                "planets": [fav.planet.serialize_slim() for fav in self.favorites if fav.planet],
                "people": [fav.character.serialize_slim() for fav in self.favorites if fav.character],
            },
            "posts": [post.serialize_slim() for post in self.posts]
        }
    
class Planet(db.Model):
    __tablename__ = 'planets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    characters = db.relationship("Character", back_populates="planet")
    favorites = db.relationship("Favorite", back_populates="planet")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "people": self.characters
        }
    
    def serialize_slim(self):
        return {   
            "id": self.id,
            "name": self.name
        }

class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    planet_id = db.Column(db.Integer, db.db.ForeignKey('planets.id'))

    planet = db.relationship("Planet", back_populates="characters")
    favorites = db.relationship("Favorite", back_populates="character")

    def serialize(self):
        return OrderedDict([
            ("id", self.id),
            ("name", self.name),
            ("description", self.description),
            ("image_url", self.image_url),
            ("planet_id", self.planet_id)
        ])
    
    def serialize_slim(self):
        return OrderedDict([
            ("id", self.id),
            ("name", self.name)
        ])

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    planet_id = db.Column(db.Integer, db.ForeignKey('planets.id'))
    character_id = db.Column(db.Integer, db.ForeignKey('characters.id'))

    user = db.relationship("User", back_populates="favorites")
    planet = db.relationship("Planet", back_populates="favorites")
    character = db.relationship("Character", back_populates="favorites")


class Post(db.Model):
    __tablename__ = 'posts'    

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="posts")  

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def serialize_slim(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }  