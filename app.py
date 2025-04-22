from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
import config
from model import *  
from routes import *  


app = Flask(__name__, static_folder='static', static_url_path='/static')


config.configure_app(app)

db.init_app(app)

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/customer')

with app.app_context():
    # db.drop_all()
    db.create_all()
    
    

########################################################################################
@app.route('/')
def index():
    return render_template('index.html')
########################################################################################



@app.route('/login', methods=['GET', 'POST'])
def user_login():
    return render_template('user_login.html')








if __name__ == "__main__":
    app.run(debug=True, port=5000)