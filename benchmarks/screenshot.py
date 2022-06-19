#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2019  Diego Torres Milano
Created on 2022-03-23 by Culebra v20.7.1
                      __    __    __    __
                     /  \  /  \  /  \  /  \ 
____________________/  __\/  __\/  __\/  __\_____________________________
___________________/  /__/  /__/  /__/  /________________________________
                   | / \   / \   / \   / \   \___
                   |/   \_/   \_/   \_/   \    o \ 
                                           \_____/--<
@author: Diego Torres Milano
@author: Jennifer E. Swofford (ascii art snake)
"""


from operator import truediv
import re
import sys
import os


import unittest

from com.dtmilano.android.viewclient import ViewClient, CulebraTestCase

TAG = 'CULEBRA'


class CulebraTests(CulebraTestCase):

    @classmethod
    def setUpClass(cls):
        cls.kwargs1 = {'verbose': True, 'ignoresecuredevice': False, 'ignoreversioncheck': False}
        cls.kwargs2 = {'forceviewserveruse': False, 'startviewserver': True, 'autodump': False, 'ignoreuiautomatorkilled': True, 'compresseddump': True, 'useuiautomatorhelper': False, 'debug': {}}
        cls.options = {'find-views-by-id': True, 'find-views-with-text': True, 'find-views-with-content-description': True, 'use-regexps': False, 'verbose-comments': False, 'unit-test-class': True, 'unit-test-method': None, 'use-jar': False, 'use-dictionary': False, 'dictionary-keys-from': 'id', 'auto-regexps': None, 'start-activity': None, 'output': 'benchmarksuite_nostates.py', 'interactive': False, 'window': -1, 'prepend-to-sys-path': False, 'save-screenshot': None, 'save-view-screenshots': None, 'gui': True, 'do-not-verify-screen-dump': True, 'scale': 0.33, 'orientation-locked': None, 'multi-device': False, 'log-actions': False, 'device-art': None, 'drop-shadow': False, 'glare': False, 'null-back-end': False, 'concertina': False, 'concertina-config': None, 'install-apk': None}
        cls.sleep = 5

 
    def setUp(self):
        super(CulebraTests, self).setUp()


    def tearDown(self):
        super(CulebraTests, self).tearDown()


    def preconditions(self):
        if not super(CulebraTests, self).preconditions():
            return False
 
        return True

    def testSomething(self):
        if not self.preconditions():
            self.fail('Preconditions failed')

        _s = CulebraTests.sleep
        _v = CulebraTests.verbose
        print("Running Screenshot Script")
        self.device.Log.d(TAG, "dumping content of window=-1",  _v)
        self.vc.dump(window=-1)
        self.device.touchDip(201.65, 455.1, 0)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.vc.writeImageToFile(dir_path+'/results'+'/${serialno}-${focusedwindowname}-${timestamp}.png', 'PNG', None, False, False)
        print("Screenshot Saved as "+dir_path+'/results/'+'/${serialno}-${focusedwindowname}-${timestamp}.png')


if __name__ == '__main__':
    CulebraTests.main()