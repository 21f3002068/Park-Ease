from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash


admin_bp= Blueprint('admin', __name__)

admin_username = "admin"
admin_password = "admin"

admin_password = generate_password_hash("admin")

def check_admin_credentials(username, password):
    return username == admin_username and check_password_hash(admin_password, password)

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if check_admin_credentials(username, password):
            session['admin_logged_in'] = True
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin/admin_login.html')


@admin_bp.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    return render_template('admin/dashboard.html')


@admin_bp.route('/users', methods=['GET', 'POST'])
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)



@admin_bp.route('/search', methods=['GET', 'POST'])
def admin_search():
    return render_template('admin/search.html')


@admin_bp.route('/activity_log', methods=['GET', 'POST'])
def activity_log():
    return render_template('admin/activity_log.html')



@admin_bp.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template('admin/statistics.html')




@admin_bp.route('/admin/flag_user_confirmation/', methods=['GET', 'POST'])
def flag_user_confirmation():
    return render_template('partials/_flag_user_confirmation.html')




