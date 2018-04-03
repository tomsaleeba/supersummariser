# -*- coding: utf-8 -*-
"""Test app"""
import unittest

from flask import Flask
from flask.json import loads

import supersummariser.app as object_under_test


def test_add_routes01():
    """ can we add all the expected routes """
    test_app = Flask('test_add_routes01')
    object_under_test.add_routes(test_app)
    result = [x.rule for x in test_app.url_map.iter_rules()]
    result.index('/hpcsummary/simple/<int:year>/<int:month>')
    result.index('/hpcsummary/rollup/<int:year>/<int:month>')
    result.index('/hpcsummary/detailed/<int:year>/<int:month>')
    result.index('/hpcsummary/chart')
    result.index('/allocationsummary/simple/<int:year>/<int:month>')
    result.index('/hpcstorage/simple/<int:year>/<int:month>')
    result.index('/process')


class ServicesTestCase(unittest.TestCase):

    def setUp(self):
        app = Flask('ServicesTestApp')
        app.testing = True
        object_under_test.add_routes(app)
        self.app = app.test_client()

    def test_process01(self):
        """ can we process for the default number of months? """
        def stub_process(months_back, config):
            assert months_back == 2
            return {'success': True}
        object_under_test.services.process = stub_process
        result = self.app.get('/process')
        assert loads(result.data)['success'] == True


    def test_process02(self):
        """ can we process for a custom number of months? """
        def stub_process(months_back, config):
            assert months_back == 3
            return {'success': True}
        object_under_test.services.process = stub_process
        result = self.app.get('/process?months_back=3')
        assert loads(result.data)['success'] == True
