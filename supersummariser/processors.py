import logging

import requests
import pendulum

import supersummariser.database as database

logger = logging.getLogger('processors')
logger.setLevel(logging.DEBUG)
db = database.db

adelaide_tz = 'Australia/Adelaide'
CONTRACT_TYPE_ERSA_ACCOUNT = 'ersa_account'
CONTRACT_TYPE_TANGO = 'tango_contract'
CONTRACT_TYPE_NECTAR = 'nectar_contract'
CONTRACT_TYPE_STORAGE = 'attached_storage'
CONTRACT_TYPE_STORAGE_BACKUP = 'attached_storage_backup'

def get(field_name, target):
    try:
        result = target[field_name]
        return result
    except KeyError:
            return None


def _log(year, month, service):
    logger.debug('%d/%d processing %s' % (year, month, service))


def _dedupe_list_of_dicts(list_of_dicts):
    # thanks https://stackoverflow.com/a/31793090/1410035
    return list(map(dict, frozenset(frozenset(i.items()) for i in list_of_dicts)))


def _apiv2_contract_helper(url, contract_type, config):
    def handler(json_body):
        orig_length = len(json_body)
        dedupe_json_body = _dedupe_list_of_dicts(json_body)
        dedupe_length = len(dedupe_json_body)
        dupes_count = orig_length - dedupe_length
        logger.debug('retrieved %d records for contract_type=%s, %d were duplicates' % (orig_length, contract_type, dupes_count))
        for curr in dedupe_json_body:
            order_id = get('orderID', curr)
            name = get('name', curr)
            biller = get('biller', curr)
            allocated = get('allocated', curr)
            openstack_project_id=get('OpenstackProjectID', curr)
            file_system_name=get('FileSystemName', curr)
            # if other columns are added to the model, make sure this
            # delete query is specific enough to find unique records
            existing_records = database.Account.query.filter(
                database.Account.id==database.Contract.account_id,
                database.Account.order_id==order_id,
                database.Account.name==name,
                database.Account.biller==biller,
                database.Contract.openstack_project_id==openstack_project_id,
                database.Contract.file_system_name==file_system_name,
                database.Contract.allocated==allocated,
                database.Contract.contract_type==contract_type).all()
            for curr_existing in existing_records:
                curr_existing.account_contact.delete()
                curr_existing.contract.delete()
                curr_existing.delete()
            account_contact = database.AccountContact(
                managerusername=get('managerusername', curr),
                manageremail=get('manageremail', curr),
                managertitle=get('managertitle', curr),
                managerunit=get('managerunit', curr),
                manager=get('manager', curr),
            )
            contract = database.Contract(
                contract_type=contract_type,
                allocated=allocated,
                unit_price=get('unitPrice', curr),
                file_system_name=file_system_name,
                openstack_project_id=openstack_project_id
            )
            account = database.Account(
                order_id=order_id,
                name=name,
                biller=biller,
                account_contact=account_contact,
                contract=contract
            )
            account.save(commit=False)
        db.session.commit()
    _get_json(config, url, handler)


def process_ersaaccount(config):
    """ pull and store the HPC contract data """
    url = config.get('CRM_SERVER') + '/api/v2/contract/ersaaccount/'
    _apiv2_contract_helper(url, CONTRACT_TYPE_ERSA_ACCOUNT, config)


def process_tango_contract(config):
    url = config.get('CRM_SERVER') + '/api/v2/contract/tangocloudvm/'
    _apiv2_contract_helper(url, CONTRACT_TYPE_TANGO, config)


def process_nectar_contract(config):
    url = config.get('CRM_SERVER') + '/api/v2/contract/nectarcloudvm/'
    _apiv2_contract_helper(url, CONTRACT_TYPE_NECTAR, config)


def process_attachedstorage(config):
    """ pull and store the attached storage contract data """
    url = config.get('CRM_SERVER') + '/api/v2/contract/attachedstorage/'
    _apiv2_contract_helper(url, CONTRACT_TYPE_STORAGE, config)


def process_attachedstoragebackup(config):
    """ pull and store the attached storage for backups contract data """
    url = config.get('CRM_SERVER') + '/api/v2/contract/attachedbackupstorage/'
    _apiv2_contract_helper(url, CONTRACT_TYPE_STORAGE_BACKUP, config)


def get_start(year, month):
    return pendulum.create(year, month, 1, 0, 0, 0, 0, tz=adelaide_tz)


def get_start_ms(year, month):
    return get_start(year, month).int_timestamp


def get_end_ms(year, month):
    start_of_month = get_start(year, month)
    end_of_month = start_of_month.end_of('month')
    return end_of_month.int_timestamp


def get_year_month_for_n_months_ago(months_ago):
    now = pendulum.now(tz=adelaide_tz)
    earlier = now.subtract(months=months_ago)
    return {
        'year': earlier.year,
        'month': earlier.month
    }


def process_hpcsummary(year, month, config):
    """ pull and store the HpcSummary data """
    _log(year, month, 'HPC Summary')
    start_ms = get_start_ms(year, month)
    end_ms = get_end_ms(year, month)
    def handler(json_body):
        db.session.query(database.HpcSummaryUsage).filter(
            database.HpcSummaryUsage.year==year,
            database.HpcSummaryUsage.month==month).delete()
        for curr in json_body:
            record = database.HpcSummaryUsage(
                year=year,
                month=month,
                cores=get('cores', curr),
                cpu_seconds=get('cpu_seconds', curr),
                job_count=get('job_count', curr),
                owner=get('owner', curr),
                queue=get('queue', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/hpc/job/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), start_ms, end_ms),
        handler)

def _process_allocationsummary_hnasvv(year, month, start_ms, end_ms, config):
    def handler(json_body):
        db.session.query(database.HnasVVUsage).filter(
            database.HnasVVUsage.year==year,
            database.HnasVVUsage.month==month).delete()
        for curr in json_body:
            record = database.HnasVVUsage(
                year=year,
                month=month,
                filesystem=get('filesystem', curr),
                owner=get('owner', curr),
                usage=get('usage', curr),
                files=get('files', curr),
                virtual_volume=get('virtual_volume', curr),
                quota=get('quota', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/hnas/virtual-volume%2Fusage/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), start_ms, end_ms),
        handler)

def _process_allocationsummary_hnasfs(year, month, start_ms, end_ms, config):
    def handler(json_body):
        db.session.query(database.HnasFSUsage).filter(
            database.HnasFSUsage.year==year,
            database.HnasFSUsage.month==month).delete()
        for curr in json_body:
            record = database.HnasFSUsage(
                year=year,
                month=month,
                live_usage=get('live_usage', curr),
                filesystem=get('filesystem', curr),
                capacity=get('capacity', curr),
                snapshot_usage=get('snapshot_usage', curr),
                free=get('free', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/hnas/filesystem%2Fusage/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), start_ms, end_ms),
        handler)


def _process_allocationsummary_hcp(year, month, start_ms, end_ms, config):
    def handler(json_body):
        db.session.query(database.HcpUsage).filter(
            database.HcpUsage.year==year,
            database.HcpUsage.month==month).delete()
        for curr in json_body:
            record = database.HcpUsage(
                year=year,
                month=month,
                ingested_bytes=get('ingested_bytes', curr),
                bytes_in=get('bytes_in', curr),
                namespace=get('namespace', curr),
                reads=get('reads', curr),
                writes=get('writes', curr),
                raw_bytes=get('raw_bytes', curr),
                metadata_only_bytes=get('metadata_only_bytes', curr),
                metadata_only_objects=get('metadata_only_objects', curr),
                deletes=get('deletes', curr),
                tiered_objects=get('tiered_objects', curr),
                bytes_out=get('bytes_out', curr),
                objects=get('objects', curr),
                tiered_bytes=get('tiered_bytes', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/hcp/usage/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), start_ms, end_ms),
        handler)


def _process_allocationsummary_xfs(year, month, start_ms, end_ms, config):
    def handler(json_body):
        db.session.query(database.XfsUsage).filter(
            database.XfsUsage.year==year,
            database.XfsUsage.month==month).delete()
        for curr in json_body:
            record = database.XfsUsage(
                year=year,
                month=month,
                hard=get('hard', curr),
                usage=get('usage', curr),
                soft=get('soft', curr),
                filesystem=get('filesystem', curr),
                host=get('host', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/xfs/usage/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), start_ms, end_ms),
        handler)


def process_allocationsummary(year, month, config):
    """ pull and store the components of the AllocationSummary (National Storage) data """
    _log(year, month, 'Allocation Summary')
    start_ms = get_start_ms(year, month)
    end_ms = get_end_ms(year, month)
    _process_allocationsummary_hnasvv(year, month, start_ms, end_ms, config)
    _process_allocationsummary_hcp(year, month, start_ms, end_ms, config)
    _process_allocationsummary_hnasfs(year, month, start_ms, end_ms, config)
    _process_allocationsummary_xfs(year, month, start_ms, end_ms, config)


class ProcessingFailedError(Exception):
    pass


def _get_json(config, url, callback):
    headers = {config.get('AUTH_HEADER_KEY') : config.get('ERSA_AUTH_TOKEN')}
    resp = requests.get(url, headers=headers, verify=config.get('SSL_VERIFY'),
            timeout=config.get('REMOTE_SERVER_CONNECT_TIMEOUT_SECS'))
    expected_status_code = 200
    actual_status_code = resp.status_code
    if actual_status_code == 404:
        logger.info('No data (404) at url=%s, skipping and continuing' % url)
        return None # TODO is this appropriate? Maybe should return a poison-pill.
    if actual_status_code != expected_status_code:
        raise ProcessingFailedError('Expected %d response code but got %d when calling %s' %
            (expected_status_code, actual_status_code, url))
    try:
        return callback(resp.json())
    except ValueError as e:
        content_type = resp.headers['Content-type']
        raise ProcessingFailedError('Expected a JSON response from %s but got %s' % (url, content_type)) from e


class NoFilesystemIdFoundError(Exception):
    pass


def _get_filesystem_id(name, config):
    def handler(json_body):
        for curr in json_body:
            curr_name = curr['name']
            if name in curr_name: # FIXME copied existing JS code but worried about false positives
                return curr['id']
        raise NoFilesystemIdFoundError('Data problem: no match found for filesystem name="%s",' +
                ' cannot continue without it' % name)
    return _get_json(config, '{}/xfs/filesystem'.format(config.get('USAGE_SERVER')), handler)


def process_hpcstorage(year, month, config):
    """ pull and store HPC Storage (Home Account Storage) """
    _log(year, month, 'HPC Storage')
    start_ms = get_start_ms(year, month)
    end_ms = get_end_ms(year, month)
    filesystem_name = config.get('HPC_STORAGE_FSNAME')
    filesystem_id = _get_filesystem_id(filesystem_name, config)
    def handler(json_body):
        db.session.query(database.HpcHomeUsage).filter(
            database.HpcHomeUsage.year==year,
            database.HpcHomeUsage.month==month).delete()
        for curr in json_body:
            record = database.HpcHomeUsage(
                year=year,
                month=month,
                hard=get('hard', curr),
                usage=get('usage', curr),
                soft=get('soft', curr),
                owner=get('owner', curr)
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, '{}/xfs/filesystem/{}/summary?start={}&end={}'.\
            format(config.get('USAGE_SERVER'), filesystem_id, start_ms, end_ms),
        handler)


def process_nectar(year, month, config):
    """ pull and store NECTAR """
    _log(year, month, 'NECTAR')
    start_ms = get_start_ms(year, month)
    end_ms = get_end_ms(year, month)
    def handler(json_body):
        def get_manager_prop(record, index):
            try:
                return record['manager'][index]
            except IndexError:
                return None
        db.session.query(database.NectarUsage).filter(
            database.NectarUsage.year==year,
            database.NectarUsage.month==month).delete()
        for curr in json_body:
            record = database.NectarUsage(
                year=year,
                month=month,
                flavor=get('flavor', curr),
                instance_id=get('instance_id', curr),
                biller=get_manager_prop(curr, 0),
                managerunit=get_manager_prop(curr, 1),
                server=get('server', curr),
                server_id=get('server_id', curr),
                az=get('az', curr),
                tenant=get('tenant', curr),
                account=get('account', curr),
                image=get('image', curr),
                span=get('span', curr),
                hypervisor=get('hypervisor', curr),
            )
            record.save(commit=False)
        db.session.commit()
    try:
        _get_json(config, '{}/usage/nova/NovaUsage_{}_{}.json'.\
                format(config.get('REPORTING_SERVER'), start_ms, end_ms),
            handler)
    except ProcessingFailedError as e:
        logger.warn('Problem getting NECTAR data for %d/%d. ' % (month, year) +
                "Endpoint doesn't use 404 status code like we want.")


def process_tango(year, month, config):
    """ pull and store Tango """
    _log(year, month, 'Tango')
    start_ms = get_start_ms(year, month)
    end_ms = get_end_ms(year, month)
    def handler(json_body):
        db.session.query(database.TangoUsage).filter(
            database.TangoUsage.year==year,
            database.TangoUsage.month==month).delete()
        for curr in json_body:
            record = database.TangoUsage(
                year=year,
                month=month,
                business_unit=get('businessUnit', curr),
                core=get('core', curr),
                vm_id=get('id', curr),
                os=get('os', curr),
                ram=get('ram', curr),
                server=get('server', curr),
                storage=get('storage', curr),
                span=get('span', curr),
            )
            record.save(commit=False)
        db.session.commit()
    try:
        _get_json(config, '{}/vms/instance?start={}&end={}'.\
                format(config.get('USAGE_SERVER'), start_ms, end_ms),
            handler)
    except ProcessingFailedError as e:
        logger.warn('Problem getting Tango data for %d/%d. ' % (month, year) +
                "Endpoint doesn't use 404 status code like we want")


def process_nova_flavor(config):
    """ pull and store the NECTAR Nova flavor data """
    url = config.get('USAGE_SERVER') + '/nova/flavor'
    def handler(json_body):
        logger.debug('retrieved %d records nova flavor' % len(json_body))
        for curr in json_body:
            flavor_id = get('id', curr)
            database.NovaFlavor.query.filter_by(flavor_id=flavor_id).delete()
            record = database.NovaFlavor(
                flavor_id=flavor_id,
                vcpus=get('vcpus', curr),
                ephemeral=get('ephemeral', curr),
                name=get('name', curr),
                ram=get('ram', curr),
                disk=get('disk', curr),
                is_public=get('public', curr),
                openstack_id=get('openstack_id', curr),
            )
            record.save(commit=False)
        db.session.commit()
    _get_json(config, url, handler)
