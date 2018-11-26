import os, random, string
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

def key_par(s):
  return s.split('#')[1:]

def rem_vow(s):
  vowels = ('a','e','i','o','u','A','E','I','O','U',' ')
  return ''.join([l for l in s if l not in vowels])

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "Problem connecting to DB"
    import traceback; traceback.print_exc()
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

@app.route('/student_groups')
def student_groups():
  cursor = g.conn.execute("SELECT grp_id, grp_name FROM student_group")
  student_groups = []
  for result in cursor:
    temp = []
    temp.append(result['grp_id'])
    temp.append(result['grp_name'])
    student_groups.append(temp)
  cursor.close()

  context = dict(data = student_groups)
  
  return render_template("student_groups.html", **context)

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

@app.route('/events/new')
def new_ev():
  ev_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
  cursor = g.conn.execute("SELECT ev_id FROM event WHERE ev_id ='"+ev_id+"'")
  while(cursor.fetchone()):
    ev_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    cursor = g.conn.execute("SELECT ev_id FROM event WHERE ev_id ='"+ev_id+"'")

  # need to "reserve" the unique ID for the time being, might just add blank values
  
  cursor = g.conn.execute("SELECT grp_id, grp_name FROM student_group")
  stu_grp = {}
  for result in cursor:
    stu_grp[result['grp_id']] = {'grp_name':result['grp_name']}
  
  cursor = g.conn.execute("SELECT sch_id, sch_name FROM partner_school")
  par_sch = {}
  for result in cursor:
    par_sch[result['sch_id']] = {'sch_name':result['sch_name']}

  cursor = g.conn.execute("SELECT fac_id, fac_name FROM faculty")
  fac_att = {}
  for result in cursor:
    fac_att[result['fac_id']] = {'fac_name':result['fac_name']}

  cursor = g.conn.execute("SELECT * FROM partner_school")
  pat_ins = {}
  for result in cursor:
    pat_ins[result['sch_id']] = {'sch_name':result['sch_name']}

  cursor = g.conn.execute("SELECT * FROM keyword")
  top_key = {}
  for result in cursor:
    top_key[result['top_id']] = {'top_name':result['top_name']}
 
  context = dict([('top_key',top_key),('pat_ins',pat_ins),('fac_att',fac_att),('ev_id', ev_id),('stu_grp',stu_grp),('par_sch',par_sch)])

  return render_template("event_form.html", **context)

@app.route('/events/~<ev_id>')
def event_page(ev_id):
  cursor = g.conn.execute("SELECT * FROM event WHERE ev_id = '"+ ev_id+"'")
  res = cursor.fetchone()

  #get student group names involved
  cursor = g.conn.execute("SELECT grp_name FROM event e INNER JOIN hold h ON e.ev_id = h.ev_id INNER JOIN student_group sg ON h.grp_id = sg.grp_id WHERE e.ev_id='"+ev_id+"' ")
  sg = []
  for result in cursor:
    sg.append(result['grp_name'])

  #get partner school names involved
  cursor = g.conn.execute("SELECT sch_name FROM event e INNER JOIN partner p ON e.ev_id = p.ev_id INNER JOIN partner_school ps ON p.sch_id = ps.sch_id WHERE e.ev_id='"+ev_id+"' ")
  ps = []
  for result in cursor:
    ps.append(result['sch_name'])

  #get keywords/topics about event
  cursor = g.conn.execute("SELECT top_name FROM event e INNER JOIN cover c ON e.ev_id = c.ev_id INNER JOIN keyword k ON c.top_id = k.top_id WHERE e.ev_id='"+ev_id+"' ")
  kt = []
  for result in cursor:
    kt.append(result['top_name'])

  #get faculty involved
  cursor = g.conn.execute("SELECT fac_name FROM event e INNER JOIN attend a ON e.ev_id = a.ev_id INNER JOIN faculty f ON a.fac_id = f.fac_id WHERE e.ev_id='"+ev_id+"' ")
  ft = []
  for result in cursor:
    ft.append(result['fac_name'])

  #get admin involved


  cursor.close()
  context = dict([('fac_name',ft),('key_name',kt),('sch_name',ps),('ev_type',res['ev_type'],),('time_per_session',res['time_per_session'],),('total_time',res['total_time']),('general_act', res['general_act']),('term',res['term']),('ev_id',res['ev_id']), ('ev_name', res['ev_name']),('ev_des', res['ev_des']),('day_start',res['day_start']),('day_end',res['day_end']),('specific_act',res['specific_act']),('photo',res['photo']),('notes',res['notes']), ('group_names', sg)])
  
  return render_template("event_page.html", **context)

@app.route('/events/~<ev_id>/add', methods=['POST'])
def add_event(ev_id):
  print 'Im warking hereee'

  day_start = request.form['day_start']
  day_end = request.form['day_end']
  general_act = request.form['general_act']
  specific_act = request.form['specific_act']
  photo = request.form['photo']
  total_time = request.form['total_time']
  time_per_session = request.form['time_per_session']
  notes = request.form['notes']
  term = request.form['term']
  ev_name = request.form['ev_name']
  ev_type = request.form['ev_type']
  ev_des = request.form['ev_des']
  
  grp_id = request.form.getlist('grp_id')
  print grp_id
  top_id = request.form['top_id']
  top_id = key_par(top_id)
  print top_id
  fac_id = request.form.getlist('fac_id')
  print fac_id
  sch_id = request.form.getlist('sch_id')
  print sch_id

  print 'you made it pass the get form value requests'

  cursor = g.conn.execute("SELECT * FROM keyword")
  top_dict = {}
  for result in cursor:
    top_dict[result['top_id']] = result['top_name']

  key_dict = {}
  for t in top_id:
    key_dict[rem_vow(t).upper()[:10]] = t

  for n in key_dict:
    if n not in top_dict:
      cmd = 'INSERT INTO keyword VALUES(:top_id1, :top_name1)'
      g.conn.execute(text(cmd), top_id1 = n, top_name1=key_dict[n])
    else: 
      if key_dict[n] not in top_dict[n]:
        top_dict[n] = top_dict[n] + ', ' + key_dict[n]


  g.conn.execute("DELETE FROM hold WHERE ev_id = '"+ev_id+"'")
  g.conn.execute("DELETE FROM cover WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM partner WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM attend WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM event WHERE ev_id ='"+ev_id+"'")

  insert_event = 'INSERT INTO event VALUES (:ev_id1, :day_start1, :day_end1, :general_act1, :specific_act1, :photo1, :total_time1, :time_per_session1, :notes1, :term1, :ev_name1, :ev_type1, :ev_des1)' 
  insert_cover = 'INSERT INTO cover VALUES (:ev_id1,:top_id1)'
  insert_attend = 'INSERT INTO attend VALUES (:ev_id1,:fac_id1)'
  insert_partner = 'INSERT INTO partner VALUES (:ev_id1,:sch_id1)'
  insert_hold = 'INSERT INTO hold VALUES (:grp_id1, :ev_id1)'

  g.conn.execute(text(insert_event),ev_id1 = ev_id, day_start1 = day_start, day_end1 = day_end, general_act1 = general_act, specific_act1 = specific_act, photo1 = photo, total_time1 = total_time, time_per_session1 = time_per_session, notes1 = notes, term1 = term, ev_name1 =ev_name, ev_type1 = ev_type, ev_des1 = ev_des)
  for n in grp_id:
    g.conn.execute(text(insert_hold),ev_id1 = ev_id, grp_id1 = n)
  for n in key_dict:
    g.conn.execute(text(insert_cover),ev_id1 = ev_id, top_id1 = n)
  for n in fac_id:
    g.conn.execute(text(insert_attend),ev_id1 = ev_id, fac_id1 = n)
  for n in sch_id:
    g.conn.execute(text(insert_partner),ev_id1 = ev_id, sch_id1 = n)
  
  return redirect('/events/~'+ev_id)

@app.route('/events/~<ev_id>/edit_ev')
def edit_ev(ev_id):
  #get event info
  cursor = g.conn.execute("SELECT * FROM event WHERE ev_id = '"+ ev_id+"'")
  res = cursor.fetchone()

  #get list of student group names involved
  cursor = g.conn.execute("SELECT grp_name FROM event e INNER JOIN hold h ON e.ev_id = h.ev_id INNER JOIN student_group sg ON h.grp_id = sg.grp_id WHERE e.ev_id='"+ev_id+"' ")
  sg = []
  for result in cursor:
    sg.append(result['grp_name'])

  #get list of partner school names involved
  cursor = g.conn.execute("SELECT sch_name FROM event e INNER JOIN partner p ON e.ev_id = p.ev_id INNER JOIN partner_school ps ON p.sch_id = ps.sch_id WHERE e.ev_id='"+ev_id+"' ")
  ps = []
  for result in cursor:
    ps.append(result['sch_name'])

  #get keywords/topics about event
  cursor = g.conn.execute("SELECT top_name FROM event e INNER JOIN cover c ON e.ev_id = c.ev_id INNER JOIN keyword k ON c.top_id = k.top_id WHERE e.ev_id='"+ev_id+"' ")
  kt = []
  for result in cursor:
    kt.append(result['top_name'])

  #get list of faculty involved
  cursor = g.conn.execute("SELECT fac_name FROM event e INNER JOIN attend a ON e.ev_id = a.ev_id INNER JOIN faculty f ON a.fac_id = f.fac_id WHERE e.ev_id='"+ev_id+"' ")
  ft = []
  for result in cursor:
    ft.append(result['fac_name'])

  #get admin involved

  #get list of possibe student groups
  cursor = g.conn.execute("SELECT grp_id, grp_name FROM student_group")
  stu_grp = {}
  for result in cursor:
    stu_grp[result['grp_id']] = {'grp_name':result['grp_name']}
  
  #get list of possible partner institutions
  cursor = g.conn.execute("SELECT sch_id, sch_name FROM partner_school")
  par_sch = {}
  for result in cursor:
    par_sch[result['sch_id']] = {'sch_name':result['sch_name']}

  #get list of possible faculty involved
  cursor = g.conn.execute("SELECT fac_id, fac_name FROM faculty")
  fac_att = {}
  for result in cursor:
    fac_att[result['fac_id']] = {'fac_name':result['fac_name']}

  #get list of possible p
  cursor = g.conn.execute("SELECT * FROM partner_school")
  pat_ins = {}
  for result in cursor:
    pat_ins[result['sch_id']] = {'sch_name':result['sch_name']}

  cursor = g.conn.execute("SELECT * FROM keyword")
  top_key = {}
  for result in cursor:
    top_key[result['top_id']] = {'top_name':result['top_name']}

  cursor.close()
  context_prev = dict([('fac_name',ft),('key_name',kt),('sch_name',ps),('ev_type',res['ev_type'],),('time_per_session',res['time_per_session'],),('total_time',res['total_time']),('general_act', res['general_act']),('term',res['term']), ('ev_name', res['ev_name']),('day_start',res['day_start']),('day_end',res['day_end']),('specific_act',res['specific_act']),('photo',res['photo']),('notes',res['notes']), ('ev_des',res['ev_des']),('group_names', sg)])
  context_poss = dict([('top_key',top_key),('pat_ins',pat_ins),('fac_att',fac_att),('ev_id', ev_id),('stu_grp',stu_grp),('par_sch',par_sch)])

  context = context_prev.copy()
  context.update(context_poss)


  return render_template("event_form.html", **context)


@app.route('/events/~<ev_id>/delete_ev')
def delete_ev(ev_id):
  g.conn.execute("DELETE FROM hold WHERE ev_id = '"+ev_id+"'")
  g.conn.execute("DELETE FROM cover WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM partner WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM attend WHERE ev_id ='"+ev_id+"'")
  g.conn.execute("DELETE FROM event WHERE ev_id ='"+ev_id+"'")
  return redirect('/events')

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
'''
@app.errorhandler(404)
def page_not_found(e):
  return render_template('404.html'), 404
'''

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