# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
import logging

from flask import Flask, jsonify, request, abort, Response, current_app
from voluptuous import All, Length, Range, Coerce, Schema,\
    MultipleInvalid, Optional, Any

from supersummariser.extensions import db, migrate
from supersummariser.settings import ProdConfig
import supersummariser.services as services

logging.basicConfig()
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    _log_config(app.config)
    register_extensions(app)
    add_routes(app)
    return app


def _log_config(config):
    def log_for(key):
        logger.info('%s=%s' % (key, config.get(key)))
    logger.info('Configuration dump:')
    log_for('REPORTING_SERVER')
    log_for('CRM_SERVER')
    log_for('USAGE_SERVER')
    log_for('HPC_STORAGE_FSNAME')
    log_for('STORAGE_BLOCK_SIZE_GB')
    log_for('HPC_HOME_BLOCK_PRICE')
    log_for('NECTAR_NOVA_VCPU_PRICE')
    log_for('SQLALCHEMY_DATABASE_URI')
    log_for('ERSA_AUTH_TOKEN')
    log_for('AUTH_HEADER_KEY')
    log_for('SSL_VERIFY')


def register_extensions(app):
    """Register Flask extensions."""
    db.init_app(app)
    migrate.init_app(app, db)
    return None


def _handle_with_schema_validation(success_handler, schema_dict):
    """ validates that the request is valid before calling the handler """
    try:
        schema = Schema(schema_dict)
        args = schema(request.args.to_dict())
    except MultipleInvalid as e:
        return abort(400, 'value at %s failed validation: %s' % (e.path, e.msg))
    result = success_handler(args)
    return jsonify(result)


def _handle_with_year_month_validation(success_handler, year, month):
    """
        validates that the year and month values are in range
        before calling the handler.
    """
    try:
        schema = Schema({
            'month': All(int, Range(min=1, max=12)),
            'year': Schema(All(int, Range(min=2010, max=2100)))
        })
        schema({
            'month': month,
            'year': year
        })
    except MultipleInvalid as e:
        return abort(400, 'value at %s failed validation: %s' % (e.path, e.msg))
    result = success_handler(year, month, current_app.config)
    return jsonify(result)


def _chart_delegate(service_fn):
    def handler(args):
        org_filter = args['org'] # TODO might not want case sensitivity
        month_window = args['month_window']
        return service_fn(org_filter, month_window, current_app.config)
    return _handle_with_schema_validation(handler, {
        Optional('org', default=None): Any(None, All(str, Length(min=1))),
        Optional('month_window', default=12): All(Coerce(int), Range(min=1, max=24))
    })


def add_routes(app):
    @app.route('/hpcsummary/simple/<int:year>/<int:month>')
    def get_hpcsummary_simple(year, month):
        return _handle_with_year_month_validation(
            services.get_hpcsummary_simple, year, month)


    @app.route('/hpcsummary/rollup/<int:year>/<int:month>')
    def get_hpcsummary_rollup(year, month):
        return _handle_with_year_month_validation(
            services.get_hpcsummary_rollup, year, month)


    @app.route('/hpcsummary/detailed/<int:year>/<int:month>')
    def get_hpcsummary_detailed(year, month):
        return _handle_with_year_month_validation(
            services.get_hpcsummary_detailed, year, month)


    @app.route('/hpcsummary/chart')
    def get_hpcsummary_chart():
        return _chart_delegate(services.get_hpcsummary_chart)


    @app.route('/allocationsummary/simple/<int:year>/<int:month>')
    def get_allocationsummary_simple(year, month):
        return _handle_with_year_month_validation(
            services.get_allocationsummary_simple, year, month)


    @app.route('/allocationsummary/chart')
    def get_allocationsummary_chart():
        return _chart_delegate(services.get_allocationsummary_chart)


    @app.route('/hpcstorage/simple/<int:year>/<int:month>')
    def get_hpcstorage_simple(year, month):
        return _handle_with_year_month_validation(
            services.get_hpcstorage_simple, year, month)


    @app.route('/hpcstorage/chart')
    def get_hpcstorage_chart():
        return _chart_delegate(services.get_hpcstorage_chart)


    @app.route('/nectar/simple/<int:year>/<int:month>')
    def get_nectar_simple(year, month):
        return _handle_with_year_month_validation(
            services.get_nectar_simple, year, month)


    @app.route('/nectar/chart')
    def get_nectar_chart():
        return _chart_delegate(services.get_nectar_chart)


    @app.route('/tango/simple/<int:year>/<int:month>')
    def get_tango_simple(year, month):
        return _handle_with_year_month_validation(
            services.get_tango_simple, year, month)


    @app.route('/tango/chart')
    def get_tango_chart():
        return _chart_delegate(services.get_tango_chart)


    @app.route('/process')
    def process():
        def handler(args):
            months_back = args['months_back']
            return services.process(months_back, current_app.config)
        return _handle_with_schema_validation(handler,
            {Optional('months_back', default=2): All(Coerce(int), Range(min=1, max=100))}
        )
