import gc

import pygame.image

from src.EduDraw import edudraw
import time

s = edudraw.EduDraw(500, 500)
d = edudraw.EduDraw(250, 250, True)

flag_done = False
tests = []

end = 0
start = time.time()

antialias = False

def pressed(data):
    global antialias
    antialias = not antialias


def setup():
    s.set_controls(key_down=pressed)

flag_has_null = False

def draw():
    global flag_done, start, end, flag_has_null

    # print(s._get_data_object().custom_font_object)

    if antialias:
        s.toggle_antialiasing()

    if len(tests) == 0:
        # d.quit()
        if flag_done:
            s.quit()
            end = time.time()
            print(f"Test done: {str(test_null_mode)}, Elapsed time: {end - start}, Avg. FPS: {s.frame_count / (end - start)}")
            print("All tests done.")
            return
        else:
            if not flag_has_null:
                start = time.time()
                d.start(dummy, inner_drawing, "This should not appear")
                flag_has_null = True
            test_null_mode()
    else:
        tests[-1]()
        if flag_done:
            end = time.time()
            test_ran = tests.pop()
            flag_done = False
            print(f"Test done: {str(test_ran)}, Elapsed time: {end - start}, Avg. FPS: {s.frame_count / (end - start)}")
            start = time.time()
            s.frame_count = 0
            gc.collect()
            # d.frame_count = 0


def dummy():
    pass

position = [d.width/2, d.height//2]
velocity = [3, 4]
def inner_drawing():
    # d.background((200, 200, 200))
    global position, velocity
    if position[0] < 0 or position[0] > d.width:
        velocity[0] *= -1

    if position[1] < 0 or position[1] > d.height:
        velocity[1] *= -1

    position[0] += velocity[0]
    position[1] += velocity[1]

    d.fill((255, 0, 0))
    d.stroke((0, 0, 255))
    d.circle(position[0], position[1], 5)


def test_rect_mode():
    global flag_done
    s.background((200, 200, 200))

    s.no_fill()

    s.stroke((255, 0, 0))
    s.rect(50, 25, 100, 50)  # Rectangle with RECT_MODE as TOP_LEFT

    s.stroke((0, 0, 255))
    s.rect_mode('CENTER')
    s.rect(50, 25, 100, 50)  # Same rectangle with RECT_MODE as CENTER

    s.stroke((0, 0, 0))
    s.stroke_weight(3)
    s.point(50, 25)  # Point at the (x,y) coordinates passed in for the rectangles above
    if s.frame_count > 60:
        flag_done = True


tests.append(test_rect_mode)


def test_circle_mode():
    global flag_done
    s.background((200, 200, 200))

    s.no_fill()
    s.stroke_weight(3)

    # Three circles at the same starting pos. with circle_mode as TOP_LEFT
    s.circle_mode('TOP_LEFT')

    s.stroke((255, 0, 0))
    s.circle(50, 50, 25)

    s.stroke((0, 255, 0))
    s.circle(50, 50, 18)

    s.stroke((0, 0, 255))
    s.circle(50, 50, 8)

    # Three circles at the same starting pos. with circle_mode as CENTER
    s.circle_mode('CENTER')

    s.circle(150, 50, 25)
    s.stroke((255, 0, 0))
    s.circle(150, 50, 18)
    s.stroke((0, 255, 0))
    s.circle(150, 50, 8)

    s.stroke((0, 0, 0))
    s.point(150, 50)
    s.point(50, 50)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_circle_mode)


def test_fill_no_fill():
    global flag_done
    s.background((255, 255, 255))

    s.stroke_weight(2)
    s.no_fill()
    s.stroke((0, 255, 0))
    s.square(50, 50, 50)

    s.fill((255, 255, 0))
    s.circle(100, 150, 25)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_fill_no_fill)

pygame.font.init()

font1 = pygame.font.Font(pygame.font.match_font('arial', bold=True), 25)
font2 = pygame.font.Font(pygame.font.match_font('calibri', italic=True), 30)
font3 = pygame.font.Font(pygame.font.match_font('roboto'), 25)
font3.set_underline(True)


def test_font():
    global flag_done

    s.background((200, 200, 200))
    s.fill((255, 255, 0))
    s.text("Hello,", 0, 0)

    s.font_from_instance(font1)
    s.text("world!", 0, 20)

    s.font_from_instance(font2)
    s.text("This is a", s.width//2, 0)

    s.font_from_instance(font3)
    s.text("test!", s.width//2, 30)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_font)


def test_stroke_no_stroke():
    global flag_done
    s.background((200, 200, 200))

    s.stroke_weight(2)

    s.fill((255, 0, 0))
    s.no_stroke()

    s.square(20, 30, 60)

    s.fill((100, 100, 100))
    s.stroke((0, 0, 255))

    s.triangle(200, 200, 300, 300, 350, 150)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_stroke_no_stroke)


def test_stroke_weight():
    global flag_done
    s.background((200, 200, 200))

    s.stroke_weight(1)
    s.line(0, 20, s.width, 20)

    s.stroke_weight(2)
    s.line(0, 40, s.width, 40)

    s.stroke_weight(4)
    s.line(0, 60, s.width, 60)

    s.stroke_weight(8)
    s.line(0, 80, s.width, 80)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_stroke_weight)


def test_push_pop_1():
    global flag_done
    s.background((200, 200, 200))
    s.circle_mode('TOP_LEFT')

    s.stroke_weight(2)

    s.fill((255, 0, 0))
    s.stroke((0, 0, 255))

    s.square(50, 50, 50)
    s.circle(100, 50, 25)

    s.push()
    s.fill((255, 255, 0))
    s.square(100, 100, 50)
    s.pop()

    s.circle(50, 100, 25)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_push_pop_1)


def test_push_pop_2():
    global flag_done
    # Setting up visuals
    s.circle_mode('TOP_LEFT')
    s.stroke_weight(2)
    s.background((255, 255, 255))
    s.translate(50, 0)
    s.stroke((0, 0, 255))

    # Main state: Red circle
    s.fill((255, 0, 0))
    s.circle(0, 50, 25)

    s.push()
    # Second state: Green circle, translated 10px below main state
    s.translate(0, 10)
    s.fill((0, 255, 0))
    s.circle(50, 50, 25)

    s.push()
    # Third state: Blue circle, translated 10px below second state (20px below main state - it's cumulative)
    s.translate(0, 10)
    s.fill((0, 0, 255))
    s.circle(100, 50, 25)

    s.pop()
    # Leave third state
    s.circle(150, 50, 25)

    s.pop()
    # Leave second state
    s.circle(200, 50, 25)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_push_pop_2)


def test_mouse_pos_1():
    global flag_done
    s.background((200, 200, 200))

    mouse_x, mouse_y = s.mouse_pos()
    s.no_fill()

    if 75 <= mouse_x <= 150:
        if 75 <= mouse_y <= 150:
            s.fill((255, 255, 0))

    s.circle(mouse_x, mouse_y, 3)

    s.square(75, 75, 75)

    s.fill((0, 255, 0))
    s.text(f"X: {mouse_x}", 10, 10)
    s.fill((255, 0, 0))
    s.text(f"Y: {mouse_y}", 10, 30)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_mouse_pos_1)


def test_mouse_pos_2():
    global flag_done
    s.set_account_for_transformations(False)
    s.background((255, 255, 255))
    s.stroke((200, 0, 200))

    s.scale(1.1, 1.4)
    s.rotate(s.frame_count)
    s.translate(s.width // 2, s.height // 2)

    # Line to illustrate rotation of the canvas
    s.line(s.width // 2, s.height // 2, 0, 0)

    no_account = s.mouse_pos()

    s.set_account_for_transformations(True)

    account = s.mouse_pos()

    # Light blue circle where the perceived mouse position is
    s.fill((150, 150, 255))
    s.circle(account[0], account[1], 12)

    # Red blue circle where the actual mouse position is
    s.fill((255, 0, 0))
    s.circle(no_account[0], no_account[1], 12)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_mouse_pos_2)


def test_rotate_1():
    global flag_done
    s.background((255, 255, 255))
    s.stroke((255, 0, 0))
    s.line(50, 50, 100, 50)

    s.rotate(10)
    # Current angle: 10 degrees

    s.stroke((0, 0, 255))
    s.line(50, 50, 100, 50)

    s.rotate(10)
    # Current angle: 20 degrees

    s.stroke((100, 255, 100))
    s.line(50, 50, 100, 50)

    s.rotate(-15)
    # Current angle: 5 degrees

    s.stroke((255, 200, 0))
    s.line(50, 50, 100, 50)

    s.rotate(-10)
    # Current angle: -5 degrees (355 degrees)

    s.stroke((0, 255, 255))
    s.line(50, 50, 100, 50)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_rotate_1)


def test_rotate_2():
    global flag_done
    s.background((255, 255, 255))
    s.fill((0, 0, 0))
    s.fill((255, 0, 0))
    s.circle_mode('CENTER')
    s.rotate(s.frame_count)
    s.translate(s.width // 2, s.height // 2)
    s.circle(0, 0, 10)
    s.push()
    s.fill((0, 255, 0))
    s.reset_translation()
    s.rotate(s.frame_count)
    s.translate(s.width // 2, s.height // 2)
    s.circle(20, 0, 10)
    s.push()
    s.fill((0, 0, 255))
    s.reset_translation()
    s.rotate(s.frame_count)
    s.translate(s.width // 2, s.height // 2)
    s.circle(40, 0, 10)
    s.pop()
    s.circle(60, 0, 10)
    s.pop()
    s.circle(80, 0, 10)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_rotate_2)


def test_scale():
    global flag_done
    s.background((255, 255, 255))
    s.fill((200, 200, 0))

    s.square(50, 50, 25)

    s.scale(2, 0.5)

    s.fill((0, 0, 200))
    s.square(50, 50, 25)

    s.reset_scaling()
    s.scale(0.75, 1.25)

    s.fill((255, 0, 0))
    s.square(50, 50, 25)

    s.reset_scaling()

    s.fill((0, 255, 0))
    s.square(75, 75, 25)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_scale)


def test_translate():
    global flag_done

    s.translate(0, 0)
    s.background((255, 255, 255))
    s.fill((125, 125, 125))
    s.square(50, 50, 50)

    s.translate(-50, 50)
    s.fill((200, 200, 0))
    s.square(50, 50, 50)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_translate)


def test_point():
    global flag_done

    if s.frame_count > 60:
        flag_done = True


tests.append(test_point)


def test_circle():
    global flag_done

    s.background((255, 255, 255))
    s.circle_mode('CENTER')
    s.translate(s.width//2, s.height//2)
    s.no_fill()
    s.circle(0, 0, s.width // 2)
    s.stroke((255, 0, 0))
    s.circle(0, 0, s.width // 3)
    s.stroke((0, 255, 0))
    s.circle(0, 0, s.width // 4)
    s.stroke((0, 0, 255))
    s.circle(0, 0, s.width // 5)
    s.stroke((255, 0, 255))
    s.circle(0, 0, s.width // 6)
    s.fill((255, 255, 0))
    s.circle(0, 0, s.width // 7)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_circle)


def test_ellipse():
    global flag_done

    s.scale(1.25, 1)
    s.rotate(s.frame_count//3)
    s.background((200, 200, 200))

    s.stroke_weight(3)
    s.circle_mode('TOP_LEFT')

    s.fill((100, 100, 100))
    s.stroke((0, 0, 255))
    s.ellipse(62, 40, 45, 70)

    s.no_fill()
    s.stroke((255, 0, 0))
    s.ellipse(50, 50, 70, 30)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_ellipse)


def test_background():
    global flag_done

    r = s.frame_count
    g = 255 - s.frame_count
    b = (r * g) % 256

    color = (r, g, b)
    s.background(color)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_background)


def test_text():
    global flag_done

    s.background((200, 200, 200))

    s.rotate(s.frame_count)
    s.translate(s.width // 2, s.height // 2)
    s.text('Hello, world!', 0, 0)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_text)


def test_line():
    global flag_done

    s.rotate(s.frame_count//3)
    s.background((200, 200, 200))
    s.stroke_weight(3)

    s.line(0, 0, s.width, s.height)
    s.stroke((0, 0, 255))
    s.line(0, s.height // 2, s.width, s.height // 2)
    s.stroke((255, 0, 0))
    s.line(200, 300, 400, 250)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_line)


def test_square():
    global flag_done

    s.background((255, 255, 255))
    s.scale(0.75, 1.25)
    s.rotate(-s.frame_count)

    s.no_stroke()
    s.fill((0, 0, 0))

    for i in range(0, s.width, 25):
        for j in range(0, s.height, 25):
            if ((i + j) % 2) == 0:
                s.square(i, j, 25)

    if s.frame_count > 60:
        flag_done = True


tests.append(test_square)


def test_rect():
    global flag_done
    s.background((200, 200, 200))
    s.stroke_weight(3)

    x = 50
    y = 60

    dx = 5
    dy = 5

    s.no_fill()

    s.rect(x, y, 50, 90)

    s.stroke((255, 0, 0))
    s.rect(y, x, 90, 50)

    s.stroke((0, 0, 255))
    s.rect(x + dx, y + dy, 50 - dx * 2, 90 - dy * 2)
    if s.frame_count > 60:
        flag_done = True


tests.append(test_rect)


def test_triangle():
    global flag_done
    s.background((200, 200, 200))

    s.fill((255, 255, 0))

    s.triangle(40, 40, 120, 40, 80, 120)
    s.triangle(120, 40, 200, 40, 160, 120)
    s.triangle(80, 120, 160, 120, 120, 200)

    if s.frame_count > 45:
        flag_done = True


tests.append(test_triangle)


def test_polygon():
    global flag_done
    s.background((200, 200, 200))

    s.rotate(s.frame_count)
    s.fill((100, 255, 255))
    points = [
        (50, 50),
        (100, 50),
        (120, 100),
        (75, 135),
        (30, 100)
    ]

    s.polygon(points)

    if s.frame_count > 40:
        flag_done = True


tests.append(test_polygon)

# Note: This is just a test picture, nothing special
img = pygame.image.load(r"C:\Users\Murilo Luis\Desktop\logo.png")


def test_image():
    global flag_done

    s.scale(0.75, 1.25)
    s.background((200, 200, 200))
    s.image(img, 50, 50, 200, 200)
    s.rotate(s.frame_count)
    s.rect_mode("CENTER")
    s.translate(s.width // 2, s.height // 2)
    s.image(img, 0, 0, 200, 200, force_transparency=True)

    if s.frame_count > 60:
        flag_done = True




tests.append(test_image)


def test_null_mode():
    global flag_done
    s.background((255, 255, 255))
    s.rotate(s.frame_count)
    s.rect_mode("CENTER")
    s.translate(s.width // 2, s.height // 2)
    s.image(d.screen, 0, 0)

    if s.frame_count > 150:
        flag_done = True


# tests.append(test_null_mode)

s.start(setup, draw, "Running tests")

