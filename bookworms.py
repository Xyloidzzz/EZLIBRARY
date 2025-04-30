from flask import Flask, render_template, request, redirect
import pymysql.cursors
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
import scrypt
import os
import base64

manager=LoginManager()
app = Flask(__name__)
manager.init_app(app)
app.config['MYSQL_DATABASE_HOST'] = 'bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com' # Specify Endpoint
app.config['MYSQL_DATABASE_USER'] = 'admin' # Specify Master username
app.config['MYSQL_DATABASE_PASSWORD'] = 'administrator' # Specify Master password
app.config['MYSQL_DATABASE_DB'] = 'bookworms-flask' # Specify database name
app.config['SECRET_KEY'] = os.urandom(64)
 
connection = pymysql.connect(host='bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com',
                             user='admin',
                             password='administrator',
                             database='bookworms',
                             cursorclass=pymysql.cursors.DictCursor)
phash=scrypt.encrypt(base64.b64encode(os.urandom(32)).decode('utf-8')[:32],'admin',5)

@manager.user_loader
def load_user(user_id):
    connection = pymysql.connect(host='bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com',
                             user='admin',
                             password='administrator',
                             database='bookworms',
                             cursorclass=pymysql.cursors.DictCursor)
    with connection:
            with connection.cursor() as cursor:
                cursor.execute(''' select role,email,user_id from users where user_id=%s ''' % (user_id))
                data=cursor.fetchone()
                if data is None:
                    return None
                else:
                    return generate_user(data['email'],data['role'],data['user_id'])
    return None

@app.route("/")
@app.route("/home")
def home():
    return render_template('/Home.html')

@app.route('/login',methods=["GET", "POST"])
def login():
    return render_template('/Login.html')

@app.route('/login/auth', methods=["GET","POST"])
def auth():
    if request.method=='POST':
        email=request.form.get('email')
        psw=request.form.get('psw')
        connection = pymysql.connect(host='bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com',
                             user='admin',
                             password='administrator',
                             database='bookworms',
                             cursorclass=pymysql.cursors.DictCursor)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(''' select pass_hash, role,email,user_id from users where email="%s" ''' % (email))
                data=cursor.fetchone()
                try:
                    scrypt.decrypt(data['pass_hash'][1:-1], psw, 10)
                    cur_user=generate_user(data['email'],data['user_id'],data['role'])
                    login_user(cur_user)
                    if data['role']=='user':
                        return redirect('/account')
                    else:
                        return redirect('/directory')
                except scrypt.error:
                    return redirect('/login?state=error')
    return render_template('/Login.html')

@app.route('/directory')
@login_required
def directory():
    return render_template('/Directory.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('/Home.html')

class user():
    def __init__(self,email,user_id,role):
        self.email=email
        self.id=str(user_id)
        self.role=role

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        if self.role=='user':
            return False
        else:
            return True

    def get_id(self):
        return self.id
        
def generate_user(email,role,user_id):
    return user(email,role,user_id)