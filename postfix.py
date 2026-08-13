CONCAT = "&"
UNARY_OPERATORS = {"*", "+", "?"}
BINARY_OPERATORS = {"|", "^", CONCAT}
OPERATORS = UNARY_OPERATORS | BINARY_OPERATORS | {"(", ")"}


class RegexSyntaxError(ValueError):
    pass


def format_token(token):
    return "." if token == CONCAT else token


def tokenize(expression):
    compact = expression.replace(" ", "")
    tokens = []
    index = 0
    while index < len(compact):
        if compact[index] == "\\":
            if index + 1 == len(compact):
                raise RegexSyntaxError("La expresión termina con un escape incompleto")
            tokens.append(compact[index:index + 2])
            index += 2
        else:
            tokens.append(compact[index])
            index += 1
    return tokens


def add_concatenation(tokens):
    result = []
    for index, token in enumerate(tokens):
        result.append(token)
        if index + 1 == len(tokens):
            continue
        following = tokens[index + 1]
        left_can_end = _is_symbol(token) or token == ")" or token in UNARY_OPERATORS
        right_can_start = _is_symbol(following) or following == "("
        if left_can_end and right_can_start:
            result.append(CONCAT)
    return result


def conversion_steps(expression):
    tokens = add_concatenation(tokenize(expression))
    if not tokens:
        raise RegexSyntaxError("La expresión está vacía")
    _validate(tokens)
    output = []
    stack = []
    steps = []

    def capture(action, active_token):
        steps.append({
            "action": action,
            "active_tok": active_token,
            "stack": list(stack),
            "output": list(output),
        })

    for index, token in enumerate(tokens):
        if token == "(":
            stack.append(token)
            capture("Agregar '(' a la pila", index)
        elif token == ")":
            while stack and stack[-1] != "(":
                popped = stack.pop()
                output.append(popped)
                capture(f"Mover '{format_token(popped)}' a la salida", index)
            stack.pop()
            capture("Descartar '('", index)
        elif token in UNARY_OPERATORS | BINARY_OPERATORS:
            while stack and stack[-1] != "(" and _precedence(stack[-1]) >= _precedence(token):
                popped = stack.pop()
                output.append(popped)
                capture(f"Mover '{format_token(popped)}' a la salida", index)
            stack.append(token)
            capture(f"Agregar '{format_token(token)}' a la pila", index)
        else:
            output.append(token)
            capture(f"Mover '{format_token(token)}' a la salida", index)

    while stack:
        popped = stack.pop()
        output.append(popped)
        capture(f"Vaciar '{format_token(popped)}' a la salida", len(tokens) - 1)
    return tokens, steps


def infix_to_postfix(expression):
    _, steps = conversion_steps(expression)
    return " ".join(format_token(token) for token in steps[-1]["output"])


def _is_symbol(token):
    return token not in OPERATORS or token.startswith("\\")


def _precedence(token):
    levels = {"(": 1, "|": 2, CONCAT: 3, "*": 4, "+": 4, "?": 4, "^": 5}
    return levels.get(token, 0)


def _validate(tokens):
    balance = 0
    expects_operand = True
    for token in tokens:
        if token == "(":
            balance += 1
            expects_operand = True
        elif token == ")":
            if balance == 0 or expects_operand:
                raise RegexSyntaxError("Paréntesis inválidos")
            balance -= 1
            expects_operand = False
        elif token in BINARY_OPERATORS:
            if expects_operand:
                raise RegexSyntaxError(f"El operador '{format_token(token)}' no tiene operando izquierdo")
            expects_operand = True
        elif token in UNARY_OPERATORS:
            if expects_operand:
                raise RegexSyntaxError(f"El operador '{token}' no tiene operando")
            expects_operand = False
        else:
            if not expects_operand:
                raise RegexSyntaxError("Falta un operador entre símbolos")
            expects_operand = False
    if balance:
        raise RegexSyntaxError("Hay paréntesis sin cerrar")
    if expects_operand:
        raise RegexSyntaxError("La expresión termina con un operador")


def expand_infix_tokens(tokens):
    """Return a new token list where '+' and '?' are expanded in infix form.

    Rules:
    - X+  -> ( X X* )
    - X?  -> ( X | ε )

    `tokens` should be the raw list from `tokenize()`.
    """
    result = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ('+', '?'):
            if not result:
                raise RegexSyntaxError(f"Falta un operando para '{tok}' al expandir infix")
            # find the last operand in result
            if result[-1] == ')':
                # find matching '('
                depth = 0
                j = len(result) - 1
                while j >= 0:
                    if result[j] == ')':
                        depth += 1
                    elif result[j] == '(':
                        depth -= 1
                        if depth == 0:
                            break
                    j -= 1
                if j < 0:
                    raise RegexSyntaxError(f"Paréntesis no balanceados al expandir '{tok}'")
                operand = result[j:]
                result = result[:j]
            else:
                operand = [result.pop()]

            if tok == '+':
                expanded = ['('] + operand + operand + ['*'] + [')']
            else:  # '?'
                expanded = ['('] + operand + ['|', 'ε'] + [')']

            result.extend(expanded)
            i += 1
        else:
            result.append(tok)
            i += 1

    return result


def expand_postfix(tokens):
    """Return a new postfix token list where '+' and '?' are expanded:
    - r+ -> r r * &  (operand, operand, '*', concat)
    - r? -> r ε |
    The function works on raw tokens produced by `conversion_steps` (uses CONCAT).
    """
    stack = []
    for tok in tokens:
        if tok == '+':
            if not stack:
                raise RegexSyntaxError("Falta un operando para '+' al expandir postfix")
            s = stack.pop()
            cloned = list(s)
            # r+ -> r r* &  (we use CONCAT token for concatenation)
            combined = s + cloned + ['*', CONCAT]
            stack.append(combined)
        elif tok == '?':
            if not stack:
                raise RegexSyntaxError("Falta un operando para '?' al expandir postfix")
            s = stack.pop()
            # r? -> r ε |
            combined = s + ['ε', '|']
            stack.append(combined)
        elif tok in UNARY_OPERATORS | BINARY_OPERATORS:
            if tok in UNARY_OPERATORS:
                if not stack:
                    raise RegexSyntaxError(f"Falta un operando para '{tok}' al expandir postfix")
                s = stack.pop()
                stack.append(s + [tok])
            else:
                # binary operator: pop right then left
                if len(stack) < 2:
                    raise RegexSyntaxError(f"Faltan operandos para '{tok}' al expandir postfix")
                right = stack.pop()
                left = stack.pop()
                stack.append(left + right + [tok])
        else:
            # operand
            stack.append([tok])

    if not stack:
        return []
    # there may be multiple items if original postfix represented multiple expressions;
    # merge them by concatenating their lists
    result = []
    for part in stack:
        result.extend(part)
    return result
