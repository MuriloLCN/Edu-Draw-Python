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

            if self.interval != 0:
                time.sleep(self.interval)

    def quit(self):
        self.flag = True

    def change_interval(self, new_deltatime: int):
        self.interval = new_deltatime / 1000


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

        self.erase_state = False

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
            if event.type == pygame.ACTIVEEVENT:
                if hasattr(event, 'state'):
                    self.main_instance.focused = not event.state == 1
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

        self.timeloop: None | _RepeatTimer = None
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

        self.focused = True

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
            self.remove_icon()

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

        if data.erase_state:
            stroke_color = data.current_background_color
            fill_color = data.current_background_color

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

        # scale_tf = data.transformations['SCL']

        final_width *= data.cumulative_scaling_factor[0]
        final_height *= data.cumulative_scaling_factor[1]

        # for transformation in data.applied_transformations:
        #     # Sizes are only affected by scaling
        #     if transformation[0] == scale_tf:
        #         final_width *= transformation[1][0]
        #         final_height *= transformation[1][1]

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

    @staticmethod
    def _compute_bezier_points(vertices: list, num_points: int = None):
        """
        Function found at: https://www.pygame.org/wiki/BezierCurve
        Credits: Victor Blomqvist, 2007

        Computes the points to be used when drawing a bezier curve
        :param vertices: The control points to be used for the curve. Needs at least 4
        :param num_points: The number of points to be used as steps. Higher numbers make a more rounded shape.
        """

        if num_points is None:
            num_points = 30

        if num_points <= 2 or len(vertices) != 4:
            return None

        result = []

        b0x = vertices[0][0]
        b0y = vertices[0][1]
        b1x = vertices[1][0]
        b1y = vertices[1][1]
        b2x = vertices[2][0]
        b2y = vertices[2][1]
        b3x = vertices[3][0]
        b3y = vertices[3][1]

        # Compute polynomial coefficients from Bezier points
        ax = -b0x + 3 * b1x + -3 * b2x + b3x
        ay = -b0y + 3 * b1y + -3 * b2y + b3y

        bx = 3 * b0x + -6 * b1x + 3 * b2x
        by = 3 * b0y + -6 * b1y + 3 * b2y

        cx = -3 * b0x + 3 * b1x
        cy = -3 * b0y + 3 * b1y

        dx = b0x
        dy = b0y

        # Set up the number of steps and step size
        num_steps = num_points - 1  # arbitrary choice
        h = 1.0 / num_steps  # compute our step size

        # Compute forward differences from Bezier points and "h"
        point_x = dx
        point_y = dy

        first_fdx = ax * (h * h * h) + bx * (h * h) + cx * h
        first_fdy = ay * (h * h * h) + by * (h * h) + cy * h

        second_fdx = 6 * ax * (h * h * h) + 2 * bx * (h * h)
        second_fdy = 6 * ay * (h * h * h) + 2 * by * (h * h)

        third_fdx = 6 * ax * (h * h * h)
        third_fdy = 6 * ay * (h * h * h)

        # Compute points at each step
        result.append((int(point_x), int(point_y)))

        for i in range(num_steps):
            point_x += first_fdx
            point_y += first_fdy

            first_fdx += second_fdx
            first_fdy += second_fdy

            second_fdx += third_fdx
            second_fdy += third_fdy

            result.append((int(point_x), int(point_y)))

        return result

    @staticmethod
    def _get_intersection_arc_edge(angle: int, width: int, height: int) -> tuple:
        """
        Gets the intersection of an angle in an ellipse with the rectangle containing said ellipse.

        :param angle: The angle to get the intersection from
        :param width: The width of the rectangle containing the ellipse
        :param height: The height of the rectangle containing the ellipse
        :return: The (x, y) coordinates of the intersection
        """
        if angle == 0:
            return width, height//2

        elif 0 < angle < 90:
            tan_theta = math.tan(math.radians(angle))
            tan_sigma = math.tan(math.radians(90 - angle))
            d_h = tan_theta * width//2
            d_w = tan_sigma * height//2

            if d_w > width//2:
                return width, height//2 - d_h

            else:
                return width//2 + d_w, 0

        elif angle == 90:
            return width//2, 0

        elif 90 < angle < 180:
            tan_sigma = math.tan(math.radians(180 - angle))
            tan_theta = math.tan(math.radians(angle - 90))

            d_w = tan_theta * (height // 2)
            d_h = tan_sigma * (width // 2)

            if d_w > width//2:
                return 0, height//2 - d_h
            else:
                return width//2 - d_w, 0

        elif angle == 180:
            return 0, height//2

        elif 180 < angle < 270:
            tan_sigma = math.tan(math.radians(270 - angle))
            tan_theta = math.tan(math.radians(angle - 180))

            d_h = tan_theta * (width // 2)
            d_w = tan_sigma * (height // 2)

            if d_w > width // 2:
                return 0, height//2 + d_h
            else:
                return width//2 - d_w, height

        elif angle == 270:
            return width//2, height

        else:
            tan_theta = math.tan(math.radians(angle - 270))
            tan_sigma = math.tan(math.radians(360 - angle))

            d_w = tan_theta * (height // 2)
            d_h = tan_sigma * (width // 2)

            if d_w > width // 2:
                return width, height//2 + d_h
            else:
                return width//2 + d_w, height

    @staticmethod
    def _get_intersection_angle_ellipse(angle: int, width: int, height: int) -> tuple:
        """
        Finds the intersection of an angle with the circumference of an ellipse
        Got the formulas from here: https://math.stackexchange.com/q/22068

        :param angle: The angle to find the intersection
        :param width: The width of the rectangle containing the ellipse
        :param height: The height of the rectangle containing the ellipse
        :return: The intersection of the angle with the circumference
        """

        if angle < 0:
            angle += 360
        # Cases where tg(x) is undefined
        if angle == 0:
            return width, height//2
        if angle == 90:
            return width//2, height
        if angle == 180:
            return 0, height//2
        if angle == 270:
            return width//2, 0

        tg_angle = math.tan(math.radians(angle))
        a = width // 2
        b = height // 2
        denominator = math.sqrt(b * b + a * a * tg_angle * tg_angle)
        x_numerator = a * b
        x = x_numerator / denominator
        y_numerator = a * b * tg_angle
        y = y_numerator / denominator
        if 90 < angle < 270:
            return -x + a, -y + b
        else:
            return x + a, y + b

    @staticmethod
    def _sorting_keys(e):
        """ Dummy function to help sorting """
        return e[0]

    @staticmethod
    def _get_intersections_line_rect(point: tuple, angle: int, width: int, height: int) -> list:
        """
        Finds the intersections between a line given by a point and an angle with the four line defining a rectangle.

        :param point: The known point
        :param angle: The angle the line forms
        :param width: The width of the rect
        :param height: The height of the rect
        """
        if angle == 90 or angle == 270:
            return [(point[0], 0), (point[0], height)]
        if angle == 0 or angle == 180:
            return [(0, point[1]), (width, point[1])]

        angle = math.radians(angle)
        sigma = angle - math.pi/2
        alpha = math.pi/2 - sigma

        tg_sigma = math.tan(sigma)
        tg_alpha = math.tan(alpha)

        dx_top = point[1] * tg_sigma
        dy_left = point[0] * tg_alpha
        dy_right = (width - point[0]) * tg_alpha
        dx_bottom = (height - point[1]) * tg_sigma

        point_top = (point[0] + dx_top, 0)
        point_left = (0, point[1] + dy_left)
        point_right = (width, point[1] - dy_right)
        point_bottom = (point[0] - dx_bottom, height)

        points = []
        if 0 < point_top[0] < width:
            points.append(point_top)

        if 0 < point_bottom[0] < width:
            points.append(point_bottom)

        if 0 < point_left[1] < height:
            points.append(point_left)

        if 0 < point_right[1] < height:
            points.append(point_right)

        return points

    @staticmethod
    def _get_angle_from_points(p1: tuple, p2: tuple) -> int:
        """
        Retrieves angle from two points.

        :param p1: The first point
        :param p2: The second point
        :return: The angle (in degrees)
        """
        if p1[0] == p2[0]:
            if p2[1] > p1[0]:
                return 90
            else:
                return 270
        if p1[1] == p2[1]:
            if p2[0] > p1[0]:
                return 0
            else:
                return 180

        dy = p2[1] - p1[1]
        dx = p2[0] - p1[0]

        angle = int(math.degrees(math.atan(dy / dx)))

        return angle

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

    def erase(self):
        """
        Makes all drawings erase from the canvas (i.e, their color will be the current background color)
        """
        self._get_data_object().erase_state = True

    def no_erase(self):
        """
        Stops erasing shapes
        """
        self._get_data_object().erase_state = False
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

        try:
            self.screen.blit(new_surface, (int(pos_x - new_width / 2), int(pos_y - new_height / 2)))
        except pygame.error:
            pass

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

        try:
            self.screen.blit(img, box)
        except pygame.error:
            pass

    def bezier_curve(self, control_points: list, num_points: int | None = None):
        """
        Draws a bezier curve from a set of control points

        :param control_points: A list of tuples containing the coordinates of the control points for the curve
        :param num_points: The number of points to be used as steps for the lines. Default: 30
        """
        data = self._get_data_object()

        b_points = self._compute_bezier_points(control_points, num_points)

        if b_points is None:
            return

        for i, elem in enumerate(b_points):
            new_point = self._apply_transformations_coords(elem[0], elem[1])
            b_points[i] = new_point

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()

        if data.stroke_state:
            pygame.draw.lines(self.screen, stroke_color, False, b_points, stroke_weight)

    def arc_open(self, start_angle: int, stop_angle: int, x: int, y: int, width: int, height: int):
        """
        Draws an open arc onto the canvas.

        :param start_angle: The starting angle (in degrees) of the arc
        :param stop_angle: The stopping angle (in degrees) of the arc
        :param x: The x coordinate to draw the arc, if circle mode is top_left, it's the top left of the rectangle
        containing the ellipse, else it's the center of the ellipse
        :param y: The y coordinate to draw the arc
        :param width: The width of the ellipse to create the arc
        :param height: The height of the ellipse to create the arc
        """
        data = self._get_data_object()
        color = data.current_stroke_color

        if data.cumulative_rotation_angle == 0:
            has_rotation = False
        else:
            has_rotation = True

        pos_x, pos_y = self._get_circle_box(x, y, width, height, has_rotation)
        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y)
        pos_x, pos_y = int(pos_x), int(pos_y)

        width, height = self._apply_transformations_length(width, height)
        width, height = int(width), int(height)

        # Circles and non-slanted ellipses have simple drawings
        if width == height or not has_rotation:
            stop_angle -= data.cumulative_rotation_angle
            start_angle -= data.cumulative_rotation_angle

            start_angle = math.radians(start_angle)
            stop_angle = math.radians(stop_angle)

            # pos_x -= width//2
            # pos_y -= height//2

            pygame.draw.arc(self.screen, color, (pos_x, pos_y, width, height), start_angle,
                            stop_angle, data.current_stroke_weight)
            return

        start_angle = math.radians(start_angle)
        stop_angle = math.radians(stop_angle)

        new_surface = pygame.surface.Surface((width + 1, height + 1), pygame.SRCALPHA)

        pygame.draw.arc(new_surface, color, (0, 0, width + 1, height + 1), start_angle, stop_angle,
                        data.current_stroke_weight)

        new_surface = pygame.transform.rotate(new_surface, -data.cumulative_rotation_angle)

        new_width, new_height = new_surface.get_size()

        try:
            self.screen.blit(new_surface, (int(pos_x - new_width / 2), int(pos_y - new_height / 2)))
        except pygame.error:
            pass

    def arc_pie(self, start_angle: int, stop_angle: int, x: int, y: int, width: int, height: int,
                close_edges: bool = True):
        """
        Draws a pie-like arc in a counter-clockwise direction from the starting angle up to the stopping angle.

        :param start_angle: The starting angle to draw the pie.
        :param stop_angle: The angle to stop the pie
        :param x: The x coordinate to draw the ellipse of the pie
        :param y: The y coordinate to draw the ellipse of the pie
        :param width: The horizontal diameter of the ellipse
        :param height: The vertical diameter of the ellipse
        :param close_edges: Whether the lines from the edges of the pie should be drawn. Default: True
        """
        if abs(start_angle) >= 360:
            start_angle = start_angle % 360

        if abs(stop_angle) >= 360:
            stop_angle = stop_angle % 360

        if start_angle == stop_angle:
            return

        inverted = False
        if start_angle > stop_angle:
            inverted = True

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()
        data = self._get_data_object()

        pos_x, pos_y = self._get_circle_box(x, y, width, height, True)
        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y)
        pos_x, pos_y = int(pos_x), int(pos_y)

        width, height = self._apply_transformations_length(width, height)
        width, height = int(width), int(height)

        new_image = pygame.surface.Surface((width + 1, height + 1), flags=pygame.SRCALPHA)

        # Drawing ellipse
        if data.anti_aliasing:
            if data.stroke_state:
                gfxdraw.aaellipse(new_image, width//2, height//2, width//2, height//2, stroke_color)
            if data.fill_state:
                gfxdraw.filled_ellipse(new_image, width//2, height//2, width//2, height//2, fill_color)
        else:
            if data.fill_state:
                pygame.draw.ellipse(new_image, fill_color, (0, 0, width, height), 0)

            if data.stroke_state:
                pygame.draw.ellipse(new_image, stroke_color, (0, 0, width, height), stroke_weight)

        # Calculating and drawing polygon to make pie shape
        sorted_points = []

        unsorted_points = [(start_angle, self._get_intersection_arc_edge(start_angle, width, height)),
                           (stop_angle, self._get_intersection_arc_edge(stop_angle, width, height))]

        theta = math.degrees(math.atan(height / width))
        angle_top_right = theta
        angle_top_left = 180 - theta
        angle_bottom_left = 180 + theta
        angle_bottom_right = 360 - theta

        if inverted:
            if start_angle > angle_top_right > stop_angle:
                unsorted_points.append((angle_top_right, (width, 0)))

            if start_angle > angle_top_left > stop_angle:
                unsorted_points.append((angle_top_left, (0, 0)))

            if start_angle > angle_bottom_left > stop_angle:
                unsorted_points.append((angle_bottom_left, (0, height)))

            if start_angle > angle_bottom_right > stop_angle:
                unsorted_points.append((angle_bottom_right, (width, height)))

        else:
            if not (start_angle < angle_top_right < stop_angle):
                unsorted_points.append((angle_top_right, (width, 0)))

            if not (start_angle < angle_top_left < stop_angle):
                unsorted_points.append((angle_top_left, (0, 0)))

            if not (start_angle < angle_bottom_left < stop_angle):
                unsorted_points.append((angle_bottom_left, (0, height)))

            if not (start_angle < angle_bottom_right < stop_angle):
                unsorted_points.append((angle_bottom_right, (width, height)))

        unsorted_points.sort(key=self._sorting_keys)

        starting_index = -1
        for i in range(len(unsorted_points)):
            sorted_points.append(unsorted_points[i][1])
            if unsorted_points[i][0] == start_angle:
                starting_index = i + 1

        # for index, point in enumerate(unsorted_points):
        #     if point[0] == start_angle:
        #         starting_index = index
        #     sorted_points.append(point[1])

        sorted_points.insert(starting_index, (width//2, height//2))

        pygame.draw.polygon(new_image, data.current_background_color, sorted_points, 0)

        if close_edges:
            point_start = self._get_intersection_angle_ellipse(-start_angle, width, height)
            point_stop = self._get_intersection_angle_ellipse(-stop_angle, width, height)

            pygame.draw.line(new_image, stroke_color, (width//2, height//2), point_start, stroke_weight)
            pygame.draw.line(new_image, stroke_color, (width//2, height//2), point_stop, stroke_weight)

        new_image = pygame.transform.rotate(new_image, -data.cumulative_rotation_angle)

        new_width, new_height = new_image.get_size()

        new_image.set_colorkey(data.current_background_color)
        try:
            self.screen.blit(new_image, (int(pos_x - new_width / 2), int(pos_y - new_height / 2)))
            # self.screen.blit(new_image, (int(pos_x), int(pos_y)))
        except pygame.error:
            pass

    def arc_closed(self, start_angle: int, stop_angle: int, x: int, y: int, width: int, height: int,
                   close_edges: bool = True):
        """
        Draws a closed arc between two angles in an ellipse

        :param start_angle: The starting angle of the arc
        :param stop_angle: The stopping angle of the arc
        :param x: The x coordinate to place the arc's ellipse
        :param y: The y coordinate to place the arc's ellipse
        :param width: The width of the ellipse
        :param height: The height of the ellipse
        :param close_edges: Whether the edges between the starting and stopping angles should be connected
        """

        if abs(start_angle) >= 360:
            start_angle = start_angle % 360

        if abs(stop_angle) >= 360:
            stop_angle = stop_angle % 360

        if start_angle == stop_angle:
            return

        inverted = False
        if start_angle > stop_angle:
            inverted = True

        stroke_color, fill_color, stroke_weight = self._get_stroke_fill_and_weight()
        data = self._get_data_object()

        pos_x, pos_y = self._get_circle_box(x, y, width, height, True)
        pos_x, pos_y = self._apply_transformations_coords(pos_x, pos_y)
        pos_x, pos_y = int(pos_x), int(pos_y)

        width, height = self._apply_transformations_length(width, height)
        width, height = int(width), int(height)

        new_image = pygame.surface.Surface((width + 1, height + 1), flags=pygame.SRCALPHA)

        # Drawing ellipse
        if data.anti_aliasing:
            if data.stroke_state:
                gfxdraw.aaellipse(new_image, width // 2, height // 2, width // 2, height // 2, stroke_color)
            if data.fill_state:
                gfxdraw.filled_ellipse(new_image, width // 2, height // 2, width // 2, height // 2, fill_color)
        else:
            if data.fill_state:
                pygame.draw.ellipse(new_image, fill_color, (0, 0, width, height), 0)

            if data.stroke_state:
                pygame.draw.ellipse(new_image, stroke_color, (0, 0, width, height), stroke_weight)

        # Calculating and drawing polygon to make shape
        sorted_points = []

        point_start_angle = self._get_intersection_angle_ellipse(-start_angle, width, height)
        point_stop_angle = self._get_intersection_angle_ellipse(-stop_angle, width, height)

        angle = self._get_angle_from_points(point_start_angle, point_stop_angle)

        intersections = self._get_intersections_line_rect(point_start_angle, angle, width, height)

        unsorted_points = []

        if len(intersections) != 2:
            return

        new_angles = []

        for point in intersections:
            theta = math.degrees(math.atan2(point[1] - height//2, point[0] - width//2))
            if theta < 0:
                theta *= -1
            else:
                theta = 180 + (180 - theta)

            theta = theta % 360
            new_angles.append(theta)
            unsorted_points.append((theta, point))

        theta = math.degrees(math.atan(height / width))
        angle_top_right = theta
        angle_top_left = 180 - theta
        angle_bottom_left = 180 + theta
        angle_bottom_right = 360 - theta

        start_angle = new_angles[1]
        stop_angle = new_angles[0]

        if inverted:
            if start_angle < stop_angle:
                start_angle, stop_angle = stop_angle, start_angle

            if start_angle > angle_top_right > stop_angle:
                unsorted_points.append((angle_top_right, (width, 0)))

            if start_angle > angle_top_left > stop_angle:
                unsorted_points.append((angle_top_left, (0, 0)))

            if start_angle > angle_bottom_left > stop_angle:
                unsorted_points.append((angle_bottom_left, (0, height)))

            if start_angle > angle_bottom_right > stop_angle:
                unsorted_points.append((angle_bottom_right, (width, height)))

        else:
            if start_angle > stop_angle:
                start_angle, stop_angle = stop_angle, start_angle

            if not (start_angle < angle_top_right < stop_angle):
                unsorted_points.append((angle_top_right, (width, 0)))

            if not (start_angle < angle_top_left < stop_angle):
                unsorted_points.append((angle_top_left, (0, 0)))

            if not (start_angle < angle_bottom_left < stop_angle):
                unsorted_points.append((angle_bottom_left, (0, height)))

            if not (start_angle < angle_bottom_right < stop_angle):
                unsorted_points.append((angle_bottom_right, (width, height)))

        unsorted_points.sort(key=self._sorting_keys)

        for i in range(len(unsorted_points)):
            sorted_points.append(unsorted_points[i][1])

        pygame.draw.polygon(new_image, data.current_background_color, sorted_points, 0)

        if close_edges:
            pygame.draw.line(new_image, stroke_color, point_start_angle, point_stop_angle, stroke_weight)

        new_image = pygame.transform.rotate(new_image, -data.cumulative_rotation_angle)

        new_width, new_height = new_image.get_size()

        new_image.set_colorkey(data.current_background_color)
        try:
            self.screen.blit(new_image, (int(pos_x - new_width / 2), int(pos_y - new_height / 2)))
            # self.screen.blit(new_image, (int(pos_x), int(pos_y)))
        except pygame.error:
            pass
        pass

    # Other methods -----------------------------------------------------------------------------------------------
    @staticmethod
    def load_sound(file: str) -> pygame.mixer.Sound:
        """
        Creates a new pygame.mixer.Sound instance from a file

        :param file: The file to load the sound from
        :return: A created pygame.mixer.Sound instance
        """
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        return pygame.mixer.Sound(file=file)

    @staticmethod
    def play_sound(sound: pygame.mixer.Sound, loops: int = 0, max_time: int = 0, fade_time: int = 0):
        """
        Plays a sound

        :param sound: The sound to be played
        :param loops: The amount of times to loop the audio
        :param max_time: The maximum time (in ms) to play the audio
        :param fade_time: The fading time (in ms) of the audio
        """
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        sound.play(loops=loops, maxtime=max_time, fade_ms=fade_time)

    def retrieve_frame(self) -> pygame.surface.Surface:
        """
        Retrieves the current frame of the simulation as a pygame Surface image.

        :return: The currently drawn frame from when this method was called.
        """
        return self.screen

    def change_icon(self, image: pygame.surface.Surface):
        """
        Changes icon to a user-defined image

        :param image: The image to be used as icon
        """
        if not self.null_mode:
            pygame.display.set_icon(image)

    @staticmethod
    def lerp_color(color_1: tuple, color_2: tuple, amount: float = 0.5) -> tuple:
        """
        Mixes two color to find an intermediary color between them

        :param color_1: The color to lerp from
        :param color_2: The color to lerp to
        :param amount: How close the resulting color should be to the two colors to be mixed. 0.5 makes it an average.
        """

        iterations = 4
        result = [0, 0, 0, 255]

        if len(color_1) == 3 and len(color_2) == 3:
            iterations = 3
            result = [0, 0, 0]

        else:
            if len(color_1) == 3:
                color_1 = list(color_1)
                color_1.append(255)
                color_1 = tuple(color_1)

            if len(color_2) == 3:
                color_2 = list(color_2)
                color_2.append(255)
                color_2 = tuple(color_2)

        for i in range(iterations):
            difference = color_2[i] - color_1[i]
            difference *= amount
            result[i] = int(color_1[i] + difference)

            if result[i] < 0:
                result[i] = 0

            if result[i] > 255:
                result[i] = 255

        return tuple(result)

    @staticmethod
    def remove_icon():
        """
        Removes icon from window
        """
        new_image = pygame.surface.Surface((32, 32), flags=pygame.SRCALPHA)
        pygame.display.set_icon(new_image)

    def get_color_from_pos(self, x: int, y: int) -> tuple:
        """
        Retrieves the color from a given position in the current frame

        :param x: The x coordinate to retrieve the color from
        :param y: The y coordinate to retrieve the color from
        :return: A (r,g,b,a) tuple with the color at that position
        """
        return tuple(self.screen.get_at((x, y)))

    def is_focused(self) -> bool:
        """
        Gets whether the display is focused or not.

        :return: True if display is focused, False if not
        """
        if not self.null_mode:
            return self.focused

    def set_mouse_visibility(self, visible: bool):
        """
        Changes the visibility of the cursor

        :param visible: Whether the mouse should be visible or hidden
        """
        if not self.null_mode:
            pygame.mouse.set_visible(visible)

    def frame_rate(self, fps: int):
        """
        Sets the desired frame rate. Note that EduDraw using python is slower than it's C# counterpart.
        :param fps: The desired FPS rate.
        """

        if fps == 0:
            return

        self.deltatime = 1000 / fps

        if self.timeloop is not None:
            self.timeloop.change_interval(int(self.deltatime))

    def use_max_frame_rate(self):
        """
        Changes the inner time between frames to zero, the frame rate is determined by computation speed and may vary
        """

        self.deltatime = 0

        if self.timeloop is not None:
            self.timeloop.interval = 0

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
