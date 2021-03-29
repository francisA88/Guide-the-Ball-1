import kivy

'''Made by Francis Ali. Check out my profile at https://github.com/francisA88'''


import sys
if sys.version_info[:2] not in [(3,6), (3,7)]:
	raise Exception('This game is only tested with 3.7, should work with 3.6, but not working on later or earlier versions of Python.')

from kivy.app import App
#from kivy.core.window import Window
#from kivy.graphics import *
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition, FadeTransition
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.factory import Factory
#from kivy.uix.widget import Widget
from kivy.properties import *
from kivy.event import EventDispatcher
#from kivy.animation import Animation
from kivy.core.audio import SoundLoader

#from pymupnk import *
import os
#from math import ceil
from gamelogic import Game, deepcopy, db, win as Window

#Checking if game is running in Pydroid 3
if os.access('/data/user/0/ru.iiec.pydroid3/lib/libpydr.so', os.R_OK):
	Window.rotation = -90
###
#Meant for non-mobiles only
if kivy.platform.lower() != "android":
	Window.size = 740, 480
		
class MainManager(ScreenManager):
	def __init__(self, *args, **kws):
		super().__init__(*args, **kws)
		self.add_widget(Factory.StartScreen())
		self.add_widget(Factory.InGameScreen())
		self.add_widget(Factory.PauseMenu())
		self.add_widget(Factory.Menu())
		self.add_widget(Factory.LevelsPanel())
		self.add_widget(Factory.SettingsScreen())

def resize(e, texture):
	#print(dir(texture))
	if texture:
		e.width = texture.width+5

#Load all the layouts{
Builder.load_file(os.path.join("kvfiles", "_header.kv"))
for file in os.listdir("kvfiles"):
	if "_header" not in file:
		Builder.load_file(os.path.join("kvfiles", file))
#}#
def getscreen(mngr, name):
	for s in mngr.screens:
		if s.name == name:
			return s

#Code's a little bit hacky though since i had to find solutions to some major bugs, which was really tiring.
class NGame(Game):
	app = None
	def on_ball_entered_tunnel(self, e):
		super().on_ball_entered_tunnel(e)
		self.app.failSuccess("success")
		self.app.resetStuff()
		
	def on_ball_off_screen(self, ball):
		super().on_ball_off_screen(ball)
		self.app.failSuccess("fail")
		self.app.resetStuff()
		
_ = os.path.join
fail_sound = SoundLoader.load(_('res','fail.mp3'))
pass_sound = SoundLoader.load(_('res','pass.mp3'))

class MainActivity(App):
 #set to a max_score for a particular level
	ballname = StringProperty(db.getCurrentBall())
	current_level = 1
	_highscore = db.getHighscoreForLevel(current_level)
	highscore = NumericProperty(_highscore) #set to a highscore for a particular level
	_timeleft = db.getTimeMaxLimitForLevel(current_level)
	timeleft = NumericProperty(_timeleft)
	_max_time = db.getTimeMaxLimitForLevel(current_level)
	max_time = NumericProperty(_max_time) #set to max_time for a particular level
	score= NumericProperty(6000 if _timeleft <15 else 7000 if 15<=_timeleft <21 else 8000)
	unlocked_lvls = ListProperty(list(range(1,db.getLastUnlockedLevel()+1)))
	db = db
		
	def build(self):
		self.mm = MainManager()
		for sc in self.mm.screens:
			pass
		#mm.current = "pm"
		scr_names = ['main-menu','levels', 'igs', 'pm']
		#Open the exit confirmation when window requests to be closed (back button on Android)
		#This callback basically does some screen switching when the back or close button is pressed until it gets to the main screen which then shows an exit confirmation.
		def callback_for_close(*args, **kws):
			cur_screen = self.mm.current
			if cur_screen == 'start': return True
			elif cur_screen == 'settings':
				self.mm.current = 'main-menu'
			else:
				i = scr_names.index(cur_screen)
				if self.mm.current == 'igs':
					self.game.is_paused = True
				if i==0:
					Factory.ExitConf().open()
				else:
					self.mm.current = scr_names[i-1]
			return True
			
		Window.on_request_close = callback_for_close
		
		self.igsscreen = [sc for sc in self.mm.screens if sc.name=="igs"][0]
		ftr = FadeTransition()
		self.mm.transition = ftr
		self.mm.current = "start"
		return self.mm
		
	def initGame(self, lvl=1):
		self.game = NGame((0, -1600), self.igsscreen)
		self.game.app = self
		
	def on_start(self):
		self.mm.current = "start"
		#self.gameloop.start()
		sscr = getscreen(self.mm, "start")
		lvlscr = getscreen(self.mm, "levels")
		#self.game = Game((0, -1200), self.igsscreen, (150 if Window.height>590 else 100))
		self.initGame()
		#Clock.schedule_interval(lambda x:x, 1)
		def loading(dt):
			sscr.loading_ind_angle +=5
		ev = Clock.schedule_interval(loading, .05)
		def cancel_and_start(dt):
			ev.cancel()
			self.mm.current = "main-menu"
		Clock.schedule_once(cancel_and_start, 8.4)
	
	def isLevelDisabled(self, lvl:str):
		return db.getLastUnlockedLevel()<int(lvl if lvl else "1")
		
	def on_pause(self):
		if self.mm.current =="igs" and not self.game.is_paused:
			self.mm.current = "pm"
			self.game.is_paused = True
		return True
	
	def restore_play_btn(self):
		self.igsscreen.ids.playbtn.disabled = False
	def resetStuff(self):
		try:
			self.updsc.cancel()
			self.updtl.cancel()
		except AttributeError: pass
		self._timeleft = db.getTimeMaxLimitForLevel(self.current_level)
		self.timeleft = self._timeleft
		self.score = 6000 if self._timeleft <15 else 7000 if 15<=self._timeleft <21 else 8000
		
	def update_scores(self):
		def __update_time_left(dt):
			if self.game.is_paused: return
			self.timeleft -=1
			#print(self.max_time)
			#if self.timeleft == 0: self.game.is_paused = True
			if self.timeleft == 0:
				self.failSuccess()
				self.game.is_paused = True
				return False
		def __update_score(dt):
			if self.game.is_paused: return
			if self.timeleft == 0: return False
			self.score -=1
		self.updtl = Clock.schedule_interval(__update_time_left, 1)
		self.updsc = Clock.schedule_interval(__update_score, .09)
		
	def failSuccess(self, passfail="fail"):
		if passfail == "fail":
			Factory.LosePopup().open()
			if fail_sound: fail_sound.play()
			return 
		elif passfail == "success":
			Factory.WinPopup().open()
			if pass_sound: pass_sound.play()
			#print(db.getLastUnlockedLevel(), self.current_level)
			if db.getLastUnlockedLevel() == self.current_level and not db.getLastUnlockedLevel()==db.getTotalLevels():
				db.addNewLevel(self.current_level+1)
			db.addScore(self.current_level, self.score)
			self.unlocked_lvls.append(self.current_level+1)
		#db.addScore
			
if __name__ == '__main__':
	MainActivity().run()