from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

user_bp = Blueprint('user', __name__)



@user_bp.route('/user_signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        address = request.form.get('address')
        pin = request.form.get('pin')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('user/user_signup.html')

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('User already exists with this email.', 'error')
            return render_template('user/user_signup.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(
            firstname=firstname,
            lastname=lastname,
            email=email,
            gender=gender,
            phone=phone,
            password=hashed_password,
            address=address,
            pin=pin
        )

        # Add to DB
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('user.user_login'))
        
    return render_template('user/user_signup.html')




@user_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')

        # Try fetching by email or username
        user = User.query.filter(
            (User.email == username_or_email) | (User.username == username_or_email)
        ).first()

        if user and check_password_hash(user.password, password):
            # Store user info in session or however you manage auth
            login_user(user)
            # flash('Logged in successfully!', 'success')
            return redirect(url_for('user.dashboard'))  # Redirect to user dashboard or homepage
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('user/user_login.html')

    return render_template('user/user_login.html')


@user_bp.route('/user_dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('user/dashboard.html')




@user_bp.route('/search', methods=['GET', 'POST'])
def search():
    return render_template('user/search.html')



@user_bp.route('/bookings', methods=['GET', 'POST'])
def bookings():
    return render_template('user/bookings.html')




@user_bp.route('/stats', methods=['GET','POST'])
def statistics():
    return render_template('user/statistics.html')



@user_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template('user/profile.html')