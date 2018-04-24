from flask import Flask, request, redirect, render_template, abort, Response
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from passlib.hash import pbkdf2_sha256
import sqlite3
import paho.mqtt.client as mqtt
import redis
import os
r = redis.Redis('localhost',db=0)
host = "0.0.0.0"
database="SimpleWeb.db"

client = mqtt.Client()
#client.tls_set("ca.pem")
client.tls_set("ca.pem","web_server2.pem","web_server2.key")
client.connect_async('iot.pue.es', 8883)

r = redis.Redis('localhost',db=0)


in_topic = '/lego/in/'





app = Flask(__name__)

app.config.update(
    SECRET_KEY = 'secret_xxx'
)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
def get_data(r):
	data=dict()
	for i in ('temp','hum','door','doorbell','led','ldr'):
		if(r.exists(i)==False):
			data[i]=0
			r.set(i, str(data[i]).encode('utf-8'))
		else:
			try:
				data[i]=float(r.get(i).decode('utf-8'))
			except:
				data[i]=-1

	return data

def update_data(r,data,client):
	for d in ( 'door', 'led'):
		if str(data[d]) != r.get(d).decode('utf-8') :
			client.reconnect()
			client.publish(in_topic+str(d),data[d],0)
			r.set(d, str(data[d]).encode('utf-8'))

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.name = username

def verify_user(user,password):
    global database
    db = sqlite3.connect(database)
    c = db.cursor()
    c.execute("select id, password from users where name = ? ",(user,))
    result = c.fetchall()
    db.close()
    if len(result) == 1:
        [(id, hash_password)] = result
        if pbkdf2_sha256.verify(password,hash_password):
            return User(id,user)
        else:
            return None
    else:
        return None

@app.route("/",  methods=['POST','GET'])
@login_required
def root():
	data = get_data(r)
	if request.method == 'POST':
		if 'door' in request.form:
			data['door']=int(request.form['door'])
		else:
			data['door']=0
		if 'led' in request.form:
			data['led']=int(request.form['led'])
		else:
			data['led']=0
		try:
			update_data(r,data,client)
		except:
			pass
	data['now'] = os.path.getmtime('static/photo.jpg')
	return render_template('index.html',**data)


@app.route("/login", methods=["GET", "POST"])
def login():
    global user_admin
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_info = verify_user(username,password)
        if user_info != None:
            login_user(user_info)
            return redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
         return render_template('login.html')

# somewhere to logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/", code=302)





# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return redirect("/", code=302)

# callback to reload the user object
@login_manager.user_loader
def load_user(userid):
    global database
    db = sqlite3.connect(database)
    c = db.cursor()
    c.execute("select id, name from users where id = ? ",(userid,))
    result = c.fetchall()
    db.close()
    [(id, name)] = result
    return User(id,name)


if __name__ == "__main__":
    app.run(host=host, debug=True)

