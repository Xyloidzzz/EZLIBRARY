from flask import Flask, render_template
import pymysql.cursors
 
app = Flask(__name__)
 
app.config['MYSQL_DATABASE_HOST'] = 'bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com' # Specify Endpoint
app.config['MYSQL_DATABASE_USER'] = 'admin' # Specify Master username
app.config['MYSQL_DATABASE_PASSWORD'] = 'administrator' # Specify Master password
app.config['MYSQL_DATABASE_DB'] = 'bookworms-flask' # Specify database name
 
connection = pymysql.connect(host='bookworms-flask.c9e4q2aoy2op.us-east-2.rds.amazonaws.com',
                             user='admin',
                             password='administrator',
                             database='bookworms',
                             cursorclass=pymysql.cursors.DictCursor)

with connection:
    with connection.cursor() as cursor:
        cursor.execute(''' SELECT * FROM test ''')
        data=cursor.fetchone()
        print(data)
     
@app.route("/")
@app.route("/home")
def home():
    return render_template('/Home.html')