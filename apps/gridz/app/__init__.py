from flask import Flask

# configuration
DATABASE = '/tmp/gridz.db'
DEBUG = True
SECRET_KEY = 'aeoffoxxx11'

app = Flask(__name__)
app.config.from_object(__name__)
from app import main
