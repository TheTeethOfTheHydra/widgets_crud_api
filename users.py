import sys
import peewee
import uuid
from server_config import *

db = peewee.SqliteDatabase(DATABASE_FILEPATH)

# define a User object for data marshaling


class User(peewee.Model):
    name = peewee.CharField(max_length=64)
    api_key = peewee.CharField(max_length=36)

    class Meta:
        database = db


db.connect()
db.create_tables([User], safe=True)


def main():
    """
    This python file allows for API key generation to submit requests to the
    CRUD REST API.

    The three operations allowed, selected by inclusion in the command line
    calling this file, are 'create', 'delete', and 'regen'.

    In each case, a preferred user name (str) should also be submitted in the
    command line.

    Create and Regen operations produce an API Key for a user. Delete will
    remove the user/api key from the database.

    """

    if len(sys.argv) < 2:
        return

    operation = sys.argv[1]
    match operation:
        case "create":
            if len(sys.argv) != 3:
                print("Incorrect arguments.")
            else:
                try:
                    existing_user = User.get(User.name == sys.argv[2])
                    print("Username already exists, try again!")
                except User.DoesNotExist:
                    user = User(name=sys.argv[2], api_key=uuid.uuid4())
                    user.save()
                    print("Creating api user " + str(user.name) +
                          " with key " + str(user.api_key))

        case "delete":
            if len(sys.argv) != 3:
                print("Incorrect arguments.")
            else:
                try:
                    existing_user = User.get(User.name == sys.argv[2])
                    existing_user.delete_instance()
                    print("User deleted!")
                except User.DoesNotExist:
                    print("User not found!")

        case "regen":
            if len(sys.argv) != 3:
                print("Incorrect arguments.")
            else:
                try:
                    existing_user = User.get(User.name == sys.argv[2])
                    print("User key is " + str(existing_user.api_key))
                except User.DoesNotExist:
                    print("User not found!")


if __name__ == "__main__":
    main()
