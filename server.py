
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

global keyword
global user
global ingre_count
global ingred, db_did
keyword=""
user = {'id': "guest0", "name": "Guest", 'user_type': "u"}
ingre_count=1
ingred = ['start']
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
  global keyword, user
  print(user)
  keyword=""
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

  cursor = g.conn.execute("SELECT dish_id, dish_name FROM recipe")
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()

  #context = dict(data = names)
  dish = dict(dish = dishes)
  user_info = dict(user_info=user) 

  return render_template("home.html", **dish, **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/search', methods=['POST'])
def search():
  global keyword, user
  user_info = dict(user_info=user) 
  keyword = request.form['keyword']
  if not keyword:
    return redirect('/')
  keyword = keyword.lower()
  by_dish = "SELECT R.dish_id, R.dish_name FROM Recipe R WHERE LOWER(R.dish_name) LIKE %s"
  by_author = "SELECT R.dish_id, R.dish_name FROM Recipe R, Writes W, Author A WHERE R.dish_id=W.dish_id AND W.auth_id=A.auth_id AND LOWER(A.auth_name) LIKE %s"
  by_cuisine = "SELECT R.dish_id, R.dish_name FROM Recipe R, Type_of T, Cuisine C WHERE R.dish_id=T.dish_id AND C.cuisine_id=T.cuisine_id AND LOWER(C.region_name) LIKE %s"
  by_ingredients = "SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id AND LOWER(I.ingredient_name) LIKE %s"
  by_cookware = "SELECT R.dish_id, R.dish_name FROM Recipe R, Utilizes U, Cookware C WHERE R.dish_id=U.dish_id AND U.cookware_id=C.cookware_id AND LOWER(C.cookware_name) LIKE %s"
  
  connect = ' UNION '
  query = by_dish + connect + by_author + connect + by_ingredients + connect + by_cookware + connect + by_cuisine
  cursor = g.conn.execute(query,('%'+keyword+'%','%'+keyword+'%','%'+keyword+'%','%'+keyword+'%','%'+keyword+'%'))
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
  return render_template("home.html", **dish, **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/sort', methods=['POST'])
def sort():
  sorting = request.form['sorting']
  global keyword, user
  user_info = dict(user_info=user) 
  keyword = keyword.lower()
  criteria = sorting.split("_")[0]
  order = sorting.split("_")[1]
  
  if criteria=="calorie":
    cursor = g.conn.execute("SELECT R.dish_id, R.dish_name, SUM(I.calorie*C.quantity) AS calorie FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id AND LOWER(R.dish_name) LIKE '%%"+keyword+"%%' GROUP BY R.dish_id ORDER BY calorie "+order+", R.dish_name "+order) 
  elif criteria=="prep":
    criteria="prep_time"
    cursor = g.conn.execute("SELECT dish_id, dish_name, prep_time FROM Recipe WHERE LOWER(dish_name) LIKE '%%"+keyword+"%%' ORDER BY prep_time "+order+", dish_name "+order) 
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    temp[criteria] = result[criteria]
    dishes.append(temp)
  cursor.close()
  dish = dict(dish = dishes)
  return render_template("home.html", **dish, **user_info)

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

  cursor = g.conn.execute("SELECT C.region_name FROM Recipe R, Type_of T, Cuisine C WHERE C.cuisine_id=T.cuisine_id and T.dish_id=R.dish_id and R.dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['cuisine'] = content['region_name']
  cursor.close()

  cursor = g.conn.execute("SELECT A.auth_id, A.auth_name FROM Recipe R, Writes W, Author A WHERE W.auth_id=A.auth_id and W.dish_id=R.dish_id and R.dish_id=%s",(id)) 
  content = cursor.fetchone()
  infos['auth_id'] = content['auth_id']
  infos['auth_name'] = content['auth_name']
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
    temp['quantity'] = quantity
    temp['unit'] = result['unit']
    temp['carb'] = result['carb']*quantity
    temp['protein'] = result['protein']*quantity
    temp['fat'] = result['fat']*quantity
    calorie = result['calorie']*quantity
    cal += calorie
    temp['calorie'] = calorie
    ingredients.append(temp)
  cursor.close()

  infos['cal'] = cal
  info = dict(info=infos)
  ingredient = dict(ingredient = ingredients)

  return render_template('view.html',**info,**ingredient, **user_info)

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
  cursor = g.conn.execute("SELECT R.dish_id, R.dish_name FROM Author A, Writes W, Recipe R WHERE A.auth_id=W.auth_id AND W.dish_id=R.dish_id AND A.auth_id=%s", auth_id)
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()
  info = dict(info=infos)
  dish = dict(dish=dishes)
  return render_template('view_auth.html', **info, **dish, **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/login', methods=['POST'])
def login():
  global user
  userid = request.form['id']
  pswd = request.form['pswd']
  cursor = g.conn.execute("SELECT * FROM Users WHERE user_id=%s AND user_password=%s", userid, pswd)
  content = cursor.fetchone()
  if content:
    user['id'] = content['user_id']
    user['name'] = content['user_name']
    #return redirect("/collection/"+user['id'])
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

@app.route('/auth_login', methods=['POST'])
def auth_login():
  global user
  auth_email = request.form['email']
  pswd = request.form['pswd']
  cursor = g.conn.execute("SELECT * FROM Author WHERE auth_email='"+auth_email+"' AND auth_password=%s",(pswd))
  content = cursor.fetchone()
  if content:
    user['id'] = content['auth_id']
    user['name'] = content['auth_name']
    user['user_type'] = 'a'
    user['email'] = content['auth_email']
    #return redirect("/collection/"+author['id'])
    return redirect("home")
  else:
    error_msg = "Incorrect author email and password combination."
    error = dict(error=error_msg)
    return render_template("login.html", **error)

@app.route('/auth_login_page')
def auth_login_page():
  #login_type = "Author"
  #login_link = "/auth_login"
  #login_info = {"login_type": login_type, "login_link": login_link}
  #login = dict(login=login_info)
  #return render_template("auth_login.html", **login)
  return render_template("auth_login.html")

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
  return redirect("/collection/"+user['id'])

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

@app.route('/follow', methods=['POST'])
def follow():
  global user
  auth_id = request.form['id']
  cursor = g.conn.execute('SELECT * FROM Author A, Follows F, Users U WHERE F.user_id=U.user_id AND A.auth_id=F.auth_id AND A.auth_id=%s AND U.user_id=%s', (auth_id, user['id'], ))
  result = cursor.fetchone()
  print(result)
  if not result:
    g.conn.execute('INSERT INTO follows VALUES (%s, %s)', (user['id'], auth_id))
  return redirect("/following/"+user['id'])

# -----------------------------------------------------------------------------------------------

@app.route('/signup_page', methods=['POST', 'GET'])
def signup_page():
  if request.method == 'POST':
    user_id = request.form['user_id']
    name = request.form['name']
    password = request.form['password']
    email = request.form['email']
    if g.conn.execute('SELECT (%s, %s, %s, %s) FROM Users', (user_id, name, password, email)) == False:
      g.conn.execute('INSERT INTO Users VALUES (%s, %s, %s, %s)', (user_id, name, password, email))
    return render_template('signup.html')
  
  elif request.method == 'GET':
    return render_template('signup.html')

# -----------------------------------------------------------------------------------------------

@app.route('/recs_page', methods=['POST', 'GET'])
def recs_page():
  global user
  user_info = dict(user_info=user)
  if request.method == 'POST':
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
    l = 'SELECT R.dish_id, R.dish_name FROM Recipe r, Likes l WHERE r.dish_id=l.dish_id GROUP BY R.dish_id HAVING COUNT(L.dish_id)>2'
    q = 'SELECT dish_id, dish_name FROM Recipe WHERE prep_time < 30'
    d = 'SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id GROUP BY R.dish_id HAVING SUM(I.calorie*C.quantity)<600'
    p = 'SELECT R.dish_id, R.dish_name FROM Recipe R, Contains C, Ingredients I WHERE R.dish_id=C.dish_id AND C.ingredient_id=I.ingredient_id GROUP BY R.dish_id HAVING SUM(I.protein*C.quantity)>50'

    plus = ' INTERSECT '
    res = ''
    counter = 0

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
      
    cursor = g.conn.execute(res)
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
@app.route('/next_ingred', methods=['POST', 'GET'])
def next_ingred():
  global user, ingred
  user_info = dict(user_info=user)
  if request.method=='POST':
    #print(request.form)
    temp = dict()
    temp['id'] = request.form['ingredient_info'].split('_')[0]
    temp['name'] = request.form['ingredient_info'].split('_')[1]
    ingred.append(temp)
    ingreds = dict(ingreds=ingred)
    return redirect("add_ingredient")
  elif request.method=='GET':
    return render_template('add_ingredient.html', **ingreds,**user_info)




@app.route('/add_ingredient', methods=['POST', 'GET'])
def add_ingredient():
  global user, ingre_count
  user_info = dict(user_info=user)
  if request.method == 'POST':
    ingre_count = int(request.form["ingre_count"])
    ingre = []
    ingre_id=1
    for i in range(ingre_count):
      ingre.append(str(ingre_id))
      ingre_id+=1
    ingreds = dict(ingred=ingre)
    return render_template('add_ingredient.html', **ingreds,**user_info)
  elif  request.method == 'GET':
    cursor = g.conn.execute('select * from ingredients')
    db_ingred = []
    for result in cursor:
      temp = dict()
      temp['ingredient_id']=result['ingredient_id']
      temp['ingredient_name']=result['ingredient_name']
      db_ingred.append(temp)
    db_ingreds = dict(db_ingreds=db_ingred)
    ingreds = dict(ingreds=ingred)
    return render_template("add_ingredient.html", **user_info, **db_ingreds, **ingreds)

@app.route('/enter_ingredient', methods=['POST', 'GET'])
def enter_ingredient():
  #print(request.form)
  global user, ingred, ingre_count
  user_info = dict(user_info=user)
  cursor = g.conn.execute('select ingredient_id from ingredients where ingredient_id=(select max(ingredient_id) from ingredients)')
  result = cursor.fetchone()
  current_id = int(result['ingredient_id'].split("i")[1])

  if request.method == 'POST':
    current_id += 1
    ingredient_id = 'i'+str(current_id)
    ingredient_name = request.form['ingredient_name']
    if not ingredient_name:
      return redirect("add_ingredient")
    temp = dict()
    temp['id'] = ingredient_id
    temp['name'] = ingredient_name
    ingred.append(temp)
    protein = request.form['protein']
    carb = request.form['carb']
    fat = request.form['fat']
    calorie = request.form['calorie']
    unit = request.form['units']
    g.conn.execute('INSERT INTO Ingredients(ingredient_id, ingredient_name, protein, carb, fat, calorie, unit) VALUES (%s, %s, %s, %s, %s, %s, %s)', (ingredient_id, ingredient_name, protein, carb, fat, calorie, unit))
    return redirect("add_ingredient")
      #if g.conn.execute('SELECT %s FROM Ingredients', ingredient_name) == False:
      #  g.conn.execute('INSERT INTO Ingredients(ingredient_id, ingredient_name, protein, carb, fat, calorie, units) VALUES (%s, %s, %d, %d, %d, %d, %s)', (ingredient_id, ingredient_name, protein, carb, fat, calorie, units))
  elif  request.method == 'GET':
    return render_template("add_ingredient.html", **user_info)

# -----------------------------------------------------------------------------------------------

@app.route('/add_recipe', methods=['POST', 'GET'])
def add_recipe():
  global user, ingred, db_did
  user_info = dict(user_info=user)
  ingreds = dict(ingred=ingred)
  if request.method == 'POST':
    print(request.form)
    #ingredient_id = g.conn.execute('SELECT MAX(ASCII(ingredient_id)) FROM Ingredients')
    #auth_name = request.form['auth_name']
    #auth_email = request.form['auth_email']
    auth_id = user['id']
    cookware_name = request.form['cookware_name']
    region_name = request.form['region_name']
    instructions = request.form['instructions']
    prep_time = request.form['prep_time']
    is_spicy = request.form['is_spicy']=='on'

    #cursor = g.conn.execute('select dish_id from recipe where dish_id=(select max(dish_id) from recipe)')
    #result = cursor.fetchone()
    #dish_id = 'd'+str(int(result['dish_id'].split("d")[1])+1)
    dish_id = 'd'+str(db_did)
    dish_name = request.form['dish_name']

    print('INSERT INTO Recipe(dish_id, dish_name, instructions, prep_time, is_spicy) VALUES (%s, %s, %s, %s, %s, %s, %s)', (dish_id, dish_name, instructions, prep_time, is_spicy))

    #if g.conn.execute('SELECT %s FROM Recipe', dish_name) == False:
      #g.conn.execute('INSERT INTO Recipe VALUES (%s, %s, %s, %d, %r)', (dish_id, dish_name, instructions, prep_time, is_spicy))

    portion = request.form['portion']
    #if g.conn.execute('SELECT (%s, %s, %d) FROM Contains', (dish_id, ingredient_id, portion)) == False:
    #  g.conn.execute('INSERT INTO Contains(dish_id, ingredient_id, portion) VALUES (%s, %s, %d)', (dish_id, ingredient_id, portion))
    for item in ingreds:
      ingredient_id = item['id']
      print('INSERT INTO Contains(dish_id, ingredient_id, portion) VALUES (%s, %s, %s)', (dish_id, ingredient_id, portion))

    
    #if g.conn.execute('SELECT (%s, %s) FROM Cuisine', (cuisine_id, region_name)) == False:
    #  g.conn.execute('INSERT INTO Cuisine(cuisine_id, region_name) VALUES (%s, %s)', (cuisine_id, region_name))
    cuisine_id = 'c'+ str(db_did)
    print('INSERT INTO Cuisine(cuisine_id, region_name) VALUES (%s, %s)', (cuisine_id, region_name))
    print(('INSERT INTO Type_Of(dish_id, cuisine_id) VALUES (%s, %s)', (dish_id, cuisine_id)))

    #cuisine_id = g.conn.execute('SELECT MAX(ASCII(cuisine_id)) FROM Type_Of')
    #if g.conn.execute('SELECT (%s, %s) FROM Type_Of', (dish_id, cuisine_id)) == False:
    #  g.conn.execute('INSERT INTO Type_Of(dish_id, cuisine_id) VALUES (%s, %s)', (dish_id, cuisine_id))
    cookware_id = 'w5'
    #cookware_name = request.form['cookware_name']
    #is_electric = request.form['is_electric']=='on'

    #if g.conn.execute('SELECT (%s, %s, %r) FROM Cookware', (cookware_id, cookware_name, is_electric)) == False:
    #  g.conn.execute('INSERT INTO Cookware(cookware_id, cookware_name, is_electric) VALUES (%s, %s, %r)', (cookware_id, cookware_name, is_electric))

    #print('INSERT INTO Cookware(cookware_id, cookware_name, is_electric) VALUES (%s, %s, %r)', (cookware_id, cookware_name, is_electric))

    #cookware_id = g.conn.execute('SELECT MAX(ASCII(cookware_id)) FROM Utilizes')
    #if g.conn.execute('SELECT (%s,%s) FROM Utilizes', (dish_id, cookware_id)) == False:
    #  g.conn.execute('INSERT INTO Utilizes(dish_id, cookware_id) VALUES (%s, %s)', (dish_id, cookware_id))
    print('INSERT INTO Utilizes(dish_id, cookware_id) VALUES (%s, %s)', (dish_id, cookware_id))

    
    #cookware_id = g.conn.execute('SELECT MAX(ASCII(cookware_id)) FROM Utilizes')
    #if g.conn.execute('SELECT (%s,%s,%s) FROM Author', (auth_id, auth_name, auth_email, auth_password)) == False:
    #  g.conn.execute('INSERT INTO Author(auth_id, auth_name, auth_email, auth_password) VALUES (%s, %s, %s)', (auth_id, auth_name, auth_email))

    #auth_id = g.conn.execute('SELECT MAX(ASCII(auth_id)) FROM Writes')
    #if g.conn.execute('SELECT (%s,%s) FROM Writes', (auth_id, dish_id)) == False:
    #  g.conn.execute('INSERT INTO Writes(auth_id, dish_id) VALUES (%s, %s)', (auth_id, dish_id))

    print(('INSERT INTO Writes(auth_id, dish_id) VALUES (%s, %s)', (auth_id, dish_id)))

    return render_template('add_recipe.html', **ingreds,**user_info)
  elif  request.method == 'GET':
    return render_template('add_recipe.html', **ingreds,**user_info)

# -----------------------------------------------------------------------------------------------

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8110, type=int)
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
