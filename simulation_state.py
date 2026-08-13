from postfix import OPERATORS, conversion_steps, format_token
from syntax_tree import tree_steps


class SimulationState:
    def __init__(self, expressions):
        if not expressions:
            raise ValueError("Se necesita al menos una expresión")
        self.expressions = expressions
        self.expression_index = 0
        self.auto_play = True
        self.timer = 0.0
        self.time = 0.0
        self.node_animations = {}
        self.push_animation = None
        self.load_expression()

    @property
    def expression(self):
        return self.expressions[self.expression_index]

    @property
    def postfix_step(self):
        if self.phase == "postfix":
            return self.postfix_steps[min(self.step_index, len(self.postfix_steps) - 1)]
        return self.postfix_steps[-1]

    @property
    def tree_step(self):
        if self.phase == "tree":
            return self.tree_build_steps[min(self.step_index, len(self.tree_build_steps) - 1)]
        return None

    @property
    def current_action(self):
        step = self.postfix_step if self.phase == "postfix" else self.tree_step
        return step["action"] if step else ""

    @property
    def total_steps(self):
        return len(self.postfix_steps if self.phase == "postfix" else self.tree_build_steps)

    @property
    def progress(self):
        return (self.step_index + 1) / max(1, self.total_steps)

    def load_expression(self):
        # Tokenize original expression and expand '+'/'?' in infix form so
        # both the INFIX row and the conversion animation use the simplified version.
        try:
            from postfix import tokenize, expand_infix_tokens, expand_postfix

            raw_tokens = tokenize(self.expression)
            simplified_infix_tokens = expand_infix_tokens(raw_tokens)
            simplified_expr = "".join(simplified_infix_tokens)
            self.tokens, self.postfix_steps = conversion_steps(simplified_expr)
            postfix = self.postfix_steps[-1]["output"]
            simplified_postfix = expand_postfix(postfix)
        except Exception:
            # fallback to original behavior on error
            self.tokens, self.postfix_steps = conversion_steps(self.expression)
            postfix = self.postfix_steps[-1]["output"]
            try:
                from postfix import expand_postfix

                simplified_postfix = expand_postfix(postfix)
            except Exception:
                simplified_postfix = postfix

        # Replace the final postfix output with the simplified version so the UI shows it
        try:
            self.postfix_steps[-1]["output"] = simplified_postfix
        except Exception:
            pass
        self.tree_build_steps = tree_steps(simplified_postfix)
        self.phase = "postfix"
        self.step_index = 0
        self.timer = 0.0
        self.node_animations = {}
        self.push_animation = None

    def change_expression(self, offset):
        self.expression_index = (self.expression_index + offset) % len(self.expressions)
        self.load_expression()

    def advance(self):
        if self.phase == "postfix" and self.step_index < len(self.postfix_steps) - 1:
            previous = self.postfix_steps[self.step_index]["stack"]
            self.step_index += 1
            current = self.postfix_steps[self.step_index]["stack"]
            if len(current) > len(previous):
                token = current[-1]
                self.push_animation = {
                    "val": format_token(token),
                    "type": "operator" if token in OPERATORS else "operand",
                    "t": 0.0,
                }
        elif self.phase == "postfix":
            self.phase = "tree"
            self.step_index = 0
            self._initialize_nodes()
        elif self.step_index < len(self.tree_build_steps) - 1:
            self.step_index += 1
            self._initialize_nodes()

    def retreat(self):
        if self.phase == "tree" and self.step_index == 0:
            self.phase = "postfix"
            self.step_index = len(self.postfix_steps) - 1
        elif self.step_index > 0:
            self.step_index -= 1

    def toggle_play(self):
        self.auto_play = not self.auto_play
        self.timer = 0.0

    def update(self, delta, step_delay, animation_speed):
        self.time += delta
        self.timer += delta
        if self.push_animation is not None:
            self.push_animation["t"] = min(1.0, self.push_animation["t"] + delta * animation_speed)
            if self.push_animation["t"] >= 1.0:
                self.push_animation = None
        if self.phase == "tree" and self.tree_step:
            self._initialize_nodes()
            for node in self.tree_step["nodes"]:
                animation = self.node_animations[node["id"]]
                animation["alpha"] = min(255.0, animation["alpha"] + delta * animation_speed * 255)
                animation["scale"] = min(1.0, animation["scale"] + delta * animation_speed * 0.6)
        if self.auto_play and self.timer >= step_delay:
            self.timer = 0.0
            if self.phase == "postfix" or self.step_index < len(self.tree_build_steps) - 1:
                self.advance()

    def _initialize_nodes(self):
        if not self.tree_step:
            return
        for node in self.tree_step["nodes"]:
            self.node_animations.setdefault(node["id"], {"alpha": 0.0, "scale": 0.4})
