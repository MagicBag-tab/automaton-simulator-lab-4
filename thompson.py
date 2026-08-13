from afn import State, AFN

EPSILON = "ε"

def create_basic_afn(symbol):
    start = State()
    accept = State(is_accept=True)
    start.add_transition(symbol, accept)
    return AFN(start, accept)

def afn_union(afn1, afn2):
    start = State()
    accept = State(is_accept=True)
    
    start.add_transition(EPSILON, afn1.start_state)
    start.add_transition(EPSILON, afn2.start_state)
    
    afn1.accept_state.is_accept = False
    afn2.accept_state.is_accept = False
    
    afn1.accept_state.add_transition(EPSILON, accept)
    afn2.accept_state.add_transition(EPSILON, accept)
    
    return AFN(start, accept)

def afn_concatenation(afn1, afn2):
    afn1.accept_state.is_accept = False
    afn1.accept_state.add_transition(EPSILON, afn2.start_state)
    return AFN(afn1.start_state, afn2.accept_state)

def afn_star(afn):
    start = State()
    accept = State(is_accept=True)
    
    start.add_transition(EPSILON, afn.start_state)
    start.add_transition(EPSILON, accept)
    
    afn.accept_state.is_accept = False
    afn.accept_state.add_transition(EPSILON, afn.start_state)
    afn.accept_state.add_transition(EPSILON, accept)
    
    return AFN(start, accept)

def build_afn_from_postfix(postfix_tokens):
    State.reset_counter()
    stack = []
    
    for token in postfix_tokens:
        if token == '*':
            afn = stack.pop()
            stack.append(afn_star(afn))
        elif token == '|':
            afn2 = stack.pop()
            afn1 = stack.pop()
            stack.append(afn_union(afn1, afn2))
        elif token == '&':
            afn2 = stack.pop()
            afn1 = stack.pop()
            stack.append(afn_concatenation(afn1, afn2))
        else:
            stack.append(create_basic_afn(token))
            
    if stack:
        return stack.pop()
    return None

if __name__ == "__main__":
    from postfix import conversion_steps, CONCAT, expand_postfix
    
    test_regex = "(a*|b*)+"
    _, steps = conversion_steps(test_regex)
    postfix_tokens = steps[-1]["output"]
    
    expanded_tokens = expand_postfix(postfix_tokens)
    
    print(f"Tokens expandidos: {expanded_tokens}")
    afn = build_afn_from_postfix(expanded_tokens)
    print(f"Estado inicial AFN: {afn.start_state.id}")
    print(f"Estado final AFN: {afn.accept_state.id}")
