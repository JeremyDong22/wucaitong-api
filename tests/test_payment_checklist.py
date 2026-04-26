import pytest
from app.core.checklist import PaymentChecklist

@pytest.mark.asyncio
async def test_checklist_initialization():
    assert PaymentChecklist is not None
