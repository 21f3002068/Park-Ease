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
        return redirect(url_for('user_login'))
        
    return render_template('user/user_signup.html')