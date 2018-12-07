import os, random, string, datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session
from flask_hashing import Hashing
from forms import *

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
stat_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, template_folder=tmpl_dir, static_folder=stat_dir)
app.secret_key = b'\xef\x9d\x89Q\xa3\x0b4nAY\x13\xccg\x83&\xfc'
hashing = Hashing(app)

DB_USER = "jc4408"
DB_PASSWORD = "y4h6k9g9"
DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"

engine = create_engine(DATABASEURI)

my_salt = 'jcnyw4111'

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

@app.route('/', methods=['GET', 'POST'])
def index():
  if session:
    form = SearchForm(request.form)
    context = dict(loggedIn=session)
    context['form'] = form
    if request.method == 'POST':
        return search_results(form)
    return render_template("index.html", **context)
  else:
    return redirect('/login/')

@app.route('/search/')
def search_results(searchForm):
  # form = SearchForm(request.form)
  results = {}
  search_text = searchForm.searchText.data
  cmd = ''
  if searchForm.searchText.data == '':
      cmd = "SELECT * FROM event"
  cmd = "SELECT DISTINCT e.ev_id, e.ev_name, e.day_start, e.day_end FROM event e INNER JOIN cover c ON (e.ev_id=c.ev_id) INNER JOIN keyword k ON (c.top_id=k.top_id) WHERE LOWER(k.top_name) LIKE LOWER(\'%" + search_text + "%\')"
  cursor = g.conn.execute(text(cmd))
  for res in cursor:
    results[res['ev_id']] = {'ev_name':res['ev_name'], 'day_start':res['day_start'], 'day_end':res['day_end']}
  # if not results:
  #     # flash('No results found!')
  #     return redirect('/')
  context = dict(results=results, search_text=search_text, form=searchForm)
  return render_template('search_results.html', **context)


@app.route('/student_groups')
def student_groups():
  if session:
    cursor = g.conn.execute("SELECT grp_id, grp_name, email FROM student_group")
    student_groups = []
    for result in cursor:
      temp = []
      temp.append(result['grp_id'])
      temp.append(result['grp_name'])
      temp.append(result['email'])
      student_groups.append(temp)
    cursor.close()

    context = dict(data = student_groups, loggedIn=session)
    
    return render_template("student_groups.html", **context)
  else:
    return redirect('/login')

@app.route('/events')
def events():
  if session:
    cursor = g.conn.execute("SELECT ev_id, ev_name, day_start, day_end FROM event ORDER BY day_start DESC")
    events = []
    for result in cursor:
      temp = []
      temp.append(result['ev_id'])
      temp.append(result['ev_name'])
      temp.append(result['day_start'])
      temp.append(result['day_end'])
      events.append(temp)
    cursor.close()

    context = dict(data = events, loggedIn=session)
    
    return render_template("events.html", **context)
  else:
    return redirect('/login/')

@app.route('/events/new')
def new_ev():
  if session:
    today = datetime.datetime.now()
    today = today.strftime("%Y-%m-%d")
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
    
    cursor = g.conn.execute("SELECT * FROM admin")
    admin = {}
    for result in cursor:
      admin[result['adm_id']] = result['adm_name']
  
    context = dict([('today',today),('admin', admin),('top_key',top_key),('pat_ins',pat_ins),('fac_att',fac_att),('ev_id', ev_id),('stu_grp',stu_grp),('par_sch',par_sch)])
    context['loggedIn'] = session

    return render_template("event_form.html", **context)
  else:
    return redirect('/login/')

@app.route('/events/~<ev_id>')
def event_page(ev_id):
  if session:
    cmd = "SELECT * FROM event WHERE ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    res = cursor.fetchone()

    #get student group names involved
    cmd = "SELECT grp_name FROM event e INNER JOIN hold h ON e.ev_id = h.ev_id INNER JOIN student_group sg ON h.grp_id = sg.grp_id WHERE e.ev_id = :ev_id1 "
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    sg = []
    for result in cursor:
      sg.append(result['grp_name'])

    #get partner school names involved
    cmd = "SELECT ps.sch_id, sch_name FROM event e INNER JOIN partner p ON e.ev_id = p.ev_id INNER JOIN partner_school ps ON p.sch_id = ps.sch_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ps = {}
    for result in cursor:
      ps[result['sch_id']] = result['sch_name']

    #get keywords/topics about event
    cmd = "SELECT c.top_id, top_name FROM event e INNER JOIN cover c ON e.ev_id = c.ev_id INNER JOIN keyword k ON c.top_id = k.top_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    kt = {}
    for result in cursor:
      kt[result['top_id']] = result['top_name']
      
    #get faculty involved
    cmd = "SELECT a.fac_id, fac_name FROM event e INNER JOIN attend a ON e.ev_id = a.ev_id INNER JOIN faculty f ON a.fac_id = f.fac_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ft = {}
    for result in cursor:
      ft[result['fac_id']] = result['fac_name']

    #get admin involved
    cmd = "SELECT a.adm_id, adm_name FROM event e INNER JOIN administrate a ON e.ev_id = a.ev_id INNER JOIN admin ad ON ad.adm_id = a.adm_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ad = {}
    for result in cursor:
      ad[result['adm_id']] = result['adm_name']

    #get participant groups
    cmd = "SELECT p.par_id, p.par_name, number, type FROM event e INNER JOIN participate par ON e.ev_id = par.ev_id INNER JOIN participant p ON  par.par_id = p.par_id WHERE e.ev_id =:ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    par = {}
    for result in cursor:
      par[result['par_id']] = {'par_name':result['par_name'],'number':result['number'],'type':result['type']}

    cursor.close()

    context = dict([('participants',par),('admin', ad),('faculty',ft),('key_name',kt),('partners',ps),('ev_type',res['ev_type'],),('time_per_session',res['time_per_session'],),('total_time',res['total_time']),('general_act', res['general_act']),('term',res['term']),('ev_id',res['ev_id']), ('ev_name', res['ev_name']),('ev_des', res['ev_des']),('day_start',res['day_start']),('day_end',res['day_end']),('specific_act',res['specific_act']),('photo',res['photo']),('notes',res['notes']), ('group_names', sg)])
    context['loggedIn'] = session

    return render_template("event_page.html", **context)
  else:
    return redirect('/login/')

@app.route('/events/~<ev_id>/add', methods=['POST'])
def add_event(ev_id):
  if session:
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
    
    admin = request.form.getlist('admin')
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

    cmd = "DELETE FROM administrate WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM participate WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM volunteer WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM hold WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM cover WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM partner WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM attend WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM event WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)

    insert_event = 'INSERT INTO event VALUES (:ev_id1, :day_start1, :day_end1, :general_act1, :specific_act1, :photo1, :total_time1, :time_per_session1, :notes1, :term1, :ev_name1, :ev_type1, :ev_des1)' 
    insert_cover = 'INSERT INTO cover VALUES (:ev_id1,:top_id1)'
    insert_attend = 'INSERT INTO attend VALUES (:ev_id1,:fac_id1)'
    insert_partner = 'INSERT INTO partner VALUES (:ev_id1,:sch_id1)'
    insert_hold = 'INSERT INTO hold VALUES (:grp_id1, :ev_id1)'
    insert_admin = 'INSERT INTO administrate VALUES (:adm_id1, :ev_id1)'

    g.conn.execute(text(insert_event),ev_id1 = ev_id, day_start1 = day_start, day_end1 = day_end, general_act1 = general_act, specific_act1 = specific_act, photo1 = photo, total_time1 = total_time, time_per_session1 = time_per_session, notes1 = notes, term1 = term, ev_name1 =ev_name, ev_type1 = ev_type, ev_des1 = ev_des)
    for n in grp_id:
      g.conn.execute(text(insert_hold),ev_id1 = ev_id, grp_id1 = n)
    for n in key_dict:
      g.conn.execute(text(insert_cover),ev_id1 = ev_id, top_id1 = n)
    for n in fac_id:
      g.conn.execute(text(insert_attend),ev_id1 = ev_id, fac_id1 = n)
    for n in sch_id:
      g.conn.execute(text(insert_partner),ev_id1 = ev_id, sch_id1 = n)
    for n in admin:
      g.conn.execute(text(insert_admin), ev_id1 = ev_id, adm_id1 = n)
    
    return redirect('/events/~'+ev_id)
  else:
    return redirect('/login/')

@app.route('/events/~<ev_id>/edit_ev')
def edit_ev(ev_id):
  if session:
    #get event info
    cmd = "SELECT * FROM event WHERE ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    res = cursor.fetchone()

    #get list of student group names involved
    cmd = "SELECT grp_name FROM event e INNER JOIN hold h ON e.ev_id = h.ev_id INNER JOIN student_group sg ON h.grp_id = sg.grp_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    sg = []
    for result in cursor:
      sg.append(result['grp_name'])

    #get list of partner school names involved
    cmd = "SELECT sch_name FROM event e INNER JOIN partner p ON e.ev_id = p.ev_id INNER JOIN partner_school ps ON p.sch_id = ps.sch_id WHERE e.ev_id= :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ps = []
    for result in cursor:
      ps.append(result['sch_name'])

    #get keywords/topics about event
    cmd = "SELECT top_name FROM event e INNER JOIN cover c ON e.ev_id = c.ev_id INNER JOIN keyword k ON c.top_id = k.top_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    kt = []
    for result in cursor:
      kt.append(result['top_name'])

    #get list of faculty involved
    cmd = "SELECT a.fac_id, fac_name FROM event e INNER JOIN attend a ON e.ev_id = a.ev_id INNER JOIN faculty f ON a.fac_id = f.fac_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ft = {}
    for result in cursor:
      ft[result['fac_id']] = result['fac_name']

    #get admin involved
    cmd = "SELECT a.adm_id, adm_name FROM event e INNER JOIN administrate a ON e.ev_id = a.ev_id INNER JOIN admin ad ON ad.adm_id = a.adm_id WHERE e.ev_id = :ev_id1"
    cursor = g.conn.execute(text(cmd), ev_id1 = ev_id)
    ad = {}
    for result in cursor:
      ad[result['adm_id']] = result['adm_name']

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

    #get list of possible participating institutions
    cursor = g.conn.execute("SELECT * FROM partner_school")
    pat_ins = {}
    for result in cursor:
      pat_ins[result['sch_id']] = {'sch_name':result['sch_name']}

    #get list of possible keywords
    cursor = g.conn.execute("SELECT * FROM keyword")
    top_key = {}
    for result in cursor:
      top_key[result['top_id']] = {'top_name':result['top_name']}

    #get list of possible admin
    cursor = g.conn.execute("SELECT * FROM admin")
    admin = {}
    for result in cursor:
      admin[result['adm_id']] = result['adm_name']

    cursor.close()
    context_prev = dict([('admin_name', ad),('faculty',ft),('key_name',kt),('sch_name',ps),('ev_type',res['ev_type'],),('time_per_session',res['time_per_session'],),('total_time',res['total_time']),('general_act', res['general_act']),('term',res['term']), ('ev_name', res['ev_name']),('day_start',res['day_start']),('day_end',res['day_end']),('specific_act',res['specific_act']),('photo',res['photo']),('notes',res['notes']), ('ev_des',res['ev_des']),('group_names', sg)])
    context_poss = dict([('admin', admin),('top_key',top_key),('pat_ins',pat_ins),('fac_att',fac_att),('ev_id', ev_id),('stu_grp',stu_grp),('par_sch',par_sch)])

    context = context_prev.copy()
    context.update(context_poss)
    context['loggedIn']=session

    return render_template("event_form.html", **context)
  else:
    return redirect('/login/')


@app.route('/events/~<ev_id>/delete_ev')
def delete_ev(ev_id):
  if session:
    cmd = "DELETE FROM administrate WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM volunteer WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM hold WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM cover WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM partner WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM attend WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    cmd = "DELETE FROM event WHERE ev_id = :ev_id1"
    g.conn.execute(text(cmd), ev_id1 = ev_id)
    return redirect('/events')
  else:
    return redirect('/login/')


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
  form = SignUpForm(request.form)
  if request.method == 'POST' and form.validate():
      student_group_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
      student_group_name = form.student_group_name.data
      email = form.email.data
      password = hashing.hash_value(form.password.data, salt=my_salt)
      cmd = 'INSERT INTO student_group VALUES (:grp_id1, :grp_name1, :password1, :email1)'
      g.conn.execute(text(cmd), grp_id1=student_group_id, grp_name1=student_group_name, password1=password, email1=email)
      return redirect('/login/')
  context = dict(form=form, loggedIn=session)
  return render_template('signup.html', **context)

@app.route('/login/', methods=['GET', 'POST'])
def login():
  form = LogInForm(request.form)
  if request.method == 'POST':
      email = form.email.data
      password = form.password.data
      cmd = 'SELECT * FROM student_group WHERE email = :email1'
      cursor = g.conn.execute(text(cmd), email1=email)
      res = cursor.fetchone()
      isValid = True if res and hashing.check_value(res.password, password, salt=my_salt) else False
      if form.validate(res, isValid):
        session['stu_grp'] = dict(grp_id=res.grp_id, grp_name=res.grp_name, email=email)
        return redirect('/')
  context = dict(form=form, loggedIn=session)
  return render_template('login.html', **context)

@app.route('/faculty')
def faculty():
  if session:
    cursor = g.conn.execute("SELECT * FROM faculty ORDER BY fac_name")
    faculty = {}
    for result in cursor:
      faculty[result['fac_id']] = {'fac_name': result['fac_name'], 'evaluation':result['evaluation'], 'dep_id':result['dep_id']}
    cursor.close()

    context = dict(faculty = faculty)
    context['loggedIn'] = session
    return render_template("faculty.html", **context)
  else:
    return redirect('/login/')

@app.route('/faculty/new')
def new_faculty():
  if session:
    cursor = g.conn.execute('SELECT * FROM Department')
    dept = {}
    for result in cursor:
      dept[result['dep_id']] = result['dep_name']

    context = dict(dept = dept)
    context['loggedIn'] = session
    return render_template("faculty_form.html",**context)
  else:
    return redirect('/login/')

@app.route('/faculty/add', methods=['GET','POST'])
def add_faculty():
  if session:
    fac_id = request.form['fac_id']
    fac_name = request.form['fac_name']
    evaluation = request.form['evaluation']
    dep_id = request.form['dep_id']

    try:
      cmd = "INSERT INTO faculty VALUES (:fac_id1, :fac_name1, :evaluation1, :dep_id1)"
      g.conn.execute(text(cmd), fac_id1 = fac_id, fac_name1 = fac_name, evaluation1 = evaluation, dep_id1 = dep_id)
    except:
      cmd = "UPDATE faculty SET fac_name = :fac_name1, evaluation = :evaluation1, dep_id = :dep_id1 WHERE fac_id = :fac_id1"
      g.conn.execute(text(cmd), fac_id1 = fac_id, fac_name1 = fac_name, evaluation1 = evaluation, dep_id1 = dep_id)

    return redirect("/faculty/@"+fac_id)
  else:
    return redirect('/login/')

@app.route('/faculty/@<fac_id>')
def get_faculty(fac_id):
  if session:
    cmd = "SELECT * FROM faculty f INNER JOIN department d ON f.dep_id = d.dep_id WHERE f.fac_id = :fac_id1"
    cursor = g.conn.execute(text(cmd), fac_id1 = fac_id)
    result = cursor.fetchone()
    context = {'fac_id': result['fac_id'],'fac_name': result['fac_name'], 'evaluation':result['evaluation'], 'dep_id':result['dep_id'], 'dep_name':result['dep_name']}
    
    events = {}

    try:
      cmd = "SELECT e.ev_id, e.ev_name, e.day_start, e.day_end FROM event e INNER JOIN attend a ON e.ev_id = a.ev_id WHERE a.fac_id = :fac_id1 ORDER BY e.day_start DESC"
      cursor = g.conn.execute(text(cmd), fac_id1 = fac_id)
      for result in cursor:
        events[result['ev_id']] = {'ev_name':result['ev_name'], 'day_start':result['day_start'], 'day_end':result['day_end']}
      tmp = dict(events = events)
      context.update(tmp)
    except: 
      print "something went wrong fetching recent events"
    
    cursor.close()  
    context['loggedIn'] = session
    return render_template("faculty_page.html", **context)
  else:
    return redirect('/login/')

@app.route('/faculty/@<fac_id>/edit_faculty')
def edit_faculty(fac_id):
  if session:
    cmd = "SELECT * FROM faculty WHERE fac_id = :fac_id1"
    cursor = g.conn.execute(text(cmd), fac_id1 = fac_id)
    result = cursor.fetchone()
    context = {'fac_id': result['fac_id'],'fac_name': result['fac_name'], 'evaluation':result['evaluation'], 'dep_id':result['dep_id']}
    
    cursor = g.conn.execute('SELECT * FROM Department')
    dept = {}
    for result in cursor:
      dept[result['dep_id']] = result['dep_name']

    tmp = dict(dept = dept)
    context.update(tmp)
    context['loggedIn'] = session

    return render_template("faculty_form.html",**context)
  else: 
    return redirect('/login/')

@app.route('/faculty/@<fac_id>/del_faculty')
def del_faculty(fac_id):
  if session:
    cmd = "DELETE FROM attend WHERE fac_id = :fac_id1"
    g.conn.execute(text(cmd), fac_id1 = fac_id)
    cmd = "DELETE FROM faculty WHERE fac_id = :fac_id1"
    g.conn.execute(text(cmd), fac_id1 = fac_id)
    return redirect('/faculty')
  else:
    return redirect('/login/')

@app.route('/admin')
def admin():
  if session:
    cursor = g.conn.execute("SELECT * FROM admin")
    admin = {}
    for result in cursor:
      admin[result['adm_id']] = {'adm_name': result['adm_name'], 'dep_id':result['dep_id']}
    cursor.close()

    context = dict(admin = admin)
    context['loggedIn'] = session
    return render_template("admin.html", **context)
  else:
    return redirect('/login/')

@app.route('/admin/new')
def new_admin():
  if session:
    cursor = g.conn.execute('SELECT * FROM Department')
    dept = {}
    for result in cursor:
      dept[result['dep_id']] = result['dep_name']

    context = dict(dept = dept)
    context['loggedIn'] = session
    return render_template("admin_form.html",**context)
  else:
    return redirect('/login/')

@app.route('/admin/add', methods=['GET','POST'])
def add_admin():
  if session:
    adm_id = request.form['adm_id']
    adm_name = request.form['adm_name']
    dep_id = request.form['dep_id']

    try:
      cmd = "INSERT INTO admin VALUES (:adm_id1, :adm_name1, :dep_id1)"
      g.conn.execute(text(cmd), adm_id1 = adm_id, adm_name1 = adm_name, dep_id1 = dep_id)
    except:
      cmd = "UPDATE admin SET adm_name = :adm_name1, dep_id = :dep_id1 WHERE adm_id = :adm_id1"
      g.conn.execute(text(cmd), adm_id1 = adm_id, adm_name1 = adm_name, dep_id1 = dep_id)

    return redirect("/admin/+"+adm_id)
  else:
    return redirect('/login/')

@app.route('/admin/+<adm_id>')
def get_admin(adm_id):
  if session:
    cmd = "SELECT * FROM admin a INNER JOIN department d ON a.dep_id = d.dep_id WHERE a.adm_id = :adm_id1"
    cursor = g.conn.execute(text(cmd), adm_id1 = adm_id)
    result = cursor.fetchone()
    context = {'adm_id': result['adm_id'],'adm_name': result['adm_name'], 'dep_id':result['dep_id'], 'dep_name':result['dep_name']}
    
    events = {}

    try:
      cmd = "SELECT e.ev_id, e.ev_name, e.day_start, e.day_end FROM event e INNER JOIN administrate a ON e.ev_id = a.ev_id WHERE a.adm_id = :adm_id1 ORDER BY e.day_start DESC"
      cursor = g.conn.execute(text(cmd), adm_id1 = adm_id)
      for result in cursor:
        events[result['ev_id']] = {'ev_name':result['ev_name'], 'day_start':result['day_start'], 'day_end':result['day_end']}
      tmp = dict(events = events)
      context.update(tmp)
    except: 
      print "something went wrong fetching recent events"
    
    cursor.close()  
    context['loggedIn'] = session
    return render_template("admin_page.html", **context)
  else:
    return redirect('/login/')

@app.route('/admin/+<adm_id>/edit_admin')
def edit_admin(adm_id):
  if session:
    cmd = "SELECT * FROM admin WHERE adm_id = :adm_id1"
    cursor = g.conn.execute(text(cmd), adm_id1 = adm_id)
    result = cursor.fetchone()
    context = {'adm_id': result['adm_id'],'adm_name': result['adm_name'], 'dep_id':result['dep_id']}
    
    cursor = g.conn.execute('SELECT * FROM Department')
    dept = {}
    for result in cursor:
      dept[result['dep_id']] = result['dep_name']

    tmp = dict(dept = dept)
    context.update(tmp)
    context['loggedIn'] = session

    return render_template("admin_form.html",**context)
  else:
    return redirect('/login/')

@app.route('/admin/+<adm_id>/del_admin')
def del_admin(adm_id):
  if session:
    cmd = "DELETE FROM administrate WHERE adm_id = :adm_id1"
    g.conn.execute(text(cmd), adm_id1 = adm_id)
    cmd = "DELETE FROM admin WHERE adm_id = :adm_id1"
    g.conn.execute(text(cmd), adm_id1 = adm_id)
    return redirect('/admin')
  else:
    return redirect('/login/')

@app.route('/partners')
def partners():
  if session:
    cursor = g.conn.execute("SELECT * FROM partner_school")
    partners = {}
    for result in cursor:
      partners[result['sch_id']] = {'sch_name': result['sch_name']}
    cursor.close()

    context = dict(partners = partners)
    context['loggedIn'] = session
    return render_template("partners.html", **context)
  else:
    return redirect('/login/')

@app.route('/partners/-<part_id>')
def get_partner(part_id):
  if session:
    cmd = "SELECT * FROM partner_school WHERE sch_id = :sch_id1"
    cursor = g.conn.execute(text(cmd), sch_id1 = part_id)
    result = cursor.fetchone()
    context = {'part_id':result['sch_id'],'part_name':result['sch_name']}
    events = {}

    try:
      cmd = "SELECT e.ev_id, e.ev_name, e.day_start, e.day_end FROM event e INNER JOIN partner p ON e.ev_id = p.ev_id WHERE p.sch_id = :sch_id1"
      cursor = g.conn.execute(text(cmd), sch_id1 = part_id)
      for result in cursor:
        events[result['ev_id']] = {'ev_name':result['ev_name'], 'day_start':result['day_start'], 'day_end':result['day_end']}
      tmp = dict(events = events)
      context.update(tmp)
    except: 
      print "something went wrong fetching recent events"

    cursor.close()
    context['loggedIn'] = session
    return render_template("partner_page.html", **context)
  else:
    return redirect('/login/')

@app.route('/partners/new')
def new_partner():
  if session:
    context = {}
    context['loggedIn'] = session
    return render_template("partner_form.html", **context)
  else:
    return redirect('/login/')

@app.route('/partners/add', methods=['GET','POST'])
def add_partner():
  if session:
    part_id = request.form['part_id'][:10]
    part_name = request.form['part_name']

    try:
      cmd = "INSERT INTO partner_school VALUES (:sch_id1, :sch_name1)"
      g.conn.execute(text(cmd), sch_id1 = part_id, sch_name1 = part_name)
    except:
      cmd = "UPDATE partner_school SET sch_name = :sch_name1 WHERE sch_id = :sch_id1"
      g.conn.execute(text(cmd), sch_id1 = part_id, sch_name1 = part_name)

    return redirect("/partners/-"+part_id)
  else:
    return redirect('/login/')

@app.route('/partners/-<part_id>/edit_partner')
def edit_partner(part_id):
  if session:
    cmd = "SELECT * FROM partner_school WHERE sch_id = :part_id1"
    cursor = g.conn.execute(text(cmd), part_id1 = part_id)
    result = cursor.fetchone()
    context = {'part_id': result['sch_id'],'part_name': result['sch_name']}
    context['loggedIn'] = session
    return render_template("partner_form.html", **context)
  else:
    return redirect('/login/')

@app.route('/partners/-<part_id>/del_partner')
def del_partner(part_id):
  if session:
    cmd = "DELETE FROM partner WHERE sch_id = :sch_id1"
    g.conn.execute(text(cmd), sch_id1 = part_id)
    cmd = "DELETE FROM partner_school WHERE sch_id = :sch_id1"
    g.conn.execute(text(cmd), sch_id1 = part_id)

    return redirect('/partners')
  else: 
    return redirect('/login/')

@app.route('/keywords')
def keywords():
  if session:
    cursor = g.conn.execute("SELECT * FROM keyword")
    keywords = {}
    for result in cursor:
      keywords[result['top_id']] = result['top_name']
    cursor.close()
    
    context = dict(keywords = keywords)
    context['loggedIn'] = session
    return render_template("keywords.html", **context)
  else:
    return redirect('/login/')

@app.route('/keywords/$<key_id>')
def get_keyword(key_id):
  if session:
    print "get keyword accessed"
    cmd = "SELECT * FROM keyword WHERE top_id = :top_id1"
    cursor = g.conn.execute(text(cmd), top_id1 = key_id)
    result = cursor.fetchone()
    context = {'key_id':result['top_id'],'key_name':result['top_name']}
    events = {}

    try:
      cmd = "SELECT e.ev_id, e.ev_name, e.day_start, e.day_end FROM event e INNER JOIN cover c ON e.ev_id = c.ev_id WHERE c.top_id = :top_id1"
      cursor = g.conn.execute(text(cmd), top_id1 = key_id)
      for result in cursor:
        events[result['ev_id']] = {'ev_name':result['ev_name'], 'day_start':result['day_start'], 'day_end':result['day_end']}
      tmp = dict(events = events)
      context.update(tmp)
    except: 
      print "something went wrong fetching recent events"

    cursor.close()
    context['loggedIn'] = session
    return render_template("keyword_page.html", **context)
  else:
    return redirect('/login/')

@app.route('/logout/')
def logout():
  session.pop('stu_grp', None)
  return redirect('/')

@app.route('/profile/~<id>/')
def profile(id):
  context = dict(grp_name=session['stu_grp']['grp_name'], email=session['stu_grp']['email'])
  return render_template('profile.html', **context)

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