import time
import copy
import math

import pygame
from pygame import gfxdraw
from threading import Thread


class _InstanceControl:
    """
    Helper class to control null mode instances' closures when main instance quits
    """
    def __init__(self):
        self.instances = []

    def add(self, new_instance):
        self.instances.append(new_instance)

    def quit_all(self):
        for instance in self.instances:
            instance.quitted = True


_instance_handler = _InstanceControl()


class _RepeatTimer:
    """
    Helper class for a repeated timer
    """

    def __init__(self, deltatime: int, func):
        self.interval = deltatime / 1000
        self.func = func
        self.flag = False
        self.thread = Thread(target=self.repeat)

    def start(self):
        self.thread.start()

    def repeat(self):
        while True:
            if self.flag:
                return

            if self.func is None:
                return
            else:
                self.func()

            if self.interval > 0.005:
                time.sleep(self.interval)

    def quit(self):
        self.flag = True


class _SimulationData:
    """
    Helper class to hold simulation data
    """
    def __init__(self):
        self.draw_mode = {'TOP_LEFT': 0, 'CENTER': 1}
        self.transformations = {'ROT': 0, 'TRA': 1, 'SCL': 2}

        self.applied_transformations = []

        self.flag_has_rotation = False
        self.cumulative_rotation_angle = 0

        self.flag_has_scaling = False
        self.cumulative_scaling_factor = [1, 1]

        self.account_for_transformations = False

        self.current_rect_mode = self.draw_mode['TOP_LEFT']
        self.current_circle_mode = self.draw_mode['CENTER']

        self.current_stroke_color = (0, 0, 0)
        self.current_fill_color = (0, 0, 0)
        self.current_background_color = (125, 125, 125)
        self.current_stroke_weight = 1

        self.anti_aliasing = False

        self.fill_state = True
        self.stroke_state = True

        self.current_text_font = pygame.font.get_default_font()
        self.custom_font_object = None


class _ControlClass:
    """
    Helper class to interface with pygame controls
    """
    def __init__(self, main_instance):
        self.main_instance = main_instance

        self.quit = None
        self.key_down = None
        self.key_up = None
        self.mouse_motion = None
        self.mouse_button_up = None
        self.mouse_button_down = None
        self.mouse_wheel = None

    @staticmethod
    def run(func, data):
        if func is not None:
            func(data)

    def event_handler(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.main_instance.quit()
                return
            if event.type == pygame.KEYDOWN:
                self.run(self.key_down, event.__dict__)
            if event.type == pygame.KEYUP:
                self.run(self.key_up, event.__dict__)
            if event.type == pygame.MOUSEMOTION:
                self.run(self.mouse_motion, event.__dict__)
            if event.type == pygame.MOUSEBUTTONUP:
                self.run(self.mouse_button_up, event.__dict__)
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.run(self.mouse_button_down, event.__dict__)
            if event.type == pygame.MOUSEWHEEL:
                self.run(self.mouse_wheel, event.__dict__)


class EduDraw:
    def __init__(self, width: int, height: int, null_mode: bool = False):
        global _instance_handler
        self.width = width
        self.height = height

        self.timeloop = None
        self.deltatime = 1

        self.null_mode = null_mode

        if null_mode:
            _instance_handler.add(self)

        self.screen: pygame.surface.Surface | None = None

        self.setup = None
        self.draw = None

        self.quitted = False
        self.reset_after_loop = True
        self.frame_count = 0

        self.original_font_instance = None

        self.data = _SimulationData()
        # Data stack used for temporary states
        self.data_stack = []

        self.controls = _ControlClass(self)

    def _reset_variables(self):
        """
        Resets all variables to their default state
        """

        self.data = _SimulationData()
        self.data_stack = []
        self.data.custom_font_object = self.original_font_instance

    def _proto_setup(self):
        self.setup()

    def timer_tick(self):
        """
        Function called every tick of the timer. Serves as the backbone of the draw() function
        """
        if self.quitted:
            self.timeloop.quit()
            return

        self.frame_count += 1

        self.draw()

        if not self.null_mode:
            pygame.display.update()

        if self.reset_after_loop:
            self._reset_variables()

    def _proto_draw(self):
        """
        Sets up environment for drawing
        """
        self.timeloop = _RepeatTimer(self.deltatime, self.timer_tick)
        self.timeloop.start()

        if self.null_mode:
            return

        pygame.display.flip()
        while not self.quitted:
            self.controls.event_handler(pygame.event.get())

    def start(self, setup, draw, window_title: str):
        """
        Starts the simulation

        :param setup: setup() function to be used
        :param draw: draw() function to be used
        :param window_title: The title to give the drawing window
        """
        self.setup = setup
        self.draw = draw

        if not pygame.font.get_init():
            pygame.font.init()

        data = self._get_data_object()
        self.original_font_instance = pygame.font.SysFont(data.current_text_font, 15)
        data.custom_font_object = self.original_font_instance

        if self.null_mode:
            self.screen = pygame.surface.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(window_title)

        self._proto_setup()
        self._proto_draw()

    def _get_data_object(self) -> _SimulationData:
        """
        Retrieves the correct simulation data class to operate upon
        :return: An instace of _SimulationData
        """
        if not self.data_stack:
            return self.data
        else:
            return self.data_stack[-1]

    def _get_rect_box(self, x: int, y: int, w: int, h: int, inverted: bool = False) -> tuple:
        """
        Gets the correct place for the (x,y) coordinates of the top-left corner of rectangle-based geometry

        :param x: The original x coordinate of the top-left coordinate
        :param y: The original y coordinate of the top-left coordinate
        :param w: The width of the rectangle
        :param h: The height of the rectangle
        :param inverted: Whether the box needs to be inverted (for certain cases of rotation)
        :return: The (x,y) tuple of the new positions
        """

        data = self._get_data_object()

        if data.current_rect_mode == data.draw_mode['TOP_LEFT']:
            if inverted:
                return x + w / 2, y + h / 2
            return x, y
        else:
            if inverted:
                return x, y
            return x - w / 2, y - h / 2

    def _get_circle_box(self, x: int, y: int, w: int, h: int, inverted: bool = False) -> tuple:
        """
        Gets the correct place for the (x,y) coordinates of the top-left corner of circle-based geometry

        :param x: The original x coordinate of the top-left coordinate
        :param y: The original y coordinate of the top-left coordinate
        :param w: The width of the rectangle containing the circle (2 * radius on circles)
        :param h: The height of the rectangle containing the circle
        :param inverted: Whether the box needs to be inverted (for certain cases of rotation)
        :return: The (x,y) tuple of the new positions
        """

        data = self._get_data_object()

        if data.current_circle_mode == data.draw_mode['TOP_LEFT']:
            if inverted:
                return x + w / 2, y + h / 2
            return x, y
        else:
            if inverted:
                return x, y
            return x - w / 2, y - h / 2

    def _get_stroke_fill_and_weight(self) -> tuple:
        """
        Gets the correct stroke_color and fill_color to be used in current state conditions

        :return: A tuple containing (stroke_color, fill_color), which both are tuples of (R, G, B) values
        """

        data = self._get_data_object()

        stroke_color = data.current_stroke_color
        fill_color = data.current_fill_color
        stroke_weight = data.current_stroke_weight

        if not data.stroke_state:
            stroke_color = None
        if not data.fill_state:
            fill_color = None

        return stroke_color, fill_color, stroke_weight

    def _apply_transformations_coords(self, x: int, y: int, no_rotation: bool = False) -> tuple:
        """
        Applies all transformations to coordinates in order defined by usage

        :param x: X value of coordinates
        :param y: Y value of coordinates
        :param no_rotation: Whether rotation should be skipped
        :return: A tuple containing the (X, Y) values of the new coordinate location
        """
        final_x = x
        final_y = y

        data = self._get_data_object()

        scale_tf = data.transformations['SCL']
        translate_tf = data.transformations['TRA']
        rotate_tf = data.transformations['ROT']

        for transformation in data.applied_transformations:
            if transformation[0] == scale_tf:
                final_x *= transformation[1][0]
                final_y *= transformation[1][1]

            if transformation[0] == translate_tf:
                final_x += transformation[1][0]
                final_y += transformation[1][1]

            if transformation[0] == rotate_tf and not no_rotation:
                angle_sin = math.sin(math.radians(transformation[1]))
                angle_cos = math.cos(math.radians(transformation[1]))
                x = final_x * angle_cos - final_y * angle_sin
                y = final_x * angle_sin + final_y * angle_cos
                final_x = x
                final_y = y

        return final_x, final_y

    def _apply_transformations_length(self, width: int, height: int) -> tuple:
        """
        Applies all transformations to a set of lengths in order defined by usage

        :param width: The width to be manipulated
        :param height: The height to be manipulated
        :return: A tuple with the resulting width and height after transformations
        """
        final_width = width
        final_height = height

        data = self._get_data_object()

        scale_tf = data.transformations['SCL']

        for transformation in data.applied_transformations:
            # Sizes are only affected by scaling
            if transformation[0] == scale_tf:
                final_width *= transformation[1][0]
                final_height *= transformation[1][1]

        return final_width, final_height

    def _undo_transformations_coords(self, x: int, y: int) -> tuple:
        """
        Undoes all transformations of a coordinate to retrieve it's original place.
        Used for mouse_pos()

        :param x: The x coordinate
        :param y: The y coordinate
        :return: A tuple with the (x, y) original coordinates
        """
        final_x = x
        final_y = y

        data = self._get_data_object()

        scale_tf = data.transformations['SCL']
        translate_tf = data.transformations['TRA']
        rotate_tf = data.transformations['ROT']

        for transformation in reversed(data.applied_transformations):
            if transformation[0] == scale_tf:
                final_x /= transformation[1][0]
                final_y /= transformation[1][1]

            if transformation[0] == translate_tf:
                final_x -= transformation[1][0]
                final_y -= transformation[1][1]

            if transformation[0] == rotate_tf:
                angle_sin = math.sin(math.radians(transformation[1]))
                angle_cos = math.cos(math.radians(transformation[1]))
                x = final_x * angle_cos + final_y * angle_sin
                y = -final_x * angle_sin + final_y * angle_cos
                final_x = x
                final_y = y

        return final_x, final_y

    # State methods --------------------------------------------------------------------------------------

    def rect_mode(self, mode: str):
        """
        Changes the way in which rectangles will be drawn onto the screen

        :param mode: Mode may be 'TOP_LEFT' or 'CENTER'
        """

        data = self._get_data_object()
        new_mode = data.draw_mode[mode]
        data.current_rect_mode = new_mode

    def circle_mode(self, mode: str):
        """
        Changes the way in which circles will be drawn onto the screen

        :param mode: Mode may be 'TOP_LEFT' or 'CENTER'
        """
        data = self._get_data_object()
        new_mode = data.draw_mode[mode]
        data.current_circle_mode = new_mode

    def fill(self, color: tuple):
        """
        Changes the color to which shapes will be filled with

        :param color: A tuple containing the (R, G, B) values to fill subsequent shapes
        """
        data = self._get_data_object()
        data.fill_state = True
        data.current_fill_color = color

    def no_fill(self):
        """
        Specifies that subsequent shapes should not be filled in
        """

        data = self._get_data_object()
        data.fill_state = False

    def stroke(self, color: tuple):
        """
        Specifies the color to be used for the outlines of shapes

        :param color: The color to be used, in an (R, G, B) tuple
        """
        data = self._get_data_object()
        data.stroke_state = True
        data.current_stroke_color = color

    def no_stroke(self):
        """
        Specifies that subsequent shapes should not have their outlines drawn
        """

        data = self._get_data_object()
        data.stroke_state = False

    def stroke_weight(self, new_weight: int):
        """
        Changes the thickness of the outlines to be drawn

        :param new_weight: The size (in px) of the lines
        """

        data = self._get_data_object()
        data.current_stroke_weight = new_weight

    def push(self):
        """
        Starts temporary state
        """

        previous_data = self._get_data_object()

        new_data = copy.copy(previous_data)

        # To avoid referencing
        new_data.applied_transformations = [i for i in previous_data.applied_transformations]

        self.data_stack.append(new_data)

    def pop(self):
        """
        Leaves temporary state
        """
        if len(self.data_stack) != 0:
            self.data_stack.pop()

    def mouse_pos(self) -> tuple:
        """
        Retrieves the current mouse position relative to the top-left corner of the window

        :return: A (x, y) tuple with the positions
        """

        data = self._get_data_object()

        if self.null_mode:
            return 0, 0

        original_pos = pygame.mouse.get_pos()

        if not data.account_for_transformations:
            return original_pos

        final_pos = self._undo_transformations_coords(original_pos[0], original_pos[1])
        return int(final_pos[0]), int(final_pos[1])

    def rotate(self, angle: int):
        """
        Rotates the drawing clockwise by the defined amount of degrees

        :param angle: The angle (in degrees) to rotate the drawing
        """
        data = self._get_data_object()
        data.flag_has_rotation = True
        data.cumulative_rotation_angle += angle
        data.applied_transformations.append((data.transformations['ROT'], angle))

    def scale(self, scale_x: float, scale_y: float):
        """
        Scales the drawing's axis by the desired multipliers

        :param scale_x: The rate to scale the x axis by
        :param scale_y: The rate to scale the y axis by
        """
        if scale_x == 0 or scale_y == 0:
            return

        data = self._get_data_object()
        data.flag_has_scaling = True
        data.cumulative_scaling_factor[0] *= scale_x
        data.cumulative_scaling_factor[1] *= scale_y
        data.applied_transformations.append((data.transformations['SCL'], (scale_x, scale_y)))

    def translate(self, translate_x: int, translate_y: int):
        """
        Changes the origin of the plane of drawing

        :param translate_x: The amount to translate in the x axis
        :param translate_y: The amount to translate in the y axis
        """
        data = self._get_data_object()
        data.applied_transformations.append((data.transformations['TRA'], (translate_x, translate_y)))

    def reset_transformations(self):
        """
        Resets all transformations
        """
        data = self._get_data_object()
        data.applied_transformations = []
        data.flag_has_rotation = False
        data.flag_has_scaling = False
        data.cumulative_rotation_angle = 0
        data.cumulative_scaling_factor = [1, 1]

    def _remove_transformation(self, transformation: int):
        """
        Removes a desired transformation type from the set of applied transformations

        :param transformation: The transformation type to remove
        """
        data = self._get_data_object()
        data.applied_transformations = [tf for tf in data.applied_transformations if tf[0] != transformation]

    def reset_scaling(self):
        """
        Resets all scaling operations done
        """
        data = self._get_data_object()
        scaling = data.transformations['SCL']
        self._remove_transformation(scaling)
        data.cumulative_scaling_factor = [1, 1]
        data.flag_has_scaling = False

    def reset_translation(self):
        """
        Resets all translation operations done
        """
        data = self._get_data_object()
        translation = data.transformations['TRA']
        self._remove_transformation(translation)

    def reset_rotation(self):
        """
        Resets all rotation operations done
        """
        data = self._get_data_object()
        rotation = data.transformations['ROT']
        self._remove_transformation(rotation)
        data.flag_has_rotation = False
        data.cumulative_rotation_angle = 0

    def set_account_for_transformations(self, state: bool):
        """
        Makes mouse_pos() take into account the transformations and give the original location instead
        :param state: The state of whether it should be taken into account or not
        """
        data = self._get_data_object()
        data.account_for_transformations = state

    def set_controls(self, key_down=None, key_up=None, mouse_motion=None, mouse_button_up=None,
                     mouse_button_down=None, mouse_wheel=None):
        """
        Sets functions to be ran on each specific event. None means that nothing will occur on those events.
        Each function must have a parameter to receive a dictionary containing the data related to that event (such
        as which key was pressed, where the mouse is, etc.)

        :param key_down: The function to be ran when a key is pressed down
        :param key_up: The function to be ran when a key is released
        :param mouse_motion: The function to be ran when the mouse is moved
        :param mouse_button_up: The function to be ran when a mouse button is released
        :param mouse_button_down: The function to be ran when a mouse button is pressed
        :param mouse_wheel: The function to be ran when the mouse wheel is scrolled
        """
        self.controls.key_down = key_down
        self.controls.key_up = key_up
        self.controls.mouse_motion = mouse_motion
        self.controls.mouse_button_up = mouse_button_up
        self.controls.mouse_button_down = mouse_button_down
        self.controls.mouse_wheel = mouse_wheel

    def toggle_antialiasing(self):
        """
        Toggles antialiasing for drawing shapes. Antialiasing is off by default.
        """
        data = self._get_data_object()

        data.anti_aliasing = not data.anti_aliasing

    # Draw methods --------------------------------------------------------------------------------------

    def point(self, x: int, y: int):
        """
        Draws a point onto the desired x,y coordinates with the current stroke color

        :param x: The x coordinate to draw the point
        :param y: The y coordinate to draw the point
        """

        data = self._get_data_object()

        if not data.stroke_state:
            return

        stroke_color = data.current_stroke_color

        x, y = self._apply_transformations_coords(x, y)

        pygame.draw.circle(self.screen, stroke_color, (x, y), 1, 0)

    def text(self, string: str, x: int, y: int):
        """
        Displays a string of text onto the screen

        :param string: The text to be written
        :param x: The x coordinate of the text (if rect_mode is center, this will be the center of the rectangle
        containing the text, otherwise, it'll be the top-left corner of said rectangle)
        :param y: The y coordinate of the text
        """
        if string == '':
            return

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        data = self._get_data_object()

        font = data.custom_font_object

        new_image = font.render(string, data.anti_aliasing, fill_color)

        self.image(new_image, x, y)

    def font(self, new_font: str, font_size: int = 12, bold=False, italic=False, underline=False):
        """
        Changes the font to be used when writing text.
        When the font is changed, all text will have it's font size, so the parameter for size in the text() method
        is not used. Note: This is a costly method, if possible, it's recommended to use it once in setup() instead
        of every frame in draw(). If you need to change font mid-drawing, it's recommended to use font_from_instance()
        instead.

        :param new_font: The name of the new font to be used
        :param font_size: The size of the font to be used
        :param bold: Whether the font should be bold or not
        :param italic: Whether the font should be italic or not
        :param underline: Whether the font should have an underline or not
        """
        font_path = pygame.font.match_font(new_font)
        font_object = pygame.font.Font(font_path, font_size)

        font_object.set_bold(bold)
        font_object.set_italic(italic)
        font_object.set_underline(underline)

        data = self._get_data_object()
        data.custom_font_object = font_object

    def change_default_font(self, new_font: str, font_size: int = 12, bold=False, italic=False, underline=False):
        """
        Changes the default font to be used when writing text. If you want to change the font only once
        in your drawing, it's recommended that you use this method in setup() instead of using font() in
        draw(), this is way better for performance.

        :param new_font: The name of the new font to be used
        :param font_size: The size of the font to be used
        :param bold: Whether the font should be bold or not
        :param italic: Whether the font should be italic or not
        :param underline: Whether the font should have an underline or not
        """
        font_path = pygame.font.match_font(new_font)
        font_object = pygame.font.Font(font_path, font_size)

        font_object.set_bold(bold)
        font_object.set_italic(italic)
        font_object.set_underline(underline)

        self.original_font_instance = font_object
        data = self._get_data_object()
        data.custom_font_object = font_object

    def font_from_instance(self, new_font: pygame.font.Font):
        """
        Sets the font to be used when writing text to a premade instance of a pygame.font.Font object.
        It is recommended that, if you need to change fonts mid-drawing, you preload those fonts once before in your
        program and use this method to change them, instead of using the normal font() method, since it's costly to
        keep creating new instances every frame and the effect this has on performance is noticeable.

        :param new_font: A pygame font instance to be used
        """
        data = self._get_data_object()
        data.custom_font_object = new_font

    def reset_font(self):
        """
        Resets the font used to the default font
        """
        data = self._get_data_object()
        data.custom_font_object = None

    def background(self, color: tuple):
        """
        Draws a background over current image. NOTE: Should be called before other drawings so they don't get
        erased by the background.

        :param color: The color to draw the background (a (R, G, B) tuple)

        Note: Fast mode simply draws a rectangle
        that fills the entire image, disabling it will cause EduDraw.clear() to be called which is more costly
        in terms of processing.
        """

        data = self._get_data_object()
        data.current_background_color = color

        pygame.draw.rect(self.screen, color, (0, 0, self.width, self.height))

    def circle(self, x: int, y: int, radius: int):
        """
        Draws a circle on the screen. If circle_mode is center, the coordinates will be the center of the circle,
        otherwise, will be the top-left coordinate of a rectangle containing the circle.

        :param x: The x coordinate to draw the circle
        :param y: The y coordinate to draw the circle
        :param radius: The radius of the circle
        """

        self.ellipse(x, y, radius * 2, radius * 2)

    def ellipse(self, x: int, y: int, width: int, height: int):
        """
        Draws an ellipse on the screen

        :param x: The x coordinate to draw the ellipse (if circle_mode is center, this will be the center of the
        ellipse, otherwise, will be the top-left coordinate of a rectangle containing the ellipse)
        :param y: The y coordinate to draw the ellipse
        :param width: The width of the x-axis of the ellipse
        :param height: The height of the y-axis of the ellipse
        """

        data = self._get_data_object()

        if data.cumulative_rotation_angle == 0:
            has_rotation = False
        else:
            has_rotation = True

        pos_x, pos_y = self._get_circle_box(x, y, width, height, has_rotation)
        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y)
        pos_x, pos_y = int(pos_x), int(pos_y)

        width, height = self._apply_transformations_length(width, height)
        width, height = int(width), int(height)

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        if not has_rotation or width == height:
            if data.fill_state:
                if data.anti_aliasing:
                    gfxdraw.filled_ellipse(self.screen, pos_x + width // 2, pos_y + height // 2, width // 2,
                                           height // 2, fill_color)
                else:
                    pygame.draw.ellipse(self.screen, fill_color, (pos_x, pos_y, width, height), 0)

            if data.stroke_state:
                if data.anti_aliasing:
                    gfxdraw.aaellipse(self.screen, pos_x + width // 2, pos_y + height // 2, width // 2,
                                      height // 2, stroke_color)
                else:
                    pygame.draw.ellipse(self.screen, stroke_color, (pos_x, pos_y, width, height),
                                        data.current_stroke_weight)
            return

        new_surface = pygame.surface.Surface((width + 1, height + 1), pygame.SRCALPHA)

        if data.anti_aliasing:
            if data.stroke_state:
                gfxdraw.aaellipse(new_surface, width//2, height//2, width//2, height//2, stroke_color)
            if data.fill_state:
                gfxdraw.filled_ellipse(new_surface, width//2, height//2, width//2, height//2, fill_color)
        else:
            if data.fill_state:
                pygame.draw.ellipse(new_surface, fill_color, (0, 0, width, height), 0)

            if data.stroke_state:
                pygame.draw.ellipse(new_surface, stroke_color, (0, 0, width, height),
                                    data.current_stroke_weight)

        new_surface = pygame.transform.rotate(new_surface, -data.cumulative_rotation_angle)

        new_width, new_height = new_surface.get_size()
        self.screen.blit(new_surface, (int(pos_x - new_width / 2), int(pos_y - new_height / 2)))

    def line(self, x1: int, y1: int, x2: int, y2: int):
        """
        Draws a line between two points

        :param x1: The x coordinate of the first point
        :param y1: The y coordinate of the first point
        :param x2: The x coordinate of the second point
        :param y2: The y coordinate of the second point
        """
        x1, y1 = self._apply_transformations_coords(x1, y1)
        x2, y2 = self._apply_transformations_coords(x2, y2)
        x1, y1 = int(x1), int(y1)
        x2, y2 = int(x2), int(y2)

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        data = self._get_data_object()

        if data.anti_aliasing:
            gfxdraw.line(self.screen, x1, y1, x2, y2, stroke_color)
        else:
            pygame.draw.line(self.screen, stroke_color, (x1, y1), (x2, y2), stroke_weight)

    def rect(self, x: int, y: int, width: int, height: int):
        """
        Draws a rectangle onto the screen

        :param x: The x coordinate to draw the rectangle (if rect_mode is center, this will be the center of the
        rectangle, otherwise will be the top-left corner of the rectangle)
        :param y: The y coordinate to draw the rectangle
        :param width: The width of the rectangle
        :param height: The height of the rectangle
        """
        pos_x, pos_y = self._get_rect_box(x, y, width, height)
        data = self._get_data_object()

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        if data.cumulative_rotation_angle != 0:
            pts = [(pos_x, pos_y), (pos_x + width, pos_y), (pos_x + width, pos_y + height), (pos_x, pos_y + height)]

            self.polygon(pts)
            return

        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y, True)
        width, height = self._apply_transformations_length(width, height)

        if data.fill_state:
            if data.anti_aliasing:
                gfxdraw.box(self.screen, (pos_x, pos_y, width, height), fill_color)
            else:
                pygame.draw.rect(self.screen, fill_color, (pos_x, pos_y, width, height), 0)

        if data.stroke_state:
            if data.anti_aliasing:
                gfxdraw.rectangle(self.screen, (pos_x, pos_y, width, height), stroke_color)
            else:
                pygame.draw.rect(self.screen, stroke_color, (pos_x, pos_y, width, height), stroke_weight)

    def square(self, x: int, y: int, side_size: int):
        """
        Draws a rectangle onto the screen

        :param x: The x coordinate to draw the square (if rect_mode is center, this will be the center of the
        square, otherwise will be the top-left corner of the square)
        :param y: The y coordinate to draw the square
        :param side_size: The size of the sides of the square
        """
        self.rect(x, y, side_size, side_size)

    def triangle(self, x1: int, y1: int, x2: int, y2: int, x3: int, y3: int):
        """
        Draws a triangle onto the screen based on the three points of it's tips

        :param x1: The x coordinate of the first point
        :param y1: The y coordinate of the first point
        :param x2: The x coordinate of the second point
        :param y2: The y coordinate of the second point
        :param x3: The x coordinate of the third point
        :param y3: The y coordinate of the third point
        """
        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        x1, y1 = self._apply_transformations_coords(x1, y1)
        x2, y2 = self._apply_transformations_coords(x2, y2)
        x3, y3 = self._apply_transformations_coords(x3, y3)

        data = self._get_data_object()

        if data.fill_state:
            if data.anti_aliasing:
                gfxdraw.filled_trigon(self.screen, x1, y1, x2, y2, x3, y3, fill_color)
            else:
                pygame.draw.polygon(self.screen, fill_color, ((x1, y1), (x2, y2), (x3, y3)), 0)

        if data.stroke_state:
            if data.anti_aliasing:
                gfxdraw.aatrigon(self.screen, x1, y1, x2, y2, x3, y3, stroke_color)
            else:
                pygame.draw.polygon(self.screen, stroke_color, ((x1, y1), (x2, y2), (x3, y3)), stroke_weight)

    def polygon(self, points: list | tuple):
        """
        Draws a polygon onto the screen

        :param points: A list containing the tuples of the coordinates of the points to be connected, as in [(x1, y1),
        (x2, y2), (x3, y3), ..., (xn, yn)]
        """
        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        data = self._get_data_object()

        points = [self._apply_transformations_coords(x[0], x[1]) for x in points]

        if data.fill_state:
            if data.anti_aliasing:
                gfxdraw.filled_polygon(self.screen, points, fill_color)
            else:
                pygame.draw.polygon(self.screen, fill_color, points, 0)

        if data.stroke_state:
            if data.anti_aliasing:
                gfxdraw.aapolygon(self.screen, points, stroke_color)
            else:
                pygame.draw.polygon(self.screen, stroke_color, points, stroke_weight)

    def image(self, img: pygame.surface.Surface, x: int, y: int, width: int = None, height: int = None,
              force_transparency: bool = False):
        """
        Displays an image onto the screen on the (x,y) position.
        If specified a width or height, the image will be resized to those sizes, otherwise, the image will be drawn
        to it's original size.

        :param img: The Image to be displayed
        :param x: The x coordinate of the top-left corner of the image
        :param y: The y coordinate of the top-left corner of the image
        :param width: (Optional) The width to resize the image
        :param height: (Optional) The height to resize the image
        :param force_transparency: (Optional) Whether or not to force transparency on non-rgba images.
        """

        size = img.get_size()

        if force_transparency:
            intermediary_surface = pygame.surface.Surface(size, flags=pygame.SRCALPHA)
            intermediary_surface.blit(img, (0, 0))
            img = intermediary_surface

        data = self._get_data_object()

        if width is None:
            width = size[0]

        if height is None:
            height = size[1]

        target_width, target_height = self._apply_transformations_length(width, height)

        if target_width == 0 or target_height == 0:
            return

        if target_width < 0 or target_height < 0:
            raise ValueError

        img = pygame.transform.scale(img, (target_width, target_height))
        img = pygame.transform.rotate(img, -data.cumulative_rotation_angle)

        has_rotation = data.cumulative_rotation_angle != 0

        if not has_rotation:
            invert = False
        else:
            invert = True

        x, y = self._get_rect_box(x, y, width, height, invert)
        x, y = self._apply_transformations_coords(x, y)

        real_w, real_h = img.get_size()

        if not has_rotation:
            box = (int(x), int(y), real_w, real_h)
        else:
            box = (int(x - real_w//2), int(y - real_h//2), real_w, real_h)

        self.screen.blit(img, box)

    def frame_rate(self, fps: int):
        """
        Sets the desired frame rate. Note that EduDraw using python is slower than it's C# counterpart.
        :param fps: The desired FPS rate.
        """
        self.deltatime = 1000 / fps

    def save(self, filename: str):
        """
        Saves a picture of the current frame

        :param filename: The name to give the resulting file (Ex: 'MyPhoto.png')
        """
        if filename == '':
            filename = f'{self.frame_count}.png'
        # self.current_frame.save(filename)
        pygame.image.save(self.screen, filename)

    def quit(self):
        global _instance_handler
        """
        Stops the simulation
        """

        self.quitted = True

        if not self.null_mode:
            _instance_handler.quit_all()
