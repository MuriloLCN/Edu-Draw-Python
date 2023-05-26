# Edu-Draw-Python

This is the Python version of EduDraw, for the C# version, please see [Edu Draw C#](https://github.com/MuriloLCN/Simple-Draw-Csharp)

This project is aimed to provide an interface that allows for a simplified experience when using basic 2D graphics in the Python language. 

The general design of the interface is heavily (if not all) inspired by the [P5.js](https://p5js.org/) library and the Processing library, and is intended to make simple graphical programs easy to do in the .NET environment in the shape of a Windows Forms app and/or in the Python language.

The details of installation and documentation of the respective versions are below. 

## Installation

In order to use the Python version you can simply download the ```edudraw.py``` and import it in your code like any other library. You'll also need the requirements, which can be installed from the ```requirements.txt``` file.

## Setting up

In order to begin using the EduDraw class to make your drawings, you need to do a few steps first:
  
#### 1. Install the requirements

You need to install the requirements from the requirements file, you can do this by adding the file on your directory and running the following command:

    pip3 install -r requirements.txt

#### 2. Import the implementation file

You can do this by adding this to your imports:

    from edudraw import EduDraw

Make sure the file is in the same directory as the file from which you are using it from or that you properly add the path otherwise.

#### 3. Create an instance of the EduDraw class
  
This can be done by simply creating a new EduDraw instance like this:
    
    width, height = 500, 500  # Any size you want
    s = EduDraw(width, height)
    
#### 4. Create a ```setup()``` and a ```draw()``` function

These functions are the core of your drawing. ```setup()``` runs once and before ```draw()```, and it is used to set up the environment for the drawings that you want to do. Some things (like the frame rate) must be set in here, before the drawing actually begins. 
  
```draw()```, on the other hand, runs every frame, and is where you will give life to your graphics. Here is where shapes and elements will get drawn to the screen.

#### 5. Call ```s.start(setup, draw, window_title)``` 
 
Once you run this method on the instance you made for the EduDraw class, the simulation will start and keep running until you give it a halt command or close the window.
You need to pass the ```setup()``` and ```draw()``` functions you made, and also a ```window_title``` to give the running window a name.

The general structure of your form code may look something like this:

```
from eduraw import EduDraw

def setup():
    # Setting up goes here...

def draw():
    # Drawing goes here...

s = EduDraw(500, 500)
s.start(setup, draw, "My cool window")
```

And now you're ready to get onto some drawings :D

## Getting started (with a simple example)

Now that you have your canvas ready for the show, it's time to actually draw something on the screen. To begin with,let's draw a circle on the screen with a white background. Our code might look something like this:

```
from edudraw import EduDraw

s = EduDraw(500, 300)

def setup():
    pass

def draw():
    s.background((255, 255, 255))
    s.circle_mode('TOP_LEFT')
    s.circle(s.width // 2, s.height // 2, 24)

s.start(setup, draw, "My first drawing")
```

And our canvas looks like this:


![img1](https://github.com/MuriloLCN/Simple-Draw-Python/assets/88753590/b6ec2e1f-9b75-4c02-88fc-d66ef73c6909)


That's our circle! But this is not very interesting, so let's give it a red filling color, a blue outline and make it move around.

```
from edudraw import EduDraw

s = EduDraw(500, 300)


def setup():
    pass


velocity = 5
ball_position = [50, 50]


def draw():
    global ball_position
    s.background((255, 255, 255))
    s.circle_mode('TOP_LEFT')
    s.fill((255, 0, 0))
    s.stroke((0, 0, 255))
    ball_position[0] += velocity
    ball_position[1] += velocity

    s.circle(ball_position[0], ball_position[1], 24)

s.start(setup, draw, "My first drawing")
```

![img2](https://github.com/MuriloLCN/Simple-Draw-Python/assets/88753590/b780f016-ef8f-4f66-8d29-120736602985)


Now we have a moving red ball :D, but it leaves the screen fairly quickly, so let's make it bounce around.

```
from edudraw import EduDraw

s = EduDraw(500, 300)

width, height = 0, 0
velocity = [5, 5]
ball_position = [50, 50]


def setup():
    global width, height
    width = s.width
    height = s.height


def draw():
    global ball_position, velocity
    s.background((255, 255, 255))
    s.circle_mode('CENTER')
    s.fill((255, 0, 0))
    s.stroke((0, 0, 255))

    if ball_position[1] < 0 or ball_position[1] + 42 > height:
        velocity[1] *= -1

    if ball_position[0] < 0 or ball_position[0] + 42 > width:
        velocity[0] *= -1

    ball_position[0] += velocity[0]
    ball_position[1] += velocity[1]

    s.circle(ball_position[0], ball_position[1], 24)


s.start(setup, draw, "My first drawing")
```

![bouncing_ball](https://github.com/MuriloLCN/Simple-Draw-Python/assets/88753590/7ff0d89d-95c0-4cab-bd57-13fa8cee4f47)


And just like that, we've got a ball that bounces around like a DVD screensaver (I wonder when it'll hit the corners...), you should try for yourself.

This example was just to give you an idea of how you can work with this interface, and there is so much you can do with this, it's all up to you.

# Documentation

## State methods

These methods don't directly draw onto the screen, but rather control aspects of the simulation.

### EduDraw(width: int, height: int, null_mode: bool = False)

Initializer for the EduDraw class.

Parameters:

width, height: The width and height of the window to be created

null_mode: Whether null mode should be used or not. Default: False. See more about null mode at the end.

Returns a new instance of the EduDraw class.

### EduDraw.start(setup, draw, window_title: str)

Starts the simulation.

Parameters:

setup: The setup() function written by the user

draw: The draw() function written by the user

window_title: A string to be used as a title for the window running the simulation.

### EduDraw.rect_mode(mode: str)

Changes the current mode for drawing squares, rectangles and images.

If ```mode``` is ```'TOP_LEFT'``` (which is the default), the (X,Y) coordinates passed in for the ```rect()``` and ```square()``` methods will represent the top left coordinate of the rectangle.

On the other hand, if ```mode``` is ```'CENTER'```, the (X,Y) coordinates passed in for the methods above will represent the position of the center of the rectangle and the resulting position will be calculated based on it. 

Example:
```
    def draw():
        s.background((200, 200, 200))

        s.no_fill()

        s.stroke((255, 0, 0))
        s.rect(50, 25, 100, 50) # Rectangle with RECT_MODE as TOP_LEFT

        s.stroke((0, 0, 255))
        s.rect_mode('CENTER')
        s.rect(50, 25, 100, 50) # Same rectangle with RECT_MODE as CENTER

        s.stroke((0,0,0))
        s.stroke_weight(3)
        s.point(50, 25)  # Point at the (x,y) coordinates passed in for the rectangles above
    
```

![rectmode](https://user-images.githubusercontent.com/88753590/233815069-b4ab097a-52f3-4475-967c-9c4a65fa881c.png)


### EduDraw.circle_mode(mode: str)

Changes the current mode for drawing circles and ellipses.

If ```mode``` is ```'TOP_LEFT'```, the (X,Y) coordinates passed in for the ```circle()``` and ```ellipse()``` methods will represent the top left coordinate of the rectangle which contains the ellipse. 

On the other hand, if ```mode``` is ```'CENTER'``` (which is the default), the (X,Y) coordinates passed in for the methods above will represent the position of the center of the ellipse and the resulting position will be calculated based on it. 

```
def draw():
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
```

![circlemode](https://user-images.githubusercontent.com/88753590/233815073-8bb60f23-9c03-4c0d-982e-fc4e8a2319fc.png)


---

### EduDraw.fill(color: tuple)

Makes all shapes drawn after this call to be filled in with a given color.

Parameters:

color: A tuple containing the (R, G, B) values of the color to fill the subsequent shapes.

Example:
```
    def draw():
        s.background((255, 255, 255))
        
        s.stroke_weight(2)
        s.no_fill()
        s.stroke((0, 255, 0))
        s.square(50, 50, 50)

        s.fill((255, 255, 0))
        s.circle(100, 150, 25)
```

![fill](https://user-images.githubusercontent.com/88753590/233815075-ed143b96-8cae-4f8d-ba53-338467a036d9.png)

### EduDraw.no_fill()

Makes all shapes drawn after this call to not be filled in.

### EduDraw.change_font(font: PIL.ImageFont)

Changes the font used in the canvas. If temp state is on, it will change the temporary font only.

Parameters:

font: A PIL.ImageFont instance to be used on the simulation

### EduDraw.stroke(color: tuple)

Makes all shapes drawn after this call to have their outlines drawn with a given color.

Parameters:

color: A tuple containing the (R, G, B) values of the color to draw the outlines of the subsequent shapes.

Example:
```
def draw():
    s.background((200, 200, 200))

    s.stroke_weight(2)

    s.fill((255, 0, 0))
    s.no_stroke()

    s.square(20, 30, 60)

    s.fill((100, 100, 100))
    s.stroke((0, 0, 255))

    s.triangle(200, 200, 300, 300, 350, 150)
```

![stroke](https://user-images.githubusercontent.com/88753590/233815081-9336437f-1eb6-41d9-81a2-15ecfcc8d0b4.png)

### EduDraw.no_stroke()

Makes all subsequent shapes not have their outlines drawn. 

### EduDraw.stroke_weight(new_weight: int)

Changes how thick or thin the stroke lines are, smaller numbers means thinner outlines, bigger numbers mean thicker outlines.

Parameters:

new_weight: The size (in px) of the stroking line.

Example:
```
def draw():
    s.background((200, 200, 200))

    s.stroke_weight(1)
    s.line(0, 20, s.width, 20)

    s.stroke_weight(2)
    s.line(0, 40, s.width, 40)

    s.stroke_weight(4)
    s.line(0, 60, s.width, 60)

    s.stroke_weight(8)
    s.line(0, 80, s.width, 80)
```

![strokeweight](https://user-images.githubusercontent.com/88753590/233815088-a628b74a-5d95-4188-bcd0-14c96c4ac359.png)


### EduDraw.push() 

Toggles the temporary state on. All color, font and weight changes made while this mode is on will be reverted once it is left.

### EduDraw.pop()

Toggles the temporary state off.

Example:
```
    def draw():
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
```

![pushpop](https://user-images.githubusercontent.com/88753590/233815098-cd98f137-5065-4fb5-89e8-8606ac9637a3.png)

Example 2:
```
    def draw():
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
```

![pushpop2](https://user-images.githubusercontent.com/88753590/236652838-d6181f0e-9349-4437-bf7e-9cc1ae241e12.png)



### EduDraw.mouse_pos()-> tuple

Gets the current mouse position (relative to the top left corner of the canvas).
Returns a tuple with the X,Y position of the cursor.

Returns:

A tuple with the coordinates of the mouse relative to the canvas

Example 1:
```
def draw():
    s.background((200, 200, 200))

    mouse_x, mouse_y = s.mouse_pos()
    s.no_fill()

    if 75 <= mouse_x <= 150:
        if 75 <= mouse_y <= 150:
            s.fill((255, 255, 0))

    s.circle(mouse_x, mouse_y, 3)

    s.square(75, 75, 75)

    s.stroke((0, 255, 0))
    s.text(f"X: {mouse_x}", 10, 10)
    s.stroke((255, 0, 0))
    s.text(f"Y: {mouse_y}", 10, 30)
```

![mousepos](https://user-images.githubusercontent.com/88753590/233815197-3eb81842-bb44-4e51-95ad-f4e4ffe52be4.gif)

You can set whether this function should or not revert transformations to retrieve the perceived position by using
`EduDraw.set_account_for_transformations(True)`, the example below illustrates the difference:

Example 2:
```
    def draw():
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

        s.line(0, 0, account[0], account[1])
```

![mouseaccount](https://user-images.githubusercontent.com/88753590/236652900-93e10e80-1e5a-4c06-8db6-00b7f9afd7bd.gif)


### EduDraw.rotate(angle: int)

Rotates the drawing clockwise by the defined amount of degrees.
Note: Is cumulative with other rotations.

Parameters:

angle: The angle (in degrees) to rotate the drawing

Example:
```
def draw():
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
```

![rotation](https://user-images.githubusercontent.com/88753590/236652911-7dba1539-0b43-468c-a1ba-d707c20a8730.png)

Example 2:

```
def draw():
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
```

![advancedexample](https://user-images.githubusercontent.com/88753590/236653135-d38838d1-518c-4b70-a664-ea121cf71315.gif)



### EduDraw.scale(scale_x: float, scale_y: float) 

Scales the drawing's axis by the desired multipliers
Note: Is cumulative with other scalars.

Parameters:

scale_x: The multiplier to apply in the x axis
scale_y: The multiplier to apply in the y axis

Example:
```
 def draw():
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
```

![scale](https://user-images.githubusercontent.com/88753590/236652949-f882daf2-fba5-4cd4-8e62-5d418b3fbfee.png)


### EduDraw.translate(translate_x: int, translate_y: int)

Changes the origin of the plane of drawing.
Note: Is cumulative with other translations.

Parameters:

translate_x: The amount to translate in the x axis
translate_y: The amount to translate in the y axis

Example:
```
def draw():
    s.translate(0, 0)
    s.background((255, 255, 255))
    s.fill((125, 125, 125))
    s.square(50, 50, 50)

    s.translate(-50, 50)
    s.fill((200, 200, 0))
    s.square(50, 50, 50)
```

![translate](https://user-images.githubusercontent.com/88753590/236652958-1b89304d-9cb0-4104-9806-82dc0c8e9f3c.png)


### EduDraw.reset_transformations()

Resets all transformations applied.

### EduDraw.reset_scaling() 

Resets all scaling transformations applied.

### EduDraw.reset_translation() 

Resets all translation transformations applied.

### EduDraw.reset_rotation() 

Resets all rotation transformations applied.

### EduDraw.set_account_for_transformations(state: bool) 

Changes wether `mouse_pos()` should yield the real or perceived position of the mouse.

Parameters:

state: The state to apply to this setting. `True` yields the perceived position, whereas `False` (the default) yields the real position.

### EduDraw.set_controls(key_down=None, key_up=None, mouse_motion=None, mouse_button_up=None, mouse_button_down=None, mouse_wheel=None)

Sets functions to be ran on each specific Pygame event. `None` means that nothing will occur on those events.
Each function must have a parameter to receive a dictionary containing the data related to that event (such
as which key was pressed, where the mouse is, etc.)

Parameters:

key_down: The function to be ran when a key is pressed down

key_up: The function to be ran when a key is released

mouse_motion: The function to be ran when the mouse is moved

mouse_button_up: The function to be ran when a mouse button is released

mouse_button_down: The function to be ran when a mouse button is pressed

mouse_wheel: The function to be ran when the mouse wheel is scrolled
        
Example:

```
s = EduDraw(400, 400)

bg_color = (200, 200, 200)
text = ''

def setup():
    s.set_controls(mouse_button_down=do_stuff_on_click)

def draw():
    s.background(bg_color)
    s.text(text, s.width // 2, s.height // 2)

count = 0
def do_stuff_on_click(data: dict):
    global count, bg_color, text
    if count % 2 == 0:
        bg_color = (0, 0, 0)
        text = ''
    else:
        bg_color = (255, 255, 255)
        text = 'Clicked!'
    count += 1

s.start(setup, draw, 'Hello')
```

Example 2:

```
pos = 4
my_char = ''

def setup():
    s.set_controls(key_down=get_char)

def draw():
    s.stroke((255, 255, 255))
    s.scale(2, 2)
    s.text(my_char, pos, s.height // 4)

def get_char(data: dict):
    global my_char, pos
    my_char = data['unicode']
    pos += 5
```

![helloworld](https://user-images.githubusercontent.com/88753590/236653191-08dfcdd3-6c9b-47ec-bed0-da9866c821aa.gif)


## Drawing methods

These methods draw onto the canvas.

### EduDraw.point(x: int, y: int)

Draws a point at coordinates (x,y)

Parameters:

x, y: The x,y coordinates to draw the point onto.

### EduDraw.text(string: str, x: int, y: int)

Writes a string of text onto the screen.

Parameters:

string: The text to be written

x, y: The coordinates of the top-left corner of the text if rect_mode is 'TOP_LEFT' or the middle of the text is rect_mode is 'CENTER'.


### EduDraw.clear()

Clears the entire canvas and just leaves it's background.
Note: This method is somewhat costly.

### EduDraw.background(color: tuple, fast_mode: bool = True)

Sets a new background color and clears the canvas to it.

Parameters:

color: A tuple containing the (R, G, B) values of the desired color.

(Optional) fast_mode: Whether to use or not fast mode to draw the background. Fast mode simply draws a rectangle to fill the entire canvas, normal mode clears the entire image to a new one, which is more costly. It's only recommended you use normal mode if you are dealing with edges and can see outside of the background.

### EduDraw.circle(x: int, y: int, radius: int)

Draws a circle onto the screen.

Parameters:

x, y: The coordinates of the top-left part of the rectangle that contains the circle if circle_mode is 'TOP_LEFT', or the center of the circle if circle_mode is 'CENTER'.

r: The radius of the circle.

### EduDraw.ellipse(x: int, y: int, width: int, height: int)

Draws an ellipse onto the screen.

Parameters:

x, y: The coordinates of the top-left part of the rectange that contains the ellipse if circle_mode is 'TOP_LEFT', or the center of the ellipse if circle_mode is 'CENTER'.

w, h: The width and height of the rectangle that contains the ellipse.

Example:
```
def draw():
    s.background((200, 200, 200))

    s.stroke_weight(3)
    s.circle_mode('TOP_LEFT')

    s.fill((100, 100, 100))
    s.stroke((0, 0, 255))
    s.ellipse(62, 40, 45, 70)

    s.no_fill()
    s.stroke((255, 0, 0))
    s.ellipse(50, 50, 70, 30)
```

![ellipse](https://user-images.githubusercontent.com/88753590/233815202-95fc61d6-b328-4783-85ec-e5f7df4b153a.png)


### EduDraw.line(x1: int, y1: int, x2: int, y2: int)

Draws a line between two points.

Parameters:

x1, y1: The coordinates of the first point.

x2, y2: The coordinates of the second point.

Example:
```
def draw():
    s.background((200, 200, 200))
    s.stroke_weight(3)

    s.line(0, 0, s.width, s.height)
    s.stroke((0, 0, 255))
    s.line(0, s.height // 2, s.width, s.height // 2)
    s.stroke((255, 0, 0))
    s.line(200, 300, 400, 250)
```

![line](https://user-images.githubusercontent.com/88753590/233815204-d355aed5-f9e0-42f3-88b2-90feaf1bfe11.png)


### EduDraw.rect(x: int, y: int, width: int, height: int)

Draws a rectangle onto the screen.

Parameters:

x, y: The coordinates of the top-left corner of the rectangle if rect_mode is 'TOP_LEFT', or the center of the rectangle if rect_mode is 'CENTER'.

width, height: The width and height of the rectangle.

Example:
```
def draw():
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
```

![rect](https://user-images.githubusercontent.com/88753590/233815207-f7f8732b-88ae-4f17-92b7-16006b05237a.png)


### EduDraw.square(x: int, y: int, side_size: int)

Draws a square onto the screen.

Parameters:

x, y: The coordinates of the top-left corner of the square if rect_mode is 'TOP_LEFT', or the center of the square if rect_mode is 'CENTER'.

side_size: The size of the sides of the square.

Example:
```
def draw():
    s.background((255, 255, 255))

    s.no_stroke()
    s.fill((0, 0, 0))

    for i in range(0, s.width, 25):
        for j in range(0, s.height, 25):
            if ((i + j) % 2) == 0:
                s.square(i, j, 25)
```

![square](https://user-images.githubusercontent.com/88753590/233815209-c043af52-74ed-4b87-939f-39024043e458.png)


### EduDraw.triangle(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int)

Draws a triangle onto the screen.

Parameters:

x1,y1: The coordinates of the first vertex of the triangle.

x2,y2: The coordinates of the second vertex of the triangle.

x3,y3: The coordinates of the third vertex of the triangle.

Example:
```
def draw():
    s.background((200, 200, 200))

    s.fill((255, 255, 0))

    s.triangle(40, 40, 120, 40, 80, 120)
    s.triangle(120, 40, 200, 40, 160, 120)
    s.triangle(80, 120, 160, 120, 120, 200)
```

![triangle](https://user-images.githubusercontent.com/88753590/233815214-5f44f6b7-4d0a-41f8-88f8-3b384e1d117f.png)



### EduDraw.polygon(points: list)

Draws any polygon onto the screen.

Parameters:

points: An array containing tuples with all of the vertices of the polygon.

Example:
```
def draw():
    s.background((200, 200, 200))

    s.fill((100, 255, 255))
    points = [
        (50, 50),
        (100, 50),
        (120, 100),
        (75, 135),
        (30, 100)
    ]

    s.polygon(points)
```

![polygon](https://user-images.githubusercontent.com/88753590/233815221-2da1f919-571f-40a2-ad96-cb4e4084875b.png)


---

### EduDraw.image(img: PIL.Image, x: int, y: int, x2=None, y2=None) 

Draws an image onto the screen at the given position with a determined size. If no size is passed in, the image will have it's original size. This method is very costly depending on the resolution of the images used.

Parameters:

img: The image to be drawn onto the canvas.
    
x, y : The coordinates of the top left corner of the image.

(Optional) x2, y2: The coordinates of the bottom right corner of the image. If left by default (None), images will have their original size, else, they'll be scaled to fit onto the box generated by the two corners.

Examples:
```
img = PIL.Image.open("testimage.jpeg", 'r')

def draw():
    s.background((200, 200, 200))

    s.image(img, 50, 50, 450, 450)
```

![image](https://user-images.githubusercontent.com/88753590/233815229-cc8f4911-005d-44eb-92c3-eb2b4d4a3a16.png)

### EduDraw.image_sized(img: PIL.Image, x: int, y: int, width: int = None, height: int = None)
    
Displays an image onto the screen on the (x,y) position. If specified a width or height, the image will be resized to those sizes, otherwise, the image will be drawn to it's original size.
    
Parameters:

img: The image to be drawn onto the canvas
    
x, y: The position to draw the image
    
(Optional) width, height: The sizes to set the image to

### EduDraw.frame_rate(fps: int)

Changes the framerate of the simulation. Must be called in ```setup()```.
Note that in the Python version the simulation does not run as fast as the C# one, to run the simulation as fast as possible set the EduDraw.deltatime to zero.

Parameters:

int frames: The number of FPS to set the simulation to.


### EduDraw.save(filename: str)

Saves the current frame as an image file.
If filename is empty, the name will be the frame count of when the photo was saved.


### EduDraw.quit()

Quits the simulation.

### Null mode

Just like the C# version, you can use an instance of the EduDraw class without canvas to make a drawing inside of a drawing.
For more details, check the C# section about it.

Note, however, that due to the way Pygame screens work, the final window size will be that of the last instance declared, so in order for your main drawing to have it's intended size, make sure to declare it last.

Example:

```
# Good example
inner_drawing = EduDraw(300, 300)
main_drawing = EduDraw(600, 600)

# Screen created will have 600x600 size, as intended

# Bad example
inner_drawing_1 = EduDraw(200, 200)
main_drawing = EduDraw(600, 600)
inner_drawing_2 = EduDraw(300, 450)

# Screen created will have 300x450 size, while the main drawing was intended to have it's size as 600x600
```
