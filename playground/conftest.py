import pytest
from playground.services.pc_service import PCService

@pytest.fixture
def pc_service():
    """создаёт новый сервис перед каждым тестом"""
    return PCService()

# можно в тестах просто писать без ручного создания svc = PCService() каждый раз
# def test_init_and_list(pc_service):
#    pc = pc_service.init_pc("PC-01")
#     ...
