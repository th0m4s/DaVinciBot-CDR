from abc import ABC
from typing import Callable, Dict
import pygame


class PygCdrObject(ABC):
    def __init__(self, pos, size=None, object=None, cursor_data=None, onclick=None, onhover=None, onenter=None, onleave=None, onreleased=None, onkeydown=None, anchor=(0, 0)):
        self.x, self.y = pos
        self.visible = True
        self.anchor = anchor
        self.object = object
        self.cursor_data = cursor_data

        self.focused = False

        self.onclick = onclick
        self.onhover = onhover
        self.onenter = onenter
        self.onleave = onleave
        self.onreleased = onreleased
        self.onkeydown = onkeydown

        self.onfocus = None
        self.onblur = None

        self.is_hovered = False
        self.is_clicked = False
        self.update_size(size)

    def update_size(self, size):
        self.size = size
        if self.x is not None and self.x is not None and size is not None:
            self.rect = pygame.Rect(*(self.compute_pos()), size[0], size[1])
        else:
            self.rect = None

    def compute_pos(self):
        """Computes the position of the object based on its anchor."""
        return (self.x - self.size[0] * self.anchor[0], self.y - self.size[1] * self.anchor[1])

    def show(self, screen):
        """Shows the object on the screen."""
        if self.visible and self.object is not None:
            screen.blit(self.object, self.compute_pos())

    def clickable(self) -> bool:
        """Returns True if the object is clickable."""
        return self.onclick is not None

    def focusable(self) -> bool:
        """Returns True if the object can be focused."""
        return self.onfocus is not None or self.onblur is not None

    def clicked(self, relative_mouse_pos):
        if self.clickable():
            self.is_clicked = True
            if self.onclick.__code__.co_argcount >= 1:
                self.onclick(relative_mouse_pos)
            else:
                self.onclick()

    def get_cursor(self, relative_mouse_pos):
        """Returns the hover cursor used when the mouse is over this object. It should return a tuple with a cursor id."""
        if self.cursor_data is not None:
            return self.cursor_data
        elif self.clickable():
            return ("tri_left", pygame.cursors.tri_left)
        else:
            return (None, None)

    def detect_mouse(self, mouse_pos) -> bool:
        """Returns True if the mouse is over the object."""
        x, y = mouse_pos
        return self.rect is not None and self.rect.collidepoint(x, y)

    def keydown(self, event):
        if self.onkeydown is not None:
            if self.onkeydown.__code__.co_argcount >= 1:
                self.onkeydown(event)
            else:
                self.onkeydown()


class PygCdrScene():
    def __init__(self, window):
        self.elements: Dict[str, PygCdrObject] = {}
        self.focused_element: PygCdrObject = None
        self.groups = {}
        self.last_cursor = None
        self.window = window

    def add_element(self, name: str, element: PygCdrObject):
        self.elements[name] = element
        return element

    def remove_element(self, name: str):
        del self.elements[name]

    def __getitem__(self, key):
        return self.elements[key]

    def add_to_group(self, group, *elements):
        if group not in self.groups:
            self.groups[group] = []

        for element in elements:
            self.groups[group].append(element)

    def show_group(self, group):
        if group in self.groups:
            for name in self.groups[group]:
                self.elements[name].visible = True

    def hide_group(self, group):
        if group in self.groups:
            for name in self.groups[group]:
                self.elements[name].visible = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.clicked()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.released()
            elif event.type == pygame.MOUSEMOTION:
                self.hover()
            elif event.type == pygame.KEYDOWN:
                self.keydown(event)

        return False

    def keydown(self, event):
        if self.focused_element is not None:
            if event.key == pygame.K_ESCAPE:
                self.focused_element.focused = False
                if self.focused_element.onblur is not None:
                    self.focused_element.onblur()
                self.focused_element = None
            else:
                self.focused_element.keydown(event)

    def clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        for element in self.elements.values():
            detected = element.detect_mouse(mouse_pos)
            if element.focusable() and detected:
                if self.focused_element is not None and self.focused_element is not element:
                    self.focused_element.focused = False
                    if self.focused_element.onblur is not None:
                        self.focused_element.onblur()

                if not element.focused:
                    if element.onfocus is not None:
                        element.focused = True
                        element.onfocus()
                    self.focused_element = element

                break
            elif element.clickable() and detected:
                element.clicked((mouse_pos[0] - element.x, mouse_pos[1] - element.y))
                break

            if self.focused_element is not None:
                self.focused_element.focused = False
                if self.focused_element.onblur is not None:
                    self.focused_element.onblur()
                self.focused_element = None

    def show(self):
        self.window.fill((255, 255, 255))
        for element in self.elements.values():
            element.show(self.window)
        pygame.display.update()

    def hover(self):
        cursor_got = False
        mouse_pos = pygame.mouse.get_pos()
        for element in self.elements.values():
            if element.detect_mouse(mouse_pos):
                relative_mouse_pos = (mouse_pos[0] - element.x, mouse_pos[1] - element.y)

                cursor_got = True
                cursor_id, cursor = element.get_cursor(relative_mouse_pos)
                if cursor_id is not None and cursor_id is not self.last_cursor:
                    pygame.mouse.set_cursor(*cursor)
                    self.last_cursor = cursor_id

                if not element.is_hovered and element.onenter is not None:
                    element.onenter()
                element.is_hovered = True
                if element.onhover is not None:
                    if element.onhover.__code__.co_argcount >= 1:
                        element.onhover(relative_mouse_pos)
                    else:
                        element.onhover()
            else:
                if element.is_hovered and element.onleave is not None:
                    element.onleave()
                element.is_hovered = False

        if not cursor_got and self.last_cursor is not "arrow":
            pygame.mouse.set_cursor(*pygame.cursors.arrow)
            self.last_cursor = "arrow"

    def released(self):
        for element in self.elements.values():
            if element.is_clicked:
                element.is_clicked = False
                if element.onreleased is not None:
                    element.onreleased()


class PygCdrText(PygCdrObject):
    """Inspired by https://pythonprogramming.altervista.org/buttons-in-pygame/"""

    def __init__(self, text, font_size=14, bg_color="white", font_color="black", font_name="Arial", **kwargs):
        self.bg_color = bg_color
        self.font_color = font_color
        self.font = pygame.font.SysFont(font_name, font_size)
        self.given_size = "size" in kwargs

        super().__init__(**kwargs)
        self.render_text(text)

    def render_text(self, text):
        self.text_obj = self.font.render(text, True, pygame.Color(self.font_color))
        text_size = self.text_obj.get_size()
        tx, ty = 0, 0

        if self.given_size:
            tx = (self.size[0] - text_size[0]) // 2
            ty = (self.size[1] - text_size[1]) // 2
        else:
            self.size = text_size

        self.object = pygame.Surface(self.size, pygame.SRCALPHA)
        self.object.fill(self.bg_color)
        self.object.blit(self.text_obj, (tx, ty))


class PygCdrInputBox(PygCdrObject):
    def __init__(self, default_text="", bg_color="#dddddd", focused_color="#aaaaaa", font_color="black", font_name="Arial", font_size=14, max_length=None, onchange=None, oninput=None, **kwargs):
        self.text = default_text
        self.bg_color = bg_color
        self.focused_color = focused_color
        self.font_color = font_color
        self.font = pygame.font.SysFont(font_name, font_size)
        self.max_length = max_length

        self.onchange = onchange
        self.oninput = oninput

        super().__init__(**kwargs)

        self.onfocus = lambda: self.render_text()
        self.onblur = lambda: self.render_text()

        if self.size is None:
            self.update_size((200, 20))

        self.render_text()

    def render_text(self):
        self.text_obj = self.font.render(self.text, 1, pygame.Color(self.font_color))

        self.object = pygame.Surface(self.size, pygame.SRCALPHA)
        self.object.fill(self.focused_color if self.focused else self.bg_color)
        self.object.blit(self.text_obj, (0, 0))

    def keydown(self, event):
        super().keydown(event)

        if self.focused:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if self.max_length is None or len(self.text) < self.max_length:
                    self.text += event.unicode

            if self.onchange is not None:
                self.onchange(self.text)

            self.render_text()


class PygCdrSlider(PygCdrObject):
    def __init__(self, min_value, max_value, step, default_value, bg_color, line_color, handle_color, handle_radius=10, line_size=10, onchange=None, oninput=None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.current_value = default_value
        self.bg_color = bg_color
        self.line_color = line_color
        self.handle_color = handle_color
        self.handle_radius = handle_radius
        self.line_size = line_size

        self.onchange = onchange
        self.oninput = oninput
        self.original_onreleased = kwargs.get("onreleased", None)
        kwargs["onreleased"] = self.__onreleased
        self.original_onhover = kwargs.get("onhover", None)
        kwargs["onhover"] = self.__onhover
        self.original_onclick = kwargs.get("onclick", None)
        kwargs["onclick"] = self.__onclick

        super().__init__(**kwargs)

        if self.size is None:
            self.update_size((200, 20))

        half_size = self.size[1] // 2
        if handle_radius > half_size:
            handle_radius = half_size
        if line_size > half_size:
            line_size = half_size

        self.render_slider()

    def __onreleased(self):
        if self.original_onreleased is not None:
            self.original_onreleased()

        if self.oninput.__code__.co_argcount >= 1:
            self.oninput(self.current_value)
        else:
            self.oninput()

    def __onhover(self, relative_mouse_pos):
        if self.is_clicked:
            x = relative_mouse_pos[0] - self.click_dx - self.handle_radius
            new_value = self.min_value + x / (self.size[0] - self.handle_radius * 2) * (self.max_value - self.min_value)
            new_value = min(max(round(new_value / self.step) * self.step, self.min_value), self.max_value)

            if new_value != self.current_value:
                self.current_value = new_value
                self.render_slider()
                if self.onchange is not None:
                    if self.onchange.__code__.co_argcount >= 1:
                        self.onchange(self.current_value)
                    else:
                        self.onchange()

            self.render_slider()

        if self.original_onhover is not None:
            if self.original_onhover.__code__.co_argcount >= 1:
                self.original_onhover(relative_mouse_pos)
            else:
                self.original_onhover()

    def __onclick(self, relative_mouse_pos):
        self.click_dx = relative_mouse_pos[0] - self.__handle_pos()

        if self.original_onclick is not None:
            if self.original_onclick.__code__.co_argcount >= 1:
                self.original_onclick(relative_mouse_pos)
            else:
                self.original_onclick()

    def __handle_pos(self):
        return self.handle_radius + (self.current_value - self.min_value) / (self.max_value - self.min_value) * (self.size[0] - 2 * self.handle_radius)

    def __is_over_handle(self, relative_mouse_pos):
        mx, my = relative_mouse_pos
        handle_pos = self.__handle_pos()
        return handle_pos - self.handle_radius <= mx < handle_pos + self.handle_radius

    def get_cursor(self, relative_mouse_pos):
        if self.__is_over_handle(relative_mouse_pos):
            return ("tri_left", pygame.cursors.tri_left)
        else:
            return ("arrow", pygame.cursors.arrow)

    def render_slider(self):
        self.object = pygame.Surface(self.size)
        self.object.fill(self.bg_color)

        pygame.draw.rect(self.object, self.line_color, pygame.Rect(self.handle_radius, (self.size[1] - self.line_size) // 2, self.size[0] - self.handle_radius * 2, self.line_size))
        pygame.draw.circle(self.object, self.handle_color, (self.__handle_pos(), self.size[1] // 2), self.handle_radius)


class PygCdrSurface(PygCdrObject):
    """
    Represents a canvas on which graphics can be painted inside the `draw` callback.
    """

    def __init__(self, draw: Callable[[pygame.Surface], None], **kwargs):
        super().__init__(**kwargs)

        self.object = pygame.Surface(self.size, pygame.SRCALPHA)
        self.draw = draw

    def show(self, window):
        if self.draw is not None:
            self.draw(self.object)

        super().show(window)


class PygCdrCheckbox(PygCdrObject):
    def __init__(self, text, checked=False, font_name="Arial", font_size=15, fg_color=(0, 0, 0), bg_color=(255, 255, 255), onchange=None, **kwargs):
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.checked = checked
        self.fg_color = fg_color
        self.bg_color = bg_color

        self.onchange = onchange
        self.original_onclick = kwargs.get("onclick", None)
        kwargs["onclick"] = self.__onclick

        super().__init__(**kwargs)
        self.render_checkbox()

    def render_checkbox(self):
        self.object = pygame.Surface(self.size)
        self.object.fill(self.bg_color)

        box_size = self.size[1]
        pygame.draw.rect(self.object, self.fg_color, (0, 0, box_size, box_size))

        box_border = int(box_size * 0.15)
        pygame.draw.rect(self.object, self.bg_color, (box_border, box_border, box_size - box_border * 2, box_size - box_border * 2))

        if self.checked:
            inside_size = int(box_size * 0.6)
            pygame.draw.rect(self.object, self.fg_color, (box_border * 2, box_border * 2, inside_size, inside_size))

        PygCdrText(self.text, self.font_size, (0, 0, 0, 0), self.fg_color, self.font_name, pos=(int(box_size * 1.3), 0)).show(self.object)

    def __onclick(self, relative_mouse_pos):
        self.checked = not self.checked
        self.render_checkbox()

        if self.onchange is not None:
            self.onchange(self.checked)

        if self.original_onclick is not None:
            if self.original_onclick.__code__.co_argcount >= 1:
                self.original_onclick(relative_mouse_pos)
            else:
                self.original_onclick()

    def show(self, screen):
        super().show(screen)
