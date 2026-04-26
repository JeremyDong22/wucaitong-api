-- =====================================================
-- 物采通数据库建表脚本 v6.1
-- 数据库：wucaitong_db
-- PostgreSQL 16
-- 修复：broker_tasks 移至 purchase_orders 之前、恢复 warehouse_keepers.merchant_id
-- =====================================================

CREATE DATABASE wucaitong_db;
\c wucaitong_db;

-- =====================================================
-- 1. 用户身份层
-- =====================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(16) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL,
    status VARCHAR(16) DEFAULT 'active',
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_users_role CHECK (role IN ('W', 'C', 'B', 'A', 'BROKER', 'DRIVER', 'WAREHOUSE_KEEPER')),
    CONSTRAINT chk_users_status CHECK (status IN ('active', 'suspended', 'deleted'))
);

CREATE TABLE user_wx_auth (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mini_program_appid VARCHAR(64) NOT NULL,
    open_id VARCHAR(64) NOT NULL,
    union_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(mini_program_appid, open_id)
);

CREATE TABLE natural_persons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    real_name VARCHAR(64) NOT NULL,
    id_card_no VARCHAR(18),
    id_card_front_oss VARCHAR(512),
    id_card_back_oss VARCHAR(512),
    auth_status VARCHAR(16) DEFAULT 'pending',
    auth_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_natural_persons_auth_status CHECK (auth_status IN ('pending', 'verified', 'failed'))
);

CREATE TABLE enterprises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    credit_code VARCHAR(32) UNIQUE,
    legal_person VARCHAR(64),
    license_oss VARCHAR(512),
    auth_status VARCHAR(16) DEFAULT 'pending',
    auth_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_enterprises_auth_status CHECK (auth_status IN ('pending', 'verified', 'failed'))
);

-- =====================================================
-- 2. 商品字典层（必须在 merchant_relations 之前）
-- =====================================================

CREATE TABLE product_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_code VARCHAR(32) NOT NULL UNIQUE,
    category_name VARCHAR(64) NOT NULL,
    sub_category VARCHAR(64),
    spec_template JSON,
    grade_options JSON,
    tax_code VARCHAR(32),
    tax_rate DECIMAL(5,2),
    unit VARCHAR(16) DEFAULT 'ton',
    is_hazardous BOOLEAN DEFAULT FALSE,
    status VARCHAR(16) DEFAULT 'active',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_product_categories_status CHECK (status IN ('active', 'inactive'))
);

-- =====================================================
-- 3. 角色档案层
-- =====================================================

CREATE TABLE merchants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enterprise_id UUID NOT NULL REFERENCES enterprises(id),
    merchant_type VARCHAR(8) NOT NULL,
    sub_domain VARCHAR(64) UNIQUE,
    logo_oss VARCHAR(512),
    primary_color VARCHAR(16),
    allowed_product_categories JSON,
    status VARCHAR(16) DEFAULT 'pending',
    approved_by UUID,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_merchants_type CHECK (merchant_type IN ('C', 'B')),
    CONSTRAINT chk_merchants_status CHECK (status IN ('pending', 'active', 'suspended'))
);

CREATE TABLE brokers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    natural_person_id UUID NOT NULL REFERENCES natural_persons(id),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_brokers_status CHECK (status IN ('active', 'suspended'))
);

CREATE TABLE broker_merchant_relations (
    broker_id UUID NOT NULL REFERENCES brokers(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    invited_by UUID REFERENCES users(id),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (broker_id, merchant_id),
    CONSTRAINT chk_broker_merchant_status CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    natural_person_id UUID NOT NULL REFERENCES natural_persons(id),
    license_no VARCHAR(32),
    license_photo_oss VARCHAR(512),
    status VARCHAR(16) DEFAULT 'pending',
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_drivers_status CHECK (status IN ('pending', 'verified', 'active', 'suspended'))
);

CREATE TABLE driver_merchant_relations (
    driver_id UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
    invited_by UUID REFERENCES users(id),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (driver_id, merchant_id),
    CONSTRAINT chk_driver_merchant_status CHECK (status IN ('active', 'inactive'))
);

-- merchant_id 恢复，标识仓管员归属商户（C或B均可管理）
CREATE TABLE warehouse_keepers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    natural_person_id UUID NOT NULL REFERENCES natural_persons(id),
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    warehouse_id UUID,
    sign_authorized BOOLEAN DEFAULT FALSE,
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_warehouse_keepers_status CHECK (status IN ('active', 'suspended'))
);

-- =====================================================
-- 4. 关系绑定层
-- =====================================================

CREATE TABLE merchant_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upstream_merchant_id UUID NOT NULL REFERENCES merchants(id),
    downstream_merchant_id UUID NOT NULL REFERENCES merchants(id),
    product_category_id UUID NOT NULL REFERENCES product_categories(id),
    status VARCHAR(16) DEFAULT 'active',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(upstream_merchant_id, downstream_merchant_id, product_category_id),
    CONSTRAINT chk_merchant_relations_status CHECK (status IN ('active', 'suspended'))
);

CREATE TABLE merchant_supplier_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    supplier_id UUID NOT NULL REFERENCES natural_persons(id),
    product_category_id UUID REFERENCES product_categories(id),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(merchant_id, supplier_id),
    CONSTRAINT chk_merchant_supplier_status CHECK (status IN ('active', 'blocked'))
);

-- =====================================================
-- 5. 采购公告与认售
-- =====================================================

CREATE TABLE purchase_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    product_category_id UUID NOT NULL REFERENCES product_categories(id),
    product_name VARCHAR(128),
    specification JSON,
    grade VARCHAR(64),
    unit_price DECIMAL(15,4) NOT NULL,
    quantity DECIMAL(15,3) NOT NULL,
    remaining_quantity DECIMAL(15,3) NOT NULL DEFAULT 0,
    deadline DATE NOT NULL,
    transport_arrangement VARCHAR(16),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_announcement_transport CHECK (transport_arrangement IN ('BUYER', 'SELLER')),
    CONSTRAINT chk_announcement_status CHECK (status IN ('active', 'paused', 'closed'))
);

CREATE TABLE supply_commitments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID NOT NULL REFERENCES purchase_announcements(id),
    supplier_id UUID NOT NULL REFERENCES natural_persons(id),
    broker_id UUID REFERENCES brokers(id),
    quantity DECIMAL(15,3) NOT NULL,
    expected_delivery_date DATE,
    status VARCHAR(16) DEFAULT 'pending',
    confirmed_by UUID REFERENCES users(id),
    confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_commitment_status CHECK (status IN ('pending', 'confirmed', 'rejected'))
);

-- =====================================================
-- 6. 经纪人任务（必须在 purchase_orders 之前）
-- =====================================================

CREATE TABLE broker_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_no VARCHAR(64) NOT NULL UNIQUE,
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    broker_id UUID NOT NULL REFERENCES brokers(id),
    product_category_id UUID NOT NULL REFERENCES product_categories(id),
    product_name VARCHAR(128),
    specification JSON,
    grade VARCHAR(64),
    quantity DECIMAL(15,3) NOT NULL,
    unit_price DECIMAL(15,4),
    deadline DATE,
    status VARCHAR(16) DEFAULT 'pending',
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_broker_task_status CHECK (status IN ('pending', 'accepted', 'processing', 'completed'))
);

-- =====================================================
-- 7. 订单层
-- =====================================================

CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES merchants(id),
    order_no VARCHAR(64) NOT NULL UNIQUE,
    order_type VARCHAR(16) NOT NULL,
    parent_order_id UUID REFERENCES purchase_orders(id),
    broker_task_id UUID REFERENCES broker_tasks(id),

    -- 买方（始终是商户 C 或 B）
    buyer_merchant_id UUID NOT NULL REFERENCES merchants(id),

    -- 卖方（拆分：TRADE 订单填 seller_merchant_id，DIRECT/SUB 订单填 seller_supplier_id）
    seller_merchant_id UUID REFERENCES merchants(id),
    seller_supplier_id UUID REFERENCES natural_persons(id),

    product_category_id UUID NOT NULL REFERENCES product_categories(id),
    product_name VARCHAR(128),
    specification JSON,
    grade VARCHAR(64),
    quantity DECIMAL(15,3) NOT NULL,
    unit VARCHAR(16) DEFAULT 'ton',
    unit_price DECIMAL(15,4) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,

    resale_to_merchant_id UUID REFERENCES merchants(id),

    transport_arrangement VARCHAR(16),
    driver_id UUID REFERENCES drivers(id),
    plate_no VARCHAR(16),

    -- 物流节点时间（过磅数据统一从 weighbridge_records 查询）
    dispatched_at TIMESTAMP,
    arrived_source_at TIMESTAMP,
    source_weighed_at TIMESTAMP,
    in_transit_at TIMESTAMP,
    arrived_warehouse_at TIMESTAMP,
    warehouse_weighed_at TIMESTAMP,
    warehousing_at TIMESTAMP,
    warehoused_at TIMESTAMP,

    -- 合同（不建外键，避免循环引用）
    contract_id UUID,
    paid_at TIMESTAMP,

    status VARCHAR(32) DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_order_type CHECK (order_type IN ('DIRECT', 'TRADE', 'SUB')),
    CONSTRAINT chk_transport_arrangement CHECK (transport_arrangement IN ('BUYER', 'SELLER')),
    CONSTRAINT chk_order_status CHECK (status IN (
        'DRAFT', 'COMMITTED', 'DISPATCHED', 'ARRIVED_SOURCE', 'SOURCE_WEIGHED',
        'IN_TRANSIT', 'ARRIVED_WAREHOUSE', 'WAREHOUSE_WEIGHED', 'WAREHOUSING',
        'WAREHOUSED', 'CONTRACT_PENDING', 'CONTRACTED', 'PAYING', 'PAID',
        'COMPLETED', 'CANCELLED'
    ))
);

CREATE TABLE order_status_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    from_status VARCHAR(32),
    to_status VARCHAR(32) NOT NULL,
    operator_id UUID NOT NULL REFERENCES users(id),
    operator_role VARCHAR(32) NOT NULL,
    remark TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 8. 运输层
-- =====================================================

CREATE TABLE transport_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES purchase_orders(id),
    driver_id UUID NOT NULL REFERENCES drivers(id),
    plate_no VARCHAR(16) NOT NULL,
    route JSON,
    status VARCHAR(16) DEFAULT 'assigned',
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_transport_task_status CHECK (status IN (
        'assigned', 'departed', 'arrived_source', 'source_weighed',
        'in_transit', 'arrived_warehouse', 'completed', 'cancelled'
    ))
);

CREATE TABLE gps_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transport_task_id UUID NOT NULL REFERENCES transport_tasks(id) ON DELETE CASCADE,
    checkpoint_type VARCHAR(16) NOT NULL,
    latitude DECIMAL(10,7) NOT NULL,
    longitude DECIMAL(10,7) NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_gps_type CHECK (checkpoint_type IN ('depart', 'arrive_source', 'arrive_warehouse'))
);

-- =====================================================
-- 9. 过磅层（唯一重量数据源）
-- =====================================================

CREATE TABLE weighbridge_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES purchase_orders(id),
    record_type VARCHAR(16) NOT NULL,
    gross_weight DECIMAL(15,3) NOT NULL,
    tare_weight DECIMAL(15,3) NOT NULL,
    net_weight DECIMAL(15,3) NOT NULL,
    deduction DECIMAL(15,3),
    actual_weight DECIMAL(15,3),
    recorded_by UUID NOT NULL REFERENCES users(id),
    recorded_by_role VARCHAR(32) NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_weighbridge_type CHECK (record_type IN ('source', 'warehouse'))
);

-- =====================================================
-- 10. 入库层
-- =====================================================

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    name VARCHAR(128) NOT NULL,
    address VARCHAR(256),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_warehouse_status CHECK (status IN ('active', 'inactive'))
);

-- warehouses 建完后补充外键
ALTER TABLE warehouse_keepers
    ADD CONSTRAINT fk_warehouse_keeper_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);

CREATE TABLE warehouse_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES purchase_orders(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    keeper_id UUID NOT NULL REFERENCES warehouse_keepers(id),
    product_category_id UUID NOT NULL REFERENCES product_categories(id),
    quantity DECIMAL(15,3) NOT NULL,
    actual_weight DECIMAL(15,3) NOT NULL,
    location VARCHAR(64),
    signed BOOLEAN DEFAULT FALSE,
    signed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 11. 合同层
-- =====================================================

CREATE TABLE contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_no VARCHAR(64) NOT NULL UNIQUE,
    order_id UUID NOT NULL,   -- 不建外键，避免与 purchase_orders.contract_id 循环引用
    buyer_id UUID NOT NULL,
    seller_id UUID NOT NULL,
    product_name VARCHAR(128),
    quantity DECIMAL(15,3),
    unit_price DECIMAL(15,4),
    total_amount DECIMAL(15,2),
    contract_pdf_oss VARCHAR(512),
    status VARCHAR(16) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_contract_status CHECK (status IN ('pending', 'signed', 'cancelled'))
);

CREATE TABLE contract_signatures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    signer_id UUID NOT NULL REFERENCES users(id),
    signer_role VARCHAR(32) NOT NULL,
    signature_oss VARCHAR(512),
    signed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 12. 支付层
-- =====================================================

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_no VARCHAR(64) NOT NULL UNIQUE,
    order_id UUID NOT NULL REFERENCES purchase_orders(id),
    payer_id UUID NOT NULL,
    payee_id UUID NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_type VARCHAR(16) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    status VARCHAR(16) DEFAULT 'pending',
    channel VARCHAR(32),
    channel_trade_no VARCHAR(128),
    paid_at TIMESTAMP,
    failed_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_payment_type CHECK (payment_type IN ('GOODS_PAYMENT', 'SERVICE_FEE')),
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'success', 'failed'))
);

-- =====================================================
-- 13. 开票层
-- =====================================================

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_no VARCHAR(64) NOT NULL UNIQUE,
    order_id UUID NOT NULL REFERENCES purchase_orders(id),
    seller_id UUID NOT NULL,
    buyer_id UUID NOT NULL,
    invoice_type VARCHAR(16) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    tax_rate DECIMAL(5,2),
    tax_amount DECIMAL(15,2),
    invoice_pdf_oss VARCHAR(512),
    status VARCHAR(16) DEFAULT 'pending',
    api_request_id VARCHAR(128),
    api_response TEXT,
    issued_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_invoice_type CHECK (invoice_type IN ('REVERSE', 'FORWARD')),
    CONSTRAINT chk_invoice_status CHECK (status IN ('pending', 'issued', 'failed'))
);

CREATE TABLE reverse_invoice_charges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    merchant_id UUID NOT NULL REFERENCES merchants(id),
    invoice_amount DECIMAL(15,2) NOT NULL,
    charge_amount DECIMAL(15,2) NOT NULL,
    status VARCHAR(16) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_charge_status CHECK (status IN ('pending', 'paid'))
);

-- =====================================================
-- 14. 附件层
-- =====================================================

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES merchants(id),
    related_type VARCHAR(32) NOT NULL,
    related_id UUID NOT NULL,
    uploader_id UUID NOT NULL REFERENCES users(id),
    uploader_role VARCHAR(32) NOT NULL,
    file_type VARCHAR(16),
    oss_url VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_attachment_type CHECK (file_type IN ('image', 'video', 'pdf'))
);

-- =====================================================
-- 15. 消息层
-- =====================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(32),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_notification_type CHECK (type IN ('order', 'payment', 'transport', 'system'))
);

-- =====================================================
-- 16. 索引
-- =====================================================

CREATE INDEX idx_orders_tenant_id ON purchase_orders(tenant_id);
CREATE INDEX idx_orders_status ON purchase_orders(status);
CREATE INDEX idx_orders_buyer_merchant_id ON purchase_orders(buyer_merchant_id);
CREATE INDEX idx_orders_seller_merchant_id ON purchase_orders(seller_merchant_id);
CREATE INDEX idx_orders_seller_supplier_id ON purchase_orders(seller_supplier_id);
CREATE INDEX idx_orders_parent_order_id ON purchase_orders(parent_order_id);
CREATE INDEX idx_orders_contract_id ON purchase_orders(contract_id);
CREATE INDEX idx_order_logs_order_id ON order_status_logs(order_id);
CREATE INDEX idx_transport_tasks_order_id ON transport_tasks(order_id);
CREATE INDEX idx_transport_tasks_driver_id ON transport_tasks(driver_id);
CREATE INDEX idx_transport_tasks_status ON transport_tasks(status);
CREATE INDEX idx_weighbridge_records_order_id ON weighbridge_records(order_id);
CREATE INDEX idx_weighbridge_records_recorded_at ON weighbridge_records(recorded_at);
CREATE INDEX idx_warehouse_receipts_order_id ON warehouse_receipts(order_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_attachments_related ON attachments(related_type, related_id);
CREATE INDEX idx_attachments_tenant_id ON attachments(tenant_id);
CREATE INDEX idx_merchant_relations_upstream ON merchant_relations(upstream_merchant_id);
CREATE INDEX idx_merchant_relations_downstream ON merchant_relations(downstream_merchant_id);
CREATE INDEX idx_merchant_supplier_relations_merchant ON merchant_supplier_relations(merchant_id);
CREATE INDEX idx_merchant_supplier_relations_supplier ON merchant_supplier_relations(supplier_id);
CREATE INDEX idx_broker_merchant_relations_broker ON broker_merchant_relations(broker_id);
CREATE INDEX idx_broker_merchant_relations_merchant ON broker_merchant_relations(merchant_id);
CREATE INDEX idx_broker_tasks_merchant ON broker_tasks(merchant_id);
CREATE INDEX idx_broker_tasks_broker ON broker_tasks(broker_id);
CREATE INDEX idx_driver_merchant_relations_driver ON driver_merchant_relations(driver_id);
CREATE INDEX idx_driver_merchant_relations_merchant ON driver_merchant_relations(merchant_id);
CREATE INDEX idx_user_wx_auth_user_id ON user_wx_auth(user_id);
CREATE INDEX idx_user_wx_auth_openid ON user_wx_auth(mini_program_appid, open_id);
CREATE INDEX idx_payments_idempotency_key ON payments(idempotency_key);

-- =====================================================
-- 17. 种子数据（密码由部署后 API 初始化设置）
-- =====================================================

INSERT INTO users (id, phone, password_hash, role, status)
VALUES ('11111111-1111-1111-1111-111111111111', 'admin', 'REQUIRED_TO_BE_SET_BY_API', 'W', 'active');

INSERT INTO natural_persons (id, user_id, real_name, auth_status)
VALUES ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', '平台管理员', 'verified');
