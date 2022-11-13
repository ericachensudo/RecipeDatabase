
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
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

global keyword
keyword=""

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
@app.route('/')
def index():
  global keyword
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

  return render_template("index.html", **dish)


@app.route('/search', methods=['POST'])
def search():
  global keyword
  keyword = request.form['keyword']
  if not keyword:
    return redirect('/')
  return redirect('/search/'+keyword)

@app.route('/search/<keyword>')
def search_result(keyword=None):
  keyword = keyword.lower()
  cursor = g.conn.execute("SELECT R.dish_id, R.dish_name FROM Recipe R WHERE LOWER(R.dish_name) LIKE '%%"+keyword+"%%'") 
  dishes = []
  for result in cursor:
    temp = dict()
    temp['dish_id'] = result['dish_id']
    temp['dish_name'] = result['dish_name']
    dishes.append(temp)
  cursor.close()
  dish = dict(dish = dishes)
  return render_template("search_result.html", **dish)


@app.route('/sort', methods=['POST'])
def sort():
  sorting = request.form['sorting']
  return redirect('/sort/'+sorting)

@app.route('/sort/<sorting>')
def sort_result(sorting=None):
  global keyword
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
  return render_template("index.html", **dish)


@app.route('/view/<id>')
def view(id=None):
  infos = dict()
  cursor = g.conn.execute("SELECT dish_name, prep_time, is_spicy, instructions FROM Recipe WHERE dish_id='"+id+"'") 
  content = cursor.fetchone()
  infos['dish_name'] = content['dish_name']
  infos['prep_time'] = content['prep_time']
  is_spicy = content['is_spicy']
  spicy = "No"
  if is_spicy:
    spicy = "Yes"
  infos['spicy'] = spicy
  infos['instruction'] = content['instructions']
  cursor.close()

  cursor = g.conn.execute("SELECT C.region_name FROM Recipe R, Type_of T, Cuisine C WHERE C.cuisine_id=T.cuisine_id and T.dish_id=R.dish_id and R.dish_id='"+id+"'") 
  content = cursor.fetchone()
  infos['cuisine'] = content['region_name']
  cursor.close()

  cursor = g.conn.execute("SELECT A.auth_name FROM Recipe R, Writes W, Author A WHERE W.auth_id=A.auth_id and W.dish_id=R.dish_id and R.dish_id='"+id+"'") 
  content = cursor.fetchone()
  infos['auth_name'] = content['auth_name']
  cursor.close()

  cursor = g.conn.execute("SELECT C.cookware_name, C.is_electric FROM Recipe R, Utilizes U, Cookware C WHERE C.cookware_id=U.cookware_id and U.dish_id=R.dish_id and R.dish_id='"+id+"'") 
  content = cursor.fetchone()
  infos['cookware'] = content['cookware_name']
  is_electric = content['is_electric']
  electric = "not electric"
  if is_electric:
    electric = "electric"
  infos['electric'] = electric
  cursor.close()

  cursor = g.conn.execute("SELECT I.ingredient_id, I.ingredient_name, I.carb, I.protein, I.fat, I.calorie, I.unit, C.quantity FROM Recipe R, Contains C, Ingredients I WHERE I.ingredient_id=C.ingredient_id and R.dish_id=C.dish_id and C.dish_id='"+id+"'") 
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

  return render_template('view.html',**info,**ingredient)

#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names

# Checking inputs with database of recipes (you dont need an account)
@app.route('/recs', methods=['GET', 'POST'])
def recs():
  if request.method == 'POST':
    spicy = g.conn.execute('SELECT * FROM Recipe WHERE is_spicy == True')
    quick = g.conn.execute('SELECT * FROM Recipe WHERE prep_time < 30')
    
    snack = g.conn.execute('SELECT * FROM Recipe r, Contains c WHERE dish_id r.dis_id == c.dish_id and c.portion == 1', )
    res = []
  
  return request.form.getlist('mycheckbox')

# Checking inputs (username, password) with databases of users
@app.route('/login', methods=['GET', 'POST'])
def login():
  return redirect("/")
  

# Adding new user credentials to the database
@app.route('/signup', methods=['POST'])
def signup():
  user_id = request.form['user_id']
  name = request.form['name']
  password = request.form['password']
  email = request.form['email']
  g.conn.execute('INSERT INTO Users VALUES (%s, %s, %s, %s)', user_id, name, password, email)
  return render_template('signup.html')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8112, type=int)
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
