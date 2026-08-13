import math

import pygame

from ui import ACCENT, EDGE, OPERAND, OPERAND_SOFT, OPERATOR, OPERATOR_SOFT, TEXT_MID


class TreeRenderer:
    NODE_SIZE = 38

    def draw(self, surface, rect, nodes, fonts):
        if not nodes:
            message = fonts["body"].render("Construyendo árbol...", True, TEXT_MID)
            surface.blit(message, message.get_rect(center=rect.center))
            return
        visible = [node for node in nodes if node.get("visible", True)]
        positions = self._layout(visible, rect.inflate(-38, -53))
        by_id = {node["id"]: node for node in visible}
        newest_id = max(by_id)
        for node in visible:
            parent_id = node.get("parent")
            if parent_id in by_id:
                self._draw_edge(surface, positions[node["id"]], positions[parent_id], node.get("alpha", 255))
        for node in visible:
            self._draw_node(
                surface,
                positions[node["id"]],
                node["val"],
                node["type"],
                fonts,
                node.get("alpha", 255),
                node.get("scale", 1.0),
                node["id"] == newest_id,
            )

    def _layout(self, nodes, rect):
        by_id = {node["id"]: node for node in nodes}
        children = {}
        for node in nodes:
            if node.get("parent") in by_id:
                children.setdefault(node["parent"], {})[node.get("side")] = node["id"]
        roots = [node["id"] for node in nodes if node.get("parent") not in by_id]
        depths = {}
        widths = {}

        def measure(node_id, depth=0):
            depths[node_id] = depth
            child_map = children.get(node_id, {})
            left_width = measure(child_map["left"], depth + 1) if "left" in child_map else 0
            right_width = measure(child_map["right"], depth + 1) if "right" in child_map else 0
            widths[node_id] = max(1, left_width + right_width)
            return widths[node_id]

        for root_id in roots:
            measure(root_id)
        maximum_depth = max(depths.values(), default=0)
        forest_gap = 0.75
        total_units = sum(widths[root_id] for root_id in roots) + forest_gap * max(0, len(roots) - 1)
        horizontal_gap = min(64, (rect.width - self.NODE_SIZE) / max(1, total_units))
        vertical_gap = min(63, (rect.height - self.NODE_SIZE) / max(1, maximum_depth)) if maximum_depth else 0
        forest_width = total_units * horizontal_gap
        cursor = rect.centerx - forest_width / 2
        start_y = rect.centery - maximum_depth * vertical_gap / 2
        positions = {}

        def place(node_id, left_edge):
            width = widths[node_id] * horizontal_gap
            positions[node_id] = (
                round(left_edge + width / 2),
                round(start_y + depths[node_id] * vertical_gap),
            )
            child_map = children.get(node_id, {})
            if "left" in child_map and "right" in child_map:
                place(child_map["left"], left_edge)
                place(child_map["right"], left_edge + widths[child_map["left"]] * horizontal_gap)
            elif "left" in child_map:
                child_id = child_map["left"]
                place(child_id, left_edge + (width - widths[child_id] * horizontal_gap) / 2)
            elif "right" in child_map:
                child_id = child_map["right"]
                place(child_id, left_edge + (width - widths[child_id] * horizontal_gap) / 2)

        for root_id in roots:
            place(root_id, cursor)
            cursor += (widths[root_id] + forest_gap) * horizontal_gap
        return positions

    def _draw_edge(self, surface, child, parent, alpha):
        dx = parent[0] - child[0]
        dy = parent[1] - child[1]
        distance = max(1.0, math.hypot(dx, dy))
        offset = self.NODE_SIZE / 2 - 2
        start = child[0] + dx / distance * offset, child[1] + dy / distance * offset
        end = parent[0] - dx / distance * offset, parent[1] - dy / distance * offset
        if alpha >= 255:
            pygame.draw.aaline(surface, EDGE, start, end)
            pygame.draw.aaline(surface, EDGE, (start[0] + 1, start[1]), (end[0] + 1, end[1]))
            return
        left = math.floor(min(start[0], end[0])) - 2
        top = math.floor(min(start[1], end[1])) - 2
        width = math.ceil(abs(end[0] - start[0])) + 5
        height = math.ceil(abs(end[1] - start[1])) + 5
        layer = pygame.Surface((width, height), pygame.SRCALPHA)
        local_start = start[0] - left, start[1] - top
        local_end = end[0] - left, end[1] - top
        pygame.draw.aaline(layer, (*EDGE, alpha), local_start, local_end)
        pygame.draw.aaline(layer, (*EDGE, alpha // 2), (local_start[0] + 1, local_start[1]), (local_end[0] + 1, local_end[1]))
        surface.blit(layer, (left, top))

    def _draw_node(self, surface, position, value, kind, fonts, alpha, scale, active):
        size = max(2, round(self.NODE_SIZE * scale))
        rect = pygame.Rect(0, 0, size, size)
        rect.center = position
        color = OPERATOR if kind == "operator" else OPERAND
        background = OPERATOR_SOFT if kind == "operator" else OPERAND_SOFT
        if active:
            glow_rect = rect.inflate(9, 9)
            glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*ACCENT, min(24, alpha)), glow.get_rect(), border_radius=18)
            surface.blit(glow, glow_rect.topleft)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, (*background, alpha), layer.get_rect(), border_radius=max(10, size // 3))
        pygame.draw.rect(
            layer,
            (*(ACCENT if active else color), alpha),
            layer.get_rect(),
            width=2 if active else 1,
            border_radius=max(10, size // 3),
        )
        text = fonts["token"].render(value, True, color)
        text.set_alpha(alpha)
        layer.blit(text, text.get_rect(center=(size // 2, size // 2)))
        surface.blit(layer, rect.topleft)
