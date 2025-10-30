import pytest
from playground.services.pc_service import PlayRequest

def test_pause_without_play(pc_service):
    """попытка поставить паузу без активной сессии."""
    pc = pc_service.init_pc("PC-01")
    with pytest.raises(RuntimeError, match="not playing"):
        pc_service.pause(pc.id)

def test_resume_without_pause(pc_service):
    """попытка возобновить игру, если ПК не на паузе."""
    pc = pc_service.init_pc("PC-02")
    with pytest.raises(RuntimeError):
        pc_service.resume(pc.id)

def test_stop_without_session(pc_service):
    """попытка остановить ПК, если нет активного order_id."""
    pc = pc_service.init_pc("PC-03")
    with pytest.raises(RuntimeError):
        pc_service.stop(pc.id)

def test_double_play_session(pc_service):
    """попытка начать игру на уже активном ПК."""
    pc = pc_service.init_pc("PC-04")
    req = PlayRequest(pc_id=pc.id, hours=0, minutes=30, price=20.0, payment="cash")
    pc_service.play(req)
    with pytest.raises(RuntimeError, match="already in session"):
        pc_service.play(req)
