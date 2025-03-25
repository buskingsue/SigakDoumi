
# test_main.py

import pytest

# 더미 stm32값을 가지고 main.py를 테스트 해보는 파일
# 이하 부분은 main.py에서 필요한 기능만 import 한 후 pytest 형식으로 알맞게 수정하여 테스트 진행할것
from main import *  # main.py 전부다 가져오기
from dummy_serial import DummySerial

# 더미 호출할 함수 리스트 선언
called_functions = []


# 테스트 해볼 더미 함수들
def dummy_press_button(socket):
    called_functions.append(f"press_button {socket}")

def dummy_main_function1():
    called_functions.append("main_function1")

def dummy_main_function2():
    called_functions.append("main_function2")

def dummy_take_medicine(socket):
    called_functions.append(f"take_medicine {socket}")


# dummy serial 클래스를 통해 더미 정보 전달해주는 속임수 함수
@pytest.fixture
def setup_dummy(monkeypatch):
    
    # 원터치 버튼 눌림
    dummy_events = [b'O']
    dummy_ser = DummySerial(dummy_events)
    

    # Patch the global 'ser' variable in your module with dummy_ser.
    # 시리얼 신호를 의미하는 ser 변수를 dummy_ser로 대체하여 테스트 진행하도록 설정

    monkeypatch.setattr('main.ser', dummy_ser)
    
    # Patch functions so we can record which ones get called
    monkeypatch.setattr('main.press_button', dummy_press_button)
    monkeypatch.setattr('main.main_function1', dummy_main_function1)
    monkeypatch.setattr('main.main_function2', dummy_main_function2)
    monkeypatch.setattr('main.take_medicine', dummy_take_medicine)
    
    return dummy_ser

def test_standby_processing(setup_dummy):
    
    # 아래코드 이해안됨 
    # standby()에서 무한루프 도는게 아닌 한 이터레이션만 테스한다고 함
    # Instead of running the infinite loop in standby(),
    # we simulate one iteration per dummy event.
    # from medication_app import react_to_event  # function under test

    dummy_ser = setup_dummy

    # Process each dummy event manually
    while dummy_ser.in_waiting > 0:
        event = dummy_ser.read(1)
        standby_change = react_to_event(event)
        if standby_change == '1':
            dummy_press_button('1')
        elif standby_change == '2':
            dummy_press_button('2')
        elif standby_change == '3':
            dummy_press_button('3')
        elif standby_change == 'O':
            dummy_main_function1()
        elif standby_change == 'Q':
            dummy_main_function2()
        elif standby_change == 'A':
            dummy_take_medicine('A')
        elif standby_change == 'B':
            dummy_take_medicine('B')
        elif standby_change == 'C':
            dummy_take_medicine('C')


    # 테스트 통과 조건 ('O' 버튼이 눌린 경우 main_function1 실행되어야 함)
    assert called_functions == [
        "main_function1"
    ]
