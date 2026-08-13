import copy

from postfix import BINARY_OPERATORS, UNARY_OPERATORS, RegexSyntaxError, format_token


def tree_steps(postfix_tokens):
    node_stack = []
    nodes = []
    snapshots = []
    next_id = 0

    def create_node(value, kind, left=None, right=None):
        nonlocal next_id
        node = {
            "id": next_id,
            "val": value,
            "type": kind,
            "parent": None,
            "side": None,
            "visible": True,
            "alpha": 0,
            "scale": 0.4,
        }
        next_id += 1
        nodes.append(node)
        if left is not None:
            left["parent"] = node["id"]
            left["side"] = "left"
        if right is not None:
            right["parent"] = node["id"]
            right["side"] = "right"
        return node

    def child_of(node_id, side):
        return next(
            (
                node
                for node in nodes
                if node.get("parent") == node_id and node.get("side") == side
            ),
            None,
        )

    def clone_subtree(node):
        left = child_of(node["id"], "left")
        right = child_of(node["id"], "right")
        cloned_left = clone_subtree(left) if left is not None else None
        cloned_right = clone_subtree(right) if right is not None else None
        return create_node(node["val"], node["type"], cloned_left, cloned_right)

    for raw_token in postfix_tokens:
        token = format_token(raw_token)
        if raw_token in BINARY_OPERATORS:
            if len(node_stack) < 2:
                raise RegexSyntaxError(f"Faltan operandos para '{token}'")
            right = node_stack.pop()
            left = node_stack.pop()
            node_stack.append(create_node(token, "operator", left, right))
        elif raw_token == "*":
            if not node_stack:
                raise RegexSyntaxError(f"Falta un operando para '{token}'")
            node_stack.append(create_node(token, "operator", node_stack.pop()))
        else:
            node_stack.append(create_node(token, "operand"))
        action = f"Procesar '{token}'"
        snapshots.append({
            "token": token,
            "nodes": copy.deepcopy(nodes),
            "action": action,
        })
    if len(node_stack) != 1:
        raise RegexSyntaxError("La expresión no produce un árbol válido")
    return snapshots
