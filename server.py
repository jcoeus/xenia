import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from forms import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
stat_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)

DB_USER = "jc4408"
DB_PASSWORD = "y4h6k9g9"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "Problem connecting to DB"
    import traceback; traceback.print_exec()
    g.conn = None

@app.teardown_request
def teardown_request(execption):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/')
def index():
  print request.args

  cursor = g.conn.execute("SELECT stu_name FROM seas_student")
  names = []
  for result in cursor:
    names.append(result['stu_name'])
  cursor.close()

  context = dict(data = names)

  return render_template("index.html", **context)

@app.route('/events')
def events():
  cursor = g.conn.execute("SELECT ev_id, ev_name, day_start, day_end FROM event")
  events = []
  for result in cursor:
    temp = []
    temp.append(result['ev_id'])
    temp.append(result['ev_name'])
    temp.append(result['day_start'])
    temp.append(result['day_end'])
    events.append(temp)
  cursor.close()

  context = dict(data = events)
  
  return render_template("events.html", **context)

@app.route('/events/<ev_id>')
def event_page(ev_id):
  cursor = g.conn.execute("SELECT * FROM event WHERE ev_id = '"+ ev_id+"'")
  res = []
  for result in cursor:
    res = result
  cursor = g.conn.execute("SELECT grp_name FROM event e INNER JOIN hold h ON e.ev_id = h.ev_id INNER JOIN student_group sg ON h.grp_id = sg.grp_id WHERE e.ev_id='"+ev_id+"' ")
  sg = []
  for result in cursor:
    sq.append(result['grp_name'])
  cursor.close()
  context = dict([('ev_id',res['ev_id']), ('ev_name', res['ev_name']),('day_start',res['day_start']),('day_end',res['day_end']),('general_act',res['general_act']),('specific_act',res['specific_act']),('photo',res['photo']),('notes',res['notes'])])
  

  return render_template("event_page.html", **context)

@app.route('/another')
def another():
  return render_template("anotherfile.html")

@app.route('/add', methods=['POST'])
def add():
  stu_id = request.form['stu_id']
  name = request.form['name']
  year = request.form['year']
  dep_id = request.form['dep_id']
  print stu_id, name, year, dep_id
  cmd = 'INSERT INTO seas_student VALUES (:stu_id1, :name1, :year1, :dep_id1)' 
  g.conn.execute(text(cmd),stu_id1 = stu_id,name1 = name, year1 = year, dep_id1 = dep_id)
  return redirect('/')

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
  form = SignUpForm(request.form)
  if request.method == 'POST' and form.validate():
      # add method to store new user
      return redirect('/')
  return render_template('signup.html', form=form)

@app.route('/login/', methods=['GET', 'POST'])
def login():
  form = LogInForm(request.form)
  if request.method == 'POST' and form.validate():
    # add method to authenticate current user
    return redirect('/')
  return render_template('login.html', form=form)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()