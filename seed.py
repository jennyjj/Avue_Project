"""Utility file to seed avuewarehouse database"""

from model import User, Item, Model, connect_to_db, db
from server import app
import bcrypt

def load_items():
    """Load items into database."""

    print "Items"

    Item.query.delete()


def load_models():
    """Load models into database."""

    print "Models"

    Model.query.delete()

    for row in open("seed_data/u.model3"):

        row = row.rstrip()

        model_code, description, quantity  = row.split("|")

        model = Model(model_code=model_code, description=description, quantity=quantity)

        db.session.add(model)

        db.session.commit()

def load_users():
    """Load users into database."""

    print "Users"

    User.query.delete()

    for row in open("seed_data/u.users"):

        row = row.rstrip()

        user_name, email, password = row.split("|")

        password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = User(user_name=user_name, email=email, password=password_hashed)

        db.session.add(user)

        db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    load_items()
    load_models()
    load_users()

