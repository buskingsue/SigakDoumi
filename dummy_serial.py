# stm32의 신호를 대신하는 더미 클래스

class DummySerial:
    def __init__(self, events):
        self.events = events  # a list of bytes representing events

    @property
    def in_waiting(self):
        # Return the number of remaining events
        return len(self.events)

    def read(self, size=1):
        # Return the next event (simulate reading one byte)
        if self.events:
            return self.events.pop(0)
        return b''
