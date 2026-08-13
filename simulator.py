from thompson import EPSILON

def epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    
    while stack:
        state = stack.pop()
        if EPSILON in state.transitions:
            for next_state in state.transitions[EPSILON]:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
                    
    return closure

def move(states, symbol):
    result = set()
    for state in states:
        if symbol in state.transitions:
            for next_state in state.transitions[symbol]:
                result.add(next_state)
    return result

def simulate_afn(afn, string):
    current_states = epsilon_closure({afn.start_state})
    
    for symbol in string:
        moved_states = move(current_states, symbol)
        current_states = epsilon_closure(moved_states)
        
    for state in current_states:
        if state.is_accept:
            return True
            
    return False

if __name__ == "__main__":
    from postfix import conversion_steps, expand_postfix
    from thompson import build_afn_from_postfix
    
    test_regex = "(a|b)*&a&b&b&(a|b)*"
    _, steps = conversion_steps(test_regex)
    tokens = expand_postfix(steps[-1]["output"])
    afn = build_afn_from_postfix(tokens)
    
    tests = ["abb", "aababb", "bbaabbab", "ab", "bba", ""]
    print(f"Probando AFN para regex: {test_regex}")
    for t in tests:
        result = simulate_afn(afn, t)
        print(f"Cadena '{t}': {'sí' if result else 'no'}")
