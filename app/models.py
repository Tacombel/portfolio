from app import app, db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except: # noqa
            return
        return User.query.get(id)


class Activo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(64), unique=True)
    nombre = db.Column(db.String(64), unique=True)
    tipo = db.Column(db.Integer)
    url = db.Column(db.String(256))
    moneda = db.Column(db.String(3))
    descargar = db.Column(db.Boolean)
    clase = db.Column(db.String(1))

    def __repr__(self):
        return '<Ticker {}>'.format(self.ticker)


class Cotizacion(db.Model):
    activo_id = db.Column(db.Integer, db.ForeignKey('activo.id'), primary_key=True)
    fecha = db.Column(db.DateTime, primary_key=True)
    VL = db.Column(db.Float)


class MovimientoActivo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime)
    unidades = db.Column(db.Float)
    precio = db.Column(db.Float)
    activo_id = db.Column(db.Integer, db.ForeignKey('activo.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class InvestmentMovements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime)
    cantidad = db.Column((db.Float))
    cuenta = db.Column(db.String(10))
    comments = db.Column(db.String(50))


class Variables(db.Model):
    name = db.Column(db.String(10), primary_key=True)
    value = db.Column(db.String(20))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
