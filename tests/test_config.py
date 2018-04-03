# -*- coding: utf-8 -*-
"""Test configs."""
import logging

import supersummariser.app as object_under_test
from supersummariser.settings import DevConfig, ProdConfig


def test_production_config():
    """Production config."""
    object_under_test.logger.setLevel(logging.WARN)
    app = object_under_test.create_app(ProdConfig)
    object_under_test.logger.setLevel(logging.DEBUG)
    assert app.config['ENV'] == 'prod'
    assert app.config['DEBUG'] is False


def test_dev_config():
    """Development config."""
    object_under_test.logger.setLevel(logging.WARN)
    app = object_under_test.create_app(DevConfig)
    object_under_test.logger.setLevel(logging.DEBUG)
    assert app.config['ENV'] == 'dev'
    assert app.config['DEBUG'] is True
