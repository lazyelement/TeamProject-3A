import firebase_admin
import pyrebase
from functools import wraps
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import random

app = Flask(__name__)
app.secret_key = "Uog_Team3A_HunterianProject"

config = {
    "apiKey": "AIzaSyD7zBBfqV8oDfZARSpHumUf3aVecRBsEP4",
    "authDomain": "williamcollection-a2bba.firebaseapp.com",
    "databaseURL": "https://williamcollection-a2bba.firebaseio.com",
    "projectId": "williamcollection-a2bba",
    "storageBucket": "williamcollection-a2bba.appspot.com",
    "messagingSenderId": "662135269663",
    "appId": "1:662135269663:web:e25a794e3774355f77a82a"
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

cred = credentials.Certificate('./keys/williamcollection-a2bba-3986e38ef805.json')
firebase_admin.initialize_app(cred)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'userId' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/collections', methods=['GET'])
def collections():
    if 'userId' not in session:
        return redirect(url_for('login'))
    return render_template('collections.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Create a new user account with email and password
            user = auth.create_user_with_email_and_password(email, password)
            return redirect(url_for('index'))
        except Exception as e:
            return str(e)
            if "EMAIL_EXISTS" in str(e):
                return "Email already exists"

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['userId'] = user["localId"]
            session['userEmail'] = user["email"]
            return redirect(url_for('index'))
        except Exception as e:
            if "INVALID_PASSWORD" in str(e):
                return "Password is incorrect"
            elif "EMAIL_NOT_FOUND" in str(e):
                return "Email is invalid"

    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/test', methods=['GET'])
@login_required
def test():
    # This endpoint will only be accessible if the user is logged in

    return jsonify({'data': 'Secret data only for logged-in users'}), 200


def get_random_item_from_firestore():
    # Get a reference to the "collectionquestions" collection in Firestore
    questions_collection = firestore.client().collection('collectionquestions')

    # Get all documents from the "collectionquestions" collection
    all_items = questions_collection.get()

    # Get the total number of documents in the "collectionquestions" collection
    total_items = len(all_items)

    # Check if there are any items in the collection
    if total_items == 0:
        return None

    # Get a random number between 0 and the total number of items
    random_index = random.randint(0, total_items - 1)

    # Get the random item from the collection using the random index
    random_item = all_items[random_index].to_dict()

    return random_item

print(get_random_item_from_firestore())

if __name__ == '__main__':
    app.run(debug=True)


