import pytest
from app.core.state_machine import OrderStateMachine
from app.models.order import OrderStatus

def test_valid_transitions():
    assert OrderStateMachine.can_transition(OrderStatus.DRAFT, OrderStatus.COMMITTED) == True
    assert OrderStateMachine.can_transition(OrderStatus.DRAFT, OrderStatus.CANCELLED) == True

def test_invalid_transitions():
    assert OrderStateMachine.can_transition(OrderStatus.DRAFT, OrderStatus.COMPLETED) == False
    assert OrderStateMachine.can_transition(OrderStatus.COMPLETED, OrderStatus.DRAFT) == False

def test_allowed_next_states():
    next_states = OrderStateMachine.get_allowed_next_states(OrderStatus.DRAFT)
    assert OrderStatus.COMMITTED in next_states
    assert OrderStatus.CANCELLED in next_states
