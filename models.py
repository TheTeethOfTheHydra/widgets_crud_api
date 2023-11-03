import sys
import os
import peewee
from server_config import DATABASE_FILEPATH


# check for command line arg "--clear" to start the app with an empty database
if "--clear" in sys.argv:
    file_path = "widgets.db"
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print("Database cleared.")
        except OSError as e:
            print(f"Error clearing widgets database: {e}")

db = peewee.SqliteDatabase(DATABASE_FILEPATH)

# define the Widget object for data marshaling


class Widget(peewee.Model):
    name = peewee.CharField(max_length=64)
    parts = peewee.IntegerField()
    last_user = peewee.CharField(max_length=64)
    created_date = peewee.DateTimeField()
    updated_date = peewee.DateTimeField()

    class Meta:
        database = db


db.connect()
db.create_tables([Widget], safe=True)
