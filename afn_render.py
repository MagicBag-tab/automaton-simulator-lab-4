import pygame
import math
from afn import EPSILON
from ui import PANEL, BORDER, ACCENT, TEXT_DARK, TEXT_LIGHT, TEXT_MID, BG

class AFNRenderer:
    def __init__(self):
        self.node_radius = 20
        self.layer_spacing_x = 90
        self.layer_spacing_y = 60

    def calculate_layout(self, afn, rect):
        """Calcula las posiciones de cada estado del AFN usando BFS por capas"""
        layers = {}
        queue = [(afn.start_state, 0)]
        visited_dist = {afn.start_state.id: 0}
        
        while queue:
            state, dist = queue.pop(0)
            if dist not in layers:
                layers[dist] = []
            if state not in layers[dist]:
                layers[dist].append(state)
                
            for symbol, next_states in state.transitions.items():
                for next_state in next_states:
                    if next_state.id not in visited_dist or dist + 1 < visited_dist[next_state.id]:
                        visited_dist[next_state.id] = dist + 1
                        queue.append((next_state, dist + 1))
                        
        positions = {}
        max_layer = max(layers.keys()) if layers else 0
        total_width = max_layer * self.layer_spacing_x
        
        start_x = rect.centerx - total_width // 2
        
        for layer_idx, states in layers.items():
            x = start_x + layer_idx * self.layer_spacing_x
            total_height = (len(states) - 1) * self.layer_spacing_y
            start_y = rect.centery - total_height // 2
            
            for i, state in enumerate(states):
                y = start_y + i * self.layer_spacing_y
                positions[state.id] = (x, y)
                
        self._ensure_all_positions(afn.start_state, positions, rect)
        return positions

    def _ensure_all_positions(self, start_state, positions, rect, visited=None):
        if visited is None:
            visited = set()
        if start_state.id in visited:
            return
        visited.add(start_state.id)
        if start_state.id not in positions:
            positions[start_state.id] = (rect.centerx, rect.centery)
        for states in start_state.transitions.values():
            for state in states:
                self._ensure_all_positions(state, positions, rect, visited)

    def draw(self, surface, rect, afn, fonts):
        if not afn:
            return
            
        positions = self.calculate_layout(afn, rect)
        
        visited = set()
        self._draw_transitions(surface, afn.start_state, positions, fonts, visited)
        
        visited = set()
        self._draw_nodes(surface, afn.start_state, positions, fonts, visited)

    def _draw_transitions(self, surface, state, positions, fonts, visited):
        if state.id in visited:
            return
        visited.add(state.id)
        
        start_pos = positions[state.id]
        
        for symbol, next_states in state.transitions.items():
            for next_state in next_states:
                end_pos = positions[next_state.id]
                self._draw_arrow(surface, start_pos, end_pos, symbol, fonts)
                self._draw_transitions(surface, next_state, positions, fonts, visited)

    def _draw_arrow(self, surface, start, end, label, fonts):
        color = BORDER
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        
        if dist == 0:
            center = (start[0], start[1] - self.node_radius - 15)
            pygame.draw.circle(surface, color, center, 15, 2)
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            surface.blit(text, text.get_rect(center=(center[0], center[1] - 15)))
            return
            
        ratio = (dist - self.node_radius) / dist if dist > 0 else 0
        end_x = start[0] + dx * ratio
        end_y = start[1] + dy * ratio
        
        start_ratio = self.node_radius / dist if dist > 0 else 0
        start_x = start[0] + dx * start_ratio
        start_y = start[1] + dy * start_ratio
        
        is_back = dx < 0
        
        if is_back:
            mid_x = (start_x + end_x) / 2
            mid_y = min(start_y, end_y) - 60
            points = []
            for t in range(11):
                t /= 10.0
                x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
                y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y
                points.append((x, y))
            pygame.draw.lines(surface, color, False, points, 2)
            
            angle = math.atan2(end_y - mid_y, end_x - mid_x)
            self._draw_arrow_head(surface, end_x, end_y, angle, color)
            
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            surface.blit(text, text.get_rect(center=(mid_x, mid_y - 10)))
        else:
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), 2)
            angle = math.atan2(dy, dx)
            self._draw_arrow_head(surface, end_x, end_y, angle, color)
            
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2 - 10
            surface.blit(text, text.get_rect(center=(mid_x, mid_y)))

    def _draw_arrow_head(self, surface, x, y, angle, color):
        arrow_len = 10
        angle1 = angle + math.pi - math.pi / 6
        angle2 = angle + math.pi + math.pi / 6
        
        x1 = x + arrow_len * math.cos(angle1)
        y1 = y + arrow_len * math.sin(angle1)
        x2 = x + arrow_len * math.cos(angle2)
        y2 = y + arrow_len * math.sin(angle2)
        
        pygame.draw.polygon(surface, color, [(x, y), (x1, y1), (x2, y2)])

    def _draw_nodes(self, surface, state, positions, fonts, visited):
        if state.id in visited:
            return
        visited.add(state.id)
        
        pos = positions[state.id]
        
        pygame.draw.circle(surface, PANEL, pos, self.node_radius)
        
        border_color = ACCENT if state.is_accept else BORDER
        pygame.draw.circle(surface, border_color, pos, self.node_radius, 2)
        
        if state.is_accept:
            pygame.draw.circle(surface, border_color, pos, self.node_radius - 4, 1)
            
        text = fonts["body"].render(str(state.id), True, TEXT_DARK)
        surface.blit(text, text.get_rect(center=pos))
        
        for next_states in state.transitions.values():
            for next_state in next_states:
                self._draw_nodes(surface, next_state, positions, fonts, visited)
