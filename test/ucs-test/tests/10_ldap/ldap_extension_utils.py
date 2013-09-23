#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Copyright 2013 Univention GmbH
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

from univention.testing.strings import random_name, random_int
from univention.config_registry import ConfigRegistry
import subprocess
import ldap
import ldap.schema

def get_package_name():
	return random_name()

def get_schema_name():
	return random_name()

def get_schema_attribute_id():
	return random_int() + random_int() + random_int() + random_int() + random_int()

def call_join_script(join_script_name):
	ucr = ConfigRegistry()
	ucr.load()

	join_script = '/usr/lib/univention-install/%s' % join_script_name

	return subprocess.call('%s --binddn "%s" --bindpwdfile "%s"' % (join_script, ucr.get('tests/domainadmin/account'), ucr.get('tests/domainadmin/pwdfile')), shell=True)


def fetch_schema_from_ldap_master():
	ucr = ConfigRegistry()
	ucr.load()

	ldap_uri = 'ldap://%(ldap/master)s:%(ldap/master/port)s' % ucr

	return ldap.schema.subentry.urlfetch(ldap_uri)

def fetch_schema_from_local_ldap():
	ucr = ConfigRegistry()
	ucr.load()

	ldap_uri = 'ldap://%(hostname)s:%(domainname)s' % ucr

	return ldap.schema.subentry.urlfetch(ldap_uri)

