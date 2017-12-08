from flask import Flask, request, render_template, flash, redirect, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
from datetime import date, datetime
import pytz
import bcrypt

from model import User, Item, Model, connect_to_db, db

app = Flask(__name__)
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

app.secret_key = "ABC"


@app.route('/')
def go_home():
    """Goes to the homepage.  Homepage has login box.  If the user is logged in,
     it shows nothing"""

    return render_template("index.html")

@app.route('/register', methods=['POST'])
def register():
    """Process registration."""

    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    password_hashed = bcrypt.hashpw(password.encode('utf-8'), bycrypt.gensalt())

    if User.query.filter_by(email=email).first():
        flash("User %s already exists." % email)
        return redirect("/")

    new_user = User(name=name, email=email, password=password_hashed)

    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.user_id

    flash("User %s added." % email)
    return redirect("/buttons")

@app.route('/login', methods=['POST'])
def login():
    """Logs in user.  Checks if they are in system and if password right."""

     # Get form variables
    email = request.form["email"]
    password = request.form["password"]
    password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("No such user")
        return redirect("/")

    if (bcrypt.checkpw(password.encode('utf-8'), password_hashed)) == False:
        flash("Incorrect password")
        return redirect("/")

    session["user_id"] = user.user_id

    flash("Logged in")
    return redirect("/buttons")

@app.route('/logout')
def logout():
    """Log out."""
    if session.has_key('user_id'):
        del session['user_id']
        flash("Logged Out.")
    return redirect("/")

@app.route('/buttons')
def go_to_buttons():
    """Gives choices for exploring inventory."""

    return render_template("buttons.html")

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
        db.session.add(model)
        db.session.commit()

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

    model_code = item.model_code
    print model_code
    model = Model.query.filter_by(model_code=model_code).first()
    print model
    model.quantity -= 1
    db.session.commit()

    return redirect('/')

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
            dates_shipped_in[item.shipped_in][0] += 1
            dates_shipped_in[item.shipped_in].append([item.manufacturer, "none", item.serial_number])
        else:
            dates_shipped_in[item.shipped_in] = [1]
            dates_shipped_in[item.shipped_in].append([item.manufacturer, "none", item.serial_number])
    print dates_shipped_in

    items_shipped = db.session.query(Item).filter(Item.model_code==model_code).filter(Item.shipped_out.between(starting_date, ending_date)).all()

    count_items_shipped = len(items_shipped)

    dates_shipped_out = {}

    for item in items_shipped:
        if item.shipped_out in dates_shipped_out:
            dates_shipped_out[item.shipped_out][0] += 1
            dates_shipped_out[item.shipped_out].append(["none", item.customer, item.serial_number])
        else:
            dates_shipped_out[item.shipped_out] = [1]
            dates_shipped_out[item.shipped_out].append(["none", item.customer, item.serial_number])
    print dates_shipped_out

    dates = []

    for date in dates_shipped_in:
        dates.append(date)
    for date in dates_shipped_out:
        dates.append(date)

    dates = set(dates)
    dates = list(dates)
    dates = sorted(dates)
    print dates

    dates_info = {}

    for date in dates:
        if date in dates_shipped_in and date not in dates_shipped_out:
            dates_info[date] = [dates_shipped_in[date][0]]
            dates_info[date].append(0)
        if date in dates_shipped_in and date in dates_shipped_out:
            dates_info[date] = [dates_shipped_in[date][0]]
            dates_info[date].append(dates_shipped_out[date][0])
        if date in dates_shipped_out and date not in dates_shipped_in:
            dates_info[date] = [0]
            dates_info[date].append(dates_shipped_in[date][0])
        if date in dates_shipped_in:
            dates_info[date].extend(dates_shipped_in[date][1:])
        if date in dates_shipped_out:
            dates_info[date].extend(dates_shipped_out[date][1:])
    print dates_info

    return render_template("info_for_model_number.html", model=model,  
        model_code=model_code, dates_info=dates_info,
        count_items_received=count_items_received, 
        items_received=items_received, dates_shipped_in=dates_shipped_in, 
        count_items_shipped=count_items_shipped, 
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
    app.run() 

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0", port=5001)



