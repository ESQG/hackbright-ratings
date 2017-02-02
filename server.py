"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, jsonify, request
from flask import render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Rating, Movie
from datetime import datetime

from correlation import pearson

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

@app.route('/sign-in', methods=["GET"])
def sign_in():
    """Signs user in"""

    return render_template("/sign_in.html")

@app.route('/sign-in', methods=["POST"])
def process_login():
    email=request.form.get("email")
    password=request.form.get("password")
    hypothetical_user=User.query.filter_by(email=email).first()
    if hypothetical_user is None:
        flash("That email has not been registered.  Please sign up.")
        return redirect("/register")
    elif hypothetical_user.password == password:
        flash("Successfully logged in as %s" % email)
        session['user_id'] = hypothetical_user.user_id
        session['email'] = email
        return redirect("/")
    else:
        flash("Wrong password. Please sign in again")
        return redirect("/sign-in")

@app.route('/logout')
def logout():
    """Logs user out"""

    del session["user_id"]
    del session["email"]

    flash("Logged Out")
    return redirect("/")

@app.route('/users/<user_id>')
def display_info(user_id):

    user = User.query.get(user_id)
    ratings_dict = {rating.movie.title:str(rating.score) for rating in user.ratings}
    # e.g. {u'Star Trek: First Contact': 5}

    return render_template('/user_info.html',
                            user=user, ratings_dict=ratings_dict)

@app.route('/movies')
def show_movies_list():
    """Returns a list of movies"""

    movies = Movie.query.order_by(Movie.title).order_by(Movie.released_at).all()

    return render_template("movie_list.html",
                            movies=movies)

@app.route('/movies/<movie_id>')
def display_movie(movie_id):
    """Returns info on a movie"""

    movie = Movie.query.get(movie_id)
    scores = [rating.score for rating in movie.ratings]
    release_date = movie.released_at.strftime("%B %d, %Y")
    if scores:
        average = "{:.1f}".format(sum(scores)/float(len(scores)))
    else:
        average="Nobody has rated this yet"


##return page with rating loaded if user has previously rated it
    # score = None
    # if 'user_id' in session:
    #     user = User.query.get(session['user_id'])
    #     rating = find_rating(session['user_id'], movie_id)
    #     if rating is not None:
    #         score = rating.score
    #         prediction = None
    #     else:
    #         score = None
    #         prediction = user.predict_rating(movie)
    # else:
    #     score = None
    #     prediction = None

    return render_template('/movie_info.html',
                            movie=movie,
                            average=average,
                            released=release_date)


@app.route('/rate/<movie_id>', methods=["POST"])
def update_rating(movie_id):
    """Updates or adds a rating"""

    if 'user_id' not in session:
        flash("You must be signed in to rate a movie.")
        return redirect('/sign-in')
    else:
        user_id = session['user_id']
        user = User.query.get(user_id)
        movie_id = int(movie_id)
        score = int(request.form.get("score"))   # cannot be None (Postdata, required)

        rating = find_rating(user_id, movie_id)
        if rating is not None:
            flash("Updated previous rating of %i to %i" %(rating.score, score))
            rating.score = score
            db.session.commit()
            already_rated=True
            return redirect("/movies/"+str(movie_id))
        else:
            db.session.add(Rating(user_id=user_id,
                                      movie_id=movie_id,
                                      score=score))
            db.session.commit()
            return redirect("/movies/"+str(movie_id))

def find_rating(user_id, movie_id):  # returns a rating or None
    return Rating.query.filter(Rating.user_id==user_id, Rating.movie_id==movie_id).first()


@app.route("/prediction/<movie_id>")
def show_prediction(movie_id):
    score = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        rating = find_rating(session['user_id'], movie_id)
        if rating is not None:
            score = rating.score
            prediction = None
        else:
            score = None
            movie = Movie.query.get(movie_id)
            prediction = "{:.1f}".format(user.predict_rating(movie))
    else:
        score = None
        prediction = None

    return jsonify({"prediction": prediction, "score": score})

# def predict_rating(movie, user):
#     existing_rating = find_rating(movie.movie_id, user.user_id)
#     if existing_rating is not None:
#         return existing_rating.score

#     other_ratings = Rating.query.filter_by(movie_id=m.movie_id).all()
#     other_users = [r.user for r in other_ratings]

#     weighted_users=[]
#     for other_user in other_users:
#         sim = other_user.similarity(user)
#         if sim != 0:
#             weighted_users.append((sim, other_user))

#     weighted_users.sort(reverse=True)

#     top_user = weighted_users[0]

    # Rating.query.filter(Rating.user_id==948, Rating.movie_id==496).one().score
#  u_ratings = {}
# >>> for r in u.ratings:
# ...     u_ratings[r.movie_id] = r

# >>> paired_ratings = []
# >>> 


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    
    app.run(port=5000, host='0.0.0.0')