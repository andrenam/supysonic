#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# This file is part of Supysonic.
# Supysonic is a Python implementation of the Subsonic server API.
#
# Copyright (C) 2013-2017 Alban 'spl0k' Féron
#
# Distributed under terms of the GNU AGPLv3 license.

import uuid

from supysonic.db import User, ClientPrefs

from .frontendtestbase import FrontendTestBase

class UserTestCase(FrontendTestBase):
    __module_to_test__ = 'supysonic.frontend'

    def setUp(self):
        super(UserTestCase, self).setUp()

        self.users = { u.name: u for u in self.store.find(User) }

    def test_index(self):
        self._login('bob', 'B0b')
        rv = self.client.get('/user', follow_redirects = True)
        self.assertIn('There\'s nothing much to see', rv.data)
        self.assertNotIn('Users', rv.data)
        self._logout()

        self._login('alice', 'Alic3')
        rv = self.client.get('/user')
        self.assertIn('Users', rv.data)

    def test_details(self):
        self._login('alice', 'Alic3')
        rv = self.client.get('/user/string', follow_redirects = True)
        self.assertIn('Invalid', rv.data)
        rv = self.client.get('/user/' + str(uuid.uuid4()), follow_redirects = True)
        self.assertIn('No such user', rv.data)
        rv = self.client.get('/user/' + str(self.users['bob'].id))
        self.assertIn('bob', rv.data)
        self._logout()

        prefs = ClientPrefs()
        prefs.user_id = self.users['bob'].id
        prefs.client_name = 'tests'
        self.store.add(prefs)
        self.store.commit()

        self._login('bob', 'B0b')
        rv = self.client.get('/user/' + str(self.users['alice'].id), follow_redirects = True)
        self.assertIn('There\'s nothing much to see', rv.data)
        self.assertNotIn('<h2>bob</h2>', rv.data)
        rv = self.client.get('/user/me')
        self.assertIn('<h2>bob</h2>', rv.data)
        self.assertIn('tests', rv.data)

    def test_update_client_prefs(self):
        self._login('alice', 'Alic3')
        self.skipTest('Hello logger')
        rv = self.client.post('/user/me')
        self.assertIn('updated', rv.data) # does nothing, says it's updated anyway
        # error cases, silently ignored
        self.client.post('/user/me', data = { 'garbage': 'trash' })
        self.client.post('/user/me', data = { 'a_b_c_d_e_f': 'g_h_i_j_k' })
        self.client.post('/user/me', data = { '_l': 'm' })
        self.client.post('/user/me', data = { 'n_': 'o' })
        self.client.post('/user/me', data = { 'inexisting_client': 'setting' })

        prefs = ClientPrefs()
        prefs.user_id = self.users['alice'].id
        prefs.client_name = 'tests'
        self.store.add(prefs)
        self.store.commit()

        rv = self.client.post('/user/me', data = { 'tests_format': 'mp3', 'tests_bitrate': 128 })
        self.assertIn('updated', rv.data)
        self.assertEqual(prefs.format, 'mp3')
        self.assertEqual(prefs.bitrate, 128)

        self.client.post('/user/me', data = { 'tests_delete': 1 })
        self.assertEqual(self.store.find(ClientPrefs).count(), 0)

    def test_change_username_get(self):
        self._login('bob', 'B0b')
        rv = self.client.get('/user/whatever/changeusername', follow_redirects = True)
        self.assertIn('There\'s nothing much to see', rv.data)
        self._logout()

        self._login('alice', 'Alic3')
        rv = self.client.get('/user/whatever/changeusername', follow_redirects = True)
        self.assertIn('Invalid', rv.data)
        rv = self.client.get('/user/{}/changeusername'.format(uuid.uuid4()), follow_redirects = True)
        self.assertIn('No such user', rv.data)
        self.client.get('/user/{}/changeusername'.format(self.users['bob'].id))

    def test_change_username_post(self):
        self._login('alice', 'Alic3')
        self.client.post('/user/whatever/changeusername')

        path = '/user/{}/changeusername'.format(self.users['bob'].id)
        rv = self.client.post(path, follow_redirects = True)
        self.assertIn('required', rv.data)
        rv = self.client.post(path, data = { 'user': 'bob' }, follow_redirects = True)
        self.assertIn('No changes', rv.data)
        rv = self.client.post(path, data = { 'user': 'b0b', 'admin': 1 }, follow_redirects = True)
        self.assertIn('updated', rv.data)
        self.assertIn('b0b', rv.data)
        self.assertEqual(self.users['bob'].name, 'b0b')
        self.assertTrue(self.users['bob'].admin)
        rv = self.client.post(path, data = { 'user': 'alice' }, follow_redirects = True)
        self.assertEqual(self.users['bob'].name, 'b0b')

    def test_change_mail_get(self):
        self._login('alice', 'Alic3')
        self.client.get('/user/me/changemail')
        # whatever

    def test_change_mail_post(self):
        self._login('alice', 'Alic3')
        self.client.post('/user/me/changemail')
        # whatever

    def test_change_password_get(self):
        self._login('alice', 'Alic3')
        rv = self.client.get('/user/me/changepass')
        self.assertIn('Current password', rv.data)
        rv = self.client.get('/user/{}/changepass'.format(self.users['bob'].id))
        self.assertNotIn('Current password', rv.data)

    def test_change_password_post(self):
        self._login('alice', 'Alic3')
        path = '/user/me/changepass'
        rv = self.client.post(path)
        self.assertIn('required', rv.data)
        rv = self.client.post(path, data = { 'current': 'alice' })
        self.assertIn('required', rv.data)
        rv = self.client.post(path, data = { 'new': 'alice' })
        self.assertIn('required', rv.data)
        rv = self.client.post(path, data = { 'current': 'alice', 'new': 'alice' })
        self.assertIn('password and its confirmation don', rv.data)
        rv = self.client.post(path, data = { 'current': 'alice', 'new': 'alice', 'confirm': 'alice' })
        self.assertIn('Wrong password', rv.data)
        self._logout()
        rv = self._login('alice', 'Alic3')
        self.assertIn('Logged in', rv.data)
        rv = self.client.post(path, data = { 'current': 'Alic3', 'new': 'alice', 'confirm': 'alice' }, follow_redirects = True)
        self.assertIn('changed', rv.data)
        self._logout()
        rv = self._login('alice', 'alice')
        self.assertIn('Logged in', rv.data)

        path = '/user/{}/changepass'.format(self.users['bob'].id)
        rv = self.client.post(path)
        self.assertIn('required', rv.data)
        rv = self.client.post(path, data = { 'new': 'alice' })
        self.assertIn('password and its confirmation don', rv.data)
        rv = self.client.post(path, data = { 'new': 'alice', 'confirm': 'alice' }, follow_redirects = True)
        self.assertIn('changed', rv.data)
        self._logout()
        rv = self._login('bob', 'alice')
        self.assertIn('Logged in', rv.data)


    def test_add_get(self):
        self._login('bob', 'B0b')
        rv = self.client.get('/user/add', follow_redirects = True)
        self.assertIn('There\'s nothing much to see', rv.data)
        self.assertNotIn('Add User', rv.data)
        self._logout()

        self._login('alice', 'Alic3')
        rv = self.client.get('/user/add')
        self.assertIn('Add User', rv.data)

    def test_add_post(self):
        self._login('alice', 'Alic3')
        rv = self.client.post('/user/add')
        self.assertIn('required', rv.data)
        rv = self.client.post('/user/add', data = { 'user': 'user' })
        self.assertIn('Please provide a password', rv.data)
        rv = self.client.post('/user/add', data = { 'passwd': 'passwd' })
        self.assertIn('required', rv.data)
        rv = self.client.post('/user/add', data = { 'user': 'name', 'passwd': 'passwd' })
        self.assertIn('passwords don', rv.data)
        rv = self.client.post('/user/add', data = { 'user': 'alice', 'passwd': 'passwd', 'passwd_confirm': 'passwd' })
        self.assertIn('already a user with that name', rv.data)
        self.assertEqual(self.store.find(User).count(), 2)

        rv = self.client.post('/user/add', data = { 'user': 'user', 'passwd': 'passwd', 'passwd_confirm': 'passwd', 'admin': 1 }, follow_redirects = True)
        self.assertIn('added', rv.data)
        self.assertEqual(self.store.find(User).count(), 3)
        self._logout()
        rv = self._login('user', 'passwd')
        self.assertIn('Logged in', rv.data)

    def test_delete(self):
        path = '/user/del/{}'.format(self.users['bob'].id)

        self._login('bob', 'B0b')
        rv = self.client.get(path, follow_redirects = True)
        self.assertIn('There\'s nothing much to see', rv.data)
        self.assertEqual(self.store.find(User).count(), 2)
        self._logout()

        self._login('alice', 'Alic3')
        rv = self.client.get('/user/del/string', follow_redirects = True)
        self.assertIn('Invalid', rv.data)
        rv = self.client.get('/user/del/' + str(uuid.uuid4()), follow_redirects = True)
        self.assertIn('No such user', rv.data)
        rv = self.client.get(path, follow_redirects = True)
        self.assertIn('Deleted', rv.data)
        self.assertEqual(self.store.find(User).count(), 1)
        self._logout()
        rv = self._login('bob', 'B0b')
        self.assertIn('No such user', rv.data)

    def test_lastfm_link(self):
        self._login('alice', 'Alic3')
        rv = self.client.get('/user/me/lastfm/link', follow_redirects = True)
        self.assertIn('Missing LastFM auth token', rv.data)
        self.skipTest('logging et logger sont sur un bateau')
        rv = self.client.get('/user/me/lastfm/link', query_string = { 'token': 'abcdef' }, follow_redirects = True)
        self.assertIn('No API key set', rv.data)

    def test_lastfm_unlink(self):
        self.skipTest("logger tombe a l'eau")
        self._login('alice', 'Alic3')
        rv = self.client.get('/user/me/lastfm/unlink', follow_redirects = True)
        self.assertIn('Unlinked', rv.data)

if __name__ == '__main__':
    unittest.main()

