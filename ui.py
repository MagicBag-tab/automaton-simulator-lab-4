import pygame


BG = (244, 247, 251)
PANEL = (255, 255, 255)
PANEL_MUTED = (248, 250, 253)
BORDER = (222, 228, 237)
BORDER_STRONG = (207, 216, 229)
TEXT_DARK = (27, 39, 58)
TEXT_MID = (91, 105, 126)
TEXT_LIGHT = (145, 157, 175)
ACCENT = (72, 124, 235)
ACCENT_HOVER = (61, 111, 221)
ACCENT_SOFT = (235, 242, 255)
OPERATOR = (128, 84, 190)
OPERATOR_SOFT = (245, 239, 252)
OPERAND = (42, 151, 103)
OPERAND_SOFT = (235, 248, 241)
ACTIVE_BG = ACCENT_SOFT
ACTIVE_BD = ACCENT
EDGE = (167, 178, 195)


def rounded_rect(surface, color, rect, radius=12, border=0, border_color=None):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, width=border, border_radius=radius)


def token_colors(token):
    if token in "*|+.^?()":
        return OPERATOR, OPERATOR_SOFT
    return OPERAND, OPERAND_SOFT
