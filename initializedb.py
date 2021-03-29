import sqlite3 as sql
import os

conn = sql.connect("game.db")
c = conn.cursor()
#c.execute('''
#CREATE TABLE balls(
#	name text,
#	mass INT,
#	friction DECIMAL,
#	src text,
#	bounciness DECIMAL
#)
#''')
#c.execute('''
#CREATE TABLE scores(score INT)''')
#c.execute('''CREATE TABLE scoresforlevel(level INT NOT NULL)''')
#c.execute('''CREATE TABLE unlockedLevels(level INT)''')
from os.path import join as _
ball_mappings ={
	"hexastar":{
		'src':  _("res","ball_hexastar.jpeg"),
		'mass': 50,
		'friction': .9,
		'elasticity': 1.1
	},
	"spiky":{
		'src': _('res','ball_star_double.png'),
		'mass': 40,
		'friction': 1.4,
		'elasticity': .9
	},
	"recycle":{
		'src': _('res','ball_arrow_rotate.jpg'),
		'mass': 100,
		'friction': .7,
		'elasticity': 1.2
	},
	"more-spiky":{
		'src': _('res','ball_star_multiple_red.png'),
		'mass': 60,
		'friction': 1.9,
		'elasticity': .7
	},
	'glow-green':{
		'src': _('res', 'glow_green.png'),
		'mass': 50,
		'friction': 1.2,
		'elasticity': 1.3
	},
	'glow-purple':{
		'src': _('res', 'glow_purple.png'),
		'mass': 60,
		'friction': 1.2,
		'elasticity': 1.3
	}
}
#name, mass, friction, src, bounciness
#c.execute("DELETE FROM balls")
#conn.commit()
def addBallToDB():
	for b in ball_mappings:
		name = b
		bm = ball_mappings
		mass = bm[b]["mass"]
		friction = bm[b]['friction']
		src = bm[b]['src']
		bounciness = bm[b]['elasticity']
		values = f"({mass}, {friction}, '{src}', {bounciness}, '{name}')"
		vals = [name, mass, friction, src, bounciness]
		c.execute("INSERT INTO Balls (name,mass, friction, src, bounciness) values (?,?,?,?,?)",vals)
		conn.commit()
		
#addBallToDB()
c.execute("select * from unlockedLevels")
#c.execute("create table unlockedLevels(l1)")
#c.execute("CREATE TABLE level_scores(l1)")
#c.execute("CREATE TABLE max_times_for_levels(level INT, max_time INT)")
mt = [[2, 25], [1, 20], [3, 8], [4,12], [16, 20], [5, 9], [6, 16], [7, 12], [8, 15], [9, 10], [10, 10], [11, 11], [12, 26], [13, 11], [14, 20], [15, 12], [17, 20], [18, 14], [19, 20]]
#uncomment following lines of code to update the levels available. Current number of levels is 18
################
c.execute("DELETE FROM max_times_for_levels")
conn.commit()
for li in mt:
	c.execute("INSERT INTO max_times_for_levels (level, max_time) values (?,?)", li)
	conn.commit()
##############
#conn.commit()
c.close()