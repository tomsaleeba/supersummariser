# -*- coding: utf-8 -*-
"""Application configuration."""
import os

from flask_env import MetaFlaskEnv


class Config(metaclass=MetaFlaskEnv):
    """Base configuration."""

    REPORTING_SERVER = 'https://reporting.ersa.edu.au'
    CRM_SERVER = 'https://bman.ersa.edu.au/bman'
    USAGE_SERVER = 'https://bman.ersa.edu.au'
    HPC_STORAGE_FSNAME = 'hpchome'
    STORAGE_BLOCK_SIZE_GB = 250
    HPC_HOME_BLOCK_PRICE = 5
    NECTAR_NOVA_VCPU_PRICE = 5
    ERSA_AUTH_TOKEN = 'not-supplied' # used for pulling data, not auth for calls to this server
    AUTH_HEADER_KEY = 'x-ersa-auth-token'
    SSL_VERIFY = True

    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(Config):
    """Production configuration."""

    ENV = 'prod'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://pg/supersummariser'


class TestConfig(Config):
    """Testing configuration."""

    ENV = 'test'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///"


class DevConfig(Config):
    """Development configuration."""

    ENV = 'dev'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:mysecretpassword@localhost/supersummariser"
