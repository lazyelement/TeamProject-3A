import firebase_admin
import pyrebase
import json
from functools import wraps
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import random
import os
import git
import hmac
import hashlib

app = Flask(__name__)
app.secret_key = "Uog_Team3A_HunterianProject"

os.environ["w_secret"] = "williamsocute"

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
    param = request.args.get('param')
    if 'userId' not in session:
        return redirect(url_for('basket'))
    currentUser = session.get('userId')
    userCollections = firestore.client().collection('usercollection').document(currentUser).get().to_dict()['collections']
    return render_template('loginCollection.html', collection=userCollections, param=param)


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
            #xxxxxxxxxxxxxxxxxxxxxxxxx
            return redirect(url_for('collections', param="You have exceeded the daily limit"))
    else:
        if int(questionNum) > 3:
            return redirect(url_for('congrats'))

    if currentBasket:
        basketList = json.loads(currentBasket)
        basketArr = [item["name"] for item in basketList["artifacts"]]
        if len(basketArr) >= 3:
            #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            return redirect(url_for('basket', param="You have exceeded the daily limit"))

    if currentUser and currentBasket:
        combinedArr = userCollections + basketArr
        uniqueSet = set(combinedArr)
        uniqueArr = list(uniqueSet)
        if len(uniqueArr) >= 3:
            #xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            return redirect(url_for('collections', param="You have exceeded the daily limit"))

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
    if not pastArtifact:
        return redirect(url_for('collections'))
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
    if 'congrats' in referringPage:
        page = 'congrats'
    elif 'basket' in referringPage:
        page = 'basket'
    else:
        page = 'collections'

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
    param = request.args.get('param')
    currentBasket = session.get('basket')
    basketList = 0
    if currentBasket:
        basketList = json.loads(currentBasket)

    return render_template('basket.html', basket=basketList, param=param)

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

def is_valid_signature(x_hub_signature, data, private_key):
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method != 'POST':
        return 'OK', 200
    else:
        w_secret = os.environ.get("w_secret")
        # Do initial validations on required headers
        if 'X-Github-Event' not in request.headers:
            return 'Error', 450
        if 'X-Github-Delivery' not in request.headers:
            return 'Error', 451
        if 'X-Hub-Signature' not in request.headers:
            return 'Error', 452
        if not request.is_json:
            return 'Error', 453
        if 'User-Agent' not in request.headers:
            return 'Error', 454
        ua = request.headers.get('User-Agent')
        if not ua.startswith('GitHub-Hookshot/'):
            return 'Error', 455

        event = request.headers.get('X-GitHub-Event')
        if event == "ping":
            return json.dumps({'msg': 'Hi!'})

        x_hub_signature = request.headers.get('X-Hub-Signature')
        if not is_valid_signature(x_hub_signature, request.data, w_secret):
            print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
            return 'Error', 456

        payload = request.get_json()
        if payload is None:
            print('Deploy payload is empty: {payload}'.format(payload=payload))
            return 'Error', 457

        if payload['ref'] != 'refs/heads/main':
            return json.dumps({'msg': 'Not main, ignoring'}), 458

        repo = git.Repo(os.getcwd(), search_parent_directories=True)
        origin = repo.remotes.origin
        url_with_pat = 'https://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@github.com/junwei99555/TeamProject-3A.git'
        origin.set_url(url_with_pat)

        pull_info = origin.pull()

        if len(pull_info) == 0:
            return json.dumps({'msg': "Didn't pull any information from remote!"}), 459
        if pull_info[0].flags > 128:
            return json.dumps({'msg': "Didn't pull any information from remote!"}), 460
        
        return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
