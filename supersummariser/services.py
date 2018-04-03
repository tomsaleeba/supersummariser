# -*- coding: utf-8 -*-
"""Service implementions to keep the main app file tidy"""
import math
import logging
import time

from sqlalchemy import func, or_, and_
from decimal import Decimal
import pendulum

import supersummariser.database as d
from supersummariser.extensions import db, migrate
import supersummariser.processors as p
from supersummariser.settings import ProdConfig

logger = logging.getLogger('services')
logger.setLevel(logging.DEBUG)

BYTES_TO_GB = 1073741824
MB_TO_GB = 1000


def build_dict(src, list_of_fields):
    # FIXME look at access results by dict key, not list index
    result = {}
    i = 0
    for curr in list_of_fields:
        result[curr] = src[i]
        i += 1
    return result


def merge_cols(base_cols, *cols):
    """ merges both sets of columns into a single tuple """
    return base_cols + cols


def calculate_cost(usage, cost):
    return usage * cost


def seconds_to_hours(seconds):
    seconds_per_hour = 3600
    decimal_seconds= Decimal(seconds)
    return decimal_seconds / seconds_per_hour


def _clean_types(source):
    """ converts any types that don't play nice with JSON, like decimal """
    for curr_key in source:
        val = source[curr_key]
        if (type(val) == Decimal):
            source[curr_key] = float(val)
    return source


def get_hpcsummary_simple(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price)
    found = db.session.query(
            *merge_cols(cols,
                func.sum(d.HpcSummaryUsage.cores),
                func.sum(d.HpcSummaryUsage.cpu_seconds),
                func.sum(d.HpcSummaryUsage.job_count)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HpcSummaryUsage.year == year,
            d.HpcSummaryUsage.month == month,
            d.AccountContact.managerusername == d.HpcSummaryUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'unit_price',
            'cores',
            'cpu_seconds',
            'job_count'
        ])
        item['cpu_hours'] = seconds_to_hours(item['cpu_seconds'])
        item['fee_dollars'] = calculate_cost(item['cpu_hours'], item['unit_price'])
        result.append(_clean_types(item))
    return result


def get_hpcsummary_rollup(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.AccountContact.managerusername,
            d.AccountContact.manager,
            d.AccountContact.manageremail,
            d.Contract.unit_price)
    found = db.session.query(
            *merge_cols(cols, 
                func.sum(d.HpcSummaryUsage.cores),
                func.sum(d.HpcSummaryUsage.cpu_seconds),
                func.sum(d.HpcSummaryUsage.job_count),
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HpcSummaryUsage.year == year,
            d.HpcSummaryUsage.month == month,
            d.AccountContact.managerusername == d.HpcSummaryUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'managerusername',
            'manager',
            'manageremail',
            'unit_price',
            'cores',
            'cpu_seconds',
            'job_count'
        ])
        item['cpu_hours'] = seconds_to_hours(item['cpu_seconds'])
        item['fee_dollars'] = calculate_cost(item['cpu_hours'], item['unit_price'])
        result.append(_clean_types(item))
    return result


def get_hpcsummary_detailed(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.AccountContact.managerusername,
            d.AccountContact.manager,
            d.AccountContact.manageremail,
            d.Contract.unit_price,
            d.HpcSummaryUsage.queue)
    found = db.session.query(
            *merge_cols(cols,
                func.sum(d.HpcSummaryUsage.cores),
                func.sum(d.HpcSummaryUsage.cpu_seconds),
                func.sum(d.HpcSummaryUsage.job_count)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HpcSummaryUsage.year == year,
            d.HpcSummaryUsage.month == month,
            d.AccountContact.managerusername == d.HpcSummaryUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'managerusername',
            'manager',
            'manageremail',
            'unit_price',
            'queue',
            'cores',
            'cpu_seconds',
            'job_count'
        ])
        item['cpu_hours'] = seconds_to_hours(item['cpu_seconds'])
        item['cost'] = calculate_cost(item['cpu_hours'], item['unit_price'])
        item['cpu_hours'] = item['cpu_hours']
        result.append(_clean_types(item))
    return result


def get_hpcsummary_chart(org_filter, month_window, config):
    date_bounds = p.get_year_month_for_n_months_ago(month_window)
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price,
            d.HpcSummaryUsage.year,
            d.HpcSummaryUsage.month)
    partial = db.session.query(
            *merge_cols(cols,
                func.sum(d.HpcSummaryUsage.cores),
                func.sum(d.HpcSummaryUsage.cpu_seconds),
                func.sum(d.HpcSummaryUsage.job_count)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.HpcSummaryUsage.year > date_bounds['year'],
                and_(
                    d.HpcSummaryUsage.year == date_bounds['year'],
                    d.HpcSummaryUsage.month > date_bounds['month']
                )),
            d.AccountContact.managerusername == d.HpcSummaryUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols)
    if org_filter:
        partial = partial.filter(d.Account.biller == org_filter)
    found = partial.all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'unit_price',
            'year',
            'month',
            'cores',
            'cpu_seconds',
            'job_count'
        ])
        item['cpu_hours'] = seconds_to_hours(item['cpu_seconds'])
        item['cost'] = calculate_cost(item['cpu_hours'], item['unit_price'])
        item['unit_price'] = item['unit_price']
        item['cpu_hours'] = item['cpu_hours']
        result.append(_clean_types(item))
    return result


def get_allocationsummary_simple(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price)
    contract_filter = or_(
        d.Contract.contract_type == p.CONTRACT_TYPE_STORAGE,
        d.Contract.contract_type == p.CONTRACT_TYPE_STORAGE_BACKUP)
    hnasvv_usage = db.session.query(
            *merge_cols(cols,
                func.sum(d.HnasVVUsage.usage) / MB_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HnasVVUsage.year == year,
            d.HnasVVUsage.month == month,
            d.Contract.file_system_name == d.HnasVVUsage.virtual_volume,
            contract_filter
        ).\
        group_by(*cols).\
        all()
    hnasfs_usage = db.session.query(
            *merge_cols(cols,
                func.sum(d.HnasFSUsage.live_usage) / MB_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HnasFSUsage.year == year,
            d.HnasFSUsage.month == month,
            d.Contract.file_system_name == d.HnasFSUsage.filesystem,
            contract_filter
        ).\
        group_by(*cols).\
        all()
    hcp_usage = db.session.query(
            *merge_cols(cols,
                func.sum(d.HcpUsage.ingested_bytes) / BYTES_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HcpUsage.year == year,
            d.HcpUsage.month == month,
            d.Contract.file_system_name == d.HcpUsage.namespace,
            contract_filter
        ).\
        group_by(*cols).\
        all()
    xfs_usage = db.session.query(
            *merge_cols(cols,
                func.sum(d.XfsUsage.usage) * 1000 / BYTES_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.XfsUsage.year == year,
            d.XfsUsage.month == month,
            d.Contract.file_system_name == d.XfsUsage.filesystem,
            contract_filter
        ).\
        group_by(*cols).\
        all()
    summed_totals = {}
    for curr in hnasvv_usage + hnasfs_usage + hcp_usage + xfs_usage:
        biller = curr[0]
        managerunit = curr[1]
        key = (biller, managerunit)
        unit_price = curr[2]
        usage = curr[3]
        blocks = int(math.ceil(usage / config.get('STORAGE_BLOCK_SIZE_GB')))
        cost = blocks * unit_price
        try:
            record = summed_totals[key]
        except KeyError:
            summed_totals[key] = {
                'usage': 0,
                'blocks': 0,
                'cost': 0
            }
            record = summed_totals[key]
        record['usage'] += usage
        record['blocks'] += blocks
        record['cost'] += cost
    result = [
        _clean_types({
            'biller': x[0],
            'managerunit': x[1],
            'usage': summed_totals[x]['usage'],
            'blocks': summed_totals[x]['blocks'],
            'cost': summed_totals[x]['cost']
        })
        for x in summed_totals]
    return result


def get_allocationsummary_chart(org_filter, month_window, config):
    date_bounds = p.get_year_month_for_n_months_ago(month_window)
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price)
    contract_filter = or_(
        d.Contract.contract_type == p.CONTRACT_TYPE_STORAGE,
        d.Contract.contract_type == p.CONTRACT_TYPE_STORAGE_BACKUP)
    # HNAS Virtual Volume
    hnasvv_cols = merge_cols(cols,
                d.HnasVVUsage.year,
                d.HnasVVUsage.month)
    hnasvv_partial = db.session.query(
            *merge_cols(hnasvv_cols,
                func.sum(d.HnasVVUsage.usage) / MB_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.HnasVVUsage.year > date_bounds['year'],
                and_(
                    d.HnasVVUsage.year == date_bounds['year'],
                    d.HnasVVUsage.month > date_bounds['month']
                )),
            d.Contract.file_system_name == d.HnasVVUsage.virtual_volume,
            contract_filter
        ).\
        group_by(*hnasvv_cols)
    if org_filter:
        hnasvv_partial = hnasvv_partial.filter(d.Account.biller == org_filter)
    hnasvv_usage = hnasvv_partial.all()
    # HNAS FileSystem
    hnasfs_cols = merge_cols(cols,
                d.HnasFSUsage.year,
                d.HnasFSUsage.month)
    hnasfs_partial = db.session.query(
            *merge_cols(hnasfs_cols,
                func.sum(d.HnasFSUsage.live_usage) / MB_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.HnasFSUsage.year > date_bounds['year'],
                and_(
                    d.HnasFSUsage.year == date_bounds['year'],
                    d.HnasFSUsage.month > date_bounds['month']
                )),
            d.Contract.file_system_name == d.HnasFSUsage.filesystem,
            contract_filter
        ).\
        group_by(*hnasfs_cols)
    if org_filter:
        hnasfs_partial = hnasfs_partial.filter(d.Account.biller == org_filter)
    hnasfs_usage = hnasfs_partial.all()
    # HCP
    hcp_cols = merge_cols(cols,
                d.HcpUsage.year,
                d.HcpUsage.month)
    hcp_partial = db.session.query(
            *merge_cols(hcp_cols,
                func.sum(d.HcpUsage.ingested_bytes) / BYTES_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.HcpUsage.year > date_bounds['year'],
                and_(
                    d.HcpUsage.year == date_bounds['year'],
                    d.HcpUsage.month > date_bounds['month']
                )),
            d.Contract.file_system_name == d.HcpUsage.namespace,
            contract_filter
        ).\
        group_by(*hcp_cols)
    if org_filter:
        hcp_partial = hcp_partial.filter(d.Account.biller == org_filter)
    hcp_usage = hcp_partial.all()
    # XFS
    xfs_cols = merge_cols(cols,
                d.XfsUsage.year,
                d.XfsUsage.month)
    xfs_partial = db.session.query(
            *merge_cols(xfs_cols,
                func.sum(d.XfsUsage.usage) * 1000 / BYTES_TO_GB
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.XfsUsage.year > date_bounds['year'],
                and_(
                    d.XfsUsage.year == date_bounds['year'],
                    d.XfsUsage.month > date_bounds['month']
                )),
            d.Contract.file_system_name == d.XfsUsage.filesystem,
            contract_filter
        ).\
        group_by(*xfs_cols)
    if org_filter:
        xfs_partial = xfs_partial.filter(d.Account.biller == org_filter)
    xfs_usage = xfs_partial.all()
    summed_totals = {}
    for curr in hnasvv_usage + hnasfs_usage + hcp_usage + xfs_usage:
        biller = curr[0]
        managerunit = curr[1]
        key = (biller, managerunit)
        unit_price = curr[2]
        year = curr[3]
        month = curr[4]
        usage = curr[5]
        blocks = int(math.ceil(usage / config.get('STORAGE_BLOCK_SIZE_GB')))
        cost = blocks * unit_price
        try:
            record = summed_totals[key]
        except KeyError:
            summed_totals[key] = {
                'usage': 0,
                'blocks': 0,
                'cost': 0
            }
            record = summed_totals[key]
        record['usage'] += usage
        record['blocks'] += blocks
        record['cost'] += cost
        record['month'] = month
        record['year'] = year
    result = [
        _clean_types({
            'biller': x[0],
            'managerunit': x[1],
            'usage': summed_totals[x]['usage'],
            'blocks': summed_totals[x]['blocks'],
            'cost': summed_totals[x]['cost'],
            'month': summed_totals[x]['month'],
            'year': summed_totals[x]['year']
        })
        for x in summed_totals]
    return result


def get_hpcstorage_simple(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit)
    found = db.session.query(
            *merge_cols(cols,
                func.sum(d.HpcHomeUsage.usage)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.HpcHomeUsage.year == year,
            d.HpcHomeUsage.month == month,
            d.AccountContact.managerusername == d.HpcHomeUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit'
        ])
        raw_usage = row[2]
        usage_gb = raw_usage * 1024 / BYTES_TO_GB
        item['usage'] = usage_gb
        if usage_gb < 1 and round(usage_gb) == 0:
            blocks = 0
        else:
            blocks = int(math.ceil(usage_gb / config.get('STORAGE_BLOCK_SIZE_GB')))
        item['blocks'] = blocks
        item['cost'] = blocks * config.get('HPC_HOME_BLOCK_PRICE')
        result.append(_clean_types(item))
    return result


def get_hpcstorage_chart(org_filter, month_window, config):
    date_bounds = p.get_year_month_for_n_months_ago(month_window)
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.HpcHomeUsage.year,
            d.HpcHomeUsage.month)
    partial = db.session.query(
            *merge_cols(cols,
                func.sum(d.HpcHomeUsage.usage)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.HpcHomeUsage.year > date_bounds['year'],
                and_(
                    d.HpcHomeUsage.year == date_bounds['year'],
                    d.HpcHomeUsage.month > date_bounds['month']
                )),
            d.AccountContact.managerusername == d.HpcHomeUsage.owner,
            d.Contract.contract_type == p.CONTRACT_TYPE_ERSA_ACCOUNT
        ).\
        group_by(*cols)
    if org_filter:
        partial = partial.filter(d.Account.biller == org_filter)
    found = partial.all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'year',
            'month'
        ])
        raw_usage = row[4]
        usage_gb = raw_usage * 1024 / BYTES_TO_GB
        item['usage'] = usage_gb
        if usage_gb < 1 and round(usage_gb) == 0:
            blocks = 0
        else:
            blocks = int(math.ceil(usage_gb / config.get('STORAGE_BLOCK_SIZE_GB')))
        item['blocks'] = blocks
        item['cost'] = blocks * config.get('HPC_HOME_BLOCK_PRICE')
        result.append(_clean_types(item))
    return result


def get_nectar_simple(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit)
    found = db.session.query(
            *merge_cols(cols,
                func.sum(d.NovaFlavor.vcpus)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.NectarUsage.year == year,
            d.NectarUsage.month == month,
            d.NectarUsage.flavor == d.NovaFlavor.openstack_id,
            d.NectarUsage.tenant == d.Contract.openstack_project_id,
            d.Contract.contract_type == p.CONTRACT_TYPE_NECTAR
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit'
        ])
        core_count = row[2]
        item['core'] = core_count
        item['cost'] = config.get('NECTAR_NOVA_VCPU_PRICE') * core_count
        result.append(_clean_types(item))
    return result


def get_nectar_chart(org_filter, month_window, config):
    date_bounds = p.get_year_month_for_n_months_ago(month_window)
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.NectarUsage.year,
            d.NectarUsage.month)
    partial = db.session.query(
            *merge_cols(cols,
                func.sum(d.NovaFlavor.vcpus)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.NectarUsage.year > date_bounds['year'],
                and_(
                    d.NectarUsage.year == date_bounds['year'],
                    d.NectarUsage.month > date_bounds['month']
                )),
            d.NectarUsage.flavor == d.NovaFlavor.openstack_id,
            d.NectarUsage.tenant == d.Contract.openstack_project_id,
            d.Contract.contract_type == p.CONTRACT_TYPE_NECTAR
        ).\
        group_by(*cols)
    if org_filter:
        partial = partial.filter(d.Account.biller == org_filter)
    found = partial.all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'year',
            'month'
        ])
        core_count = row[4]
        item['core'] = core_count
        item['cost'] = config.get('NECTAR_NOVA_VCPU_PRICE') * core_count
        result.append(_clean_types(item))
    return result


def get_tango_simple(year, month, config):
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price)
    found = db.session.query(
            *merge_cols(cols,
                func.sum(d.TangoUsage.core)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            d.TangoUsage.year == year,
            d.TangoUsage.month == month,
            d.TangoUsage.vm_id == d.Contract.openstack_project_id,
            d.Contract.contract_type == p.CONTRACT_TYPE_TANGO
        ).\
        group_by(*cols).\
        all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'unit_price'
        ])
        core_count = row[3]
        item['core'] = core_count
        item['cost'] = item['unit_price'] * core_count
        result.append(_clean_types(item))
    return result


def get_tango_chart(org_filter, month_window, config):
    date_bounds = p.get_year_month_for_n_months_ago(month_window)
    cols = (d.Account.biller,
            d.AccountContact.managerunit,
            d.Contract.unit_price,
            d.TangoUsage.year,
            d.TangoUsage.month)
    partial = db.session.query(
            *merge_cols(cols,
                func.sum(d.TangoUsage.core)
            )
        ).\
        join(d.AccountContact).\
        join(d.Contract).\
        filter(
            or_(d.TangoUsage.year > date_bounds['year'],
                and_(
                    d.TangoUsage.year == date_bounds['year'],
                    d.TangoUsage.month > date_bounds['month']
                )),
            d.TangoUsage.vm_id == d.Contract.openstack_project_id,
            d.Contract.contract_type == p.CONTRACT_TYPE_TANGO
        ).\
        group_by(*cols)
    if org_filter:
        partial = partial.filter(d.Account.biller == org_filter)
    found = partial.all()
    result = []
    for row in found:
        item = build_dict(row, [
            'biller',
            'managerunit',
            'unit_price',
            'year',
            'month'
        ])
        item['unit_price'] = item['unit_price']
        core_count = row[5]
        item['core'] = core_count
        item['cost'] = item['unit_price'] * core_count
        result.append(_clean_types(item))
    return result


def _now_in_ms():
    return int(round(time.time() * 1000.0))


def _get_months_to_process(months_ago, now):
    result = []
    include_current_month = -1
    count_backwards = -1
    adjusted_months_ago = months_ago - 1
    for curr in range(adjusted_months_ago, include_current_month, count_backwards):
        past = now.subtract(months=curr)
        result.append((past.year, past.month))
    return result


def _now_provider():
    """ provides a pendulum *now* in a test-friendly way """
    return pendulum.now()


def process(months_back, config):
    """ pull all the latest data and persist it """
    start_ms = _now_in_ms()
    logger.info('Processing for %d months back' % months_back)
    try:
        p.process_ersaaccount(config)
        p.process_attachedstorage(config)
        p.process_attachedstoragebackup(config)
        p.process_nova_flavor(config)
        p.process_nectar_contract(config)
        p.process_tango_contract(config)
        months = _get_months_to_process(months_back, _now_provider())
        for curr in months:
            year = curr[0]
            month = curr[1]
            p.process_hpcsummary(year, month, config)
            p.process_allocationsummary(year, month, config)
            p.process_hpcstorage(year, month, config)
            p.process_nectar(year, month, config)
            p.process_tango(year, month, config)
        return {
            'success': True,
            'months_processed': ["{}-{}".format(x[0], x[1]) for x in months],
            'elapsed_ms': _now_in_ms() - start_ms
        }
    except p.ProcessingFailedError as e:
        return {
            'success': False,
            'message': str(e),
            'elapsed_ms': _now_in_ms() - start_ms
        }
