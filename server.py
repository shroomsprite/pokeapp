#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import random
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#
DATABASEURI = "postgresql://cec2192:summer@35.185.80.252/w4111"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


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
    print "uh oh, problem connecting to database"
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
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/pokemon')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
################################################################################## 
# CODE BEGINS HERE
################################################################################## 

@app.route('/')
def name():
  return render_template('welcome.html')

@app.route('/welcome', methods=['POST'])
def welcome():
  input = []
  if request.method == 'POST':
    name_input = request.form
    #refreshes battle status to not_yet_battled
    g.conn.execute("UPDATE battle SET status='not_yet_battled' ")
    for key, value in name_input.iteritems():
      input.append(value)
    name = input[0]
    if len(name)<21 and len(name)>0:
      g.conn.execute("UPDATE player SET player_name=%s WHERE player_id='999'", name) #updates player name with input name
      return render_template('selectparty.html')
    else:
      return render_template('welcome.html')

@app.route('/view', methods=['POST', 'GET'])
def view():
  npc = []
  pokemon = []
  locations = []
  cursor = g.conn.execute("SELECT loc_name FROM locations")
  for l in cursor:
    locations.append(l)
  cursor = g.conn.execute("SELECT * FROM pokemon")
  for p in cursor:
    pokemon.append(p)
  cursor = g.conn.execute("SELECT npc_name FROM NPCs")
  for n in cursor:
    npc.append(n)
  return render_template('viewdata.html', npc=npc, pokemon=pokemon, locations=locations)

@app.route('/selectparty')
def selectparty():
  return render_template('selectparty.html')

@app.route('/result', methods=['POST', 'GET'])
def result():
  locations = []
  pokemon_ids = []
  if request.method == 'POST':
    form_result = request.form 
    for key, value in form_result.iteritems(): #iterate over dictionary
      cursor = g.conn.execute("SELECT P.pokemon_id FROM Pokemon P JOIN Ownedbyplayer O ON P.pokemon_id=O.pokemon_id WHERE O.player_id='999' AND P.pokemon_name=%s", value)
  
      for row in cursor:  # result is a row 
        pokemon_ids.append(row['pokemon_id'])
    #check for duplicate pokemon in party
    if pokemon_ids[0]==pokemon_ids[1] or pokemon_ids[1]==pokemon_ids[2] or pokemon_ids[0]==pokemon_ids[2]:
      return render_template('selectparty.html')
        #update the player_party table in database to reflect pokemon party selection
    g.conn.execute("UPDATE player_party SET pokemon_id1=%s, pokemon_id2=%s, pokemon_id3=%s WHERE player_id='999'", pokemon_ids)
    #get locations for location page
    cursor = g.conn.execute("SELECT loc_name FROM locations")
    for l in cursor:
      locations.append(l)
    cursor.close()
  return render_template("loc_battletype.html", result=result, locations=locations)

@app.route('/battle', methods=['POST', 'GET'])
def loc_battle():
  user_name = []
  wild_poke = []
  poke = []
  pokemon_encounter = []
  npcs = []
  npc_name = []
  npc_poke = []
  user_stat = 0
  poke_stat = 0
  npc_stat = 0
  battle_stat= 'loses'

  if request.method == 'POST':
    loc_battle = request.form
    result = []
    for key, value in loc_battle.iteritems():
      result.append(value)
    location = result[0]
    #get pokemon name, power and skills from player party 
    cursor = g.conn.execute("select p.pokemon_name, p.power, p.level, p.skills from player_party PP JOIN pokemon P ON PP.pokemon_id1=P.pokemon_id where PP.player_id='999'")
    for a in cursor:
      poke.append(a)
    cursor = g.conn.execute("select p.pokemon_name, p.power, p.level, p.skills from player_party PP JOIN pokemon P ON PP.pokemon_id2=P.pokemon_id where PP.player_id='999'")
    for b in cursor:
      poke.append(b)
    cursor = g.conn.execute("select p.pokemon_name, p.power, p.level, p.skills from player_party PP JOIN pokemon P ON PP.pokemon_id3=P.pokemon_id where PP.player_id='999'")
    for c in cursor:
      poke.append(c)
    
    user_stat = poke[0][1]+poke[1][1]+poke[2][1]+poke[0][2]+poke[1][2]+poke[2][2]

    #get player name
    cursor = g.conn.execute("select player_name from player where player_id='999'")
    for n in cursor:
      user_name.append(n)
    username = user_name[0]

    if result[1] == 'Pokemon':
      cursor = g.conn.execute("select pokemon_atlocation.pokemon_id from pokemon_atlocation where pokemon_atlocation.loc_name=%s", location)
      for i in cursor:
        pokemon_encounter.append(i)
      
      #code to pick random pokemon to battle in array
      random_poke = random.choice(pokemon_encounter)    
      cursor = g.conn.execute("select p.pokemon_name, p.power, p.level, p.skills from pokemon P where p.pokemon_id=%s", random_poke)
      for x in cursor:
        wild_poke.append(x)
      poke_stat = wild_poke[0][1]+wild_poke[0][2]
      if user_stat>=poke_stat:
        battle_stat= 'wins'
      cursor.close()
      return render_template('pokemonbattle.html', poke=poke, wild_poke=wild_poke, battle_stat=battle_stat, username=username)

    if result[1] == 'NPC':
      cursor = g.conn.execute("select npcs_atlocation.npc_id from npcs_atlocation where npcs_atlocation.loc_name=%s", location)
      for i in cursor:
        npcs.append(i)
      random_npc = random.choice(npcs)
      #get npc pokemon stats
      cursor = g.conn.execute("select p.pokemon_name, p.power, p.level, p.skills from ownedbynpc O JOIN pokemon P ON O.pokemon_id=P.pokemon_id where O.npc_id=%s", random_npc)
      for y in cursor:
        npc_poke.append(y)
      for i in range(0, len(npc_poke)):
        npc_stat += npc_poke[i][1]+npc_poke[i][2]
      #get npc name
      cursor = g.conn.execute("select party_name from npc_party where npc_id=%s", random_npc)
      for n in cursor:
        npc_name.append(n)
      npcname = npc_name[0]
      #update battle status in battle table
      if user_stat>=npc_stat:
        battle_stat= 'wins'
        g.conn.execute("UPDATE battle SET status='won' WHERE npc_id=%s AND player_id='999'", random_npc)
      if user_stat<npc_stat:
        g.conn.execute("UPDATE battle SET status='lost' WHERE npc_id=%s AND player_id='999'", random_npc)
      cursor.close()
      return render_template('npcbattle.html', poke=poke, npc_poke=npc_poke, battle_stat=battle_stat, username=username, npcname=npcname)
@app.route('/battle_history', methods=['POST', 'GET'])
def battle_history():
  battle_records = []
  cursor = g.conn.execute("select N.npc_name, B.status from battle B join npcs N on B.npc_id = N.npc_id where B.player_id = '999' AND B.status != 'not_yet_battled'")
  for a in cursor:
    battle_records.append(a)
  cursor.close()
  return render_template('battle_history.html', battle_records=battle_records)
################################################################################## 
# CODE ENDS HERE
################################################################################## 


  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  #context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  #return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test VALUES (NULL, ?)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
