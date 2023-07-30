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
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    return render_template('loading.html')

@app.route('/spinning')
def spinning():
    return render_template('spinningpage.html')

@app.route('/start')
def start():
    return render_template('start.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/profile')
@login_required
def profile():
    currentUserEmail = session.get('userEmail')
    return render_template('profile.html', email=currentUserEmail)

@app.route('/collections', methods=['GET'])
def collections():
    if 'userId' not in session:
        return redirect(url_for('basket'))
    currentUser = session.get('userId')
    userCollections = firestore.client().collection('usercollection').document(currentUser).get().to_dict()['collections']
    return render_template('loginCollection.html', collection=userCollections)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cfmpassword = request.form['cfmpassword']

        try:
            if(password == cfmpassword):
                # Create a new user account with email and password
                user = auth.create_user_with_email_and_password(email, password)
                return redirect(url_for('login'))
            else:
                error_message = "Passwords don't match"
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in str(e):
                error_message = "Email already exists"

    return render_template('register.html', error_message=error_message)


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
                        uc.set({"collections": firestore.ArrayUnion([item['name']])}, merge=True)

            return redirect(url_for('start'))
        except Exception as e:
            if "INVALID_PASSWORD" in str(e):
                return render_template('login.html', error="Password is incorrect")
            elif "EMAIL_NOT_FOUND" in str(e):
                return render_template('login.html', error="Email is invalid")
            else:
                return render_template('login.html', error="An error has occured")

    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.clear()
    return redirect(url_for('login'))

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

        if currentBasket:
            basketList = json.loads(currentBasket)
            while True:
                existsBasket = checkExists(basketList, artifact)
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

def checkExists(basketData, artifact):
    existsBasket = False
    for item in basketData["artifacts"]:
        if item["name"] == artifact["name"]:
            existsBasket = True
            break
    
    existsDb = False
    currentUser = session.get('userId')
    if currentUser:
        userCollections = firestore.client().collection('usercollection').document(currentUser).get().to_dict()['collections']
        for item in userCollections:
            if item == artifact["name"]:
                existsDb = True
                break

    return existsBasket or existsDb

@app.route('/congrats', methods=['GET', 'POST'])
def congrats():
    pastArtifact = session.get('pastArtifact')
    artifact = json.loads(pastArtifact)
    session.pop('pastArtifact')

    currentUser = session.get('userId')
    if currentUser:
        return render_template('congratulation.html', artifact=artifact, loggedIn=True)

    return render_template('congratulation.html', artifact=artifact, loggedIn=False)


@app.route('/artifactInfo/<name>', methods=['GET', 'POST'])
def artifactInfo(name):
    artifact = get_artifact_by_name(name)

    referringPage = request.headers.get('Referer')
    if 'collections' in referringPage:
        page = 'collections'
    else:
        page = 'congrats'

    currentUser = session.get('userId')
    if currentUser:
        return render_template('artifactInfo.html', artifact=artifact, loggedIn=True, page=page)

    return render_template('artifactInfo.html', artifact=artifact, loggedIn=False, page=page)

@app.route('/addToSession', methods=['POST'])
def addToSession():
    data = request.json
    pastArtifactString = json.dumps(data)
    session['pastArtifact'] = pastArtifactString
    return jsonify({'message': 'Success'}), 200

@app.route('/basket', methods=['GET', 'POST'])
def basket():
    currentBasket = session.get('basket')
    basketList = 0
    if currentBasket:
        basketList = json.loads(currentBasket)
    

    return render_template('basket.html', basket=basketList)


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

def get_artifact_by_name(name):
    questions_collection = firestore.client().collection('collectionquestions')
    all_items = questions_collection.get()
    
    artifact = {}
    for item in all_items:
        data = item.to_dict()
        if data['name'] == name:
            artifact = data

    return artifact

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
