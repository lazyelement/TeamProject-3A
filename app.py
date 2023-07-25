import pyrebase
from flask import Flask, request, jsonify, render_template, redirect

app = Flask(__name__)
# app.secret_key = "Uog_Team3A_HunterianProject"

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

@app.route('/')
def index():
    return render_template('index.html')

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
            return redirect(url_for('index'))
        except Exception as e:
            if "INVALID_PASSWORD" in str(e):
                return "Password is incorrect"
            elif "EMAIL_NOT_FOUND" in str(e):
                return "Email is invalid"

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)