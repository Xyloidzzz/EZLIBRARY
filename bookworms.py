from flask import Flask, render_template, request, redirect
import pymysql.cursors
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
import scrypt
import os
import base64
import re
import html
from datetime import datetime
import bleach

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
                cursor.execute(''' select role,email,user_id,first_name from users where user_id=%s ''' , (user_id))
                data=cursor.fetchone()
                cursor.close()
                if data is None:
                    return None
                else:
                    return generate_user(data['email'],data['role'],data['user_id'], data['first_name'])
    return None

@app.route("/")
@app.route("/home")
def home():
    if type(current_user.is_authenticated)==bool:
        if current_user.is_authenticated:
            return redirect('/logout')
    else:
        if current_user.is_authenticated():
            return redirect('/logout')
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
                    cursor.execute(''' select pass_hash, role,email,user_id,first_name from users where email="%s" ''' % (email))
                    data=cursor.fetchone()
                    cursor.close()
                    try:
                        scrypt.decrypt(data['pass_hash'], psw, 10)
                        cur_user=generate_user(data['email'],data['role'],data['user_id'], data['first_name'])
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
    return redirect('/home')

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
                        fname=html.escape(fname)
                        lname=html.escape(lname)
                        date=datetime.now()
                        date=date.strftime('%Y-%m-%d')
                        cursor.execute('''insert into users(email,pass_hash,first_name,last_name,role,created_at) values(%s,%s,%s,%s,"user",%s)''', (email,phash,fname,lname,date))
                        connection.commit()
                        cursor.execute('''select user_id from users where email="%s"''',(email))
                        user_id=cursor.fetchone()
                        cursor.close()
                        login_user(generate_user(email,'user',user_id))
                        return render_template('/Account.html',data=(email,fname,lname))
                    else:
                        cursor.close()
                        return render_template('/Register.html',error="Email already in use, please use another.")
        else:
            render_template('/Register.html',error="Error found in password or email, please try again.")
    else:
        redirect('/register')
        
@app.route('/account')
@login_required
def account():
    return render_template('/Account.html');

@app.route("/search")
def search():
    return render_template('/Search.html')

@app.route("/books", methods=['GET'])
@login_required
def books():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM books")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('Books.html', error="nothing there...")
                return render_template('/Books.html', data=data, user=current_user)
    else:
        redirect('/directory')
        
@app.route("/books/add", methods=['POST'])
def addbook():
    if request.method=='POST':
        title=request.form.get('title')
        author=request.form.get('author')
        isbn=request.form.get('ISBN')
        location=request.form.get('location')
        status=request.form.get('status')
        added=datetime.now()
        added=added.strftime('%Y-%m-%d')
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute('INSERT INTO books (title, author, isbn, location, status, added) VALUES (%s, %s, %s, %s, %s, %s)', (title, author, isbn, location, status, added))
                con.commit()
                book_id=cur.fetchone()
                cur.close()
                generate_book(book_id, title, author, isbn, location, status, added)
                return redirect('/books')
    else:
        cur.close()
        return redirect('/directory') 


@app.route("/checkout", methods=['GET'])
@login_required
def checkout():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                if (current_user.role=='user'):
                    cur.execute(f"SELECT * FROM checkout WHERE user_id = {current_user.id}")
                    data = cur.fetchall()
                    cur.close()
                else:
                    cur.execute(f"SELECT * FROM checkout")
                    data = cur.fetchall()
                    cur.close()
                if data is None:
                    return render_template('Checkout.html', error="nothing there...")
                return render_template('/Checkout.html', data=data, user=current_user, error=False)
    else:
        redirect('/directory')

@app.route("/checkout/add", methods=['POST'])
@login_required
def checkoutBook():
    if request.method=='POST':
        book_id=request.form.get('book_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute(f'SELECT status FROM books WHERE book_id = {book_id}')
                if (cursor.fetchone()['status'] == 'available'):
                    cursor.execute(f'UPDATE books SET status = "checked out" WHERE book_id = {book_id}')
                    con.commit()
                    cursor.execute('INSERT INTO checkout (user_id, book_id) VALUES (%s, %s)', (current_user.id, book_id))
                    con.commit()
                    cursor.close()
                    return redirect('/checkout')
                else:
                    return redirect('/checkout')
    else:
        cursor.close()
        return redirect('/directory') 

@app.route("/fines", methods=['GET'])
@login_required
def fines():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM fine")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('Fines.html', error="nothing there...")
                return render_template('/Fines.html', data=data, user=current_user)
    else:
        redirect('/directory')

@app.route("/fines/add", methods=['POST'])
@login_required
def addfine():
    if request.method=='POST':
        user_id=request.form.get('user_id')
        checkout_id=request.form.get('checkout_id')
        amount=request.form.get('amount')
        date=datetime.now()
        date=date.strftime('%Y-%m-%d')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('INSERT INTO fine (user_id, checkout_id, amount, status, issued) VALUES (%s, %s, %s, "unpaid", %s)', (user_id, checkout_id, amount, date))
                con.commit()
                fine_id=cursor.fetchone()
                cursor.close()
                generate_fine(fine_id, user_id, checkout_id, amount)
                return redirect('/fines')
    else:
        cursor.close()
        return redirect('/directory') 

@app.route("/users", methods=['GET'])
@login_required
def users():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE role = 'user'")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('Users.html', error="nothing there...")
                return render_template('/Users.html', data=data, user=current_user)
    else:
        redirect('/directory')

@app.route("/staff", methods=['GET'])
@login_required
def staff():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE role = 'staff'")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('Staff.html', error="nothing there...")
                return render_template('/Staff.html', data=data, user=current_user)
    else:
        redirect('/directory')

@app.route("/equipment", methods=['GET'])
@login_required
def equipment():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM equipment")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('/Equipment.html', error="nothing there...")
                return render_template('/Equipment.html', data=data, user=current_user)
    else:
        redirect('/directory')

@app.route("/equipment/add", methods=['POST'])
@login_required
def addequip():
    if request.method=='POST':
        name=request.form.get('Name')
        desc=request.form.get('Description')
        status=request.form.get('status')
        added=datetime.now()
        added=added.strftime('%Y-%m-%d')
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute('INSERT INTO equipment (equipment_name, description, status, added) VALUES (%s, %s, %s, %s)', (sanitize(name), sanitize(desc), status, added))
                con.commit()
                book_id=cur.fetchone()
                cur.close()
                return redirect('/equipment')
    else:
        cur.close()
        return redirect('/directory') 
        
@app.route("/reservation", methods=['GET'])
@login_required
def reservation():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM reservation")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('/Reservation.html', error="nothing there...")
                return render_template('/Reservation.html', data=data)
    else:
        redirect('/directory')

@app.route("/reservation/add", methods=['POST'])
@login_required
def addres():
    if request.method=='POST':
        user_id=request.form.get('user_id')
        room_id=request.form.get('room_id')
        start=datetime.strptime(request.form.get('start_time'),"%Y-%m-%dT%H:%M")
        print(start)
        end=datetime.strptime(request.form.get('end_time'),"%Y-%m-%dT%H:%M")
        if start > datetime.now() and end > datetime.now() and end > start:
            con = generate_connection()
            with con:
                with con.cursor() as cur:
                    cur.execute('INSERT INTO reservation (user_id, room_id, start_time, end_time) VALUES (%s, %s, %s, %s)', (user_id, room_id, start, end))
                    con.commit()
                    book_id=cur.fetchone()
                    cur.close()
                    return redirect('/reservation')
        else:
            redirect('/reservation', error='Impossible request')
    else:
        cur.close()
        return redirect('/directory') 

@app.route("/layout", methods=['GET'])
@login_required
def layout():
    if request.method == 'GET':
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute("SELECT * FROM rooms")
                data = cur.fetchall()
                cur.close()
                if data is None:
                    return render_template('/Layout.html', error="nothing there...")
                return render_template('/Layout.html', data=data)
    else:
        redirect('/directory')

@app.route("/layout/add", methods=['POST'])
@login_required
def addlay():
    if request.method=='POST':
        name=request.form.get('Name')
        cap=request.form.get('Capacity')
        loc=request.form.get('location')
        con = generate_connection()
        with con:
            with con.cursor() as cur:
                cur.execute('INSERT INTO rooms (room_name, capacity, location) VALUES (%s, %s, %s)', (sanitize(name), cap, sanitize(loc)))
                con.commit()
                cur.close()
                return redirect('/layout')
    else:
        cur.close()
        return redirect('/directory') 

class user():
    def __init__(self,email,role,user_id,name):
        self.email=email
        self.id=str(user_id)
        self.role=role
        self.name=name

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    def get_role(self):
        return self.role
        
def generate_user(email,role,user_id,name):
    return user(email,role,user_id,name)


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

class fine():
    def __init__(self, fine_id, user_id, checkout_id, amount):
        self.fine_id=fine_id
        self.user_id=str(user_id)
        self.checkout_id=checkout_id
        self.amount=amount
        self.status='unpaid'
        self.issued_at=datetime.now()

class book():
    def __init__(self, book_id, title, author, isbn, location, status, added):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.location = location
        self.status = status
        self.added =added

def generate_fine(fine_id, user_id, checkout_id, amount):
    return fine(fine_id, user_id, checkout_id, amount)

def generate_book(book_id, title, author, isbn, location, status, added):
    return book(book_id, title, author, isbn, location, status, added)

def sanitize(text):
    return bleach.clean(text)