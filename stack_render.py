import pygame

from ui import ACCENT, OPERAND, OPERAND_SOFT, OPERATOR, OPERATOR_SOFT, TEXT_LIGHT, TEXT_MID


class StackRenderer:
    ITEM_HEIGHT = 36
    GAP = 6

    def draw(self, surface, rect, stack_items, fonts, animation=None):
        # Use the same label color as other panel titles for consistency
        title = fonts["section"].render("STACK", True, TEXT_MID)
        # Remove the 'TOPE ↑' label per request
        surface.blit(title, title.get_rect(center=(rect.centerx, rect.y + 22)))
        base_y = rect.y + 68
        item_width = min(150, rect.width - 54)
        maximum = max(0, (rect.bottom - base_y - 12) // (self.ITEM_HEIGHT + self.GAP))
        visible_items = stack_items[:maximum]
        if not visible_items and not animation:
            empty = fonts["body"].render("Pila vacía", True, TEXT_LIGHT)
            empty_center_y = base_y + max(0, rect.bottom - base_y) // 2
            surface.blit(empty, empty.get_rect(center=(rect.centerx, empty_center_y)))
            return
        if animation:
            y = base_y - (1 - animation["t"]) * 28
            self._draw_item(
                surface,
                rect.centerx,
                int(y),
                item_width,
                animation["val"],
                animation["type"],
                fonts,
                int(animation["t"] * 255),
                True,
            )
        for index, (value, kind) in enumerate(visible_items):
            y = base_y + index * (self.ITEM_HEIGHT + self.GAP)
            if animation:
                y += (1 - animation["t"]) * (self.ITEM_HEIGHT + self.GAP)
            self._draw_item(surface, rect.centerx, int(y), item_width, value, kind, fonts)

    def _draw_item(self, surface, center_x, y, width, value, kind, fonts, alpha=255, active=False):
        rect = pygame.Rect(center_x - width // 2, y, width, self.ITEM_HEIGHT)
        color = OPERATOR if kind == "operator" else OPERAND
        background = OPERATOR_SOFT if kind == "operator" else OPERAND_SOFT
        if active:
            background = (237, 243, 255)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, (*background, alpha), layer.get_rect(), border_radius=10)
        pygame.draw.rect(
            layer,
            (*(ACCENT if active else color), alpha),
            layer.get_rect(),
            width=2 if active else 1,
            border_radius=10,
        )
        text = fonts["token"].render(value, True, color)
        text.set_alpha(alpha)
        layer.blit(text, text.get_rect(center=(rect.width // 2, rect.height // 2)))
        surface.blit(layer, rect.topleft)
