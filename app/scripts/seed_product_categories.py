# v1.0 - 种子数据脚本：初始化废旧物资品种字典（常见 10 个大类）
# 运行方式：PYTHONPATH=/path/to/project .venv2/bin/python app/scripts/seed_product_categories.py
import asyncio
import sys
import os

# 确保 project root 在 PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.models.product import ProductCategory
from app.models.user import User

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://wucaitong:wucaitong123@localhost:5432/wucaitong",
)

# 常见废旧物资品种（中国回收行业标准分类）
CATEGORIES = [
    {
        "category_code": "STEEL",
        "category_name": "废旧钢铁",
        "sub_category": "生铁/熟铁/钢筋/废钢/板材",
        "grade_options": ["一级品", "二级品", "三级品", "废料"],
        "spec_template": {"thickness": "mm", "length": "mm", "purity": "%"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "COPPER",
        "category_name": "废旧铜",
        "sub_category": "紫铜/黄铜/铜线/铜管",
        "grade_options": ["精铜", "二号铜", "三号铜", "废铜"],
        "spec_template": {"purity": "%", "form": "线/管/板/块"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "ALUMINUM",
        "category_name": "废旧铝",
        "sub_category": "铝合金/纯铝/铝板/铝线",
        "grade_options": ["一级铝", "二级铝", "混铝", "铝渣"],
        "spec_template": {"purity": "%", "alloy_type": "牌号"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "STAINLESS_STEEL",
        "category_name": "废旧不锈钢",
        "sub_category": "201/304/316",
        "grade_options": ["304级", "316级", "201级", "混料"],
        "spec_template": {"grade": "钢号", "thickness": "mm"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "LEAD",
        "category_name": "废旧铅",
        "sub_category": "蓄电池铅/管道铅/铅板",
        "grade_options": ["精铅", "粗铅", "铅泥"],
        "spec_template": {"purity": "%"},
        "unit": "ton",
        "tax_rate": 9.0,
        "is_hazardous": True,
    },
    {
        "category_code": "ZINC",
        "category_name": "废旧锌",
        "sub_category": "镀锌/锌合金/锌渣",
        "grade_options": ["精锌", "合金锌", "锌渣"],
        "spec_template": {"purity": "%"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "PAPER",
        "category_name": "废纸",
        "sub_category": "废旧报纸/瓦楞纸/书本纸/杂志纸",
        "grade_options": ["一类废纸", "二类废纸", "三类废纸"],
        "spec_template": {"moisture": "%", "impurity": "%"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "PLASTIC",
        "category_name": "废旧塑料",
        "sub_category": "PE/PP/PET/ABS/PS",
        "grade_options": ["透明料", "彩色料", "混料", "边角料"],
        "spec_template": {"material_type": "材质", "color": "颜色"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "RUBBER",
        "category_name": "废旧橡胶",
        "sub_category": "废旧轮胎/胶管/胶板",
        "grade_options": ["整胎", "胎块", "胶粉"],
        "spec_template": {"type": "类型"},
        "unit": "ton",
        "tax_rate": 9.0,
    },
    {
        "category_code": "BATTERY",
        "category_name": "废旧电池",
        "sub_category": "铅酸蓄电池/锂电池/镍氢电池",
        "grade_options": ["整组", "单体", "拆解料"],
        "spec_template": {"voltage": "V", "capacity": "Ah"},
        "unit": "ton",
        "tax_rate": 9.0,
        "is_hazardous": True,
    },
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 取平台管理员用户 ID 作为 created_by
        result = await session.execute(select(User).where(User.role == "W").limit(1))
        admin = result.scalar_one_or_none()
        if not admin:
            print("❌ 未找到平台管理员用户（role=W），请先运行 seed_users.py")
            return

        created_count = 0
        skipped_count = 0

        for cat_data in CATEGORIES:
            # 检查是否已存在
            exists = await session.execute(
                select(ProductCategory).where(
                    ProductCategory.category_code == cat_data["category_code"]
                )
            )
            if exists.scalar_one_or_none():
                print(f"  跳过（已存在）：{cat_data['category_name']}")
                skipped_count += 1
                continue

            category = ProductCategory(
                category_code=cat_data["category_code"],
                category_name=cat_data["category_name"],
                sub_category=cat_data.get("sub_category"),
                grade_options=cat_data.get("grade_options"),
                spec_template=cat_data.get("spec_template"),
                tax_rate=cat_data.get("tax_rate"),
                unit=cat_data.get("unit", "ton"),
                is_hazardous=cat_data.get("is_hazardous", False),
                status="active",
                created_by=admin.id,
            )
            session.add(category)
            print(f"  ✓ 创建品种：{cat_data['category_name']} ({cat_data['category_code']})")
            created_count += 1

        await session.commit()
        print(f"\n完成：新建 {created_count} 个品种，跳过 {skipped_count} 个")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
