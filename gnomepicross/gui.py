#!/usr/bin/env python
#
# Copyright (C) 2007 Sascha Peilicke <sasch.pe@gmx.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
#

import sys
try:
	import gtk,gtk.glade
	import gobject,pango
	import gnome,gnome.ui
	from gtk import gdk				# gtk.gdk.* looks ugly
except:
	print 'Error: You do not have PyGTK-2 or Glade2 properly installed.'
	print '       This application will not run without it.'
	sys.exit(1)

from game import *
from timer import *

# CONSTANTS
APP_NAME = 'GnomePicross'
APP_VERSION = '0.2'
FOLDER_DATA = './data/'
FOLDER_IMAGES = './images/'



class Gui(object):
	"""The GNOME Graphical User Interface to the paint by numbers game.
	"""

	def __init__(self):
		gnome.program_init(APP_NAME,APP_VERSION)
		# Create widget tree for the GUI and signal handlers
		self.__window = gtk.glade.XML('glade/window.glade','window')
		self.__window.signal_autoconnect(
			{
				'on_window_destroy'	: self.on_window_destroy,
				'on_new_activate'	: self.on_new_activate,
				'on_open_activate'	: self.on_open_activate,
				'on_pause_activate'	: self.on_pause_activate,
				'on_clear_activate'	: self.on_clear_activate,
				'on_prefs_activate' : self.on_prefs_activate,
				'on_about_activate'	: self.on_about_activate,
				'on_button_press_event'	: self.on_button_press_event,
			})
		# Save some pointers to specifig gui widgets
		self.__board = self.__window.get_widget('board')
		#for b in self.__board.get_children():
		#	b.modify_fg(gtk.STATE_INSENSITIVE,gdk.Color(60255,255,6660))
		self.__rowHints = self.__window.get_widget('rowHints')
		self.__colHints = self.__window.get_widget('columnHints')
		self.__level = self.__window.get_widget('level')
		self.__timeLeft = self.__window.get_widget('timeLeft')
		
		self.__desiredSkill = SKILL_MEDIUM
		self.__desiredPlayTime = 1800
		self.__gameOver = False
		self.__prefs_change = False
		
		# This will store the picross game
		self.__game = None
		self.__board.set_sensitive(False)
		self.__timer = GameTimer(delay=1,callback=self.__timerCallback)
		self.__timer.setDaemon(True)
		# Start the gtk main event loop and allow multiple threads to 
		# serialize access to the Python interpreter
		
		gdk.threads_init()
		#self.__timer.start()
		gtk.main()


	def __timerCallback(self):
		"""Periodically updates time bar and checks some game conditions.
		"""
		
		timeleft, playtime  = self.__timer.getTimes()
		if timeleft <= 0 or self.__game.isGameWon():
			self.__gameOver = True
			self.__board.set_sensitive(False)
			if not self.__game.isGameWon():
				self.__timeLeft.set_fraction(0)
				self.__timeLeft.set_text('0:0')
				print "lose"
			self.__timer.pause()
		else:
			self.__timeLeft.set_fraction(timeleft / float(playtime))
			self.__timeLeft.set_text('%s:%s' % (int(timeleft / 60),int(timeleft % 60)))

	#
	# Visibility manipulation methods
	#

	def __setBoardSize(self,size):
		"""Changes the dimensions of the board to (sizeXsize).
		It also adjusts column and row hints.

		Params:
			size	- The dimension of the boad (sizeXsize)
		"""
		if size < 1 and size > 15:
			raise ValueError,'Illegal size value'
		for i in range(15):
			if i < size:
				self.__setRowVisibility(i,True)
				self.__setColVisibility(i,True)
			else:
				self.__setRowVisibility(i,False)
				self.__setColVisibility(i,False)


	def __setRowVisibility(self,row,visible):
		"""Sets a specific row's visibility.

		Params:
			row		- The row to change
			visible	- True or False
		"""
		if row < 0 and row > 14:
			raise ValueError,'Illegal row value'
		if visible:	
			self.__rowHints.get_children()[row].show()
			start,stop = row * 15, row * 15 + 15
			for b in self.__board.get_children()[start:stop]:
				b.show()				
		else:		
			self.__rowHints.get_children()[row].hide()
			start,stop = row * 15, row * 15 + 15
			for b in self.__board.get_children()[start:stop]:
				b.hide()				

	
	def __setColVisibility(self,col,visible):
		"""Sets a specific column's visibility.

		Params:
			col		- The column to change
			visible	- True or False
		"""
		if col < 0 and col > 14:
			raise ValueError,'Illegal column value'
		if visible:	
			self.__colHints.get_children()[col].show()
			i = 0
			for b in self.__board.get_children():
				if i % 15 == col: 
					b.show()
				i += 1
		else:		
			self.__colHints.get_children()[col].hide()
			i = 0
			for b in self.__board.get_children():
				if i % 15 == col: 
					b.hide()
				i += 1

	
	def __clearBoard(self):
		"""Sets every button on the board to it's initial state.
		"""
		self.__board.set_sensitive(True)
		for b in self.__board.get_children():
			b.set_sensitive(True)
			b.set_label('')


	#
	# Debug methods
	#

	def _debug_enumerateElements(self):
		i = 0
		for b in self.__board.get_children():
			b.set_label(str(i));i += 1
		i = 0
		for r in self.__rowHints.get_children():
			r.set_label(str(i));i += 1
		i = 0
		for c in self.__colHints.get_children():
			c.set_label(str(i));i += 1


	#
	# Event handler callbacks
	#

	def on_button_press_event(self,widget,event=None):
		"""Called when the user presses a button on the board.
		"""
		if self.__game:
			row,col = widget.name.split('_')[1:]
			row,col = int(row),int(col)
			
			if event.button == 1: 	# Left mouse button
				if self.__game.openField(col,row):
					widget.set_label('')
					widget.set_sensitive(False)
				else: self.__timer.applyPenalty()
			elif event.button == 3:	# Right mouse button
				state = self.__game.markField(col,row)
				if state == FIELD_MARKED_INVALID or state == FIELD_MARKED_VALID:
					widget.set_label('X')
				else:
					widget.set_label('')

	def on_window_destroy(self,widget,event=None):
		"""Called when the user wants to quit the app.
		"""
		gtk.main_quit()
		
	def on_new_activate(self,widget,event=None):
		"""Called when the user starts a new game.
		"""
		
		if self.__prefs_change:
			self.__timer.setPlayTime(self.__desiredPlayTime)
		if self.__timer.isAlive():
			self.__timer.restart()
		else:
			self.__timer.start()
			
		self.__game = Game(skill=self.__desiredSkill)
		
		name,skill,size = self.__game.getInfo()

		self.__setBoardSize(size)
		self.__level.set_label(name)
		self.__clearBoard()

		# Update the hints for rows and columns
		for i in xrange(size):
			r = self.__rowHints.get_children()[i]
			tmp = str(self.__game.getRowHint(i)).replace(',','')
			r.set_label(tmp[1:-1])
		for i in xrange(size):
			c = self.__colHints.get_children()[i]
			tmp = str(self.__game.getColumnHint(i)).replace(', ','\n')
			c.set_label(tmp[1:-1])


	def on_open_activate(self,widget,event=None):
		# show file select dialog 
		print "on_open"

	
	def on_pause_activate(self,widget,event=None):
		"""Called when the user presses the pause button.
		"""
		if self.__timer.isAlive() and not self.__gameOver:
			self.__timer.pause()
			if self.__timer.isPaused():
				self.__board.set_sensitive(False)
			else:
				self.__board.set_sensitive(True)


	def on_clear_activate(self,widget,event=None):
		if self.__game:
			self.__game.restart()
			self.__clearBoard()

	
	def on_prefs_activate(self,widget,event=None):
		"""Displays the preferences dialog.
		"""
		wt = gtk.glade.XML('glade/prefs.glade','prefs')
		prefs = wt.get_widget('prefs')
		wt.get_widget('timeScale').set_value(self.__desiredPlayTime/60)
		if self.__desiredSkill == SKILL_EASY:
			wt.get_widget('easy').set_active(True)
		elif self.__desiredSkill == SKILL_MEDIUM:
			wt.get_widget('medium').set_active(True)
		elif self.__desiredSkill == SKILL_HARD:
			wt.get_widget('hard').set_active(True)
		result = prefs.run()
		if(result == 1):
			self.__desiredPlayTime = wt.get_widget('timeScale').get_value()*60
			if wt.get_widget('easy').get_active():
				self.__desiredSkill = SKILL_EASY
			elif wt.get_widget('medium').get_active():
				self.__desiredSkill = SKILL_MEDIUM
			elif wt.get_widget('hard').get_active():
				self.__desiredSkill = SKILL_HARD
		self.__prefs_change = True
		prefs.destroy()


	def on_about_activate(self,widget,event=None):
		about = gnome.ui.About(APP_NAME,APP_VERSION,
			'(C) 2007 Sascha Peilicke',
			'A simple paint by numbers game.',
			['Sascha Peilicke <sasch.pe@gmx.de>', 'Tvrtko Majstorovic <tvrtkom@gmail.com>'],
			None,
			u'Sascha Peilicke <sasch.pe@gmx.de>',
			gdk.pixbuf_new_from_file(FOLDER_IMAGES+'picross_64x64.png'))
		about.show()
