# -*- coding: utf-8 -*-
"""Test services"""
import logging
from decimal import Decimal

import supersummariser.services as object_under_test
import pendulum
from decimal import Decimal


def test__get_months_to_process01():
    """ can we get the list of months to process when they're in
        the same year? """
    fake_now = pendulum.create(2018, 3, 4)
    result = object_under_test._get_months_to_process(3, fake_now)
    assert len(result) == 3
    result.index((2018, 1))
    result.index((2018, 2))
    result.index((2018, 3))


def test__get_months_to_process02():
    """ can we get the list of months to process when we roll
        over a year? """
    fake_now = pendulum.create(2018, 1, 4)
    result = object_under_test._get_months_to_process(3, fake_now)
    assert len(result) == 3
    result.index((2017, 11))
    result.index((2017, 12))
    result.index((2018, 1))


def test__get_months_to_process03():
    """ can we get the list of months to process when we're at the end
        of a month that's longer than the previous? """
    fake_now = pendulum.create(2018, 4, 30)
    result = object_under_test._get_months_to_process(3, fake_now)
    assert len(result) == 3
    result.index((2018, 2))
    result.index((2018, 3))
    result.index((2018, 4))


def test__get_months_to_process04():
    """ can we get just the current month? """
    fake_now = pendulum.create(2018, 4, 30)
    result = object_under_test._get_months_to_process(1, fake_now)
    assert len(result) == 1
    result.index((2018, 4))


class MockProcesses(object):
    @staticmethod
    def process_ersaaccount(c):
        pass
    @staticmethod
    def process_attachedstorage(c):
        pass
    @staticmethod
    def process_attachedstoragebackup(c):
        pass
    @staticmethod
    def process_hpcsummary(y, m, c):
        pass
    @staticmethod
    def process_allocationsummary(y, m, c):
        pass
    @staticmethod
    def process_hpcstorage(y, m, c):
        pass
    @staticmethod
    def process_nectar(y, m, c):
        pass
    @staticmethod
    def process_tango(y, m, c):
        pass
    @staticmethod
    def process_nova_flavor(c):
        pass
    @staticmethod
    def process_tango_contract(c):
        pass
    @staticmethod
    def process_nectar_contract(c):
        pass


class StubConfig(object):
    def get(self, key):
        return None


def test_process01():
    """ can we process for the default number of months? """
    object_under_test.p = MockProcesses()
    def mock_now_provider():
        return pendulum.create(2018, 3, 15)
    object_under_test._now_provider = mock_now_provider
    object_under_test.logger.setLevel(logging.WARN)
    result = object_under_test.process(2, StubConfig())
    object_under_test.logger.setLevel(logging.DEBUG)
    assert result['success'] == True
    months_processed = result['months_processed']
    months_processed.index('2018-2')
    months_processed.index('2018-3')
    assert result['elapsed_ms'] >= 0

def test_calculate_cost01():
    """ can we calculate the cost for a simple scenario """
    usage = 100
    fee = 0.15
    result = object_under_test.calculate_cost(usage, fee)
    assert result == 15


def test_calculate_cost02():
    """ can we calculate the cost when 0 < result < 1 """
    usage = 1
    fee = 0.15
    result = object_under_test.calculate_cost(usage, fee)
    assert result == 0.15



def test_calculate_cost03():
    """ can we handle a Decimal as a param """
    usage = 12
    fee = Decimal('0.15')
    result = object_under_test.calculate_cost(usage, fee)
    assert result == Decimal('1.8')


def test_seconds_to_hours01():
    """ can we handle >1 hour as a result """
    ninety_minutes = 5400
    result = object_under_test.seconds_to_hours(ninety_minutes)
    assert result == Decimal('1.5')


def test_seconds_to_hours02():
    """ can we handle <1 hour as a result """
    result = object_under_test.seconds_to_hours(360)
    assert result == Decimal('0.1')


def test_seconds_to_hours03():
    """ is the result a Decimal, not a float """
    result = object_under_test.seconds_to_hours(360)
    assert type(result) == Decimal


def test_clean_types01():
    """ can we convert a decimal to a float? """
    source = {
        'foo': Decimal('1.23'),
        'bar': 'blah'
    }
    result = object_under_test._clean_types(source)
    assert type(result['foo']) == float
    assert result['foo'] == 1.23
    assert result['bar'] == 'blah'
