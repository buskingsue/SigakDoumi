#test_tts_stt.py

import pytest
from unittest.mock import MagicMock
from main import main_function1

# Global list to track called functions
called_functions = []

# Dummy function for analyze_memo
def dummy_analyze_memo():
    called_functions.append("analyze_memo")

# Dummy serial with a one-time 'O' signal
class DummySerialOnceO:
    def __init__(self):
        self.events = [b'O']
    
    @property
    def in_waiting(self):
        return len(self.events)

    def read(self, _):
        return self.events.pop(0)

@pytest.fixture
def setup_test(monkeypatch):
    # Patch record_and_recognize to simulate "약추가"
    monkeypatch.setattr("main.record_and_recognize", lambda *args, **kwargs: "약추가")

    # Patch get_serial to return DummySerialOnceO instance
    monkeypatch.setattr("main.get_serial", lambda: DummySerialOnceO())

    # Patch analyze_memo function
    monkeypatch.setattr("main.analyze_memo", dummy_analyze_memo)

    # Patch text_to_speech to skip actual TTS
    monkeypatch.setattr("main.text_to_speech", lambda text, filename: None)

    return True

def test_main_function1_flow(setup_test):
    # Clear previous function calls
    called_functions.clear()

    # Run main function 1, which should trigger everything
    main_function1()

    assert called_functions == [
        "analyze_memo"
    ]
