from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from model import *
import logging
from functools import wraps
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash


admin_bp= Blueprint('admin', __name__)

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin/admin_login.html')

