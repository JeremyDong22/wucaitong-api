# v1.1 - 支付前检查清单（PaymentChecklist）— 实现真实业务校验
# 修复：移除不存在的 TransportBatch/MediaFile 导入，改为 TransportTask/Attachment
# 修复：所有检查方法实现真实数据库查询，替代原来全部 passed=True 的 mock
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.order import PurchaseOrder
from app.models.transport import TransportTask
from app.models.attachment import Attachment
from app.models.weighbridge import WeighbridgeRecord
from app.models.warehouse import WarehouseReceipt
from app.models.contract import Contract, ContractSignature
from app.core.config import settings
import uuid


class PaymentChecklist:
    """支付前必过检查清单（对应计划书 12.2 节）"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(self, order_id: uuid.UUID) -> dict:
        """执行所有检查，返回汇总结果"""
        results = {"passed": True, "items": [], "failed_items": []}

        checks = [
            self._check_transport_arrived,
            self._check_unload_photos,
            self._check_driver_selfie,
            self._check_weighing,
            self._check_ocr_verified,
            self._check_warehouse_receipt,
            self._check_weight_cross_validation,
            self._check_contract_signed,
        ]
        for check_fn in checks:
            item = await check_fn(order_id)
            results["items"].append(item)
            if not item["passed"]:
                results["passed"] = False
                results["failed_items"].append(item)

        return results

    async def _check_transport_arrived(self, order_id: uuid.UUID) -> dict:
        """检查运输任务状态为已到达仓库"""
        result = await self.db.execute(
            select(TransportTask).where(TransportTask.order_id == order_id)
        )
        task = result.scalar_one_or_none()
        passed = task is not None and task.status in ("arrived_warehouse", "completed")
        return {
            "name": "运输批次到达",
            "passed": passed,
            "detail": None if passed else "运输任务未到达仓库或不存在",
        }

    async def _check_unload_photos(self, order_id: uuid.UUID) -> dict:
        """检查卸货照片已上传（至少1张）"""
        result = await self.db.execute(
            select(func.count()).select_from(Attachment).where(
                Attachment.related_type == "order",
                Attachment.related_id == order_id,
                Attachment.file_type == "unload_photo",
            )
        )
        count = result.scalar()
        passed = count > 0
        return {
            "name": "卸货照片",
            "passed": passed,
            "detail": None if passed else "请上传卸货现场照片",
        }

    async def _check_driver_selfie(self, order_id: uuid.UUID) -> dict:
        """检查人车合照已上传"""
        result = await self.db.execute(
            select(func.count()).select_from(Attachment).where(
                Attachment.related_type == "order",
                Attachment.related_id == order_id,
                Attachment.file_type == "driver_selfie",
            )
        )
        count = result.scalar()
        passed = count > 0
        return {
            "name": "人车合照",
            "passed": passed,
            "detail": None if passed else "请上传司机与车辆合照",
        }

    async def _check_weighing(self, order_id: uuid.UUID) -> dict:
        """检查仓库复磅记录已录入"""
        result = await self.db.execute(
            select(WeighbridgeRecord).where(
                WeighbridgeRecord.order_id == order_id,
                WeighbridgeRecord.record_type == "warehouse",
            )
        )
        record = result.scalar_one_or_none()
        passed = record is not None
        return {
            "name": "过磅记录",
            "passed": passed,
            "detail": None if passed else "仓库过磅数据未录入",
        }

    async def _check_ocr_verified(self, order_id: uuid.UUID) -> dict:
        """检查磅单照片已上传（OCR 集成前以照片存在为准）"""
        result = await self.db.execute(
            select(func.count()).select_from(Attachment).where(
                Attachment.related_type == "order",
                Attachment.related_id == order_id,
                Attachment.file_type == "weighbridge_ticket",
            )
        )
        count = result.scalar()
        passed = count > 0
        return {
            "name": "磅单照片",
            "passed": passed,
            "detail": None if passed else "请上传磅单原件照片",
        }

    async def _check_warehouse_receipt(self, order_id: uuid.UUID) -> dict:
        """检查入库仓单已签章"""
        result = await self.db.execute(
            select(WarehouseReceipt).where(
                WarehouseReceipt.order_id == order_id,
                WarehouseReceipt.signed == True,  # noqa: E712
            )
        )
        receipt = result.scalar_one_or_none()
        passed = receipt is not None
        return {
            "name": "入库仓单",
            "passed": passed,
            "detail": None if passed else "入库仓单未签章",
        }

    async def _check_weight_cross_validation(self, order_id: uuid.UUID) -> dict:
        """检查源头磅重与仓库复磅差值在容忍范围内"""
        source_result = await self.db.execute(
            select(WeighbridgeRecord).where(
                WeighbridgeRecord.order_id == order_id,
                WeighbridgeRecord.record_type == "source",
            )
        )
        warehouse_result = await self.db.execute(
            select(WeighbridgeRecord).where(
                WeighbridgeRecord.order_id == order_id,
                WeighbridgeRecord.record_type == "warehouse",
            )
        )
        source = source_result.scalar_one_or_none()
        warehouse = warehouse_result.scalar_one_or_none()

        if not source or not warehouse:
            return {
                "name": "重量交叉验证",
                "passed": False,
                "detail": "源头或仓库过磅数据缺失，无法校验",
            }

        s_w = Decimal(str(source.actual_weight))
        w_w = Decimal(str(warehouse.actual_weight))
        if s_w == 0:
            return {"name": "重量交叉验证", "passed": False, "detail": "源头过磅重量为0"}

        diff_pct = abs(s_w - w_w) / s_w * 100
        tolerance = Decimal(str(settings.weight_tolerance_percent))
        passed = diff_pct <= tolerance
        return {
            "name": "重量交叉验证",
            "passed": passed,
            "detail": None if passed else f"磅差 {diff_pct:.2f}% 超过允许值 {tolerance}%",
        }

    async def _check_contract_signed(self, order_id: uuid.UUID) -> dict:
        """检查合同已双方签章"""
        contract_result = await self.db.execute(
            select(Contract).where(
                Contract.order_id == order_id,
                Contract.status == "signed",
            )
        )
        contract = contract_result.scalar_one_or_none()
        passed = contract is not None
        return {
            "name": "合同双方签章",
            "passed": passed,
            "detail": None if passed else "合同尚未完成双方签章",
        }
