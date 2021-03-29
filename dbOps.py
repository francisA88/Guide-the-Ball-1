import sqlite3

#complete all function definitions here
dbfile = "game.db"

conn = sqlite3.connect(dbfile)
cur = conn.cursor()

def getHighscoreForLevel(level:int):
	scores = cur.execute(f'SELECT l{level} from level_scores')
	scoresl = [x[0] for x in scores.fetchall()]
	if scoresl: return max(scoresl)
	return 0

def addScore(level:int, score:int):
	cur.execute('INSERT INTO level_scores (l%s) values (?)'%level, [score])
	conn.commit()
	
def setHighscoreForLevel(val, level:int):
	'''Might not need this one after all'''

def addNewLevel(lvl:int):
	'''Meant to be called when a player completes a level and the next one needs to be unlocked.'''
	cur.execute(f'ALTER TABLE level_scores ADD COLUMN l{lvl} NOT NULL DEFAULT 0')
	conn.commit()
	#cur.execute(f'UPDATE level_scores SET l{lvl}=0')
	#conn.commit()	
	setLastUnlockedLevel(lvl)
		
def getLastCurrentScore():
	'''Should get the last current score. Useful in retrieving previous states such that a player can continue where the player left off.
	May decide to omit this feature later.'''
	...
def getLastState():
	'''Retrieves last state of game.
	May omit this feature'''
	...

def setCurrentBall(name='hexastar'):
	cur.execute("DELETE FROM curball")
	conn.commit()
	cur.execute("INSERT INTO curball (name) values (?)", [name])
	conn.commit()
	
def getCurrentBall():
	stmt = cur.execute("SELECT name FROM curball")
	return stmt.fetchall()[-1][0]
	
def getBalls():
	stmt = cur.execute("SELECT name from balls")
	return [i[0] for i in stmt.fetchall()]
	
def getBallInfo(name):
	'''Should return src, mass, friction, and bounciness (elasticity) for a ball of given name in form of 
		{
		"src": src,
		...
		}'''
	return dict(zip(['src','mass','friction','elasticity'],cur.execute("SELECT src,mass,friction,bounciness from Balls where 	name=?",[name]).fetchall()[0]))
	
def setLastUnlockedLevel(level:int):
	'''Sets the last unlocked level. All levels after this level is to remain locked.'''
	cur.execute('INSERT INTO unlockedLevels (level) values (?)', [level])
	conn.commit()
	
def getLastUnlockedLevel():
	c = cur.execute('SELECT level from unlockedLevels')
	return c.fetchall()[-1][0]
	
def _addNewLevel(level, obst:list):
	'''Must not be used in-game. This function is meant for me, the developer for adding new levels in future.'''
	#::param `obst`: A list of 2 item lists each containing coordinates x,y of line segments for obstacles.

def getTimeMaxLimitForLevel(level:int):
	stmt = cur.execute("SELECT max_time FROM max_times_for_levels WHERE level=?",[level])
	return stmt.fetchall()[0][0]
	
def getTotalLevels() ->int:
	#Fetches the total number of levels that I have made for this game!
	stmt = cur.execute("SELECT level FROM max_times_for_levels")
	return list(map(lambda x:x[0],stmt.fetchall()))[-1]
	
def clearData():
	cur.execute("DELETE FROM unlockedlevels")
	conn.commit()
	cur.execute("INSERT INTO unlockedlevels (level) values (1)")
	conn.commit()
	cur.execute("DROP TABLE level_scores")
	conn.commit()
	cur.execute("CREATE TABLE level_scores (l1 NOT NULL DEFAULT 0)")
	conn.commit()
	cur.execute("DELETE FROM curball WHERE rowid IS NOT 1")
	conn.commit()
	
if __name__=='__main__':
	print(getBallInfo("hexastar"))
	print(getLastUnlockedLevel())
	print(getTimeMaxLimitForLevel(1))
	print(getHighscoreForLevel(2))
	print(getTotalLevels())