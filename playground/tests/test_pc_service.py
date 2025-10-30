import pytest
from datetime import datetime
from playground.services.pc_service import PCService, PlayRequest

def test_init_and_list():
    svc = PCService()
    pc1 = svc.init_pc("PC-01")
    pc2 = svc.init_pc("PC-02")
    pcs = svc.list_pcs()
    assert len(pcs) == 2
    assert pc1.id == 1 and pc1.name == "PC-01"
    assert pc2.id == 2 and pc2.name == "PC-02"

@pytest.mark.parametrize("hours, minutes", [(1, 0), (0, 30), (2, 15)])
def test_play_valid(hours, minutes):
    svc = PCService()
    pc = svc.init_pc("PC-01")
    req = PlayRequest(pc_id=pc.id, hours=hours, minutes=minutes, price=60.0, payment="cash")
    result = svc.play(req)
    assert result["status"] == "playing"
    assert result["pc_id"] == pc.id
    assert result["price"] == 60.0
    assert result["payment"] == "cash"
    assert result["time"]["total_minutes"] == hours * 60 + minutes

@pytest.mark.parametrize("bad_minutes", [-1, 60, 100])
def test_play_invalid_minutes(bad_minutes):
    svc = PCService()
    pc = svc.init_pc("PC-01")
    req = PlayRequest(pc_id=pc.id, hours=0, minutes=bad_minutes, price=60.0, payment="card")
    with pytest.raises(ValueError):
        req.validate()

def test_pause_resume_stop_flow(monkeypatch):
    svc = PCService()
    pc = svc.init_pc("PC-01")
    req = PlayRequest(pc_id=pc.id, hours=0, minutes=10, price=20.0, payment="card")
    svc.play(req)

    # simulate some time by monkeypatching datetime.utcnow if needed
    # but we only need that pause -> resume -> stop transitions work
    out_pause = svc.pause(pc.id)
    assert out_pause["status"] == "pause"

    out_resume = svc.resume(pc.id)
    assert out_resume["status"] == "playing"

    out_stop = svc.stop(pc.id)
    assert out_stop["pc_id"] == pc.id
    assert out_stop["payment"] == "card"
