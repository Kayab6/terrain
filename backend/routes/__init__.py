from flask import Blueprint

api = Blueprint("api", __name__)

from . import errors, health, map_data, routes, evacuation, persistence
