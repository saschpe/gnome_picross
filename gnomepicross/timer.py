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

from threading import Thread
from time import sleep



class PeriodicTimer(Thread):
	"""A generic periodic timer.

	Executes a callback every 'interval' times after 'delay' time.
	
	Note on PyGTK:
		
		If you want to use PeriodicTimer and PyGTK together, you 
		have to call gtk.gdk.threads_init() before you call 
		gtk.main_loop() to allow multiple threads to serialize 
		access to the Python interpreter.
	"""


	def __init__(self,delay=0,interval=1,callback=None,args=[],kwargs={}):
		"""Initializes the timer.

		Parameters:
		delay		- Starting time after which the timer beginns to
					  periodically execute the callback ( >= 0)
		interval	- Callback execution intervall ( >= 0)
		callback	- The function to be run by the timer
		args,kwargs	- Arguments to the callback
		"""
		Thread.__init__(self)
		if delay < 0 or interval < 0:
			raise ValueError('Delay and interval must be greater than zero!')
		self.__delay = delay
		self.__interval = interval
		self.__callback = callback
		self.__args = args
		self.__kwargs = kwargs
		self.__finished = False
		self.__paused = False
		self.setDaemon(True)

	def pause(self):
		"""For suspending and resuming the timer.
		"""
		self.__paused = not self.__paused

	def cancel(self):
		"""Finish execution. 
		
		After this call, the timer has to be reinitialized if
		you want to use it again.
		"""
		self.__finished = True

	def run(self):
		sleep(self.__delay)
		while not self.__finished:
			if not self.__paused:
				if self.__callback:
					self.__callback(*self.__args,**self.__kwargs)
				sleep(self.__interval-1)
			sleep(1)
