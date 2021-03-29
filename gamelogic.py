from kivy.clock import Clock
from kivy.graphics import *
from os.path import join as _
from kivy.core.window import Window as win
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.utils import get_color_from_hex

from copy import deepcopy
from random import random
import dbOps as db

ball_mappings = {}
for ball in db.getBalls():
	ball_mappings[ball] = db.getBallInfo(ball)
	
BASE_COLOR = get_color_from_hex("#CC1414")

sound = SoundLoader.load("./res/thud1.mp3")
sound.volume = 1
print(sound.state)

class Circle(Ellipse):
	def __init__(self, radius, **kws):
		super().__init__(**kws)
		self.size = [radius*2]*2
	@property
	def center(self):
		x, y = self.pos
		w, h = self.size
		return x+w//2, y+h//2
	@center.setter
	def center(self, val):
		x, y = val
		w, h = self.size
		self.pos = x-w/2, y-h/2

bodies_and_balls = [None]

class Game:
	pymunk_loaded = False
	#is_paused = False
	#current_ball_src = "res/ball_hexastar.jpeg"
#	current_ball_name = "hexastar"
	def imp_pymunk(self):
		import threading
		def cb():
			global pymunk, PCircle
			import pymunk
			###An extension of pymunk.Circle to suit my needs
			class PCircle(pymunk.Circle):
				hasJustPreviouslyCollided = False
				
			self.pymunk_loaded ^=1
			self.space = pymunk.Space()
			self.space.gravity = self.gravity
			base_line = pymunk.Segment(self.space.static_body, (0,50), (3000, 50), 1)
			base_line.friction = 1
			base_line.elasticity = .7
			tunnel_seg_body1 = pymunk.Segment(self.space.static_body, (60,50), (60,100), 1)
			tunnel_seg_body1.friction = 1
			tunnel_seg_body1.elasticity = .7
			tunnel_seg_body2 = pymunk.Segment(self.space.static_body, (60,100), (160,100), 1)
			tunnel_seg_body2.friction =1.
			tunnel_seg_body2.elasticity = .7
			tunnel_seg_body3 = pymunk.Segment(self.space.static_body, (160, 100), (160, 50), 1)
			tunnel_seg_body3.friction = 1
			tunnel_seg_body3.elasticity = .7
			self.space.add(base_line, tunnel_seg_body1, tunnel_seg_body2, tunnel_seg_body3)
			'''Adding some more segments to prevent the ball from blocking the "play" and "undo" buttons'''
			_segs =[pymunk.Segment(self.space.static_body, (win.width-20,50), (win.width-20,80), 1),
				pymunk.Segment(self.space.static_body, (win.width-20,80), (win.width-148,80), 1),
				pymunk.Segment(self.space.static_body, (win.width-148,80), (win.width-148, 50), 1)]
			def f(x):
				x.friction= 1
				x.elasticity = .5
			[f(s) for s in _segs]
			self.space.add(*_segs)
			#self.init_level(self.lvl)
			self.on_pymunk_loaded()
		#Clock.schedule_once(cb)
		threading.Thread(target=cb).start()
		
	def __init__(self, gravity, screen, ):#lvl=1):
		self.gravity = gravity
		#self.lvl = lvl
		self.imp_pymunk()
		self.screen = screen
		self.terminate_update = False
		self.last_touch = None
		self.has_spawned_ball = False
		self.is_paused = False
		self.rc= RenderContext(use_parent_projection=True)
		self.d_line = Line(source=_('res','line_texture.png'), width=2, points=[])
		self.rc.add(self.d_line)
		self.screen.canvas.after.add(self.rc)
		#self.lines = [self.d_line]
		self.lines = [self.rc]
		self.lines_dict = {self.rc: []}
		self.screen.on_touch_move = self.drawline
		self.screen.on_touch_up = self.create_new_line
		self.obst_segs = []
		self.obst_lines = []
		self._start_update()
		
	def _start_update(self):
		self.updater = Clock.schedule_interval(self.update, 1/60)
		
	def create_new_line(self, touch):
		self.last_touch = None
		self.rc = RenderContext(use_parent_projection=True,use_parent_modelview=True)
		self.rc.add(Color(*BASE_COLOR))
		self.d_line = Line(source=_('res','line_texture.png'), width=2, points=[])
		self.rc.add(self.d_line)
		self.screen.canvas.after.add(self.rc)
			
	def drawline(self, touch):
	#print("here")
		if self.is_paused or self.terminate_update: return 
		if not self.has_spawned_ball: return
		if not self.pymunk_loaded: return
		#if self.d_line not in self.lines:
		if self.rc not in self.lines:
			#self.lines.append(self.d_line)
			self.lines.append(self.rc)
		#if self.d_line not in self.lines_dict:
		if self.rc not in self.lines_dict:
			#self.lines_dict.update({self.d_line:[]})
			self.lines_dict.update({self.rc:[]})
		#global last_touch
		if self.last_touch:
			self.d_line.points = self.d_line.points+list(touch.pos)
			if (len(self.d_line.points)>=4):
				p = self.d_line.points
				seg = pymunk.Segment(self.space.static_body, p[-4:-2], p[-2:], 0.5)
				seg.friction = .9
				seg.elasticity = .5
				self.space.add(seg)
				#self.lines_dict[self.d_line].append(seg)
				self.lines_dict[self.rc].append(seg)
		self.last_touch = touch.pos
	
	def clear_prev_line(self):
		'''Clears the last line that was created'''
		if self.lines:
			#Remove the line from the canvas
			self.screen.canvas.after.remove(self.lines[-1])
			for seg in self.lines_dict[self.lines[-1]]:
				self.space.remove(seg)
			del self.lines_dict[self.lines[-1]]
			del self.lines[-1]
	
	def update(self, dt):
		if not bodies_and_balls: return
		if bodies_and_balls[0] == None: return
		ball, body, shape, rot, canv,c = bodies_and_balls[-1]
		if self.is_paused: return
				#Checks if the ball is on the tunnel ± 2x, +(0-2)y
		if ball.center[0] > 108 and ball.center[0] < 112:
			if ball.center[1] >=135 and ball.center[1]<=138:
				an = Animation(a=0, duration=.7)
				an.start(c)
						#Animation(a=0, duration=.6).start(c)
				an.on_complete = self.on_ball_entered_tunnel
				#self.space.remove(body, shape)
				#self.screen.canvas.before.remove(canv)
				return False
				#Checks if ball has gone off screen
		if not(0 < ball.center[0] <win.width ) or not(0 < ball.center[1] < win.height):
			self.on_ball_off_screen(ball)
			#return False
		ball.center = list(body.position)
		rot.origin = ball.center
		rot.angle = body.angle* 57.293
		
		#####Doing some sound playing on ball's impact with a line###
		if bodies_and_balls[0]:
			ball = bodies_and_balls[0][0]
			circle = bodies_and_balls[0][2]
			query = self.space.point_query(ball.center, (ball.size[0]/2)+2, circle.filter)
			sp_query = filter(lambda q: isinstance(q.shape, pymunk.Segment), query)
			
			if list(sp_query):
					#if it just finished a collision, then it must be rolling along a surface and i definitely do not want the "impact" sound playing when it's rolling but only on impact
				if not query[0].shape.hasJustPreviouslyCollided:
					#sound.volume = 1.5
					sound.play()
				if isinstance(query[0].shape, PCircle):
					query[0].shape.hasJustPreviouslyCollided = True
			else:
				query[0].shape.hasJustPreviouslyCollided = False
			########
			
			self.space.step(.01)
				#return False
		
	def addBall(self, name):
		'''Must be called only when Game.pymunk_loaded == True'''
		#if self.is_paused: return
		#print(bodies_and_balls)
		self.has_spawned_ball = True
		mass = ball_mappings[name]['mass']
		radius = 35
		i_pos = self.screen.right -radius*2+20, self.screen.height -200
		mom = pymunk.moment_for_circle(mass, radius, 0)
		body = pymunk.Body(mass, mom)
		body.position = i_pos
		shape = PCircle(body, radius)
		shape.elasticity = ball_mappings[name]['elasticity']
		shape.friction = ball_mappings[name]['friction']
		self.space.add(body, shape)
		ball_canv = RenderContext(use_parent_projection=True, use_parent_modelview=True)
		c = Color(1,1,1,1)
		ball = Circle(radius=radius, source=ball_mappings[name]['src'])
		ball.center = i_pos
		ball_canv.add(c)
		ball_canv.add(ball)
		before = self.screen.canvas.before
		before.add(PushMatrix())
		rot = Rotate(1,1,0)
		before.add(rot)
		before.add(ball_canv)
		before.add(PopMatrix())
		bodies_and_balls[0]=[ball, body, shape, rot, ball_canv, c]
		#######
	def on_pymunk_loaded(self):
		pass
	
	def on_ball_entered_tunnel(self, e):
		self.has_spawned_ball = False
		
	def on_ball_off_screen(self, ball):
		'''Should be called when the ball goes off drawing area'''
		self.has_spawned_ball = False
		ball, body, shape, rot, canv = bodies_and_balls[-1][:-1]
		self.screen.canvas.before.remove(canv)
		self.space.remove(shape, body)
		bodies_and_balls[0] = None
		#self.addBall("hexastar")
	
	def clear_all_lines(self):
		for rc in self.lines:
			self.screen.canvas.after.remove(rc)
			for seg in self.lines_dict[rc]:
				'''Removes all segments associated with a graphical line'''
				self.space.remove(seg) 
		del self.lines[:] #clear the self.lines list
		self.lines_dict.clear()
	
	def fetch_obst_for_level(self, lvl):
		def getObstFromData(path, lvl):
			d = {}
			for line in open(path).read().splitlines():
				n, data = line.replace(" ","").split(":")
				#print(len(data))
				d.update({int(n):list(eval(data))})
			return d[lvl]
		#obst = deepcopy(__import__('obstacles').obstacles[lvl])
		obst = deepcopy(getObstFromData("obst.txt", lvl))
		for i in range(len(obst)):
			obst[i][0] *=win.width
			obst[i][1] *=win.height
		return obst
		
	def clear_any_obstacles(self):
		#This clears any previous obstacles
		for s in self.obst_segs: self.space.remove(s)
			#If self has attribute "obst_segs" then i assume it also has "obst_lines"
		for l in self.obst_lines: self.screen.canvas.after.remove(l)
		self.obst_segs.clear()
		self.obst_lines.clear()
		####
	def draw_obstacles(self, lvl):
		#####
		with self.screen.canvas.after:
			obst = self.fetch_obst_for_level(lvl)
			for i in range(0,len(obst), 2):
				p1 = obst[i]
				p2 = obst[i+1]
				l = Line(points=[*p1, *p2], width=2)
				seg = pymunk.Segment(self.space.static_body, p1, p2, 1)
				seg.friction = 1
				seg.elasticity = random()+.2
				self.space.add(seg)
				self.obst_segs.append(seg)
				self.obst_lines.append(l)
				
	def remove_ball(self):
		if bodies_and_balls[0]:
			ball, body, shape, rot, canv = bodies_and_balls[-1][:-1]
			self.screen.canvas.before.remove(canv)
			self.space.remove(body, shape)
			bodies_and_balls[0] = None
			
	def init_level(self, level):
		self.clear_any_obstacles()
		self.clear_all_lines()
		self.remove_ball()
		self.draw_obstacles(level)
		self.updater.cancel()
		self.is_paused = False
		self._start_update()