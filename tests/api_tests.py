import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO, BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())
        
    def test_get_post_songs(self):
        """POSTing and GETting songs"""
        #create songs to test with
        file1 = models.File(name="test1.mp3")
        file2 = models.File(name="test2.mp3")
        song1 = models.Song(file=file1)
        song2 = models.Song(file=file2)
        #add songs
        session.add_all([file1, file2, song1, song2])
        session.commit()
        #check response
        response = self.client.get(
            "/api/songs", headers=[("Accept", "application/json")])
            
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        #decode response    
        data = json.loads(response.data.decode("ascii"))
        #check against the created files
        self.assertEqual(data[0]["file"]["id"], file1.id)
        self.assertEqual(data[1]["file"]["id"], file2.id)
        
    def test_delete_song(self):
        """delete a song"""
        #create and add a song to delete
        file1 = models.File(name="deleteme_1.mp3")
        song1 = models.Song(file=file1)
        #file2 = models.File(name="deleteme_2.mp3")
        #song2 = models.Song(file=file2)
        session.add_all([file1, song1])
        session.commit()
        
        #check response
        response = self.client.get(
            "/api/songs/1/delete", headers=[("Accept", "application/json")]
            )
            
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Deleted song id1")
        
    def test_edit_song(self):

        #create and add a song to edit
        file1 = models.File(name="editme.mp3")
        song1 = models.Song(file=file1)
        #file2 = models.File(name="editme_2.mp3")
        #song2 = models.Song(file=file2)
        session.add_all([file1, song1])
        session.commit()
        #check id
        print(session.query(models.Song).all()[0].id)
        
        data = {"name": "edited.mp3"}
        #headers- sending data that works in predefined format
        response = self.client.put("/api/songs/1/edit", data=json.dumps(data),
                                    content_type="application/json", 
                                    headers=[("Accept", "application/json")])
        
        #checks:
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        
        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["file"]["name"], "edited.mp3")


    def test_get_uploaded_file(self):
        path = upload_path("test.txt")
        with open(path, "wb") as f:
            f.write(b"File contents")
            
        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, b"File contents")
    
    def test_file_upload(self):
        data = {
            "file": (BytesIO(b"File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            contents = f.read()
        self.assertEqual(contents, b"File contents")
        