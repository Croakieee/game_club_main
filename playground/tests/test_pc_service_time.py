import pytest
from datetime import timedelta
from playground.services.pc_service import PlayRequest
import playground.services.pc_service as pc_mod  # модуль, где используется datetime


def test_stop_after_time(monkeypatch, pc_service):
    """
    Проверяет, что после ~5 минут игры стоимость и минуты считаются.
    патчит datetime прямо в модуле, где он используется (pc_mod).
    """
    # стартуем сессию
    pc = pc_service.init_pc("PC-01")
    req = PlayRequest(pc_id=pc.id, hours=0, minutes=10, price=10.0, payment="cash")
    play_res = pc_service.play(req)

    # вычисляем "текущее время" = старт + 5 минут
    start_actual = pc_mod.datetime.utcnow()
    fake_now = start_actual + timedelta(minutes=5)

    class FakeDT:
        @staticmethod
        def utcnow():
            return fake_now

    # важный момент: патчим datetime именно в модуле, где он был импортирован
    monkeypatch.setattr(pc_mod, "datetime", FakeDT)

    # стопаем и проверяем расчёты
    result = pc_service.stop(pc.id)
    assert result["played_minutes"] >= 5
    assert 0 < result["price"] <= 10.0
