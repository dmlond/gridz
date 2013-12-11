from flask import Flask
import sqlite3

# configuration
DATABASE = '/tmp/gridz.db'
DEBUG = True
SECRET_KEY = 'aeoffoxxx11'

app = Flask(__name__)
app.config.from_object(__name__)
from app import main

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
