"""empty message

Revision ID: 2940ffe55dfe
Revises: 
Create Date: 2018-03-31 21:49:35.733975

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2940ffe55dfe'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.String(length=64), nullable=True),
    sa.Column('name', sa.String(length=512), nullable=True),
    sa.Column('biller', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hcp_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('ingested_bytes', sa.BigInteger(), nullable=True),
    sa.Column('bytes_in', sa.BigInteger(), nullable=True),
    sa.Column('namespace', sa.String(length=256), nullable=True),
    sa.Column('reads', sa.Integer(), nullable=True),
    sa.Column('writes', sa.Integer(), nullable=True),
    sa.Column('raw_bytes', sa.BigInteger(), nullable=True),
    sa.Column('metadata_only_bytes', sa.BigInteger(), nullable=True),
    sa.Column('metadata_only_objects', sa.Integer(), nullable=True),
    sa.Column('deletes', sa.Integer(), nullable=True),
    sa.Column('tiered_objects', sa.Integer(), nullable=True),
    sa.Column('bytes_out', sa.BigInteger(), nullable=True),
    sa.Column('objects', sa.Integer(), nullable=True),
    sa.Column('tiered_bytes', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hnas_fs_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('live_usage', sa.Integer(), nullable=True),
    sa.Column('filesystem', sa.String(length=256), nullable=True),
    sa.Column('capacity', sa.Integer(), nullable=True),
    sa.Column('snapshot_usage', sa.Integer(), nullable=True),
    sa.Column('free', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hnas_vv_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('filesystem', sa.String(length=256), nullable=True),
    sa.Column('owner', sa.String(length=64), nullable=True),
    sa.Column('usage', sa.Integer(), nullable=True),
    sa.Column('files', sa.Integer(), nullable=True),
    sa.Column('virtual_volume', sa.String(length=64), nullable=True),
    sa.Column('quota', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hpc_home_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('hard', sa.BigInteger(), nullable=True),
    sa.Column('usage', sa.BigInteger(), nullable=True),
    sa.Column('soft', sa.BigInteger(), nullable=True),
    sa.Column('owner', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('hpc_summary_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('cores', sa.Integer(), nullable=True),
    sa.Column('cpu_seconds', sa.Integer(), nullable=True),
    sa.Column('job_count', sa.Integer(), nullable=True),
    sa.Column('owner', sa.String(length=64), nullable=True),
    sa.Column('queue', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('nectar_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('flavor', sa.String(length=128), nullable=True),
    sa.Column('instance_id', sa.String(length=128), nullable=True),
    sa.Column('server', sa.String(length=128), nullable=True),
    sa.Column('server_id', sa.String(length=128), nullable=True),
    sa.Column('az', sa.String(length=128), nullable=True),
    sa.Column('tenant', sa.String(length=128), nullable=True),
    sa.Column('account', sa.String(length=128), nullable=True),
    sa.Column('image', sa.String(length=128), nullable=True),
    sa.Column('span', sa.BigInteger(), nullable=True),
    sa.Column('hypervisor', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tango_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('business_unit', sa.String(length=64), nullable=True),
    sa.Column('core', sa.Integer(), nullable=True),
    sa.Column('vm_id', sa.String(length=64), nullable=True),
    sa.Column('os', sa.String(length=64), nullable=True),
    sa.Column('ram', sa.Integer(), nullable=True),
    sa.Column('server', sa.String(length=64), nullable=True),
    sa.Column('storage', sa.Numeric(), nullable=True),
    sa.Column('span', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('xfs_usage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('hard', sa.BigInteger(), nullable=True),
    sa.Column('usage', sa.BigInteger(), nullable=True),
    sa.Column('soft', sa.BigInteger(), nullable=True),
    sa.Column('filesystem', sa.String(length=256), nullable=True),
    sa.Column('host', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('account_contact',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('managerusername', sa.String(length=64), nullable=True),
    sa.Column('manageremail', sa.String(length=64), nullable=True),
    sa.Column('managertitle', sa.String(length=256), nullable=True),
    sa.Column('managerunit', sa.String(length=256), nullable=True),
    sa.Column('manager', sa.String(length=128), nullable=True),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('contract',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contract_type', sa.String(length=32), nullable=True),
    sa.Column('allocated', sa.Integer(), nullable=True),
    sa.Column('unit_price', sa.Numeric(), nullable=True),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('file_system_name', sa.String(length=512), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['account.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('contract')
    op.drop_table('account_contact')
    op.drop_table('xfs_usage')
    op.drop_table('tango_usage')
    op.drop_table('nectar_usage')
    op.drop_table('hpc_summary_usage')
    op.drop_table('hpc_home_usage')
    op.drop_table('hnas_vv_usage')
    op.drop_table('hnas_fs_usage')
    op.drop_table('hcp_usage')
    op.drop_table('account')
    # ### end Alembic commands ###
