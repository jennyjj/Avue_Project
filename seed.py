"""Utility file to seed avuewarehouse database"""

from model import User, Item, Model, Role, UserRoles, connect_to_db, db
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

        user_name, password, role = row.split("|")

        password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user = User(user_name=user_name, password=password_hashed)

        user.roles = [role,]

        db.session.commit()

def load_roles():
    """Load roles into database."""

    print "Roles"

    Role.query.delete()

    admin_role = Role(name="Admin")
    db.session.add(admin_role)
    db.session.commit()

    demoltd_role = Role(name="Demoltd")
    db.session.add(demoltd_role)
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    load_items()
    load_models()
    load_users()
    load_roles()

