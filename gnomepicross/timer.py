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

from threading import Thread, Event
from time import sleep

DEFAULT_PLAYTIME = 1800
DEFAULT_TIME_PENALTY = 120
DEFAULT_TIME_PENALTY_CAP = 480

class GameTimer(Thread):
	"""A generic periodic timer.

	Executes a callback every 'interval' times after 'delay' time.
	
	Note on PyGTK:
		
		If you want to use PeriodicTimer and PyGTK together, you 
		have to call gtk.gdk.threads_init() before you call 
		gtk.main_loop() to allow multiple threads to serialize 
		access to the Python interpreter.
	"""


	def __init__(
			self,
			playTime=DEFAULT_PLAYTIME,
			timePenalty=DEFAULT_TIME_PENALTY,
			delay=0,
			interval=1,
			callback=None,
			args=[],kwargs={}
	):
		"""Initializes the timer.

		Parameters:
		playTime	- Time to play (in seconds)
		timePenalty	- Applied when the user opens a wrong field
		delay		- Starting time after which the timer begins to
					  periodically execute the callback ( >= 0)
		interval	- Callback execution interval ( >= 0)
		callback	- The function to be run by the timer
		args,kwargs	- Arguments to the callback
		"""
		Thread.__init__(self)
		if delay < 0 or interval < 0 or playTime < 0 or timePenalty < 0: # interval can be zero?
			raise ValueError('delay, interval, playTime, and timePenalty must be greater than zero!')
		self.__delay = delay
		self.__interval = interval
		self.__callback = callback
		self.__args = args
		self.__kwargs = kwargs
		self.__finished = False
		self.__paused = False
		self.__restart = False
		self.__pause = Event()
		self.__timeLeft = self.__playTime = playTime
		self.__currentTimePenalty = self.__timePenalty = timePenalty

	def _debug_print(self):
		print 'time left: %s play time: %s' % self.getTimes()
		for row in self.__level:
			print row

	def pause(self):
		"""For suspending and resuming the timer.
		"""
		self.__paused = not self.__paused
		if self.__paused:
			self.__pause.clear()
		else:
			self.__pause.set()

	def cancel(self):
		"""Finish execution. 
		
		After this call, the timer has to be reinitialized if
		you want to use it again.
		"""
		self.__finished = True
	
	def applyPenalty(self):
		""" Apply time penalty if non-valid field clicked on board
		"""
		self.__timeLeft -= self.__currentTimePenalty
		self.__currentTimePenalty += self.__timePenalty
		if self.__currentTimePenalty > DEFAULT_TIME_PENALTY_CAP:
			self.__currentTimePenalty = DEFAULT_TIME_PENALTY_CAP
		if self.__timeLeft < 0: 
			self.__timeLeft = 0
			
	def getTimes(self):
		"""Returns the time left and the overall time
		"""
		return self.__timeLeft, self.__playTime
	
	def setPlayTime(self, playTime):
		self.__timeLeft = self.__playTime = playTime
	
	def isPaused(self):
		return self.__paused
			
	def restart(self):
		"""Restart the timer.
		
		Used for reseting the timer for new game
		"""
		self.__restart = True
		if self.__paused:
			self.__pause.set()
		
	def run(self):
		sleep(self.__delay)
		self.__pause.set()
		while not self.__finished:
			if self.__restart:
				self.__timeLeft = self.__playTime
				self.__restart = False
			self.__pause.wait()
			self.__callback()
			sleep(self.__interval)
			self.__timeLeft -= self.__interval
