from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import config
from model import *  
from routes import *  
import os


app = Flask(__name__, static_folder='static', static_url_path='/static')

config.configure_app(app)

try:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vehicles'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'parking_lots'), exist_ok=True)
except Exception as e:
    print(f"Error creating upload directories: {e}")
    
    
db.init_app(app)

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')

with app.app_context():
    # db.drop_all()
    db.create_all()
    
    

########################################################################################
@app.route('/')
def index():
    return render_template('index.html')
########################################################################################




login_manager = LoginManager(app)
login_manager.login_view = 'user.user_login'

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    return user

@app.route('/logout')
@login_required  
def logout():
    logout_user()  
    return redirect(url_for('user.user_login'))



if __name__ == "__main__":
    app.run(debug=True, port=5000)