"""Models and database functions for avuewarehouse db."""

from flask_sqlalchemy import SQLAlchemy
# from flask_security import current_user, login_required, RoleMixin, Security, \
#     SQLAlchemyUserDatastore, UserMixin, utils

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Users using Avue Warehouse."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_name = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    # roles = db.relationship(
    #     'Role',
    #     secondary='user_roles')

    def __repr__(self):
        return "<User id=%s user_name=%s email=%s>" % (self.user_id, self.user_name, self.email)

# class Role(db.Model):
#     """Roles users can have."""

#     __tablename__ = "roles"

#     # Our Role has three fields, ID, name and description
#     role_id = db.Column(db.Integer(), primary_key=True, autoincrement=True, nullable=False)
#     name = db.Column(db.String(80), unique=True)

# # Define the UserRoles association table
# class UserRoles(db.Model):
#     __tablename__ = 'user_roles'

#     userrole_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
#     user_id = db.Column(db.Integer(), db.ForeignKey('users.user_id', ondelete='CASCADE'))
#     role_id = db.Column(db.Integer(), db.ForeignKey('roles.role_id', ondelete='CASCADE'))


class Item(db.Model):
    """Items shipped in our shipped out. Each with a model number."""

    __tablename__ = "items"

    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    model_code = db.Column(db.String(50), db.ForeignKey('models.model_code'), nullable=False)
    shipped_in = db.Column(db.Date, nullable=False)
    shipped_out = db.Column(db.Date, nullable=True)
    serial_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(300), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    customer = db.Column(db.String(100), nullable=True)
    img_url = db.Column(db.String(300), nullable=True)

    model = db.relationship('Model', backref='items')

    def __repr__(self):
        return "<Item item_id=%s model_code=%s serial_number=%s shipped_in=%s shipped_out=%s customer=%s>" % (self.item_id, self.model_code, self.serial_number, self.shipped_out, self.shipped_in, self.customer)


class Model(db.Model):
    """Model numbers for items."""

    __tablename__ = "models"

    model_code = db.Column(db.String(50), primary_key=True, nullable=False)
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    

    def __repr__(self):
        return "<Model model_code=%s quantity=%s>" % (self.model_code, self.quantity)


def init_app():
    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask
    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."


def connect_to_db(app, db_uri='postgres:///avuewarehouse'):
    """Connect the database to our Flask app."""

    # Configure to use our database.
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.app = app
    db.init_app(app)

if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    # So that we can use Flask-SQLAlchemy, we'll make a Flask app.
    from flask import Flask

    app = Flask(__name__)

    connect_to_db(app)
    print "Connected to DB."

    db.create_all()