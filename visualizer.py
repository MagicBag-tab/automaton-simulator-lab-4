import copy
import ctypes
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")


def enable_dpi_awareness():
    if sys.platform != "win32":
        return
    try:
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        pass


enable_dpi_awareness()

import pygame
import pygame.freetype

from postfix import OPERATORS, format_token
from simulation_state import SimulationState
from stack_render import StackRenderer
from tree_render import TreeRenderer
from afn_render import AFNRenderer
from ui import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_SOFT,
    ACTIVE_BD,
    ACTIVE_BG,
    BG,
    BORDER,
    BORDER_STRONG,
    OPERAND,
    OPERATOR,
    PANEL,
    PANEL_MUTED,
    TEXT_DARK,
    TEXT_LIGHT,
    TEXT_MID,
    rounded_rect,
    token_colors,
)


LOGICAL_WIDTH = 1480
LOGICAL_HEIGHT = 1000
WINDOW_WIDTH = LOGICAL_WIDTH
WINDOW_HEIGHT = LOGICAL_HEIGHT
MIN_WIDTH = LOGICAL_WIDTH
MIN_HEIGHT = LOGICAL_HEIGHT
FPS = 60
STEP_DELAY = 1.2
ANIMATION_SPEED = 8.0
MARGIN = 24
PANEL_GAP = 12
PANEL_PADDING = 17


class CrispFont:
    def __init__(self, path, size, bold=False):
        self.font = pygame.freetype.Font(path, size)
        self.font.antialiased = True
        self.font.pad = True
        self.font.strong = bold

    def render(self, text, antialias, color):
        surface, _ = self.font.render(text, fgcolor=color)
        return surface


def load_expressions(path=None):
    source = Path(path) if path else Path(__file__).with_name("expresiones.txt")
    expressions = [line.strip() for line in source.read_text(encoding="utf-8").splitlines()]
    return [expression for expression in expressions if expression]


class VisualizerApp:
    def __init__(self, expressions):
        pygame.init()
        pygame.display.set_caption("Visualizador de árbol sintáctico")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.canvas = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = self._create_fonts()
        self.state = SimulationState(expressions)
        self.stack_renderer = StackRenderer()
        self.tree_renderer = TreeRenderer()
        self.afn_renderer = AFNRenderer()
        self.buttons = {}
        self.viewport = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.scale = WINDOW_WIDTH / LOGICAL_WIDTH

    def _create_fonts(self):
        sans = pygame.font.match_font("inter,segoeui,arial,dejavusans")
        mono = pygame.font.match_font("jetbrainsmono,cascadiamono,consolas,dejavusansmono")
        return {
            "title": CrispFont(sans, 23, True),
            "expression": CrispFont(mono, 24, True),
            "section": CrispFont(sans, 12, True),
            "body": CrispFont(sans, 14),
            "body_bold": CrispFont(sans, 14, True),
            "caption": CrispFont(sans, 11),
            "caption_bold": CrispFont(sans, 11, True),
            "token": CrispFont(mono, 15, True),
        }

    def run(self):
        try:
            running = True
            while running:
                delta = self.clock.tick(FPS) / 1000.0
                running = self._handle_events()
                self.state.update(delta, STEP_DELAY, ANIMATION_SPEED)
                self._draw()
        except KeyboardInterrupt:
            pass
        finally:
            pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                size = max(MIN_WIDTH, event.w), max(MIN_HEIGHT, event.h)
                self.screen = pygame.display.set_mode(size, pygame.RESIZABLE | pygame.DOUBLEBUF)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(self._logical_position(event.pos))
        return True

    def _handle_key(self, key):
        if key == pygame.K_RIGHT:
            self.state.advance()
            self.state.timer = 0.0
        elif key == pygame.K_LEFT:
            self.state.retreat()
            self.state.timer = 0.0
        elif key == pygame.K_SPACE:
            self.state.toggle_play()
        elif key == pygame.K_r:
            self.state.load_expression()
        elif key == pygame.K_PAGEUP:
            self.state.change_expression(-1)
        elif key == pygame.K_PAGEDOWN:
            self.state.change_expression(1)

    def _handle_click(self, position):
        actions = {
            "previous_expression": lambda: self.state.change_expression(-1),
            "next_expression": lambda: self.state.change_expression(1),
            "restart": self.state.load_expression,
            "previous_step": self.state.retreat,
            "play": self.state.toggle_play,
            "next_step": self.state.advance,
            "skip_to_afn": self.state.skip_to_afn,
        }
        for name, rect in self.buttons.items():
            if rect.collidepoint(position):
                actions[name]()
                self.state.timer = 0.0
                break

    def _logical_position(self, position):
        return (
            round((position[0] - self.viewport.x) / max(self.scale, 0.001)),
            round((position[1] - self.viewport.y) / max(self.scale, 0.001)),
        )

    def _draw(self):
        self.canvas.fill(BG)
        self.buttons = {}
        self._draw_header()
        self._draw_expression()
        self._draw_conversion()
        self._draw_main_area()
        self._draw_footer()
        self._present()

    def _present(self):
        screen_width, screen_height = self.screen.get_size()
        self.scale = min(1.0, screen_width / LOGICAL_WIDTH, screen_height / LOGICAL_HEIGHT)
        target_size = round(LOGICAL_WIDTH * self.scale), round(LOGICAL_HEIGHT * self.scale)
        self.viewport = pygame.Rect(0, 0, *target_size)
        self.viewport.center = screen_width // 2, screen_height // 2
        self.screen.fill((232, 237, 244))
        if target_size == (LOGICAL_WIDTH, LOGICAL_HEIGHT):
            self.screen.blit(self.canvas, self.viewport)
        else:
            self.screen.blit(pygame.transform.smoothscale(self.canvas, target_size), self.viewport)
        pygame.display.flip()

    def _draw_panel(self, rect, title=None, emphasized=False):
        rounded_rect(
            self.canvas,
            PANEL,
            rect,
            radius=16,
            border=1,
            border_color=BORDER_STRONG if emphasized else BORDER,
        )
        if title:
            label = self.fonts["section"].render(title, True, TEXT_MID)
            self.canvas.blit(label, (rect.x + PANEL_PADDING, rect.y + 10))

    def _draw_button(self, name, rect, text, primary=False):
        self.buttons[name] = rect
        mouse = self._logical_position(pygame.mouse.get_pos())
        hovered = rect.collidepoint(mouse)
        if primary:
            background = ACCENT_HOVER if hovered else ACCENT
            border = background
            color = (255, 255, 255)
        else:
            background = PANEL_MUTED if hovered else PANEL
            border = BORDER_STRONG if hovered else BORDER
            color = TEXT_DARK if hovered else TEXT_MID
        # Use a larger radius for primary/pill buttons when the rect is wide
        radius = 22 if primary and rect.width > 64 else 11
        rounded_rect(self.canvas, background, rect, radius=radius, border=1, border_color=border)
        label = self.fonts["caption_bold"].render(text, True, color)
        self.canvas.blit(label, label.get_rect(center=rect.center))

    def _draw_header(self):
        pygame.draw.rect(self.canvas, PANEL, pygame.Rect(0, 0, LOGICAL_WIDTH, 46))
        pygame.draw.line(self.canvas, BORDER, (0, 45), (LOGICAL_WIDTH, 45), 1)
        title = self.fonts["title"].render("Visualizador de expresiones regulares", True, TEXT_DARK)
        counter = self.fonts["caption_bold"].render(
            f"Expresión {self.state.expression_index + 1} de {len(self.state.expressions)}",
            True,
            TEXT_MID,
        )
        self.canvas.blit(title, (MARGIN, 9))
        self.canvas.blit(counter, (LOGICAL_WIDTH - MARGIN - counter.get_width(), 18))

    def _draw_expression(self):
        rect = pygame.Rect(MARGIN, 57, LOGICAL_WIDTH - MARGIN * 2, 81)
        self._draw_panel(rect, "EXPRESIÓN REGULAR", emphasized=True)
        indicator = self.fonts["caption"].render(
            f"{self.state.expression_index + 1} / {len(self.state.expressions)}",
            True,
            TEXT_LIGHT,
        )
        self.canvas.blit(indicator, (rect.right - PANEL_PADDING - indicator.get_width(), rect.y + 11))
        expression = self.fonts["expression"].render(self.state.expression, True, TEXT_DARK)
        self.canvas.blit(expression, expression.get_rect(center=(rect.centerx, rect.y + 52)))
        button_size = 34
        self._draw_button(
            "previous_expression",
            pygame.Rect(rect.x + PANEL_PADDING, rect.y + 35, button_size, button_size),
            "<",
        )
        self._draw_button(
            "next_expression",
            pygame.Rect(rect.right - PANEL_PADDING - button_size, rect.y + 35, button_size, button_size),
            ">",
        )

    def _draw_conversion(self):
        rect = pygame.Rect(MARGIN, 150, LOGICAL_WIDTH - MARGIN * 2, 133)
        self._draw_panel(rect, "CONVERSIÓN INFIX → POSTFIX")
        step = self.state.postfix_step
        infix_row = pygame.Rect(rect.x + PANEL_PADDING, rect.y + 34, rect.width - PANEL_PADDING * 2, 38)
        postfix_row = pygame.Rect(rect.x + PANEL_PADDING, rect.y + 81, rect.width - PANEL_PADDING * 2, 38)
        # Show INFIX progression but always display the simplified POSTFIX (expanded '+' and '?')
        self._draw_conversion_row("INFIX", self.state.tokens, infix_row, step["active_tok"])
        try:
            final_output = self.state.postfix_steps[-1]["output"]
        except Exception:
            final_output = step["output"]
        # If we are in the postfix conversion phase, show the animated current output;
        # otherwise show the final simplified postfix.
        postfix_tokens = step["output"] if self.state.phase == "postfix" else final_output
        self._draw_conversion_row("POSTFIX", postfix_tokens, postfix_row)

    def _draw_conversion_row(self, label, tokens, rect, active_index=None):
        rounded_rect(self.canvas, PANEL_MUTED, rect, radius=12, border=1, border_color=BORDER)
        label_surface = self.fonts["caption_bold"].render(label, True, TEXT_MID)
        self.canvas.blit(label_surface, (rect.x + 10, rect.centery - label_surface.get_height() // 2))
        # Reserve slightly less horizontal space for the left label to give tokens more room
        token_area = pygame.Rect(rect.x + 60, rect.y + 4, rect.width - 70, rect.height - 8)
        self._draw_token_row(tokens, token_area, active_index)

    def _draw_token_row(self, tokens, rect, active_index=None):
        # Tweak chip size/gap so tokens fit better in narrow containers
        chip_size = 24
        gap = 6
        maximum = max(1, (rect.width + gap) // (chip_size + gap))
        visible = list(tokens[:maximum])
        clipped = len(tokens) > maximum
        if clipped:
            visible[-1] = "…"
        total_width = len(visible) * chip_size + max(0, len(visible) - 1) * gap
        # Center the row of chips within the provided rect (even if it overflows)
        start_x = rect.centerx - total_width // 2
        for index, raw_token in enumerate(visible):
            token = format_token(raw_token)
            chip = pygame.Rect(start_x + index * (chip_size + gap), rect.y + 1, chip_size, chip_size)
            active = index == active_index and not (clipped and index == len(visible) - 1)
            processed = active_index is not None and index < active_index
            foreground, soft_background = token_colors(token)
            background = ACTIVE_BG if active else (soft_background if processed else PANEL)
            border = ACTIVE_BD if active else (foreground if processed else BORDER)
            if active:
                pulse = (math.sin(self.state.time * 6) + 1) / 2
                glow_rect = chip.inflate(round(pulse * 10 + 4), round(pulse * 10 + 4))
                glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(glow, (*ACCENT, 18), glow.get_rect(), border_radius=12)
                self.canvas.blit(glow, glow_rect.topleft)
            rounded_rect(
                self.canvas,
                background,
                chip,
                radius=3,
                border=2 if active else 1,
                border_color=border,
            )
            text = self.fonts["token"].render(token, True, ACCENT if active else foreground)
            self.canvas.blit(text, text.get_rect(center=chip.center))

    def _draw_main_area(self):
        top = 294
        footer_top = LOGICAL_HEIGHT - 94
        height = footer_top - top - 12
        available_width = LOGICAL_WIDTH - MARGIN * 2 - PANEL_GAP
        
        if self.state.phase == "afn":
            # AFN ocupa todo el ancho, ocultando el stack
            afn_rect = pygame.Rect(MARGIN, top, LOGICAL_WIDTH - MARGIN * 2, height)
            self._draw_panel(afn_rect, "AFN DE THOMPSON", emphasized=True)
            self._draw_tree(afn_rect)
            return

        stack_width = round(available_width * 0.25)
        stack_rect = pygame.Rect(MARGIN, top, stack_width, height)
        tree_rect = pygame.Rect(stack_rect.right + PANEL_GAP, top, available_width - stack_width, height)
        self._draw_panel(stack_rect, emphasized=True)
        self._draw_panel(tree_rect, "ÁRBOL SINTÁCTICO", emphasized=True)
        stack_height = round(stack_rect.height * 0.58)
        action_height = 90
        stack_area = pygame.Rect(stack_rect.x, stack_rect.y, stack_rect.width, stack_height)
        processing_area = pygame.Rect(
            stack_rect.x + PANEL_PADDING,
            stack_rect.y + stack_height,
            stack_rect.width - PANEL_PADDING * 2,
            action_height,
        )
        legend_area = pygame.Rect(
            stack_rect.x + PANEL_PADDING,
            processing_area.bottom,
            stack_rect.width - PANEL_PADDING * 2,
            stack_rect.bottom - processing_area.bottom,
        )
        divider_left = stack_rect.x + PANEL_PADDING
        divider_right = stack_rect.right - PANEL_PADDING
        pygame.draw.line(self.canvas, BORDER, (divider_left, stack_area.bottom), (divider_right, stack_area.bottom), 1)
        pygame.draw.line(self.canvas, BORDER, (divider_left, processing_area.bottom), (divider_right, processing_area.bottom), 1)
        self._draw_stack(stack_area)
        self._draw_processing(processing_area)
        self._draw_legend(legend_area)
        self._draw_tree(tree_rect)

    def _draw_stack(self, rect):
        items = [
            (format_token(token), "operator" if token in OPERATORS else "operand")
            for token in reversed(self.state.postfix_step["stack"])
        ]
        self.stack_renderer.draw(self.canvas, rect, items, self.fonts, self.state.push_animation)

    def _draw_tree(self, rect):
        content = pygame.Rect(rect.x + 8, rect.y + 28, rect.width - 16, rect.height - 34)
        if self.state.phase == "afn":
            self.afn_renderer.draw(self.canvas, content, self.state.afn, self.fonts)
            return
        if self.state.phase == "postfix":
            self._draw_empty_tree(content)
            return
        nodes = copy.deepcopy(self.state.tree_step["nodes"])
        for node in nodes:
            animation = self.state.node_animations.get(node["id"], {"alpha": 255, "scale": 1.0})
            node.update(alpha=int(animation["alpha"]), scale=animation["scale"])
        self.tree_renderer.draw(self.canvas, content, nodes, self.fonts)

    def _draw_empty_tree(self, rect):
        center_x = rect.centerx
        center_y = rect.centery - 24
        points = [(center_x, center_y - 32), (center_x - 42, center_y + 18), (center_x + 42, center_y + 18)]
        pygame.draw.aaline(self.canvas, BORDER_STRONG, points[0], points[1])
        pygame.draw.aaline(self.canvas, BORDER_STRONG, points[0], points[2])
        for point in points:
            pygame.draw.circle(self.canvas, PANEL_MUTED, point, 13)
            pygame.draw.circle(self.canvas, BORDER_STRONG, point, 13, 2)
        title = self.fonts["body_bold"].render("El árbol aparecerá aquí", True, TEXT_MID)
        subtitle = self.fonts["caption"].render("Avanza hasta la fase de construcción", True, TEXT_LIGHT)
        self.canvas.blit(title, title.get_rect(center=(center_x, center_y + 66)))
        self.canvas.blit(subtitle, subtitle.get_rect(center=(center_x, center_y + 92)))

    def _draw_processing(self, rect):
        # Restore top label 'ACCIÓN ACTUAL' per user request.
        title = self.fonts["section"].render("ACCIÓN ACTUAL", True, TEXT_MID)
        counter = self.fonts["caption_bold"].render(
            f"Paso {self.state.step_index + 1} de {self.state.total_steps}",
            True,
            TEXT_MID,
        )
        self.canvas.blit(title, (rect.x, rect.y + 12))
        self.canvas.blit(counter, (rect.right - counter.get_width(), rect.y + 12))
        token = self._current_token()
        # Keep the processing token aligned to the left of the action label
        chip = pygame.Rect(rect.x, rect.y + 38, 30, 26)
        foreground, background = token_colors(token)
        rounded_rect(self.canvas, background, chip, radius=8, border=1, border_color=foreground)
        token_text = self.fonts["token"].render(token, True, foreground)
        self.canvas.blit(token_text, token_text.get_rect(center=chip.center))
        action = self.fonts["body_bold"].render(self.state.current_action, True, TEXT_DARK)
        self.canvas.blit(action, (chip.right + 10, rect.y + 43))
        progress_rect = pygame.Rect(rect.x, rect.bottom - 12, rect.width, 5)
        rounded_rect(self.canvas, (232, 236, 242), progress_rect, radius=3)
        fill = pygame.Rect(progress_rect.x, progress_rect.y, max(4, round(progress_rect.width * self.state.progress)), 4)
        rounded_rect(self.canvas, ACCENT, fill, radius=3)

    def _draw_legend(self, rect):
        entries = ((OPERAND, "Operando"), (OPERATOR, "Operador"), (ACCENT, "Activo"))
        # Move legend up and tighten spacing so labels don't overflow the left container
        start_y = rect.y + 6
        spacing = 16
        for index, (color, label) in enumerate(entries):
            y = start_y + index * spacing
            pygame.draw.circle(self.canvas, color, (rect.x + 8, y + 5), 4)
            text = self.fonts["caption"].render(label, True, TEXT_MID)
            self.canvas.blit(text, (rect.x + 20, y))

    def _current_token(self):
        if self.state.phase == "tree" and self.state.tree_step:
            return self.state.tree_step["token"]
        index = self.state.postfix_step["active_tok"]
        return format_token(self.state.tokens[index]) if self.state.tokens else "·"

    def _draw_footer(self):
        rect = pygame.Rect(MARGIN, LOGICAL_HEIGHT - 94, LOGICAL_WIDTH - MARGIN * 2, 78)
        self._draw_panel(rect, emphasized=True)
        button_size = 44
        # Make play button same style as restart (non-primary) and similar width
        specs = [
            ("previous_step", "<", button_size, False),
            ("play", "Pausar" if self.state.auto_play else "▶", 96, False),
            ("next_step", ">", button_size, False),
            ("restart", "Reiniciar", 96, False),
            ("skip_to_afn", "Ver AFN", 96, True),
        ]
        total_width = sum(item[2] for item in specs) + PANEL_GAP * (len(specs) - 1)
        x = LOGICAL_WIDTH // 2 - total_width // 2
        y = rect.centery - button_size // 2
        for name, label, width, primary in specs:
            self._draw_button(name, pygame.Rect(x, y, width, button_size), label, primary)
            x += width + PANEL_GAP
