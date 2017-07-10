import os

from flask import Flask

app = Flask(__name__)
config_path = os.environ.get("CONFIG_PATH", "tuneful.config.DevelopmentConfig")
app.config.from_object(config_path)

#had to change:
#from . import api
#from . import views
#to:
#from tuneful import api
from tuneful import api
from tuneful import views