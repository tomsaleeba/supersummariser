# -*- coding: utf-8 -*-
"""Database module, including the SQLAlchemy database object and DB-related utilities."""
from .compat import basestring
from .extensions import db
from sqlalchemy.orm import backref # 

# Alias common SQLAlchemy names
Column = db.Column
relationship = db.relationship


class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete) operations."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()


class Model(CRUDMixin, db.Model):
    """Base model class that includes CRUD convenience methods."""

    __abstract__ = True


# From Mike Bayer's "Building the app" talk
# https://speakerdeck.com/zzzeek/building-the-app
class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named ``id`` to any declarative-mapped class."""

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def get_by_id(cls, record_id):
        """Get record by ID."""
        if any(
                (isinstance(record_id, basestring) and record_id.isdigit(),
                 isinstance(record_id, (int, float))),
        ):
            return cls.query.get(int(record_id))
        return None


def reference_col(tablename, nullable=False, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::
        class Product(...):
            category_id = reference_col('category')
            category = relationship('Category', backref='products')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(tablename, pk_name)),
        nullable=nullable, **kwargs)


class MonthlyModel(Model):
    __abstract__ = True
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)


class HpcSummaryUsage(MonthlyModel, SurrogatePK):
    """ HPC usage """
    cores = db.Column(db.Integer)
    cpu_seconds = db.Column(db.Integer)
    job_count = Column(db.Integer)
    owner = db.Column(db.String(64))
    queue = db.Column(db.String(64))


class Contract(Model, SurrogatePK):
    """ eRSA contract """
    contract_type = db.Column(db.String(32))
    allocated = db.Column(db.Integer)
    unit_price = db.Column(db.Numeric)
    account_id = reference_col('account')
    file_system_name = db.Column(db.String(512)) # FIXME only used for attachedstorage contracts, might be able to split this class into a hierarchy
    openstack_project_id = db.Column(db.String(128)) # FIXME only used for tango, might split too like above

class AccountContact(Model, SurrogatePK):
    managerusername = db.Column(db.String(64))
    manageremail = db.Column(db.String(64))
    managertitle = db.Column(db.String(256))
    managerunit = db.Column(db.String(256))
    manager = db.Column(db.String(128))
    account_id = reference_col('account')


class Account(Model, SurrogatePK):
    order_id = db.Column(db.String(64))
    name = db.Column(db.String(512))
    biller = db.Column(db.String(256))
    account_contact = relationship(AccountContact, backref='account', uselist=False, cascade="all,delete,delete-orphan")
    contract = relationship(Contract, backref='account', uselist=False, cascade="all,delete,delete-orphan")


class HnasVVUsage(MonthlyModel, SurrogatePK):
    """ HNAS VV usage """
    filesystem = db.Column(db.String(256))
    owner = db.Column(db.String(64))
    usage = db.Column(db.Integer)
    files = db.Column(db.Integer)
    virtual_volume = db.Column(db.String(64))
    quota = Column(db.Integer)


class HnasFSUsage(MonthlyModel, SurrogatePK):
    """ HNAS FS usage """
    live_usage = db.Column(db.Integer)
    filesystem = db.Column(db.String(256))
    capacity = db.Column(db.Integer)
    snapshot_usage = Column(db.Integer)
    free = Column(db.Integer)


class HcpUsage(MonthlyModel, SurrogatePK):
    """ HCP usage """
    ingested_bytes = db.Column(db.BigInteger)
    bytes_in = db.Column(db.BigInteger)
    namespace = db.Column(db.String(256))
    reads = Column(db.Integer)
    writes = Column(db.Integer)
    raw_bytes = db.Column(db.BigInteger)
    metadata_only_bytes = Column(db.BigInteger)
    metadata_only_objects = Column(db.Integer)
    deletes = Column(db.Integer)
    tiered_objects = Column(db.Integer)
    bytes_out = Column(db.BigInteger)
    objects = Column(db.Integer)
    tiered_bytes = Column(db.BigInteger)


class XfsUsage(MonthlyModel, SurrogatePK):
    """ XFS usage """
    hard = db.Column(db.BigInteger)
    usage = db.Column(db.BigInteger)
    soft = db.Column(db.BigInteger)
    filesystem = db.Column(db.String(256))
    host = db.Column(db.String(256))


class HpcHomeUsage(MonthlyModel, SurrogatePK):
    """ HPC Home usage """
    hard = db.Column(db.BigInteger)
    usage = db.Column(db.BigInteger)
    soft = db.Column(db.BigInteger)
    owner = db.Column(db.String(128))


class NectarUsage(MonthlyModel, SurrogatePK):
    """ NECTAR usage """
    flavor = db.Column(db.String(128))
    instance_id = db.Column(db.String(128))
    biller = db.Column(db.String(128))
    managerunit = db.Column(db.String(128))
    server = db.Column(db.String(128))
    server_id = db.Column(db.String(128))
    az = db.Column(db.String(128))
    tenant = db.Column(db.String(128))
    account = db.Column(db.String(128))
    image = db.Column(db.String(128))
    span = db.Column(db.BigInteger)
    hypervisor = db.Column(db.String(128))


class TangoUsage(MonthlyModel, SurrogatePK):
    """ Tango usage """
    business_unit = db.Column(db.String(64))
    core = db.Column(db.Integer)
    vm_id = db.Column(db.String(64))
    os = db.Column(db.String(64))
    ram = db.Column(db.Integer)
    server = db.Column(db.String(64))
    storage = db.Column(db.Numeric)
    span = db.Column(db.BigInteger)


class NovaFlavor(Model, SurrogatePK):
    """ NECTAR Nova flavour """
    flavor_id = db.Column(db.String(128))
    vcpus = db.Column(db.Integer)
    ephemeral = db.Column(db.Integer)
    name = db.Column(db.String(128))
    ram = db.Column(db.Integer)
    disk = db.Column(db.Integer)
    is_public = db.Column(db.Boolean)
    openstack_id = db.Column(db.String(128))
