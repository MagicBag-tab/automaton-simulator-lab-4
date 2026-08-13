import pygame
import math
from thompson import EPSILON
from ui import PANEL, BORDER, ACCENT, TEXT_DARK, TEXT_LIGHT, TEXT_MID, BG

class AFNRenderer:
    def __init__(self):
        self.node_radius = 24
        self.layer_spacing_x = 115
        self.layer_spacing_y = 95

    def calculate_layout(self, afn, rect):
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
        
        available_width = rect.width - 100
        if total_width > available_width:
            self.layer_spacing_x = available_width // max(1, max_layer)
        
        start_x = rect.centerx - total_width // 2
        if total_width > available_width:
            start_x = rect.left + 50
        
        for layer_idx, states in layers.items():
            x = start_x + layer_idx * self.layer_spacing_x
            total_height = (len(states) - 1) * self.layer_spacing_y
            available_height = rect.height - 100
            
            if total_height > available_height:
                current_spacing_y = available_height // max(1, len(states) - 1)
            else:
                current_spacing_y = self.layer_spacing_y
            
            start_y = rect.centery - total_height // 2
            if total_height > available_height:
                start_y = rect.top + 50
            
            for i, state in enumerate(states):
                y = start_y + i * current_spacing_y
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
            
        self.rect_centery = rect.centery
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
        
        destinations = {}
        for symbol, next_states in state.transitions.items():
            for next_state in next_states:
                if next_state.id not in destinations:
                    destinations[next_state.id] = []
                destinations[next_state.id].append(symbol)
                
        for dest_id, symbols in destinations.items():
            end_pos = positions[dest_id]
            label = ", ".join(symbols)
            self._draw_arrow(surface, start_pos, end_pos, label, fonts)
            
        for next_states in state.transitions.values():
            for next_state in next_states:
                self._draw_transitions(surface, next_state, positions, fonts, visited)

    def _draw_arrow(self, surface, start, end, label, fonts):
        color = BORDER
        thickness = 3 
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dist = math.hypot(dx, dy)
        
        if dist == 0:
            center = (start[0], start[1] - self.node_radius - 24)
            pygame.draw.circle(surface, color, center, 24, thickness)
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            surface.blit(text, text.get_rect(center=(center[0], center[1] - 24)))
            return
            
        ratio = (dist - self.node_radius) / dist if dist > 0 else 0
        end_x = start[0] + dx * ratio
        end_y = start[1] + dy * ratio
        
        start_ratio = self.node_radius / dist if dist > 0 else 0
        start_x = start[0] + dx * start_ratio
        start_y = start[1] + dy * start_ratio
        
        is_back = dx < 0
        is_long = dx > self.layer_spacing_x * 1.5
        
        if is_back or is_long:
            edge_center_y = (start_y + end_y) / 2
            
            # Los regresos siempre por arriba, los saltos largos siempre por abajo
            # Esto forma un "círculo" o burbuja alrededor de la estructura
            if is_back:
                offset = -130
            else:
                offset = 130
                
            mid_x = (start_x + end_x) / 2
            mid_y = edge_center_y + offset
            
            points = []
            for t in range(11):
                t /= 10.0
                x = (1-t)**2 * start_x + 2*(1-t)*t * mid_x + t**2 * end_x
                y = (1-t)**2 * start_y + 2*(1-t)*t * mid_y + t**2 * end_y
                points.append((x, y))
            pygame.draw.lines(surface, color, False, points, thickness)
            
            prev_x, prev_y = points[-2]
            angle = math.atan2(end_y - prev_y, end_x - prev_x)
            self._draw_arrow_head(surface, end_x, end_y, angle, color)
            
            # El punto máximo de una curva bezier cuadrática está a la mitad del offset
            peak_y = edge_center_y + offset * 0.5
            label_offset = 16 if offset > 0 else -16
            
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            text_rect = text.get_rect(center=(mid_x, peak_y + label_offset))
            bg_rect = text_rect.inflate(14, 8)
            pygame.draw.rect(surface, BG, bg_rect)
            surface.blit(text, text_rect)
        else:
            pygame.draw.line(surface, color, (start_x, start_y), (end_x, end_y), thickness)
            angle = math.atan2(dy, dx)
            self._draw_arrow_head(surface, end_x, end_y, angle, color)
            
            text = fonts["caption_bold"].render(label, True, TEXT_DARK)
            
            t = 0.4
            label_base_x = start_x + dx * t
            label_base_y = start_y + dy * t
            
            if dy < -5:
                normal_x = dy / dist
                normal_y = -dx / dist
            elif dy > 5:
                normal_x = -dy / dist
                normal_y = dx / dist
            else:
                normal_x = 0
                normal_y = -1
                
            offset_dist = 24
            label_x = label_base_x + normal_x * offset_dist
            label_y = label_base_y + normal_y * offset_dist
            
            text_rect = text.get_rect(center=(label_x, label_y))
            bg_rect = text_rect.inflate(14, 8)
            pygame.draw.rect(surface, BG, bg_rect)
            surface.blit(text, text_rect)

    def _draw_arrow_head(self, surface, x, y, angle, color):
        arrow_len = 16
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
        pygame.draw.circle(surface, border_color, pos, self.node_radius, 3)
        
        if state.is_accept:
            pygame.draw.circle(surface, border_color, pos, self.node_radius - 6, 2)
            
        text = fonts["expression"].render(str(state.id), True, TEXT_DARK)
        surface.blit(text, text.get_rect(center=pos))
        
        for next_states in state.transitions.values():
            for next_state in next_states:
                self._draw_nodes(surface, next_state, positions, fonts, visited)
