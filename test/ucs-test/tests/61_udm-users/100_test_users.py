#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# -*- coding: utf-8 -*-
## desc: Test various things in users/user
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

import pytest
import time
from datetime import datetime, timedelta
import subprocess

from univention.config_registry import handler_set
from univention.testing.strings import random_username


class TestUsers(object):
	"""
		# TODO: test open() method:

		2.
		if self.exists():
			self._unmap_mail_forward()
			self.sambaMungedDialUnmap()
			self.sambaMungedDialParse()

		3.
		self._load_groups(loadGroups)

		# TODO: test pre_create() / pre_modify() / pre_ready() method:
		primaryGroupWithoutSamba

		different password expiry interval values!

		is the locking of uidNumber still okay, what if limits are reached?

		what if pwdChangeNextLogin = 1 and password=foo at the same time?
	"""

	@pytest.mark.parametrize('shadowLastChange,shadowMax,pwd_change_next_login,password_expiry', [
		('0', '', '1', []),
		('0', '0', '1', ['1970-01-01']),
		('0', '1', '1', ['1970-01-02']),
		('0', str(int(time.time()) / 3600 / 24 + 2), '1', (datetime.today() + timedelta(days=2)).strftime('%Y-%m-%d')),
		('', str(int(time.time()) / 3600 / 24 + 2), [], []),
		('', '', [], []),
		('', str(int(time.time()) / 3600 / 24 - 2), [], []),
		('1', str(int(time.time()) / 3600 / 24 - 2), '1', (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')),
		('0', str(int(time.time()) / 3600 / 24 - 2), '1', (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d')),
	])
	def test_unmap_pwd_change_next_login_and_password_expiry(self, udm, lo, shadowLastChange, shadowMax, pwd_change_next_login, password_expiry):
		user = udm.create_user()[0]
		attr = lo.get(user)
		ml = []
		if shadowLastChange is not None:
			ml.append(('shadowLastChange', attr.get('shadowLastChange'), shadowLastChange))
		if shadowMax is not None:
			ml.append(('shadowMax', attr.get('shadowMax'), shadowMax))
		if ml:
			lo.modify(user, ml)
		udm.verify_udm_object("users/user", user, {"pwdChangeNextLogin": pwd_change_next_login, 'passwordexpiry': password_expiry})

	@pytest.mark.parametrize('path', ['/test', '/test2/'])
	def test_unmap_automount_information(self, udm, path, random_name, lo, verify_udm_object):
		homeSharePath = random_name()
		host = random_name()
		share = udm.create_object('shares/share', name=random_name(), path=path, host=host)

		user = udm.create_user(homeShare=share, homeSharePath=homeSharePath)[0]
		udm.verify_udm_object("users/user", user, {"homeShare": share, "homeSharePath": homeSharePath})
		udm.verify_ldap_object(user, {'automountInformation': ['-rw %s:%s/%s' % (host, path.rstrip('/'), homeSharePath)]})

	def test_unmap_user_certificate(self, udm, ucr):
		certificate = subprocess.check_output(['openssl', 'x509', '-inform', 'pem', '-in', '/etc/univention/ssl/%(hostname)s/cert.pem' % ucr, '-outform', 'der', '-out', '-']).encode('base64').replace('\n', '')
		certificate_ldap = {
			'userCertificate': certificate,
			'certificateIssuerCommonName': ucr['ssl/common'],
			'certificateIssuerCountry': ucr['ssl/country'],
			'certificateIssuerLocation': ucr['ssl/locality'],
			'certificateIssuerMail': ucr['ssl/email'],
			'certificateIssuerOrganisation': ucr['ssl/organization'],
			'certificateIssuerOrganisationalUnit': ucr['ssl/organizationalunit'],
			'certificateIssuerState': ucr['ssl/state'],
			'certificateSerial': '1',
			'certificateSubjectCommonName': '%(hostname)s.%(domainname)s' % ucr,
			'certificateSubjectCountry': ucr['ssl/country'],
			'certificateSubjectLocation': ucr['ssl/locality'],
			'certificateSubjectMail': ucr['ssl/email'],
			'certificateSubjectOrganisation': ucr['ssl/organization'],
			'certificateSubjectOrganisationalUnit': ucr['ssl/organizationalunit'],
			'certificateSubjectState': ucr['ssl/state'],
			'certificateVersion': '2',
		}
		try:
			from dateutil import parser
		except ImportError:
			pass
		else:
			dates = subprocess.check_output('openssl x509 -startdate -enddate < /etc/univention/ssl/%(hostname)s/cert.pem' % ucr, shell=True)
			dates = dict(x.split('=', 1) for x in dates.splitlines()[:2])
			certificate_ldap.update({
				'certificateDateNotAfter': parser.parse(dates['notAfter']).strftime('%Y-%m-%d'),
				'certificateDateNotBefore': parser.parse(dates['notBefore']).strftime('%Y-%m-%d'),
			})
		user = udm.create_user()[0]
		udm.modify_object('users/user', dn=user, append_option=['pki'], userCertificate=certificate)
		udm.verify_udm_object('users/user', user, certificate_ldap)

	def test_unmap_locked(self):
		pass

	def test_unmap_disabled(self):
		pass

	@pytest.mark.parametrize('samba_sid,samba_rid', [
		('S-1-5-21-1290176872-3541151870-1783641248-14678', '14678'),
	])
	def test_unmap_samba_rid(self, udm, lo, samba_sid, samba_rid):
		user = udm.create_user()[0]
		lo.modify(user, [('sambaSID', [None], samba_sid)])
		udm.verify_udm_object('users/user', user, {'sambaRID': samba_rid})

	def test_unmap_user_expiry(self):
		pass

	def test_unmap_user_password(self, udm, lo):
		user = udm.create_user(password='univention')[0]
		password = lo.getAttr(user, 'userPassword')[0]
		udm.verify_udm_object('users/user', user, {'password': password})

	def test_mail_primary_group_gets_lowercased(self):
		pass  # TODO: implement create() + modify()

	def test_uid_gid_number_conflict_is_detected(self):
		pass

	def test_locking(self):
		"""
		locks (change und create): uidNumber, uid, mailPrimaryAddress
		locks confirmed after creation/modification
		locks released after removal
		locks funktionieren mit case-insensitive
		"""

	def test_prohibited_username_are_checked(self, udm, random_username):
		username = random_username()
		udm.create_object('settings/prohibited_username', name='forbidden', usernames=[username])

		with pytest.raises(Exception):
			udm.create_user(username=username)

		user = udm.create_user()[0]
		with pytest.raises(Exception):
			udm.modify_object('user/user', dn=user, username=username)

	def test_modification_of_username(self, udm, random_username, ucr):
		user, name = udm.create_user()
		username = random_username()
		assert name in user
		assert username not in user
		user = udm.modify_object('users/user', dn=user, username=username)
		assert name not in user
		assert username in user
		udm.verify_ldap_object(user, {'krb5PrincipalName': ['%s@%s' % (username, ucr['domainname'].upper())]})

	def test_kerberos_values_are_set(self, udm):
		user = udm.create_user()[0]
		udm.verify_ldap_object(user, {
			'krb5MaxLife': ['86400'],
			'krb5MaxRenew': ['604800'],
		})

	@pytest.mark.parametrize('privileges', [
		['SeMachineAccountPrivilege'],
		['SeSecurityPrivilege'],
		['SeTakeOwnershipPrivilege'],
		['SeBackupPrivilege'],
		['SeRestorePrivilege'],
		['SeRemoteShutdownPrivilege'],
		['SePrintOperatorPrivilege'],
		['SeAddUsersPrivilege'],
		['SeDiskOperatorPrivilege'],
		[
			'SeMachineAccountPrivilege',
			'SeSecurityPrivilege',
			'SeTakeOwnershipPrivilege',
			'SeBackupPrivilege',
			'SeRestorePrivilege',
			'SeRemoteShutdownPrivilege',
			'SePrintOperatorPrivilege',
			'SeAddUsersPrivilege',
			'SeDiskOperatorPrivilege',
		]
	])
	def test_modlist_samba_privileges(self, udm, privileges):
		self._test_modlist(udm, {'sambaPrivileges': privileges}, {'univentionSambaPrivilegeList': privileges, 'objectClass': ['univentionSambaPrivileges']})

	@pytest.mark.parametrize('privileges', [
		pytest.mark.xfail(['SeMachineAccountPrivilege', 'foobar'], reason='https://forge.univention.org/bugzilla/show_bug.cgi?id=46020'),
		['foobar'],
	])
	def test_modlist_samba_privileges_invalid(self, udm, privileges):
		with pytest.raises(Exception):
			udm.create_user(sambaPrivileges=privileges)

		user = udm.create_user()[0]
		with pytest.raises(Exception):
			udm.modify_object('users/user', dn=user, sambaPrivileges=privileges)

	_modlist_cn_username = random_username()

	@pytest.mark.parametrize('form,props,cn', [
		('<firstname> <lastname>', {'firstname': 'X', 'lastname': 'Y'}, 'X Y'),
		('<username> <firstname> <lastname>', {'username': _modlist_cn_username, 'firstname': 'X', 'lastname': 'Y'}, '%s X Y' % (_modlist_cn_username,)),
	])
	def test_modlist_cn(self, udm, ucr, form, props, cn):
		handler_set(['directory/manager/usercn/attributes=%s' % (form,)])
		udm.stop_cli_server()
		self._test_modlist(udm, props, {'cn': [cn]})

	def _test_modlist(self, udm, props, attrs, **kwargs):
		if kwargs.get('create', True):
			user = udm.create_user(**props)[0]
			udm.verify_ldap_object(user, attrs, strict=False)
			udm.remove_object('users/user', dn=user)

		if kwargs.get('modify', True):
			user = udm.create_user()[0]
			user = udm.modify_object('users/user', dn=user, **props)
			udm.verify_ldap_object(user, attrs, strict=False)

	@pytest.mark.parametrize('props,gecos', [
		({'firstname': 'X', 'lastname': 'Y'}, 'X Y'),
		({'firstname': ' X ', 'lastname': ' Y '}, 'X   Y'),  # FIXME: current result looks broken!
		({'firstname': 'H\xc3\xe4\xc3\xe4lo', 'lastname': 'W\xc3\xb6\xc3\xb6rld'}, 'HAaeAaelo Woeoerld'),  # FIXME: current result looks broken!
	])
	def test_modlist_gecos(self, udm, props, gecos):
		# TODO: test UCR variable overwrite of '<firstname> <lastname><:umlauts,strip>'
		# TODO: missing is a check where only lastname or only firstname changes
		self._test_modlist(udm, props, {'gecos': [gecos]})

	@pytest.mark.parametrize('props,displayName', [
		({'firstname': 'X', 'lastname': 'Y'}, 'X Y'),
		({'firstname': ' X ', 'lastname': ' Y '}, 'X   Y'),
		#({'firstname': ' H\xc3\xe4\xc3\xe4lo', 'lastname': 'W\xc3\xb6\xc3\xb6rld '}, 'Hlo W\xc3\xb6\xc3\xb6rld'),  # FIXME: pytest crashes!
	])
	def test_modlist_display_name(self, udm, props, displayName):
		# TODO: test UCR variable overwrite of '<firstname> <lastname><:strip>'
		self._test_modlist(udm, props, {'displayName': [displayName]})

	def test_modlist_krb_principal(self, udm, random_username, ucr):
		username = random_username()
		self._test_modlist(udm, {'username': username}, {'krb5PrincipalName': ['%s@%s' % (username, ucr['domainname'].upper())]})

	def test_lock_unlock_preserves_password(self, udm, lo):
		user = udm.create_user(password='univention')[0]
		password = lo.getAttr(user, 'userPassword')[0]
		assert password.startswith('{crypt}')
		udm.modify_object('users/user', dn=user, locked='all')
		udm.verify_ldap_object(user, {'userPassword': [password.replace('{crypt}', '{crypt}!')]})
		udm.modify_object('users/user', dn=user, locked='none')
		udm.verify_ldap_object(user, {'userPassword': [password]})

	def test_disable_enable_preserves_password(self, udm, lo):
		user = udm.create_user(password='univention')[0]
		password = lo.getAttr(user, 'userPassword')[0]
		udm.modify_object('users/user', dn=user, disabled='all')
		udm.verify_ldap_object(user, {'userPassword': [password]})
		udm.modify_object('users/user', dn=user, disabled='none')
		udm.verify_ldap_object(user, {'userPassword': [password]})

	@pytest.mark.parametrize('password', [
		'{KINIT}',
		'{SASL}',
		'{LANMAN}',
		'{crypt}$6$foo',
		'{foo}bar',
		'{KINIT!}',
		'{SASL}!',
		'{LANMAN}!',
		'{crypt}$6$foo!',
		'{foo}bar!',
	])
	def test_invalid_password(self, password, udm):
		with pytest.raises(Exception):
			udm.create_user(password=password)

	@pytest.mark.parametrize('disabled,flag,x', [
		('none', '126', {'modify': False}),
		('posix', '126', {}),
		('windows', '126', {}),
		('windows_posix', '126', {}),
		('kerberos', '254', {}),
		('windows_kerberos', '254', {}),
		('posix_kerberos', '254', {}),
		('all', '254', {}),
	])
	def test_modlist_krb5_kdc_flags(self, disabled, flag, x, udm):
		self._test_modlist(udm, {'disabled': disabled}, {'krb5KDCFlags': [flag]}, **x)

	def test_modlist_krb5_key(self, udm):
		pass

	def test_modlist_krb5_key_version_number(self, udm):
		user = udm.create_user()[0]
		udm.verify_ldap_object(user, {'krb5KeyVersionNumber': ['1']})
		udm.modify_object('users/user', dn=user, password='univention2')
		udm.verify_ldap_object(user, {'krb5KeyVersionNumber': ['2']})
		udm.modify_object('users/user', dn=user, password='univention3')
		udm.verify_ldap_object(user, {'krb5KeyVersionNumber': ['3']})

	def test_modlist_check_password_history(self, udm):
		pass

	def test_modlist_check_password_complexity(self, udm):
		pass

	def test_modlist_samba_nt_password(self, udm):
		user = udm.create_user()[0]
		udm.verify_ldap_object(user, {'sambaNTPassword': ['CAA1239D44DA7EDF926BCE39F5C65D0F']})
		udm.modify_object('users/user', dn=user, password='univention2')
		udm.verify_ldap_object(user, {'sambaNTPassword': ['1471C3248018E4C973F304762AD312C0']})
		udm.modify_object('users/user', dn=user, password='univention3')
		udm.verify_ldap_object(user, {'sambaNTPassword': ['5F84B8886B7B0DA26E0A175FEE92A389']})

	def test_modlist_samba_lm_password(self, udm):
		pass

	def test_modlist_samba_password_history(self, udm):
		pass

	@pytest.mark.parametrize('today,expiry_interval', [
		(long(time.time()) / 3600 / 24, None),
		(long(time.time()) / 3600 / 24, 7),
	])
	def test_modlist_shadow_max_and_last_change(self, today, expiry_interval, udm):
		kw = dict(expiryInterval=expiry_interval) if expiry_interval is not None else {}
		pwhistory = udm.create_object('policies/pwhistory', name='pw-test', **kw)
		cn = udm.create_object('container/cn', name='testusers', policy_reference=pwhistory)
		shadow_max_expiry = [str(expiry_interval)] if expiry_interval is not None else []
		shadow_max_expiry_1 = [str(expiry_interval)] if expiry_interval is not None else ['1']

		user1 = udm.create_user(position=cn)[0]
		udm.verify_ldap_object(user1, {'shadowMax': shadow_max_expiry, 'shadowLastChange': [str(today)] if expiry_interval else []})

		user2 = udm.create_user(position=cn, pwdChangeNextLogin='0')[0]
		# FIXME?: the following was possible in UCS 4.2
#		udm.verify_ldap_object(user2, {'shadowMax': shadow_max_expiry, 'shadowLastChange': [str(today)]})

		user3 = udm.create_user(position=cn, pwdChangeNextLogin='1')[0]
		udm.verify_ldap_object(user3, {'shadowMax': shadow_max_expiry_1, 'shadowLastChange': [str(today - expiry_interval - 1) if expiry_interval else str(today - 2)]})

		udm.modify_object('users/user', dn=user1, password='univention2')
		udm.verify_ldap_object(user1, {'shadowMax': shadow_max_expiry, 'shadowLastChange': [str(today)] if expiry_interval else []})

		udm.modify_object('users/user', dn=user2, password='univention2', pwdChangeNextLogin='1')
		udm.verify_ldap_object(user2, {'shadowMax': shadow_max_expiry_1, 'shadowLastChange': [str(today - expiry_interval - 1) if expiry_interval else str(today - 2)]})

		# Bug #46067:
		udm.modify_object('users/user', dn=user3, password='univention2', pwdChangeNextLogin='1')
		#udm.verify_ldap_object(user3, {'shadowMax': shadow_max_expiry_1, 'shadowLastChange': [str(today - expiry_interval - 1)]})

	def test_modlist_samba_pwd_last_set(self, udm, lo):
		self._test_modlist(udm, {'pwdChangeNextLogin': '1'}, {'sambaPwdLastSet': ['0']})
		self._test_modlist(udm, {'password': 'univention2', 'pwdChangeNextLogin': '1'}, {'sambaPwdLastSet': ['0']})
		prior = long(time.time())
		user = udm.create_user()[0]
		after = long(time.time())
		last_set = long(lo.get(user)['sambaPwdLastSet'][0])
		assert prior <= last_set <= after

	def test_modlist_krb_password_end(self, udm):
		expiry_interval = 7
		pwhistory = udm.create_object('policies/pwhistory', name='pw-test', expiryInterval=expiry_interval)
		cn = udm.create_object('container/cn', name='testusers', policy_reference=pwhistory)
		expiry = long(time.time())
		password_end = time.strftime("%Y%m%d000000Z", time.gmtime(expiry))
		password_end_policy = time.strftime("%Y%m%d000000Z", time.gmtime(expiry + expiry_interval * 3600 * 24))
		self._test_modlist(udm, {'pwdChangeNextLogin': '1'}, {'krb5PasswordEnd': [password_end]})
		self._test_modlist(udm, {'pwdChangeNextLogin': '0', 'password': 'univention2'}, {'krb5PasswordEnd': []})
		self._test_modlist(udm, {'pwdChangeNextLogin': '1', 'position': cn}, {'krb5PasswordEnd': [password_end]})
		# FIXME: correct would be: self._test_modlist(udm, {'pwdChangeNextLogin': '0', 'password': 'univention2', 'position': cn}, {'krb5PasswordEnd': [password_end_policy]})
		self._test_modlist(udm, {'pwdChangeNextLogin': '0', 'password': 'univention2', 'position': cn}, {'krb5PasswordEnd': []})

	def test_user_password_is_cryped(self, udm, lo):
		user = udm.create_user(password='univention')[0]
		password = lo.getAttr(user, 'userPassword')[0]
		assert password.startswith('{crypt}')
		udm.modify_object('users/user', dn=user, password='univention2')
		password2 = lo.getAttr(user, 'userPassword')[0]
		assert password2.startswith('{crypt}')
		assert password2 != password

	@pytest.mark.parametrize('locked,unlocked', [
		('all', 'none'),
		('all', 'posix'),
		('windows', 'none'),
		('windows', 'posix'),
	])
	def test_modlist_samba_bad_pw_count(self, udm, lo, locked, unlocked):
		user = udm.create_user()[0]
		udm.modify_object('users/user', dn=user, locked=locked)
		lo.modify(user, [('sambaBadPasswordCount', '', '20')])
		udm.modify_object('users/user', dn=user, locked=unlocked)
		udm.verify_ldap_object(user, {'sambaBadPasswordCount': ['0']})

	@pytest.mark.parametrize('props,flags', [
		({'locked': 'none', 'description': 'asdf'}, ['[U          ]']),
		({'locked': 'all'}, ['[UL         ]']),
		({'disabled': 'all'}, ['[UD         ]']),
		({'disabled': 'none', 'description': 'asdf'}, ['[U          ]']),
		({'locked': 'all', 'disabled': 'all'}, ['[UDL        ]']),
		({'locked': 'none', 'disabled': 'none', 'description': 'asdf'}, ['[U          ]']),
	])
	def test_modlist_sambaAcctFlags(self, udm, props, flags):
		self._test_modlist(udm, props, {'sambaAcctFlags': flags})

	@pytest.mark.parametrize('userexpiry,kick_off,x', [
		('2018-01-01', ['1514761200'], {}),
		('', [], {'modify': False}),
	])
	def test_modlist_samba_kickoff_time(self, userexpiry, kick_off, x, udm):
		self._test_modlist(udm, {'userexpiry': userexpiry}, {'sambaKickoffTime': kick_off}, **x)

	@pytest.mark.parametrize('userexpiry,valid_end,x', [
		('2018-01-01', ['20180101000000Z'], {}),
		('', [], {'modify': False}),
	])
	def test_modlist_krb5_valid_end(self, udm, userexpiry, valid_end, x):
		self._test_modlist(udm, {'userexpiry': userexpiry}, {'krb5ValidEnd': valid_end}, **x)

	@pytest.mark.parametrize('disabled,userexpiry,shadow_expire', [
		('none', '2018-01-01', ['17532']),
		('all', '2018-01-01', ['17532']),
		('posix', '2018-01-01', ['17532']),
		('posix_kerberos', '2018-01-01', ['17532']),
		('windows_posix', '2018-01-01', ['17532']),
		('kerberos', '', []),
		('all', '', ['1']),
		('posix', '', ['1']),
		('posix_kerberos', '', ['1']),
		('windows_posix', '', ['1']),
	])
	def test_modlist_shadow_expire(self, disabled, userexpiry, shadow_expire, udm):
		self._test_modlist(udm, {'disabled': disabled, 'userexpiry': userexpiry}, {'shadowExpire': shadow_expire})

	def test_modlist_mail_forward(self, udm):
		pass

	@pytest.mark.parametrize('birthday', [
		['2009-213'],
		['2009-05'],
		['2009-05-13'],
		['2009-W21'],
		['2009-W21-4'],
	])
	def test_modlist_univention_person_birthday(self, udm, birthday):
		self._test_modlist(udm, {'birthday': birthday[0]}, {'univentionBirthday': birthday, 'objectClass': ['univentionPerson']})

	def test_modlist_univention_person(self, udm):
		self._test_modlist(udm, {'umcProperty': ['foo bar'], 'birthday': '2009-05-13'}, {'univentionBirthday': ['2009-05-13'], 'univentionUMCProperty': ['foo=bar'], 'objectClass': ['univentionPerson']})
		self._test_modlist(udm, {'umcProperty': ['foo bar']}, {'univentionUMCProperty': ['foo=bar'], 'objectClass': ['univentionPerson']})

	def test_modlist_home_share(self, udm):
		pass

	def test_modlist_samba_mungeddial(self, udm):
		pass

	def test_modlist_samba_sid(self, udm):
		pass
