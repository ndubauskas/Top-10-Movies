from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc

import requests
import os

AUTHORIZATION_KEY = os.environ["Auth_Key"]
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars()
    return render_template("index.html",movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():


    if request.method == "POST":
        movie_name = request.form["title"]

        url = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
        headers = {"accept": "application/json",
                    "Authorization": AUTHORIZATION_KEY
                  }
        params = {"query": movie_name,
                  "language": "en-US",
                  "include_adult": True,

                  }

        response = requests.get(url, params=params, headers=headers)

        data = response.json()["results"]

        return render_template("select.html",options=data)

    return render_template("add.html")


@app.route("/edit",methods=["GET","POST"])
def edit():
    if request.method == "POST":
        movie_id = request.form["id"]
        movie_to_update = db.get_or_404(Movie,movie_id)
        movie_to_update.rating = request.form["rating"]
        movie_to_update.review = request.form["review"]
        print(f"new review{movie_to_update.review}")
        db.session.commit()
        return redirect(url_for("home"))
    movie_id = request.args.get("id")
    movie_selected = db.get_or_404(Movie,movie_id)
    return render_template("edit.html",movie=movie_selected)

@app.route("/find")
def get_movie():

    movie_api_id = request.args.get("id")
    if movie_api_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_api_id}?language=en-US"

        headers = {
                    "accept": "application/json",
                   "Authorization": AUTHORIZATION_KEY
                   }
        params = {
                 "movie_id": movie_api_id

        }
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        new_movie = Movie(
            title=data["original_title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return render_template("edit.html", movie=new_movie)

    return redirect(url_for('home'))


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
