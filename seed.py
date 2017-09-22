"""Utility file to seed avuewarehouse database"""

from model import Item, Model, connect_to_db, db
from server import app


def load_items():
    """Load items into database."""

    print "Items"

    Item.query.delete()

    # for row in open("seed_data/u.item"):
    #     row = row.rstrip()

    #     genre_id, genre_code, genre_name, artist, img_url = row.split("|")

    #     genre = Genre(genre_code=genre_code,
    #                     genre_name=genre_name,
    #                     artist=artist,
    #                     img_url=img_url)

    #     db.session.add(genre)

    #     db.session.commit()


def load_models():
    """Load models into database."""

    print "Models"

    Model.query.delete()

    for row in open("seed_data/u.model"):
        row = row.rstrip()

        model_code, description, quantity  = row.split("|")

        model = Model(model_code=model_code, description=description, quantity=quantity)

        db.session.add(model)

        db.session.commit()


    

if __name__ == "__main__":
    connect_to_db(app)

    load_items()
    load_models()
    # load_users()
