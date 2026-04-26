# v1.0 - 统一导出所有模型，确保 Alembic autogenerate 能发现全部表
from app.models.user import User, UserWxAuth, NaturalPerson, Enterprise
from app.models.merchant import (
    Merchant, Broker, BrokerMerchantRelation,
    Driver, DriverMerchantRelation, WarehouseKeeper,
)
from app.models.product import ProductCategory, MerchantRelation, MerchantSupplierRelation
from app.models.announcement import PurchaseAnnouncement, SupplyCommitment
from app.models.broker import BrokerTask
from app.models.order import PurchaseOrder, OrderStatusLog
from app.models.transport import TransportTask, GpsCheckpoint
from app.models.weighbridge import WeighbridgeRecord
from app.models.warehouse import Warehouse, WarehouseReceipt
from app.models.contract import Contract, ContractSignature
from app.models.payment import Payment
from app.models.invoice import Invoice, ReverseInvoiceCharge
from app.models.attachment import Attachment
from app.models.notification import Notification

__all__ = [
    "User", "UserWxAuth", "NaturalPerson", "Enterprise",
    "Merchant", "Broker", "BrokerMerchantRelation",
    "Driver", "DriverMerchantRelation", "WarehouseKeeper",
    "ProductCategory", "MerchantRelation", "MerchantSupplierRelation",
    "PurchaseAnnouncement", "SupplyCommitment",
    "BrokerTask",
    "PurchaseOrder", "OrderStatusLog",
    "TransportTask", "GpsCheckpoint",
    "WeighbridgeRecord",
    "Warehouse", "WarehouseReceipt",
    "Contract", "ContractSignature",
    "Payment",
    "Invoice", "ReverseInvoiceCharge",
    "Attachment",
    "Notification",
]
