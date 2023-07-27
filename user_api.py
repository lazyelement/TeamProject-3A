import firebase_admin
import pyrebase
import json
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
    return render_template('start.html')

@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/collections', methods=['GET'])
def collections():
    if 'userId' not in session:
        return redirect(url_for('login'))
    return render_template('loginCollection.html')


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

            currentBasket = session.get('basket')
            if currentBasket:
                uc = firestore.client().collection('usercollection').document(user["localId"])

                ucData = uc.get().to_dict()
                if ucData is None:
                    ucData = {}

                basketList = json.loads(currentBasket)
                for item in basketList['artifacts']:
                    if item['name'] not in ucData.get("collections", []):
                        uc.update({"collections": firestore.ArrayUnion([item['name']])})

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

@app.route('/question/<questionNum>', methods=['GET', 'POST'])
def question(questionNum):
    currentArtifact = session.get('artifact')
    currentBasket = session.get('basket')
    currentUser = session.get('userId')
    if currentUser:
        userCollections = firestore.client().collection('usercollection').document(currentUser).get().to_dict()['collections']
        pastArtifact = session.get('pastArtifact')
        if pastArtifact:
            if int(questionNum) > 3:
                artifactP = json.loads(pastArtifact)
                uc = firestore.client().collection('usercollection').document(currentUser)
                uc.update({"collections": firestore.ArrayUnion([artifactP['name']])})
                        
                
                return redirect(url_for('congrats'))
        if len(userCollections) >= 3:
            return redirect(url_for('collections'))
    else:
        if int(questionNum) > 3:
            return redirect(url_for('congrats'))

    if currentBasket:
        basketList = json.loads(currentBasket)
        basketArr = [item["name"] for item in basketList["artifacts"]]
        if len(basketArr) >= 3:
            return redirect(url_for('basket'))

    if currentUser and currentBasket:
        combinedArr = userCollections + basketArr
        uniqueSet = set(combinedArr)
        uniqueArr = list(uniqueSet)
        if len(uniqueArr) >= 3:
            return redirect(url_for('collections'))

    if currentArtifact:
        artifact = json.loads(currentArtifact)
    else:
        artifact = get_random_item_from_firestore()

        if currentUser:
            if userCollections:
                while True:
                    existsDb = checkExistsDb(userCollections, artifact)
                    if existsDb:
                        artifact = get_random_item_from_firestore()
                    else:
                        if currentBasket:
                            basketList = json.loads(currentBasket)
                            while True:
                                existsBasket = checkExistsBasket(basketList, artifact)
                                if existsBasket:
                                    artifact = get_random_item_from_firestore()
                                else:
                                    break
                        break
        else:
            if currentBasket:
                basketList = json.loads(currentBasket)
                while True:
                    existsBasket = checkExistsBasket(basketList, artifact)
                    if existsBasket:
                        artifact = get_random_item_from_firestore()
                    else:
                        break

        artifactString = json.dumps(artifact)
        session['artifact'] = artifactString

    artifact["questionNum"] = int(questionNum)
    if int(questionNum) == 3:
        if currentBasket:
            basketList = json.loads(currentBasket)
            basketList["artifacts"].append(artifact)
            basketListString = json.dumps(basketList)
            session['basket'] = basketListString
        else:
            basketList = {
                "artifacts": []
            }

            session['basket'] = json.dumps({
                "artifacts": [artifact]
            })

        session.pop('artifact')
        pastArtifactString = json.dumps(artifact)
        session['pastArtifact'] = pastArtifactString

    return render_template('question.html', artifact=artifact)

def checkExistsDb(userCollections, artifact):
    exists = False
    for item in userCollections:
        if item == artifact["name"]:
            exists = True
            break

    return exists

def checkExistsBasket(basketData, artifact):
    exists = False
    for item in basketData["artifacts"]:
        if item["name"] == artifact["name"]:
            exists = True
            break

    return exists

@app.route('/hehe', methods=['GET', 'POST'])
def hehe():
    basket = session.get('basket')
    print(basket)
    return render_template('congratulation.html')

@app.route('/congrats', methods=['GET', 'POST'])
def congrats():
    pastArtifact = session.get('pastArtifact')
    artifact = {}
    if pastArtifact:
        artifact = json.loads(pastArtifact)

    session.pop('pastArtifact')
    return render_template('congratulation.html', artifact=artifact)

@app.route('/spin', methods=['GET', 'POST'])
def spin():
    return render_template('spin.html')

@app.route('/basket', methods=['GET', 'POST'])
def basket():
    return render_template('basket.html')

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

# print(get_random_item_from_firestore())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
