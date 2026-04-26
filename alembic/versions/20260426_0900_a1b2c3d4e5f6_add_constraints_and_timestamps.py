"""add_constraints_and_timestamps

Revision ID: a1b2c3d4e5f6
Revises: f839c3f848b9
Create Date: 2026-04-26 09:00:00.000000

修复清单（22 项）对应 DB 变更：
- purchase_orders: 添加 committed_at 时间戳字段
- weighbridge_records: 添加 UniqueConstraint(order_id, record_type)
- contract_signatures: 添加 UniqueConstraint(contract_id, signer_id)
- brokers: 添加 UniqueConstraint(user_id)
- drivers: 添加 UniqueConstraint(user_id)
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f839c3f848b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. purchase_orders: 添加 committed_at 字段
    op.add_column(
        'purchase_orders',
        sa.Column('committed_at', sa.DateTime(), nullable=True)
    )

    # 2. weighbridge_records: 同一订单同类型只能录一条磅单
    op.create_unique_constraint(
        'uq_weighbridge_order_type',
        'weighbridge_records',
        ['order_id', 'record_type']
    )

    # 3. contract_signatures: 同一合同同一签章人只能签一次
    op.create_unique_constraint(
        'uq_contract_signature',
        'contract_signatures',
        ['contract_id', 'signer_id']
    )

    # 4. brokers: 一个用户只能有一个经纪人档案
    op.create_unique_constraint(
        'uq_brokers_user_id',
        'brokers',
        ['user_id']
    )

    # 5. drivers: 一个用户只能有一个司机档案
    op.create_unique_constraint(
        'uq_drivers_user_id',
        'drivers',
        ['user_id']
    )


def downgrade() -> None:
    op.drop_constraint('uq_drivers_user_id', 'drivers', type_='unique')
    op.drop_constraint('uq_brokers_user_id', 'brokers', type_='unique')
    op.drop_constraint('uq_contract_signature', 'contract_signatures', type_='unique')
    op.drop_constraint('uq_weighbridge_order_type', 'weighbridge_records', type_='unique')
    op.drop_column('purchase_orders', 'committed_at')
