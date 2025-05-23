from flask import Flask, render_template, request, redirect, flash
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
                        scrypt.decrypt(data['pass_hash'], psw, 4)
                        cur_user=generate_user(data['email'],data['role'],data['user_id'], data['first_name'])
                        login_user(cur_user)
                        if data['role']=='user':
                            return redirect('/account')
                        else:
                            return redirect('/directory')
                    except scrypt.error as a:
                        flash(str(a))
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
                    cursor.execute('''select email from users where email=%s''' , (email))
                    data=cursor.fetchone()
                    if data is None:
                        phash=scrypt.encrypt(base64.b64encode(os.urandom(4)).decode('utf-8')[:4],psw,1)
                        fname=html.escape(fname)
                        lname=html.escape(lname)
                        date=datetime.now()
                        date=date.strftime('%Y-%m-%d')
                        cursor.execute('''insert into users(email,pass_hash,first_name,last_name,role,created_at) values(%s,%s,%s,%s,"user",%s)''', (email,phash,fname,lname,date))
                        connection.commit()
                        cursor.execute('''select user_id from users where email=%s''',(email))
                        user_id=cursor.fetchone()
                        cursor.close()
                        cur_user=generate_user(email,'user',user_id['user_id'],fname)
                        login_user(cur_user)
                        if current_user.role=='user':
                            return redirect('/account')
                        else:
                            return redirect('/directory')
                        return redirect('/account')
                    else:
                        cursor.close()
                        return redirect('/register')
        else:
            return redirect('/register')
    else:
        return redirect('/register')
        
@app.route('/account')
@login_required
def account():
    return render_template('/Account.html');

@app.route('/account/edit', methods=["POST"])
@login_required
def editaccount():
    if request.method=='POST':
        connection=generate_connection()
        with connection:
            with connection.cursor() as cursor:
                email=request.form.get('email').lower()
                psw=request.form.get('psw')
                fname=request.form.get('fname')
                lname=request.form.get('lname')
                vals=[]
                base_string="update users set "
                if not email and not psw and not fname and not lname:
                    cursor.close()
                    flash("No changes done")
                    return redirect('/account')
                if email:
                    if check_email(email):
                        cursor.execute('''select email from users where email=%s''' , (email))
                        data=cursor.fetchone()
                        if data is None:
                            base_string += "email=%s, "
                            vals.append(email)
                        else:
                            flash("Email is already in use please try again")
                            return redirect('/account')
                    else:
                        flash("Invalid email, please try again")
                        return redirect('/account')
                if psw:
                    base_string += "pass_hash=%s, "
                    psw = scrypt.encrypt(base64.b64encode(os.urandom(4)).decode('utf-8')[:4],psw,1)
                    vals.append(psw)
                if fname:
                    base_string += "fname=%s, "
                    vals.append(sanitize(fname))
                if lname:
                    base_string += "lname=%s, "
                    vals.append(sanitize(lname))
                base_string=base_string[:-2]+ " where user_id=%s"
                vals.append(current_user.id)
                cursor.execute(base_string,tuple(vals))
                connection.commit()
                cur_id=current_user.id
                cur_role=current_user.role
                logout_user()
                cursor.close()
                login_user(generate_user(email,cur_role,cur_id,fname))
                flash("Successfully altered account")
                return redirect('/account')
    else:
        return redirect('/account')
    

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
def addBook():
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
    
    
@app.route("/books/edit", methods=['POST'])
@login_required
def editBook():
    if request.method=='POST':
        book_id=request.form.get('book_id')
        title=request.form.get('title')
        author=request.form.get('author')
        isbn=request.form.get('ISBN')
        location=request.form.get('location')
        status=request.form.get('status')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('UPDATE books SET title = %s, author = %s, isbn = %s, location = %s, status = %s WHERE book_id = %s', (title, author, isbn, location, status, book_id))
                con.commit()
                cursor.close()
                return redirect('/books')
    else:
        cursor.close()
        return redirect('/directory') 
    
    
@app.route("/books/remove", methods=['POST'])
@login_required
def removeBook():
    if request.method=='POST':
        book_id=request.form.get('book_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM books WHERE book_id = %s', (book_id))
                con.commit()
                cursor.close()
                return redirect('/books')
    else:
        cursor.close()
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
        status=request.form.get('status')
        date=datetime.now()
        date=date.strftime('%Y-%m-%d')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('INSERT INTO fine (user_id, checkout_id, amount, status, issued) VALUES (%s, %s, %s, %s, %s)', (user_id, checkout_id, amount, status, date))
                con.commit()
                fine_id=cursor.fetchone()
                cursor.close()
                generate_fine(fine_id, user_id, checkout_id, amount)
                return redirect('/fines')
    else:
        cursor.close()
        return redirect('/directory') 

@app.route("/fines/edit", methods=['POST'])
@login_required
def editfine():
    if request.method=='POST':
        fid=request.form.get('fine_id')
        user_id=request.form.get('user_id')
        checkout_id=request.form.get('checkout_id')
        amount=request.form.get('amount')
        status=request.form.get('status')
        date=datetime.now()
        date=date.strftime('%Y-%m-%d')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('UPDATE fine SET user_id = %s, checkout_id = %s, amount = %s, status=%s, issued=%s WHERE fine_id = %s', (user_id,checkout_id,amount,sanitize(status),date,fid))
                con.commit()
                cursor.close()
                return redirect('/fines')
    else:
        cursor.close()
        return redirect('/directory') 
    
    
@app.route("/fines/remove", methods=['POST'])
@login_required
def removefine():
    if request.method=='POST':
        fid=request.form.get('fine_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM fine WHERE fine_id = %s', (fid))
                con.commit()
                cursor.close()
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

@app.route("/users/remove", methods=['POST'])
@login_required
def removeuser():
    if request.method=='POST':
        uid=request.form.get('user_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM users WHERE user_id = %s', (uid))
                con.commit()
                cursor.close()
                return redirect('/users')
    else:
        cursor.close()
        return redirect('/directory') 

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
        return redirect('/directory')

@app.route('/staff/add', methods=['POST'])
@login_required
def addstaff():
    if request.method=='POST':
        email=request.form.get('email').lower()
        psw=request.form.get('pass')
        repsw=request.form.get('rpass')
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        if psw==repsw and check_email(email):
            connection=generate_connection()
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute('''select email from users where email="%s"''' , (email))
                    data=cursor.fetchone()
                    if data is None:
                        phash=scrypt.encrypt(base64.b64encode(os.urandom(4)).decode('utf-8')[:4],psw,1)
                        fname=sanitize(fname)
                        lname=sanitize(lname)
                        date=datetime.now()
                        date=date.strftime('%Y-%m-%d')
                        cursor.execute('''insert into users(email,pass_hash,first_name,last_name,role,created_at) values(%s,%s,%s,%s,"staff",%s)''', (email,phash,fname,lname,date))
                        connection.commit()
                        cursor.close()
                        return redirect('/staff')
                    else:
                        cursor.close()
                        return redirect('/staff')
        else:
            return redirect('/staff')
    else:
        return redirect('/staff')

@app.route("/staff/remove", methods=['POST'])
@login_required
def removestaff():
    if request.method=='POST':
        uid=request.form.get('user_id')
        if uid==82 or uid=="82":
            return redirect('/staff')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM users WHERE user_id = %s', (uid))
                con.commit()
                cursor.close()
                return redirect('/staff')
    else:
        cursor.close()
        return redirect('/directory') 

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

@app.route("/equipment/edit", methods=['POST'])
@login_required
def editequip():
    if request.method=='POST':
        eid=request.form.get('equipment_id')
        name=request.form.get('Name')
        description=request.form.get('Description')
        status=request.form.get('status')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('UPDATE equipment SET equipment_name = %s, description = %s, status = %s WHERE equipment_id = %s', (sanitize(name),sanitize(description),status,eid))
                con.commit()
                cursor.close()
                return redirect('/equipment')
    else:
        cursor.close()
        return redirect('/directory') 
    
    
@app.route("/equipment/remove", methods=['POST'])
@login_required
def removeequip():
    if request.method=='POST':
        eid=request.form.get('equipment_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM equipment WHERE equipment_id = %s', (eid))
                con.commit()
                cursor.close()
                return redirect('/equipment')
    else:
        cursor.close()
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
        end=datetime.strptime(request.form.get('end_time'),"%Y-%m-%dT%H:%M")
        if start > datetime.now() and end > datetime.now() and end > start:
            con = generate_connection()
            with con:
                with con.cursor() as cur:
                    cur.execute('select * from users where user_id=%s',(user_id))
                    data=cur.fetchone()
                    if data is None:
                        msg = "User with id: %s does not exist, please try again" % (str(user_id))
                        flash(msg)
                        return redirect('/reservation')
                        
                    cur.execute('select * from rooms where room_id=%s',(room_id))
                    data=cur.fetchone()
                    if data is None:
                        msg = "Room with id: %s does not exist please try again" % (str(room_id))
                        flash(msg)
                        return redirect('/reservation')
                        
                    cur.execute('select * from reservation where room_id=%s',(room_id))
                    data=cur.fetchall()
                    for x in data:
                        xstart=x['start_time']
                        xend=x['end_time']
                        if check_time(xstart,xend,start) or check_time(xstart,xend,end):
                            msg="Reservation conflicts with another reservation, start:%s, end:%s" % (xstart,xend)
                            flash(msg)
                            return redirect('/reservation')
                    
                    cur.execute('INSERT INTO reservation (user_id, room_id, start_time, end_time) VALUES (%s, %s, %s, %s)', (user_id, room_id, start, end))
                    con.commit()
                    cur.close()
                    return redirect('/reservation')
        else:
            flash("Chosen start or end is before the present, please try again")
            return redirect('/reservation')
    return redirect('/directory') 

@app.route("/reservation/edit", methods=['POST'])
@login_required
def editres():
    if request.method=='POST':
        rid=request.form.get('reservation_id')
        user_id=request.form.get('user_id')
        room_id=request.form.get('room_id')
        start=datetime.strptime(request.form.get('start_time'),"%Y-%m-%dT%H:%M")
        end=datetime.strptime(request.form.get('end_time'),"%Y-%m-%dT%H:%M")
        con = generate_connection()
        if start > datetime.now() and end > datetime.now() and end > start:
            with con:
                with con.cursor() as cur:
                    cur.execute('select * from users where user_id=%s',(user_id))
                    data=cur.fetchone()
                    if data is None:
                        msg = "User with id: %s does not exist, please try again" % (str(user_id))
                        flash(msg)
                        return redirect('/reservation')
                        
                    cur.execute('select * from rooms where room_id=%s',(room_id))
                    data=cur.fetchone()
                    if data is None:
                        msg = "Room with id: %s does not exist please try again" % (str(room_id))
                        flash(msg)
                        return redirect('/reservation')
                        
                    cur.execute('select * from reservation where room_id=%s and reservation_id!=%s',(room_id,rid))
                    data=cur.fetchall()
                    for x in data:
                        xstart=x['start_time']
                        xend=x['end_time']
                        if check_time(xstart,xend,start) or check_time(xstart,xend,end):
                            msg="Reservation conflicts with another reservation, start:%s, end:%s" % (xstart,xend)
                            flash(msg)
                            return redirect('/reservation')
                    
                    cur.execute('UPDATE reservation SET user_id = %s, room_id = %s, start_time=%s, end_time=%s WHERE reservation_id = %s', (user_id,room_id,start,end,rid))
                con.commit()
                cur.close()
                return redirect('/reservation')
    else:
        cursor.close()
        return redirect('/directory') 
    
    
@app.route("/reservation/remove", methods=['POST'])
@login_required
def removeres():
    if request.method=='POST':
        rid=request.form.get('reservation_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM reservation WHERE reservation_id = %s', (rid))
                con.commit()
                cursor.close()
                return redirect('/reservation')
    else:
        cursor.close()
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
        
@app.route("/layout/edit", methods=['POST'])
@login_required
def editlay():
    if request.method=='POST':
        rid=request.form.get('room_id')
        name=request.form.get('Name')
        cap=request.form.get('Capacity')
        loc=request.form.get('location')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('UPDATE rooms SET room_name = %s, capacity = %s, location = %s WHERE room_id = %s', (sanitize(name),cap,sanitize(loc),rid))
                con.commit()
                cursor.close()
                return redirect('/layout')
    else:
        cursor.close()
        return redirect('/directory') 
    
    
@app.route("/layout/remove", methods=['POST'])
@login_required
def removelay():
    if request.method=='POST':
        room_id=request.form.get('room_id')
        con = generate_connection()
        with con:
            with con.cursor() as cursor:
                cursor.execute('DELETE FROM rooms WHERE room_id = %s', (room_id))
                con.commit()
                cursor.close()
                return redirect('/layout')
    else:
        cursor.close()
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
    
def check_time(xstart,xend,value):
    return value > xstart and value < xend

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000)

