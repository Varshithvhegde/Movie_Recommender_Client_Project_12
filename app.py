from utilityFunctions import *
from SqlQuery import *
from flask import Flask, redirect, render_template, request, jsonify, url_for, session
import operator
# from annoy import AnnoyIndex
from flask_mail import Mail, Message
from random import randint
from flask_cors import CORS, cross_origin
from sklearn.neighbors import NearestNeighbors
from gensim.models import Word2Vec
import faiss
import numpy as np
import bs4 as bs
import urllib.request
import requests



app = Flask(__name__)
app.secret_key = "secret key"
CORS(app, support_credentials=True)


# Flask mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = "test@gmail.com"
app.config['MAIL_PASSWORD'] = "dleiatmoyykkaafn"
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# fetch movies data
conn = db_connection("movies")
cursor = conn.cursor()
cursor.execute(FETCH_ALL_MOVIES)
movies_result = cursor.fetchall()
conn.close()


# Home page
@app.route('/')
def index():
    # Create a session with email varshithvhgmail.com and VARSHA26 as password
    # session["user"] = "varshithvh@gmail.com"
    # session["choices"] = 1
    # return redirect(url_for("recommendations"))
    return render_template("index.html")
    
    


# Signup page
signup_email = ""
signup_password = ""
signup_mobile = ""
@app.route('/signup', methods=['GET','POST'])
def signup():
    global signup_email
    global signup_password
    global signup_mobile
    response = render_template("signup.html")

    if request.method == 'POST':
        conn = db_connection("users")
        cursor = conn.cursor()

        signup_email = request.form["email"]
        signup_mobile = request.form["mobile"]
        signup_password = request.form["password"]

        sql_query = "Select email from users where email= '"+signup_email+"'"
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()

        if len(results) != 0:
            response = "This email is already registered. <br> Please sign-in."
        else:
            session["user"] = signup_email
            session["choices"] = 0
            response = "choices"
    return response


# Signin page
signin_email = ""
@app.route('/signin', methods=['GET','POST'])
def signin():
    global signin_email
    response = render_template("signin.html")

    if request.method == 'POST':
        conn = db_connection("users")
        cursor = conn.cursor()

        signin_email = request.form["email"]
        password = request.form["password"]

        sql_query = "Select email, password from users where email= '"+signin_email+"'"
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()

        if len(results) == 0:
            response = "This email is not registered. <br> Please sign-up first."
        elif password != results[0][1]:
                response = "Incorrect Password."
        elif password == results[0][1]:
            session["user"] = signin_email
            session["choices"] = 1
            response = "recommendations"

    return response


# Choices page
@app.route('/choices', methods=['GET','POST'])
def choices():
    global signup_email
    global movies_result
    if "user" in session:
        if "choices" in session and session["choices"] == 1:
            return redirect(url_for("recommendations"))
        else:
            genre_names = []
            cast_dict = {}
            for row in movies_result:
                mov_gen = list(row[5].split("$"))
                for gen in mov_gen:
                    if gen not in genre_names and gen != '':
                        genre_names.append(gen)

                mov_cast = list(row[7].split("$"))
                for cast in mov_cast:
                    if cast in cast_dict and cast != '':
                        cast_dict[cast] = (cast_dict[cast] + 1)
                    else:
                        cast_dict[cast] = 0

            cast_dict = dict(sorted(cast_dict.items(), key=operator.itemgetter(1), reverse=True))
            cast_names = []
            counter = 0
            for key in cast_dict:
                if counter < 25:
                    cast_names.append(key)
                    counter += 1
                else:
                    break

            return render_template("choices.html", genre_names=genre_names, cast_names=cast_names)
    else:
        print("Session not found")
        return redirect(url_for("signup"))


movie_names = []
for row in movies_result:
    movie_names.append(row[2])


@app.route('/recommendations', methods=['GET','POST'])
def recommendations():
    return render_template("recommendations.html")



# Forgot page
@app.route('/forgot', methods=['POST', 'GET'])
def forgot():
    global signin_email
    global otp

    response = render_template("forgotPass.html")
    if request.method == 'POST':
        conn = db_connection("users")
        cursor = conn.cursor()

        signin_email = request.form["email"]

        sql_query = "Select email, password from users where email= '"+signin_email+"'"
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()

        if len(results) == 0:
            response = "This email is not registered. <br> Please sign-up first."
        else:
            response = "forgot"

    if response == "forgot":
        range_start = 10**(6-1)
        range_end = (10**6)-1
        otp = randint(range_start, range_end)
        message = Message("Next Up | OTP for password reset", sender="test@gmail.com", recipients=[signin_email])
        message.body = "OTP: "+str(otp)
        mail.send(message)

    return response


# reset page
@app.route('/reset', methods=['GET','POST'])
def reset():
    global otp
    response = render_template("reset.html")
    if request.method == 'POST':
        num = request.form["otp"]
        if str(num) == str(otp):
            response = "valid"
        else:
            response = "OTP entered is incorrect"

    return response


# change password in database
@app.route('/change', methods=['GET','POST'])
def change():
    global signin_email
    if request.method == 'POST':
        newPass = request.form["newPass"]
        conn = db_connection("users")
        cursor = conn.cursor()
        sql_query = "Update users set password = '"+newPass+"' where email = '"+signin_email+"'"
        cursor.execute(sql_query)
        conn.commit()
        conn.close()
        session["user"] = signin_email
        session["choices"] = 1

    return ""


# Logout
@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("choices", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)


