from flask import Flask, request, render_template, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
from datetime import date, datetime
import pytz

from model import Item, Model, connect_to_db, db

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

app.secret_key = "ABC"


@app.route('/')
def go_home():
    """Goes to the homepage.  Homepage has search box for product's location."""

    return render_template("index.html")

@app.route('/ship_in_form')
def go_shipped_in_form():
    """Gives form to fill out upon shipping in item(s)."""

    return render_template("ship_in.html")

@app.route('/ship_in', methods=["POST"])
def shipped_in():
    """Receiving item and inputting information associated with item."""

    serial_number = request.form.get("serial_number")
    description = request.form.get("description")
    model_code = request.form.get("model_code")
    manufacturer = request.form.get("manufacturer")

    pacific = pytz.timezone('US/Pacific')
    time = datetime.now(tz=pacific)
    shipped_in = "%s/%s/%s" % (time.month, time.day, time.year)

    item = Item(shipped_in=shipped_in,
                serial_number=serial_number,
                description=description,
                model_code=model_code,
                manufacturer=manufacturer)  

    model = Model.query.filter_by(model_code=model_code).first()

    if model:
        model.quantity += 1
    else:
        model = Model(model_code=model_code,
                quantity=1)

    db.session.add(item)
    db.session.commit() 

    return redirect("/")

@app.route('/ship_out_form')
def go_shipped_out_form():
    """Gives form to fill out upon shipping out item(s)."""

    return render_template("ship_out.html")

@app.route('/ship_out', methods=["POST"])
def shipped_out():
    """Shipping out an item and inputting information about customer."""

    serial_number = request.form.get("serial_number")
    customer = request.form.get("customer")

    item = Item.query.filter_by(serial_number=serial_number).first()

    pacific = pytz.timezone('US/Pacific')
    time = datetime.now(tz=pacific)
    shipped_out = "%s/%s/%s" % (time.month, time.day, time.year)

    item.shipped_out = shipped_out
    item.customer = customer
    db.session.commit()

    return redirect('/')

    # model_number = item.model_code
    # model = Model.query.filter_by(model_code=model_number):
    # model.quantity -= 1
    # db.session.commit()

@app.route('/form_for_model_number')
def see_model_number():
    """Get model number in order to give information."""

    return render_template("form_for_model_number.html")

@app.route('/info_for_model_number', methods=["POST"])
def get_info_by_model_number():
    """Get information by model number for given timeframe."""

    model_code = request.form.get("model_code")
    starting_date = request.form.get("start_date")
    ending_date = request.form.get("end_date")

    # starting_date = datetime.strptime(starting_date, "%Y-%m-%d")
    # ending_date = datetime.strptime(ending_date, "%Y-%m-%d")

    model = Model.query.filter_by(model_code=model_code).first()

    items_received = db.session.query(Item).filter(Item.model_code==model_code).filter(Item.shipped_in.between(starting_date, ending_date)).all()
    
    count_items_received = len(items_received)

    dates_shipped_in = {}

    for item in items_received:
        if item.shipped_in in dates_shipped_in:
            dates_shipped_in[item.shipped_in] += 1
        else:
            dates_shipped_out[item.shipped_in] = 1
    print dates_shipped_in

    items_shipped = db.session.query(Item).filter(Item.model_code==model_code).filter(Item.shipped_out.between(starting_date, ending_date)).all()

    count_items_shipped = len(items_shipped)

    dates_shipped_out = {}

    for item in items_shipped:
        if item.shipped_out in dates_shipped_out:
            dates_shipped_out[item.shipped_out] += 1
        else:
            dates_shipped_out[item.shipped_out] = 1
    print dates_shipped_out

    return render_template("info_for_model_number.html", model=model, model_code=model_code, 
        count_items_received=count_items_received, items_received=items_received, 
        dates_shipped_in=dates_shipped_in, count_items_shipped=count_items_shipped, 
        items_shipped=items_shipped, dates_shipped_out=dates_shipped_out)

@app.route('/form_for_serial_number')
def see_serial_number():
    """Get serial number in order to give information."""

    return render_template("form_for_serial_number.html")

@app.route('/info_for_serial_number', methods=["POST"])
def get_info_by_serial_number():
    """Give information for item with a serial number."""

    serial_number = request.form.get("serial_number")

    item = Item.query.filter_by(serial_number=serial_number).first()
    print item

    return render_template("info_for_serial_number.html", item=item)


if __name__ == "__main__":    
    connect_to_db(app)
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")



