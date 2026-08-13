class State:
    _id_counter = 0

    def __init__(self, is_accept=False):
        self.id = State._id_counter
        State._id_counter += 1
        self.is_accept = is_accept
        self.transitions = {}

    def add_transition(self, symbol, state):
        if symbol not in self.transitions:
            self.transitions[symbol] = []
        self.transitions[symbol].append(state)

    @classmethod
    def reset_counter(cls):
        cls._id_counter = 0

class AFN:
    def __init__(self, start_state, accept_state):
        self.start_state = start_state
        self.accept_state = accept_state
