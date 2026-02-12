import pytest
from src.database.connection import get_db_connection
from src.services.database_service import DatabaseService

@pytest.fixture(scope='module')
def db_service():
    connection = get_db_connection()
    service = DatabaseService(connection)
    yield service
    connection.close()

def test_insert_access_log(db_service):
    log_data = {
        'access_time': '2023-10-01 12:00:00',
        'client_ip': '192.168.1.1',
        'http_method': 'GET',
        'api_path': '/api/v4/projects',
        'http_status': 200,
        'response_size': 1024,
        'user_agent': 'Mozilla/5.0',
        'response_time': 0.123
    }
    
    result = db_service.insert_access_log(log_data)
    assert result is True  # Assuming insert_access_log returns True on success

def test_insert_access_log_invalid_data(db_service):
    log_data = {
        'access_time': 'invalid_time',
        'client_ip': 'invalid_ip',
        'http_method': 'INVALID',
        'api_path': '',
        'http_status': 999,
        'response_size': -1,
        'user_agent': '',
        'response_time': -0.1
    }
    
    with pytest.raises(ValueError):  # Assuming insert_access_log raises ValueError on invalid data
        db_service.insert_access_log(log_data)