from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import pickle
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

app = Flask(__name__)
app.secret_key = "secret123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

# Load trained model
model = pickle.load(open('model/disease_model.pkl', 'rb'))

# Routes

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if not uname or not pwd:
            return "Please fill all fields"
        existing_user = User.query.filter_by(username=uname).first()
        if existing_user:
            return "User already exists"
        db.session.add(User(username=uname, password=pwd))
        db.session.commit()
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    uname = request.form['username']
    pwd = request.form['password']
    user = User.query.filter_by(username=uname, password=pwd).first()
    if user:
        session['user'] = uname
        return render_template('home.html')  # Prediction form
    else:
        return 'Invalid credentials. Please try again.'
    
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        uname = request.form['username']
        new_pwd = request.form['new_password']
        user = User.query.filter_by(username=uname).first()
        if user:
            user.password = new_pwd
            db.session.commit()
            return render_template('login.html', message="Password reset successful! Please login with your new password.")
        else:
            return "User not found"
    return render_template('reset_password.html')




@app.route('/predict', methods=['POST'])
def predict():
    # Get binary symptoms
    fever = 1 if 'Fever' in request.form else 0
    cough = 1 if 'Cough' in request.form else 0
    headache = 1 if 'Headache' in request.form else 0
    fatigue = 1 if 'Fatigue' in request.form else 0
    cold = 1 if 'Cold' in request.form else 0

    # Get numeric inputs
    sugar = int(request.form['Sugar'])
    age = int(request.form['Age'])
    weight = int(request.form['Weight'])
    bp = int(request.form['BP'])

    # Predict
    input_features = [[fever, cough, headache, fatigue, sugar, age, weight, cold, bp]]
    prediction = model.predict(input_features)[0]

    # Create and save graph
    if not os.path.exists('static'):
        os.makedirs('static')
    plt.figure(figsize=(5, 3))
    sns.barplot(x=["Prediction"], y=[1])
    plt.title(f"Predicted: {prediction}")
    plt.savefig('static/graph.png')
    plt.close()

    return render_template('result.html', prediction=prediction, image='graph.png')

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
