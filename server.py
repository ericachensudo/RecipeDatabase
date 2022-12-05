
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
# from codejana_flask import app
from sqlalchemy.pool import NullPool
from flask import Flask, request, url_for, render_template, g, redirect, Response
# from codejana_flask.forms import RegistrationForm

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

global keyword, user, modes
#global ingre_count
global ingred, db_did
keyword=""
user = {'id': "guest0", "name": "Guest", 'user_type': "u", 'profile_edit': False}
modes = {'search': False}
#ingre_count=1
ingred = []
db_did=11

# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@34.75.94.195/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.75.94.195/proj1part2"
#
DATABASEURI = "postgresql://cz2416:4939@34.75.94.195/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
#engine.execute("""CREATE TABLE IF NOT EXISTS test (
#  id serial,
#  name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/home')
def home():
  global keyword, user, modes
  keyword=""
  modes['search'] = False
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  #cursor = g.conn.execute("SELECT name FROM test")
  #names = []
  #for result in cursor:
  #  names.append(result['name'])  # can also be accessed using result[0]
  #cursor.close()

  cursor = g.conn.execute("SELECT dish_id, dish_name FROM recipe ORDER BY dish_name ASC")
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()

  images = []
  cursor = g.conn.execute('SELECT R.dish_id, R.image[1] FROM Recipe r, Likes l WHERE r.dish_id=l.dish_id GROUP BY R.dish_id ORDER BY COUNT(*) DESC LIMIT 4')
  
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['image'] = result['image']
    images.append(temp)
  #images = result['image']
  cursor.close()

  dish = dict(dish = dishes)
  user_info = dict(user_info=user)
  mode = dict(mode=modes)
  image = dict(image=images)  

  return render_template("home.html", **dish, **user_info, **mode, **image)

# -----------------------------------------------------------------------------------------------
@app.route('/leaderboard')
def leaderboard():
  global keyword, user, modes
  cursor = g.conn.execute("SELECT a.auth_id FROM author a, follows f WHERE a.auth_id=F.auth_id AND F.user_id=%s",(user['id']))
  follow_list = []
  for result in cursor:
    follow_list.append(result[0])
  cursor.close()
  cursor = g.conn.execute("SELECT a.auth_id, a.auth_name, count(a.auth_id) as num FROM author a, follows f WHERE a.auth_id=F.auth_id GROUP BY a.auth_id ORDER BY num DESC, a.auth_name ASC")
  auths = []
  counter=0
  for result in cursor:
    counter += 1
    temp = dict()
    temp['rank'] = counter
    temp['auth_id'] = result['auth_id']
    temp['auth_name'] = result['auth_name']
    temp['followed'] = result['auth_id'] in follow_list
    auths.append(temp)
  cursor.close()
  auth = dict(auth = auths)
  user_info = dict(user_info=user)
  mode = dict(mode=modes)  

  return render_template("leaderboard.html", **auth, **user_info, **mode)

@app.route('/search', methods=['POST','GET'])
def search():
  global keyword, user, modes
  user_info = dict(user_info=user) 
  keyword = request.form['keyword']
  modes['search'] = keyword
  if not keyword:
    return redirect('/home')
    
  keyword = keyword.lower()
  by_dish = "SELECT R.dish_id, R.dish_name FROM Recipe R WHERE LOWER(R.dish_name) LIKE %s"
  by_author = "SELECT R.dish_id, R.dish_name FROM Recipe R, Writes W, Author A WHERE R.dish_id=W.dish_id AND W.auth_id=A.auth_id AND LOWER(A.auth_name) LIKE %s"
  by_cuisine = "SELECT R.dish_id, R.dish_name FROM Recipe R, Type_of T, Cuisine C WHERE R.dish_id=T.dish_id AND C.cuisine_id=T.cuisine_id AND LOWER(C.region_name) LIKE %s"
  by_ingredients = "SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id AND LOWER(I.ingredient_name) LIKE %s"
  by_cookware = "SELECT R.dish_id, R.dish_name FROM Recipe R, Utilizes U, Cookware C WHERE R.dish_id=U.dish_id AND U.cookware_id=C.cookware_id AND LOWER(C.cookware_name) LIKE %s"
  
  connect = ' UNION '
  order = ' ORDER BY dish_name ASC'
  query = by_dish + connect + by_author + connect + by_ingredients + connect + by_cookware + connect + by_cuisine + order
  cursor = g.conn.execute(query,('%'+keyword+'%','%'+keyword+'%','%'+keyword+'%','%'+keyword+'%','%'+keyword+'%'))
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    cursor1 = g.conn.execute("SELECT A.auth_name FROM Recipe R, Writes W, Author A WHERE R.dish_id=W.dish_id AND W.auth_id=A.auth_id AND R.dish_id=%s", (temp['dish_id']))
    output = cursor1.fetchone()
    temp['auth_name'] = output[0]
    cursor1.close()

    cursor1 = g.conn.execute("SELECT C.region_name FROM Recipe R, Type_of T, Cuisine C WHERE R.dish_id=T.dish_id AND C.cuisine_id=T.cuisine_id AND R.dish_id=%s", (temp['dish_id']))
    output = cursor1.fetchone()
    temp['cuisine_name'] = output[0]
    cursor1.close()

    cursor1 = g.conn.execute("SELECT C.cookware_name FROM Recipe R, Utilizes U, Cookware C WHERE R.dish_id=U.dish_id AND U.cookware_id=C.cookware_id AND R.dish_id=%s", (temp['dish_id']))
    output = cursor1.fetchone()
    temp['cookware_name'] = output[0]
    cursor1.close()

    dishes.append(temp)
  cursor.close()
  if not dishes:
    temp = dict()
    temp['dish_id'] = "d0"
    dishes.append(temp)
  dish = dict(dish = dishes)
  mode = dict(mode=modes)  
  return render_template("home.html", **dish, **user_info, **mode)

# -----------------------------------------------------------------------------------------------

@app.route('/sort', methods=['POST'])
def sort():
  global keyword, user, modes
  user_info = dict(user_info=user) 
  keyword = keyword.lower()
  if not request.form:
    return redirect('/home')
  sorting = request.form['sorting']
  criteria = sorting.split("_")[0]
  order = sorting.split("_")[1]
  
  if criteria=="calorie":
    cursor = g.conn.execute("SELECT R.dish_id, R.dish_name, SUM(I.calorie*C.quantity) AS calorie FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id AND LOWER(R.dish_name) LIKE '%%"+keyword+"%%' GROUP BY R.dish_id ORDER BY calorie "+order+", R.dish_name "+order) 
  elif criteria=="prep":
    criteria="prep_time"
    cursor = g.conn.execute("SELECT dish_id, dish_name, prep_time FROM Recipe WHERE LOWER(dish_name) LIKE '%%"+keyword+"%%' ORDER BY prep_time "+order+", dish_name "+order)
  elif criteria=="pop":
    l = 'SELECT R.dish_id, R.dish_name FROM Recipe r, Likes l WHERE r.dish_id=l.dish_id GROUP BY R.dish_id HAVING COUNT(L.dish_id)>3'
    cursor = g.conn.execute('SELECT R.dish_id, R.dish_name, count(r.dish_id) as num FROM Recipe r, Likes l WHERE r.dish_id=l.dish_id GROUP BY r.dish_id ORDER BY num '+order+', dish_name asc')


  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']

    #temp[criteria] = result[criteria]
    dishes.append(temp)
  cursor.close()
  dish = dict(dish = dishes)
  mode = dict(mode=modes)  
  return render_template("home.html", **dish, **user_info, **mode)

# -----------------------------------------------------------------------------------------------

@app.route('/view/<id>')
def view(id=None):
  global user
  user_info = dict(user_info=user) 
  infos = dict()
  cursor = g.conn.execute("SELECT * FROM Recipe WHERE dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['dish_id'] = content['dish_id']
  infos['dish_name'] = content['dish_name']
  infos['prep_time'] = content['prep_time']
  is_spicy = content['is_spicy']
  spicy = "No"
  if is_spicy:
    spicy = "Yes"
  infos['spicy'] = spicy
  infos['instruction'] = content['instructions']
  cursor.close()

# ---------------- print every picture in array
  images = []
  cursor = g.conn.execute('SELECT image FROM Recipe WHERE dish_id=%s',(infos['dish_id']))
  result = cursor.fetchone()
  #for pic in enumerate(result):
  #  images.append(pic)
  images = result[0]
  cursor.close()

# ----------------

  cursor = g.conn.execute('select count(dish_id) from likes where dish_id=%s',(infos['dish_id']))
  content = cursor.fetchone()
  infos['likes'] = content[0]
  cursor.close()

  cursor = g.conn.execute("SELECT C.region_name FROM Recipe R, Type_of T, Cuisine C WHERE C.cuisine_id=T.cuisine_id and T.dish_id=R.dish_id and R.dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['cuisine'] = content['region_name']
  cursor.close()

  cursor = g.conn.execute("SELECT A.auth_id, A.auth_name FROM Recipe R, Writes W, Author A WHERE W.auth_id=A.auth_id and W.dish_id=R.dish_id and R.dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['auth_id'] = content['auth_id']
  infos['auth_name'] = content['auth_name']
  cursor.close()
  
  cursor = g.conn.execute('select count(auth_id) from follows where auth_id=%s',(infos['auth_id']))
  content = cursor.fetchone()
  infos['follows'] = content[0]
  cursor.close()

  cursor = g.conn.execute("SELECT C.cookware_name, C.is_electric FROM Recipe R, Utilizes U, Cookware C WHERE C.cookware_id=U.cookware_id and U.dish_id=R.dish_id and R.dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['cookware'] = content['cookware_name']
  is_electric = content['is_electric']
  electric = "not electric"
  if is_electric:
    electric = "electric"
  infos['electric'] = electric
  cursor.close()

  cursor = g.conn.execute("SELECT I.ingredient_id, I.ingredient_name, I.carb, I.protein, I.fat, I.calorie, I.unit, C.quantity FROM Recipe R, Contains C, Ingredients I WHERE I.ingredient_id=C.ingredient_id and R.dish_id=C.dish_id and C.dish_id=%s",(id)) 
  ingredients = []
  cal = 0
  for result in cursor:
    temp = dict()
    temp['name'] = result['ingredient_name']
    quantity = result['quantity']
    base, unit = result['unit'].split('_')
    measure = str(int(base)*quantity)+" "+unit
    temp['measure'] = measure
    temp['carb'] = result['carb']*quantity
    temp['protein'] = result['protein']*quantity
    temp['fat'] = result['fat']*quantity
    calorie = result['calorie']*quantity
    cal += calorie
    temp['calorie'] = calorie
    ingredients.append(temp)
  cursor.close()
  cursor = g.conn.execute("SELECT SUM(I.carb*C.quantity*4+I.protein*C.quantity*4+I.fat*C.quantity*9) FROM Recipe R, Contains C, Ingredients I WHERE I.ingredient_id=C.ingredient_id and R.dish_id=C.dish_id and C.dish_id=%s GROUP BY R.dish_id",(id)) 
  result = cursor.fetchone()
  infos['cal'] = result[0]
  cursor.close()
  
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (infos['auth_id'], user['id'], ))
  result = cursor.fetchone()
  if result:
    infos['followed'] = True
  else:
    infos['followed'] = False
  cursor.close()

  cursor = g.conn.execute('SELECT R.dish_id, R.dish_name FROM Recipe R, Likes L, Users U WHERE L.user_id=U.user_id AND R.dish_id=L.dish_id AND R.dish_id=%s AND U.user_id=%s', (infos['dish_id'], user['id']))
  result = cursor.fetchone()
  if result:
    infos['liked'] = True
  else:
    infos['liked'] = False
  cursor.close()
  info = dict(info=infos)
  ingredient = dict(ingredient = ingredients)
  image = dict(image = images)

  return render_template('view.html',**info,**ingredient, **image, **user_info)

@app.route('/view_auth/<auth_id>')
def view_auth(auth_id=None):
  global user
  user_info = dict(user_info=user) 
  infos = dict()
  cursor = g.conn.execute("SELECT * FROM Author WHERE auth_id=%s", auth_id)
  result = cursor.fetchone()
  infos['auth_id'] = auth_id
  infos['auth_name'] = result['auth_name']
  infos['auth_email'] = result['auth_email']
  infos['auth_bio'] = result['bio']
  cursor = g.conn.execute("SELECT R.dish_id, R.dish_name FROM Author A, Writes W, Recipe R WHERE A.auth_id=W.auth_id AND W.dish_id=R.dish_id AND A.auth_id=%s", auth_id)
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()
  cursor = g.conn.execute('select count(auth_id) from follows where auth_id=%s',(infos['auth_id']))
  content = cursor.fetchone()
  infos['follows'] = content[0]
  cursor.close()
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (infos['auth_id'], user['id'], ))
  result = cursor.fetchone()
  if result:
    infos['followed'] = True
  else:
    infos['followed'] = False
  cursor.close()
  info = dict(info=infos)
  dish = dict(dish=dishes)
  return render_template('view_auth.html', **info, **dish, **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/login', methods=['POST'])
def login():
  global user
  user['user_type'] = 'u'
  userid = request.form['id']
  pswd = request.form['pswd']
  cursor = g.conn.execute("SELECT * FROM Users WHERE user_id=%s AND user_password=%s", userid, pswd)
  content = cursor.fetchone()
  if content:
    user['id'] = content['user_id']
    user['name'] = content['user_name']
    return redirect("/home")
  else:
    error_msg = "Incorrect user id and password combination."
    error = dict(error=error_msg)
    return render_template("login.html", **error)

@app.route('/')
def login_page():
  global user
  user = {'id': "guest0", "name": "Guest"}
  return render_template("login.html")

# -----------------------------------------------------------------------------------------------

@app.route('/tocollection')
def tocollection():
  global user
  userid = user['id']
  return redirect("/collection/"+user['id'])

@app.route('/collection/<userid>')
def collection(userid=None):
  global user
  cursor = g.conn.execute("SELECT R.dish_id, R.dish_name FROM Recipe R, Likes L, Users U WHERE L.user_id=U.user_id AND R.dish_id=L.dish_id AND U.user_id=%s",(userid))
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()
  dish = dict(dish = dishes)
  user_info = dict(user_info=user)
  return render_template("collection.html", **dish, **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/like', methods=['POST'])
def like():
  global user
  dish_id = request.form['id']
  cursor = g.conn.execute('SELECT R.dish_id, R.dish_name FROM Recipe R, Likes L, Users U WHERE L.user_id=U.user_id AND R.dish_id=L.dish_id AND R.dish_id=%s AND U.user_id=%s', (dish_id, user['id']))
  result = cursor.fetchone()
  if not result:
    g.conn.execute('INSERT INTO likes VALUES (%s, %s)', user['id'], dish_id)
  return redirect("/view/"+dish_id)

@app.route('/unlike', methods=['POST'])
def unlike():
  global user
  dish_id = request.form['id']
  g.conn.execute('delete from likes where dish_id=%s and user_id=%s', (dish_id, user['id'], ))
  return redirect("/view/"+dish_id)

# -----------------------------------------------------------------------------------------------

@app.route('/tofollowing')
def tofollowing():
  global user
  userid = user['id']
  return redirect("/following/"+user['id'])
  
@app.route('/following/<userid>')
def following(userid=None):
  global user
  user_info = dict(user_info=user)
  cursor = g.conn.execute("SELECT A.auth_id, A.auth_name FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND U.user_id=%s", (userid))
  authors = []
  for result in cursor:
    temp = dict()
    temp['auth_id'] = result['auth_id']
    temp['auth_name'] = result['auth_name']
    authors.append(temp)
  cursor.close()
  author = dict(author = authors)
  return render_template("following.html", **author, **user_info)

@app.route('/follow/<auth_id>', methods=['POST'])
def follow(auth_id=None):
  global user
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (auth_id, user['id'], ))
  result = cursor.fetchone()
  if not result:
    g.conn.execute('INSERT INTO follows VALUES (%s, %s)', (user['id'], auth_id))
  return redirect('/leaderboard')

@app.route('/unfollow/<auth_id>', methods=['POST'])
def unfollow(auth_id=None):
  global user
  g.conn.execute('delete from follows where auth_id=%s and user_id=%s', (auth_id, user['id'], ))
  return redirect('/leaderboard')

@app.route('/followa', methods=['POST'])
def followa():
  global user
  auth_id = request.form['id']
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (auth_id, user['id'], ))
  result = cursor.fetchone()
  print(result)
  if not result:
    g.conn.execute('INSERT INTO follows VALUES (%s, %s)', (user['id'], auth_id))
  return redirect('/view_auth/'+auth_id)

@app.route('/unfollowa', methods=['POST'])
def unfollowa():
  global user
  auth_id = request.form['id']
  g.conn.execute('delete from follows where auth_id=%s and user_id=%s', (auth_id, user['id'], ))
  return redirect('/view_auth/'+auth_id)

@app.route('/followv', methods=['POST'])
def followv():
  global user
  auth_id = request.form['id']
  dish_id = request.form['dish_id']
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (auth_id, user['id'], ))
  result = cursor.fetchone()
  print(result)
  if not result:
    g.conn.execute('INSERT INTO follows VALUES (%s, %s)', (user['id'], auth_id))
  return redirect("/view/"+dish_id)

@app.route('/unfollowv', methods=['POST'])
def unfollowv():
  global user
  auth_id = request.form['id']
  dish_id = request.form['dish_id']
  g.conn.execute('delete from follows where auth_id=%s and user_id=%s', (auth_id, user['id'], ))
  return redirect("/view/"+dish_id)
# -----------------------------------------------------------------------------------------------

@app.route('/recs_page', methods=['POST', 'GET'])
def recs_page():
  global user
  user_info = dict(user_info=user)
  if request.method == 'POST':
    if not request.form:
      dishes = []
      temp = {'dish_id':'d00'}
      dishes.append(temp)
      dish = dict(dish = dishes)
      return render_template("recs.html", **dish, **user_info)
    recommendation = []
    for key in request.form:
      recommendation.append(request.form[key])
    user['recommendation'] = recommendation

    spicy = 'is_spicy'
    quick = 'prep_time'
    diet = 'calorie'
    liked = 'liked'
    protein = 'protein'

    s = 'SELECT dish_id, dish_name FROM Recipe WHERE is_spicy = True'
    l = 'SELECT R.dish_id, R.dish_name FROM Recipe r, Likes l WHERE r.dish_id=l.dish_id GROUP BY R.dish_id HAVING COUNT(L.dish_id)>3'
    q = 'SELECT dish_id, dish_name FROM Recipe WHERE prep_time < 30'
    d = 'SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id GROUP BY R.dish_id HAVING SUM(I.calorie*C.quantity)<800'
    p = 'SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id GROUP BY R.dish_id HAVING SUM(I.protein*C.quantity)>30'

    plus = ' INTERSECT '
    res = ''
    counter = 0
    order = ' ORDER BY dish_name ASC'

    for n in user['recommendation']:
      if counter>0:
        res += plus
      if n == spicy:
        res += s
      elif n == quick:
        res += q
      elif n == diet:
        res += d
      elif n == liked:
        res += l
      elif n == protein:
        res += p
      counter +=1
      
    cursor = g.conn.execute(res+order)
    dishes = []
    for result in cursor:
      temp = dict()
      temp['dish_id'] = result['dish_id']
      temp['dish_name'] = result['dish_name']
      dishes.append(temp)
    cursor.close()
    if not dishes:
      temp = dict()
      temp['dish_id'] = "d0"
      dishes.append(temp)
    dish = dict(dish = dishes)
    return render_template("recs.html", **dish, **user_info)
  elif request.method == 'GET':
    return render_template('recs.html', **user_info)

# -----------------------------------------------------------------------------------------------
def getUserInfo(user_id):
    cursor = g.conn.execute('SELECT * FROM Users U WHERE U.user_id=%s', (user_id))
    result = cursor.fetchone()
    user_info = dict()
    user_info['name'] = result['user_name']
    user_info['email'] = result['user_email']

    cursor = g.conn.execute('SELECT (pref).calorie FROM Users U WHERE U.user_id=%s', (user_id))
    result = cursor.fetchone()
    user_info['calorie'] = result['calorie']

    cursor = g.conn.execute('SELECT (pref).spicy FROM Users U WHERE U.user_id=%s', (user_id))
    result = cursor.fetchone()
    user_info['spicy'] = result['spicy']

    cursor = g.conn.execute('SELECT (pref).prep_time FROM Users U WHERE U.user_id=%s', (user_id))
    result = cursor.fetchone()
    user_info['prep_time'] = result['prep_time']
    return user_info  


@app.route('/user_profile', methods=['GET','POST'])
def user_profile():
  global user
  if request.method=='GET':
    user_pref = getUserInfo(user['id'])
    cursor = g.conn.execute('SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id GROUP BY R.dish_id HAVING SUM(I.calorie*C.quantity)< %s INTERSECT SELECT dish_id, dish_name FROM Recipe WHERE is_spicy = %s INTERSECT (SELECT dish_id, dish_name FROM Recipe WHERE prep_time < %s ORDER BY prep_time DESC)', (user_pref['calorie'], user_pref['spicy'], user_pref['prep_time']))  
    dishes = []
    dish_ids = []
    for result in cursor:
      temp = dict()
      temp['dish_id'] = result['dish_id']
      temp['dish_name'] = result['dish_name']
      dish_ids.append(result['dish_id'])
      dishes.append(temp)
    cursor.close()
    if len(dishes)>=5:
      dishes = dishes[:5]
    else:
      cursor = g.conn.execute('SELECT R.dish_id, R.dish_name FROM Recipe r, Likes l GROUP BY R.dish_id ORDER BY COUNT(L.dish_id) DESC')
      for result in cursor:
        if len(dishes)==5:
          break
        if result['dish_id'] in dish_ids:
          pass
        else:
          temp = dict()
          temp['dish_id'] = result['dish_id']
          temp['dish_name'] = result['dish_name']
          dishes.append(temp)
      cursor.close()
    fav_dish = dict(fav_dish = dishes)

    user_infos=getUserInfo(user['id'])
    user_profile = dict(user_profile=user_infos)
    user_info = dict(user_info=user)
    return render_template('user_profile.html', **user_info, **user_profile, **fav_dish)
  elif request.method=='POST':
    calorie_limit = request.form['calorie']
    spicy = 'False'
    if 'is_spicy' in request.form:
      spicy = 'True'
    prep_time = request.form['prep_time']
    g.conn.execute('UPDATE Users u SET pref = (%s,%s,%s) WHERE u.user_id = %s;', (calorie_limit, spicy, prep_time, user['id']))
    user['profile_edit']= False
    return redirect('/user_profile')

# -----------------------------------------------------------------------------------------------
@app.route('/edit_profile', methods=['POST'])
def edit_profile():
  global user
  user['profile_edit']= True
  return redirect('user_profile')
# -----------------------------------------------------------------------------------------------

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
