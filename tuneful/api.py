import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

#had to change (added a models.py to tuneful dir, but the models should be in database.py??):
from . import models

from . import decorators
from . import app
from .database import session
from .utils import upload_path

file_schema = {
        "file": {
                "id": "string"
                }
            }

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    """Gets list of songs"""
    songs = session.query(models.Song).all()
    #print(songs)
    # Convert the posts to JSON and return a response
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")
    
@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
def song_post():
    """Adds a new post"""
    data = request.json
    
    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, file_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")
        
    song = models.Song(file=data["file.id"]) #should this be file.id?
    session.add(song)
    session.commit()
    
@app.route("/api/songs/<int:id>/delete", methods=["GET"])
@decorators.accept("application/json")
def song_delete(id):
    """Delete a song"""
    #get song
    song = session.query(models.Song).get(id)
    file = song.file
    
    #check if song exists if not return 404
    if not song:
        message="Could not find song with id{}".format(id)
        data = json.dumps({"message":message})
        return Response(data, 404, mimetype="application/json")
        
    session.delete(song)
    session.delete(file)
    session.commit()
    
    message= "Deleted song id{}".format(id)
    data = json.dumps({"message":message})
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>/edit")
@decorators.accept("application/json")
def song_edit(id):
    """"Edit a song"""
    data = request.json
    
    #check that json data supplied is valid
    #if not return 422 Unprocessable Entity
    try:
        validate(data, file_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="appication/json")
    
    #get song
    song = session.query(models.Song).get(id)
    file = song.file
    #edit the song
    file.name = data["name"]
    session.commit()
    
    #data = json.dumps(song.as_dictionary())
    #headers = {"Location": url_for("songs_get")}
    return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
    return send_from_directory(upload_path(), filename)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    file = request.files.get("file")
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.filename)
    db_file = models.File(filename=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")