"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, flash, jsonify, request
from flask import render_template, redirect
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    # a = jsonify([1,3])
    # return a
    return render_template("homepage.html")

@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route('/register', methods=["GET"]) 
def register_form():
    """Loads registration form"""

    return render_template("register_form.html")

@app.route('/register', methods=["POST"]) 
def process_form():
    """Process registration form"""

    email=request.form.get("email")
    age=request.form.get("age")
    zipcode=request.form.get("zipcode")
    password=request.form.get("password")

    if User.query.filter_by(email=email).first() is not None:
        flash("Email is already registered. Please sign in.")
        return redirect("/sign-in")
        #later - do a JS/AJAX check of email 
    else:
        new_user = User(email=email, age=age, zipcode=zipcode, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/")  # or user's page?

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    
    app.run(port=5000, host='0.0.0.0')
