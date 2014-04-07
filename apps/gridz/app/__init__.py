from flask import Flask

# configuration
DEBUG = True
SECRET_KEY = 'aeoffoxxx11'

app = Flask(__name__)
app.config.from_object(__name__)
from app import main
