from flask import session, redirect
from helpers.db import db
from bson import ObjectId
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class EmailUsernameNotUnique(ValueError):
    pass


def user_middleware(func):
    @wraps(func) # di flask tidak bisa menggunakan nama fungsi yang sama. jika flask menggunakan decorator/middleware di routenya
                # makan function inner dibawah akan menjdai nama function yang di daftarkan ke route
                # karena middleware itu reusable maka nama function inner akan duplikat
                #oleh karena itu @wraps(func) diperlukan
    def inner(*args, **kwargs):
        # print("USER", kwargs, args)
        user = User(session)
        args = [*args, user]
        return func(*args, **kwargs)
    
    return inner

def auth_only_middleware(func):
    @wraps(func)
    def inner(*args, **kwargs):
        # print("AUTH")
        user = User(session)
        if not user.is_login():
            return redirect('/login')
        
        return func(*args, **kwargs)
    return inner

def admin_only_middleware(func):
    @wraps(func)
    def inner(*args, **kwargs):
        user = User(session)

        if not user.is_login():
            return redirect('/login')
        
        if not user.role == "admin":
            return "403: FORBIDDEN"
        
        return func(*args, **kwargs)
    
    return inner


# @dataclass
class User:
    # name: str
    # email: str
    # avatar: str
    _DATA = None
    
    def __init__(self, session):
        self.session = session
    
    def is_login(self):
        data = self._data()
        return not data is None
    
    def login(self, id_):
        result = db.sessions.insert_one({'user_id': ObjectId(id_)})
        self.session['auth_id'] = str(result.inserted_id)
    
    def change_password(self, new_password):
        raise NotImplementedError("belum di bikin bang")
    
    def add_comment(self, article_id: ObjectId, comment: str):
        db.comments.insert_one({'article_id': article_id, 'comment': comment, 'user_id': self._id, 'published_at': datetime.now()})
    
    # def get_comments(self, article_id)
    
    def _data(self):
        if  self._DATA is None:
            auth_id = self.session.get('auth_id')
            auth = db.sessions.find_one({'_id': ObjectId(auth_id)})
            if auth is None:
                return
            
            user_id = auth['user_id']
            user = db.users.find_one({'_id': user_id})
            return user
        
        return self._DATA
    
    @staticmethod # static method biasa, bisa dibuat tanpa buat objek
    def create(username, email, raw_password, role, avatar):
        hashed_password = generate_password_hash(raw_password)
        
        if db.users.find_one({
            '$or': [
                {"email": email},
                {"username": username}
            ]
        }):
            raise EmailUsernameNotUnique("email or username not unique") # bangkitkan custom error

        db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': role,
            'avatar': avatar
        })
        return True
    
    def logout(self):
        auth_id = self.session.get('auth_id')
        auth = db.sessions.find_one_and_delete({'_id': ObjectId(auth_id)})
        return not auth is None
    
    # @property
    # def username(self):
    #     data = self._data()
    #     return data['username']
    
    # Jika objek user memanggil property/method yang tidak terdaftar, maka function ini akan dipanggil
    def __getattr__(self, name): 
        data = self._data()
        rv = data.get(name)
        if rv is None: # cek apakah field ada di collection user
            raise ValueError(f"field {name} kagak ada di database kocak")
        
        return rv
        