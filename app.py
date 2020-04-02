from flask import Flask, render_template, request, redirect, url_for, session, request, logging, flash
from flask_sqlalchemy import SQLAlchemy 
from datetime import datetime
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)
    

#Creating a table for Patients
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable = False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True, nullable = False)
    age = db.Column(db.String(50), nullable = False)
    treatment = db.Column(db.Text(300))
    infection = db.Column(db.Text(300))
    allergy = db.Column(db.Text(300))
    medication = db.Column(db.Text(300))
    prescription = db.Column(db.Text(300))
    date_treated = db.Column(db.DateTime)
    next_appointment = db.Column(db.String(20))

#Creating a table for Users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable = False)
    email = db.Column(db.String(100), unique=True, nullable = False)
    username = db.Column(db.String(100), unique=True, nullable = False)
    password = db.Column(db.String(100), nullable = False)

#Creating a table for Articles
class Blogpost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable = False)
    subtitle = db.Column(db.String(50), nullable = False)
    author = db.Column(db.String(20), nullable = False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable = False)

# Register Form Class for User Input
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=1, max=50)] )
    email = StringField('Email', [validators.Email()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        user = User(name=name, email=email,username=username,password=password)
        db.session.add(user)
        db.session.commit()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        result = User.query.filter_by(username=username).first()

        if result.username == username:
            # Get stored hash
            data = result
            password = data.password
            name = data.name

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username
                session['name'] = name

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Checking if the user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

#Home Page
@app.route('/')
def index():
    posts = Blogpost.query.order_by(Blogpost.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

#About Page
@app.route('/about')
def about():
    return render_template('about.html')

#User's Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    patients = Patient.query.order_by(Patient.date_treated.desc()).all()
    return render_template('dashboard.html', patients = patients)

#Displaying Individual Patient
@app.route('/patient/<int:patient_id>')
@is_logged_in
def patient(patient_id):
    patient = Patient.query.filter_by(id=patient_id).one()

    return render_template('patient.html', patient=patient)

#Adding Patient 
@app.route('/add_patient')
@is_logged_in
def add_patient():
    return render_template('add_patient.html')

#Adding Patients to the list
@app.route('/addpatient', methods=['POST'])
@is_logged_in
def addpatient():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    age = request.form['age']
    treatment = request.form['treatment']
    infection = request.form['infection']
    allergy = request.form['allergy']
    medication = request.form['medication']
    prescription = request.form['prescription']
    next_appointment = request.form['next_appointment']
    patient = Patient(name=name, phone=phone, email=email, age=age, treatment=treatment, infection=infection, allergy=allergy, medication=medication, prescription = prescription, date_treated=datetime.now(), next_appointment=next_appointment)
    flash('New Patient has been successfully added!', 'success')
    db.session.add(patient)
    db.session.commit()
    return redirect(url_for('dashboard'))

#Removing Patients from the list
@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
@is_logged_in
def delete_patient(patient_id):
    patient = Patient.query.filter_by(id=patient_id).one()
    db.session.delete(patient)
    db.session.commit()
    flash('The patient has been deleted!', 'success')
    return redirect(url_for('dashboard'))

#Displaying content of individual posts
@app.route('/post/<int:post_id>')
@is_logged_in
def post(post_id):
    post = Blogpost.query.filter_by(id=post_id).one()
    return render_template('post.html', post=post)

#Adding new Articles
@app.route('/add')
@is_logged_in
def add():
    return render_template('add.html')

#Adding new Articles to the list
@app.route('/addpost', methods=['POST'])
@is_logged_in
def addpost():
    title = request.form['title']
    subtitle = request.form['subtitle']
    author = request.form['author']
    content = request.form['content']
    post = Blogpost(title=title, subtitle=subtitle, author=author, content=content, date_posted=datetime.now())
    db.session.add(post)
    db.session.commit()
    flash('New Article has been successfully added!', 'success')
    return redirect(url_for('index'))

#Deleting Articles from the list
@app.route('/delete_post/<int:post_id>', methods=['POST'])
@is_logged_in
def delete_post(post_id):
    post = Blogpost.query.filter_by(id=patient_id).one()
    db.session.delete(post)
    db.session.commit()
    flash('The Article is deleted!', 'success')
    return redirect(url_for('index'))

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key='iwanttolearnmoreaboutit'
    app.run(debug=True)