#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Installer
#  installer module: bootloader configuration and installation
#
# Copyright 2004-2011 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

#
# Results of previous modules are placed in self.all_results (dictionary)
# Results of this module need to be stored in the dictionary self.result (variablename:value[,value1,value2])
#

import objects, re, inspect
from objects import *
from local import _

import os

class object(content):
	def __init__(self, max_y, max_x, last, file, cmdline):
		self.guessed = {}
		content.__init__(self, max_y, max_x, last, file, cmdline)
		self.auto_input_enabled = True
		self.max_length = 1

	def debug(self, txt):
		info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
		line = info[1]
		content.debug(self, 'BOOTLOADER:%d: %s' % (line,txt))

	def checkname(self):
		return ['bootloader_device']

	def modvars(self):
		return ['bootloader_device']

	def profile_complete(self):
		if self.check('bootloader_device'):
			return False
		return bool(self.all_results.get('bootloader_device'))

	def auto_input(self):
		# Return "next" (== F12) and disable auto_input() function.
		# This way, only one F12 keypress will be done automatically.
		self.auto_input_enabled = False
		return "next"

	def depends(self):
		# depends() is called every time the user enters this module - so we can update device list here
		# reset layout and selections
		return {'bootloader_device': ['boot_partition']}

	def find_devices(self):
		self.devices = {}
		REpartitions = re.compile('^\d+\s+\d+\s+\d+\s+(.*[^0-9])$')
		try:
			lines = [ x.strip() for x in open('/proc/partitions','r').readlines() ]
		except IOError, e:
			self.debug('ERROR: cannot read /proc/partitions: %s' % str(e))
			lines = []

		for line in lines:
			match = REpartitions.match(line)
			if not match:
				continue
			device = match.group(1)

			# is block device?
			if not os.path.exists('/sys/block/%s' % device):
				continue

			# is readonly?
			try:
				content = open('/sys/block/%s/ro' % device,'r').read()
			except IOError, e:
				self.debug('WARNING: cannot read /sys/block/%s/ro: e' % (device, e))
				content = '0'
			if not content.strip() == '0':
				continue

			# check if device is a CDROM
			try:
				content = open('/sys/block/%s/capability' % device,'r').read()
			except IOError, e:
				self.debug('WARNING: cannot read /sys/block/%s/capability: e' % (device, e))
				content = '0'
			try:
				value = int(content, 16)
			except ValueError:
				value = 0
			if value & 8:
				continue

			# valid device
			fullname = '/dev/%s' % device
			self.devices[ fullname ] = [ fullname, len(self.devices) ]

			if len(fullname)+3 > self.max_length:
				self.max_length = len(fullname) + 3

		self.debug('Possible bootloader_devices: %s' % self.devices)

		if len(self.devices) > 1:
			self.debug('More than one possible bootloader_devices - disabling auto-f12')
			self.auto_input_enabled = False

		self.selected_device = self.all_results.get('bootloader_device')
		self.debug('User selected device: %s' % self.selected_device)
		if not self.selected_device:
			 self.selected_device = self.all_results.get('boot_partition','').strip('0123456789')
			 self.debug('Guessing device: %s' % self.selected_device)
		if not self.selected_device in self.devices:
			self.selected_device = self.devices.keys()[0]
		self.debug('self.selected_device: %s' % self.selected_device)


	def layout(self):
		## clear layout
		self.reset_layout()
		# add default buttons
		self.std_button()

		self.find_devices()

		msg = _('This module is used to specifiy the device where to install the boot loader. The correct device depends on current BIOS settings and partitioning. If an incorrect device has been selected, the installed system may not boot. If unsure, continue without change.')
		self.add_elem('TA_desc', textarea(msg, self.minY-10, self.minX+5, 8, self.maxWidth+11))

		pos = self.minY - 10 + self.get_elem('TA_desc').get_number_of_lines()

		self.add_elem('TL_headline', textline(_('Select where to install the GRUB boot loader:'), pos + 1, self.minX+5))
		self.add_elem('DEVICE',select(self.devices, pos + 3, self.minX+5, self.max_length, 15, self.devices.get(self.selected_device,[0,0])[1]))
		self.move_focus(self.get_elem_id('DEVICE'))


	def input(self,key):
		if key in [ 10, 32 ] and self.btn_next():
			return 'next'
		elif key in [ 10, 32 ] and self.btn_back():
			return 'prev'
		else:
			return self.elements[self.current].key_event(key)


	def incomplete(self):
		return 0


	def helptext(self):
		return _('Boot loader \nSelect where you want the GRUB boot loader to be installed. \n ')


	def modheader(self):
		return _('Boot loader')


	def profileheader(self):
		return 'Boot loader'


	def result(self):
		result = { 'bootloader_device': '%s' % self.get_elem('DEVICE').result()[0] }
		return result
