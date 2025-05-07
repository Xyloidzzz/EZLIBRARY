from flask import Flask, render_template, request, redirect
import pymysql.cursors
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
import scrypt
import os
import base64
import re
import html
from datetime import datetime

manager=LoginManager()
app = Flask(__name__)
manager.init_app(app)
app.config['MYSQL_DATABASE_HOST'] = "bookworms.c9e4q2aoy2op.us-east-2.rds.amazonaws.com" # Specify Endpoint
app.config['MYSQL_DATABASE_USER'] = 'admin' # Specify Master username
app.config['MYSQL_DATABASE_PASSWORD'] = 'hE079T=DaPa_' # Specify Master password
app.config['MYSQL_DATABASE_DB'] = 'bookworms-flask' # Specify database name
app.config['SECRET_KEY'] = os.urandom(64)                                                                                                                      
@manager.user_loader
def load_user(user_id):
    connection = generate_connection()
    with connection:
            with connection.cursor() as cursor:
                cursor.execute(''' select role,email,user_id from users where user_id=%s ''' , (user_id))
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

@app.route("/about")
def about():
    return render_template('/About.html')

@app.route('/login',methods=["GET", "POST"])
def login():
    return render_template('/Login.html')

@app.route('/login/auth', methods=["GET","POST"])
def auth():
    if request.method=='POST':
        email=request.form.get('email')
        psw=request.form.get('psw')
        connection = generate_connection()
        if check_email(email):
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(''' select pass_hash, role,email,user_id from users where email="%s" ''' % (email))
                    data=cursor.fetchone()
                    try:
                        print(type(data['pass_hash']))
                        scrypt.decrypt(data['pass_hash'], psw, 10)
                        cur_user=generate_user(data['email'],data['user_id'],data['role'])
                        login_user(cur_user)
                        if data['role']=='user':
                            return redirect('/account')
                        else:
                            return redirect('/directory')
                    except scrypt.error:
                        return redirect('/login?state=error')
    return render_template('/Login.html', error=True)

@app.route('/directory')
@login_required
def directory():
    return render_template('/Directory.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('/Home.html')

@app.route('/register')
def register():
    return render_template('/Register.html')

@app.route('/registration', methods=['POST'])
def registration():
    if request.method=='POST':
        email=request.form.get('email').lower()
        psw=request.form.get('psw')
        repsw=request.form.get('repsw')
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        if psw==repsw and check_email(email):
            connection=generate_connection()
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute('''select email from users where email="%s"''' , (email))
                    data=cursor.fetchone()
                    if data is None:
                        phash=scrypt.encrypt(base64.b64encode(os.urandom(32)).decode('utf-8')[:32],psw,5)
                        print(phash)
                        fname=html.escape(fname)
                        lname=html.escape(lname)
                        date=datetime.now()
                        date=date.strftime('%Y-%m-%d')
                        cursor.execute('''insert into users(email,pass_hash,first_name,last_name,role,created_at) values(%s,%s,%s,%s,"user",%s)''', (email,phash,fname,lname,date))
                        connection.commit()
                        cursor.execute('''select user_id from users where email="%s"''',(email))
                        user_id=cursor.fetchone()
                        login_user(generate_user(email,'user',user_id))
                        return render_template('/Account.html',data=(email,fname,lname))
                    else:
                        return render_template('/Register.html',error="Email already in use, please use another.")
        else:
            render_template('/Register.html',error="Error found in password or email, please try again.")
    else:
        redirect('/register')
        
@app.route('/account')
def account():
    return render_template('/Account.html');

@app.route("/search")
def search():
    return render_template('/Search.html')

@app.route("/books", methods=['GET'])
def books():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM books")
                data = cur.fetchall()
                if data is None:
                    return render_template('Books.html', error="nothing there...")
                return render_template('/Books.html', data=data)
    else:
        redirect('/directory')

@app.route("/equipment", methods=['GET'])
def equipment():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM equipment")
                data = cur.fetchall()
                if data is None:
                    return render_template('/Equipment.html', error="nothing there...")
                return render_template('/Equipment.html', data=data)
    else:
        redirect('/directory')

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
        return True

    def get_id(self):
        return self.id
        
def generate_user(email,role,user_id):
    return user(email,role,user_id)

def generate_connection():
    connection=pymysql.connect(host="bookworms.c9e4q2aoy2op.us-east-2.rds.amazonaws.com",
                             user='admin',
                             password='hE079T=DaPa_',
                             database='bookworms',
                             cursorclass=pymysql.cursors.DictCursor)
    return connection

def check_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    return re.fullmatch(regex,email)