import gc
import math
import time
import copy

import pygame
import PIL.Image
from PIL import ImageDraw, ImageFont, ImageOps
from threading import Thread


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
        gc.collect()


class _SimulationData:
    """
    Helper class to hold simulation data
    """
    def __init__(self):
        # These work as enums
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

        self.fill_state = True
        self.stroke_state = True

        self.current_text_font = PIL.ImageFont.load_default()


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
                self.main_instance.quitted = True
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
        self.width = width
        self.height = height
        self.current_frame = PIL.Image.new('RGBA', (width, height))
        self.current_graphics = PIL.ImageDraw.Draw(self.current_frame, 'RGBA')
        self.null_mode = null_mode
        self.timeloop = None
        self.deltatime = 1

        self.screen = None

        self.setup = None
        self.draw = None

        self.quitted = False
        self.reset_after_loop = True
        self.frame_count = 0

        self.data = _SimulationData()
        # Data stack used for temporary states
        self.data_stack = []

        self.controls = _ControlClass(self)

    def _reset_variables(self):
        """
        Resets all variables to their default state
        """

        self.data = _SimulationData()
        gc.collect()

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
            img = pygame.image.fromstring(self.current_frame.tobytes(), self.current_frame.size, 'RGBA')
            rectangle = img.get_rect()
            rectangle.center = self.width // 2, self.height // 2
            self.screen.blit(img, rectangle)
            pygame.display.update()

        gc.collect()

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
            # for event in pygame.event.get():
            #    if event.type == pygame.QUIT:
            #        self.quitted = True

    def start(self, setup, draw, window_title: str):
        """
        Starts the simulation

        :param setup: setup() function to be used
        :param draw: draw() function to be used
        :param window_title: The title to give the drawing window
        """
        self.setup = setup
        self.draw = draw
        if not self.null_mode:
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

    def change_font(self, font: PIL.ImageFont):
        """
        Changes the font to be used in texts

        :param font: The new font to be used
        """

        data = self._get_data_object()
        data.current_text_font = font

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
        gc.collect()

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

        self.current_graphics.point([(x, y)], stroke_color)

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

        font = data.current_text_font

        size_x, size_y = self.current_graphics.textlength(string, font), \
                         self.current_graphics.textlength(string, font, direction='ttb')

        # Text written normally when not stretched or rotated
        if data.cumulative_rotation_angle == 0 and data.cumulative_scaling_factor == [1, 1]:
            x, y = self._apply_transformations_coords(x, y)

            new_x, new_y = self._get_rect_box(x, y, size_x, size_y)

            self.current_graphics.text((new_x, new_y), string, stroke_color, font)
            return

        new_image = PIL.Image.new('RGBA', (int(size_x) + 1, int(size_y) + 1), color=(0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(new_image)

        draw.text((0, 0), string, stroke_color, font)

        self.image(new_image, x, y)

    def clear(self):
        """
        Clears the entire image and replaces it with a new empty one

        NOTE: This method is costly in terms of processing
        """

        data = self._get_data_object()
        bgc = data.current_background_color

        self.current_frame = PIL.Image.new('RGBA', (self.width, self.height), color=bgc)
        self.current_graphics = PIL.ImageDraw.Draw(self.current_frame)
        gc.collect()

    def background(self, color: tuple, fast_mode: bool = True):
        """
        Draws a background over current image. NOTE: Should be called before other drawings so they don't get
        erased by the background.

        :param color: The color to draw the background (a (R, G, B) tuple)
        :param fast_mode: Whether fast mode should be used. Default: True.

        Note: Fast mode simply draws a rectangle
        that fills the entire image, disabling it will cause EduDraw.clear() to be called which is more costly
        in terms of processing.
        """

        data = self._get_data_object()
        data.current_background_color = color

        if fast_mode:
            self.current_graphics.rectangle((0, 0, self.width, self.height), color, None, 0)
        else:
            self.clear()

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
        width, height = self._apply_transformations_length(width, height)
        data = self._get_data_object()

        pos_x, pos_y = self._get_circle_box(x, y, width, height, True)
        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y)

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        # Circles and 'no rotation' ellipses don't need additional processing
        if width == height or data.cumulative_rotation_angle == 0:
            self.current_graphics.ellipse([(pos_x, pos_y), (pos_x + width, pos_y + height)], fill_color, stroke_color,
                                          stroke_weight)
            return

        final_color = (0, 0, 0, 0)

        new_image = PIL.Image.new('RGBA', (int(width) + 1, int(height) + 1), color=final_color)
        draw = PIL.ImageDraw.Draw(new_image)

        draw.ellipse([(0, 0), (width, height)], fill_color, stroke_color, stroke_weight)
        new_image = new_image.rotate(-data.cumulative_rotation_angle, expand=True)

        new_width, new_height = new_image.size

        self.current_frame.paste(new_image, (int(pos_x - new_width/2), int(pos_y - new_height/2)), new_image)

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

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        self.current_graphics.line([(x1, y1), (x2, y2)], stroke_color, stroke_weight)

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

            # TODO: See if alternative method (used in ellipse) is faster

            pts = [(pos_x, pos_y), (pos_x + width, pos_y), (pos_x + width, pos_y + height), (pos_x, pos_y + height)]

            self.polygon(pts)

        else:
            pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y, True)
            width, height = self._apply_transformations_length(width, height)

            self.current_graphics.rectangle((pos_x, pos_y, pos_x + width, pos_y + height), fill_color, stroke_color,
                                            stroke_weight)

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

        self.current_graphics.polygon((x1, y1, x2, y2, x3, y3), fill_color, stroke_color, stroke_weight)

    def polygon(self, points: list):
        """
        Draws a polygon onto the screen

        :param points: A list containing the tuples of the coordinates of the points to be connected, as in [(x1, y1),
        (x2, y2), (x3, y3), ..., (xn, yn)]
        """
        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        points = [self._apply_transformations_coords(x[0], x[1]) for x in points]

        self.current_graphics.polygon(points, fill_color, stroke_color, stroke_weight)

    def image(self, img: PIL.Image, x: int, y: int, x2: int = None, y2: int = None):
        """
        Displays an image onto the screen with it's top-left corner on the (x,y) position.
        If specified a (x2, y2) pair, the image will be resized to fit onto the rectangle that those coordinates define,
        otherwise, the image will be drawn to it's original size.
        Note: This is a very costly method

        :param img: The Image to be displayed
        :param x: The x coordinate of the top-left corner of the image
        :param y: The y coordinate of the top-left corner of the image
        :param x2: (Optional) The x coordinate of the bottom-right corner of the image
        :param y2: (Optional) The y coordinate of the bottom-right corner of the image
        """

        data = self._get_data_object()

        temp_draw_mode = data.current_rect_mode

        has_rotation = not data.cumulative_rotation_angle == 0

        width, height = img.size

        if x2 is None or y2 is None:
            target_width, target_height = self._apply_transformations_length(width, height)
        else:
            data.current_rect_mode = data.draw_mode['TOP_LEFT']
            target_width = x2 - x
            target_height = y2 - y

            if y2 < y:
                y, y2 = y2, y

            if x2 < x:
                x, x2 = x2, x

            target_width, target_height = self._apply_transformations_length(target_width, target_height)

        if target_width == 0 or target_height == 0:
            return

        if target_width < 0:
            target_width *= -1
            # x -= target_width
            img = ImageOps.mirror(img)

        if target_height < 0:
            target_height *= -1
            # y -= target_height
            img = ImageOps.flip(img)

        target_width = int(target_width)
        target_height = int(target_height)

        img = img.resize((target_width, target_height))
        img = img.rotate(-data.cumulative_rotation_angle, expand=True)

        if not has_rotation:
            invert = False
        else:
            invert = True

        x, y = self._get_rect_box(x, y, width, height, invert)
        x, y = self._apply_transformations_coords(x, y)

        real_w, real_h = img.size

        if not has_rotation:
            box = (int(x), int(y))
        else:
            box = (int(x - real_w//2), int(y - real_h//2))

        self.current_frame.paste(img, box, img)

        data.current_rect_mode = temp_draw_mode

    def image_sized(self, img: PIL.Image, x: int, y: int, width: int = None, height: int = None):
        """
        Displays an image onto the screen on the (x,y) position.
        If specified a width or height, the image will be resized to those sizes, otherwise, the image will be drawn
        to it's original size.

        :param img: The Image to be displayed
        :param x: The x coordinate of the top-left corner of the image
        :param y: The y coordinate of the top-left corner of the image
        :param width: (Optional) The width to resize the image
        :param height: (Optional) The height to resize the image
        """

        data = self._get_data_object()

        size = img.size

        if width is None:
            width = size[0]

        if height is None:
            height = size[1]

        target_width, target_height = self._apply_transformations_length(width, height)

        if target_width == 0 or target_height == 0:
            return

        if target_width < 0:
            target_width *= -1
            # x -= target_width
            img = ImageOps.mirror(img)

        if target_height < 0:
            target_height *= -1
            # y -= target_height
            img = ImageOps.flip(img)

        img = img.resize((target_width, target_height))
        img = img.rotate(-data.cumulative_rotation_angle, expand=True)

        has_rotation = data.cumulative_rotation_angle != 0

        if not has_rotation:
            invert = False
        else:
            invert = True

        x, y = self._get_rect_box(x, y, width, height, invert)
        x, y = self._apply_transformations_coords(x, y)

        real_w, real_h = img.size

        if not has_rotation:
            box = (int(x), int(y))
        else:
            box = (int(x - real_w//2), int(y - real_h//2))

        self.current_frame.paste(img, box, img)

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
        self.current_frame.save(filename)

    def quit(self):
        """
        Stops the simulation
        """

        self.quitted = True
