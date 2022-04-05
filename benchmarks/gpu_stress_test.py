# -*- coding: utf-8 -*-
"""
Copyright (C) 2013-2019  Diego Torres Milano
Created on 2022-03-22 by Culebra v20.7.1
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


import re
import sys
import os


import unittest

from com.dtmilano.android.viewclient import ViewClient, CulebraTestCase

TAG = 'CULEBRA'


class CulebraTests(CulebraTestCase):

    @classmethod
    def setUpClass(cls):
        cls.kwargs1 = {'verbose': False, 'ignoresecuredevice': False, 'ignoreversioncheck': False}
        cls.kwargs2 = {'forceviewserveruse': False, 'startviewserver': True, 'autodump': False, 'ignoreuiautomatorkilled': True, 'compresseddump': True, 'useuiautomatorhelper': False, 'debug': {}}
        cls.options = {'find-views-by-id': True, 'find-views-with-text': True, 'find-views-with-content-description': True, 'use-regexps': False, 'verbose-comments': False, 'unit-test-class': True, 'unit-test-method': None, 'use-jar': False, 'use-dictionary': False, 'dictionary-keys-from': 'id', 'auto-regexps': None, 'start-activity': None, 'output': 'gpu_stress_test.py', 'interactive': False, 'window': -1, 'prepend-to-sys-path': False, 'save-screenshot': None, 'save-view-screenshots': None, 'gui': True, 'do-not-verify-screen-dump': True, 'scale': 0.5, 'orientation-locked': None, 'multi-device': False, 'log-actions': True, 'device-art': None, 'drop-shadow': False, 'glare': False, 'null-back-end': False, 'concertina': False, 'concertina-config': None, 'install-apk': None}
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

        self.device.Log.d(TAG, "dumping content of window=-1",  _v)
        self.vc.dump(window=-1)
        self.device.Log.d(TAG, "touching point by DIP @ (94.48, 462.48) orientation=0",  _v)
        self.device.touchDip(94.48, 462.48, 0)
        self.vc.sleep(_s)
        self.device.Log.d(TAG, "dumping content of window=-1",  _v)
        self.vc.dump(window=-1)
        self.vc.sleep(_s)
        self.device.Log.d(TAG, "dumping content of window=-1",  _v)
        self.vc.dump(window=-1)
        self.device.Log.d(TAG, "touching point by DIP @ (368.76, 236.19) orientation=0",  _v)
        self.device.touchDip(368.76, 236.19, 0)
        self.vc.sleep(_s)
        self.device.Log.d(TAG, "dumping content of window=-1",  _v)
        self.vc.dump(window=-1)


if __name__ == '__main__':
    CulebraTests.main()

