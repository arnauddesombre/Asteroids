# ---------------------------------------------------------------- #
#   Asteroids                                                      #
#   Developped by Arnaud Desombre (arnauddesombre@yahoo.com)       #
# ---------------------------------------------------------------- #
#   Open source ** PLEASE DISTRIBUTE ** and give credit when due   #
# ---------------------------------------------------------------- #
"""

Coursera project requirements:
https://class.coursera.org/interactivepython-002/human_grading/view/courses/970391/assessments/35/submissions
(all requirements are fully met and/or exceeded)

Additions:
* Handling of all explosions
* Rocks bounce off each other:
        - Elastic collision
        - The mass of each rock is proportional to its rate of rotation
        - The rocks spin faster as the score increases
* Ship pulls gravitationally on rocks:
        - Newtonian gravity. The trajectory of heavier (fast spinning) rocks is therefore more affected.
* To avoid the "death blossom" strategy of spinning in place and hammering the space bar, rocks will be thrown
  directly at the ship after a period of stillness, with increasing spin and velocity.
* Hyperspace:
        - Pressing 'H' puts the ship at the 'safest' place (cost points).

Play responsibly, and enjoy!!


Note: submitted entry for Coursera was:
http://www.codeskulptor.org/#user16_JQRgHi0SN7Djoym.py
This is a later update with anti-"death blossom" (with 'ship_stillness') and Olivier PIRSON's SimpleGUICS2Pygame addition.

The original source was developped during Coursera's course
"An Introduction to Interactive Programming in Python"
by Joe Warren, John Greiner, Stephen Wong, Scott Rixner

This version of the game can be played:
in Codeskulptor:     as is
locally with Python: create local .\_img\ and .\_snd\ directories for image and sound files
                     command line:  python -O -OO asteroids.py --stop-timers [--no-controlpanel]
                     use --no-controlpanel to remove the control panel from the left side of the canvas
                     (configuration buttons are accessible by keyboard (b -> bounce / m -> music / s -> sound))

"""
##################################################################

# replace CodeSkulptor's simplegui import with Olivier PIRSON's module, downloaded from:
# https://bitbucket.org/OPiMedia/simpleguics2pygame
# documentation:
# http://www.opimedia.be/DS/SimpleGUICS2Pygame/doc_html/
try:
    import simplegui
    www = True
except:
    import SimpleGUICS2Pygame.simpleguics2pygame as simplegui
    www = True

import math
import random

# declaration of global variables for user interface

# size of the canvas (can be changed, but the location for number of lives, score and help screen would not resize)
WIDTH  = 800
HEIGHT = 600

# initialize sound on/off defaults
sound_on = True
music_on = False

# rocks bounce off each other or not
# original Asteroids' mode was False, but True is much cooler (but slows down the game)
bounce_mode = True

# number of lives per game
MAX_LIVES = 3

# Security perimeter (in number of ship radius) around the ship
SHIP_SECURITY_PERIMETER = 5.0

# constants for ship / rocks / missiles
SHIP_ANGLE_INCREMENT = (2.0 * math.pi) / 54.0
SHIP_ACCELERATION = 0.2
SHIP_GRAVITY_PULL = 1500.0
SPACE_FRICTION = 0.04
VELOCITY_MAX_SHIP = 20.0

ROCK_MAX_NUMBER = 10
VELOCITY_MIN_ROCK = 0.5
VELOCITY_MAX_ROCK = 3.0
ROTATION_MAX_ROCK = 1.0
ROTATION_MIN_ROCK = 0.25

VELOCITY_MISSILE  = 4.0
# lifespan of missiles
# if the ship fires at rest, a missile disappears after travelling about 0.35 of the canvas width
MISSILE_LIFE = (0.35 * WIDTH) // VELOCITY_MISSILE
# number of allowed missile at one time (can actually be somehow redundant with MISSILE_LIFE)
MISSILE_MAX_NUMBER = 10

# 1: game not started / 2: game in play (normal) / 3: game paused / 4: game over
game_in_play = 1

# declare all other global variables
score = 0
lives = 0
time = 0
ship_stillness = 0.0
rock_group = set()
missile_group = set()
explosion_group = set()
text_group = set()
# 'my_ship' global variable is declared after the 'Class ship():' declaration

##################################################################

# Hyperspace grid:
# define elementary cell for hyperspace (no need to make it much smaller than the ship)
hyper_cell = [40, 40]
# define grid
HYPER_GRID = []
for i in range(0, WIDTH // hyper_cell[0]):
    for j in range(0, HEIGHT // hyper_cell[1]):
        HYPER_GRID += [(hyper_cell[0] * (i + 1/2),
                        hyper_cell[1] * (j + 1/2))]

##################################################################


# Image class
class ImageInfo:
    def __init__(self, center, size, radius = 0, lifespan = None, animated = False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated
        return

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated

##################################################################

# Art assets created by Kim Lathrop
# may be freely re-used in non-commercial projects, please credit Kim

# SimpleGUICS2Pygame requirement:
# local images or sounds (.ogg format) must be placed .\_img\ and .\_snd\ directories

# debris images - debris1_brown.png, debris2_brown.png, debris3_brown.png, debris4_brown.png
#                 debris1_blue.png, debris2_blue.png, debris3_blue.png, debris4_blue.png, debris_blend.png
debris_info = ImageInfo([320, 240], [640, 480])
if www:
    debris_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/debris2_blue.png")
else:
    debris_image = simplegui.load_image("_img\debris2_blue.png")

# nebula images - nebula_brown.png, nebula_blue.png
nebula_info = ImageInfo([400, 300], [800, 600])
if www:
    nebula_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/nebula_blue.png")
else:
    nebula_image = simplegui.load_image("_img\nebula_blue.png")

# ship image
ship_info = ImageInfo([45, 45], [90, 90], 35)
if www:
    ship_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/double_ship.png")
else:
    ship_image = simplegui.load_image("_img\double_ship.png")

# missile image - shot1.png, shot2.png, shot3.png
# Note that these images have different sizes:
# missile_info = ImageInfo([5,5],   [10, 10], 3, life) for shot1.png and shot2.png
# missile_info = ImageInfo([10,10], [20, 20], 3, life) for shot3.png
missile_info = ImageInfo([10, 10], [20, 20], 3, MISSILE_LIFE)
if www:
    missile_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/shot3.png")
else:
    missile_image = simplegui.load_image("_img\shot3.png")

# asteroid images - asteroid_blue.png, asteroid_brown.png, asteroid_blend.png
asteroid_info = ImageInfo([45, 45], [90, 90], 40)
if www:
    asteroid_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/asteroid_blue.png")
else:
    asteroid_image = simplegui.load_image("_img\asteroid_blue.png")

# animated explosion - explosion_orange.png, explosion_blue.png, explosion_blue2.png, explosion_alpha.png
explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
if www:
    explosion_image1 = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/explosion_alpha.png")
    explosion_image2 = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/explosion_orange.png")
else:
    explosion_image1 = simplegui.load_image("_img\explosion_alpha.png")
    explosion_image2 = simplegui.load_image("_img\explosion_orange.png")

# sound assets purchased from sounddogs.com
# please do not redistribute!
if www:
    soundtrack = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/soundtrack.ogg")
    missile_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/missile.ogg")
    ship_thrust_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/thrust.ogg")
    explosion_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/explosion.ogg")
else:
    soundtrack = simplegui.load_sound("_snd\soundtrack.ogg")
    missile_sound = simplegui.load_sound("_snd\missile.ogg")
    ship_thrust_sound = simplegui.load_sound("_snd\thrust.ogg")
    explosion_sound = simplegui.load_sound("_snd\explosion.ogg")

missile_sound.set_volume(.5)

##################################################################

def angle_to_vector(ang):
    # transformation angle (in radian) -> vector ([x,y])
    return [math.cos(ang), math.sin(ang)]

def dist_squared(p, q):
    # distance between 2 points p and q squared
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

def dist(p, q, curved_space = True):
    # distance between 2 points p and q
    if curved_space:
        # opposites side of the canvas are actually connected
        # and this 'dist' calculation takes this into account
        return min(math.sqrt((p[0] - q[0]) ** 2              + (p[1] - q[1]) ** 2),
                   math.sqrt((WIDTH - abs(p[0] - q[0])) ** 2 + (p[1] - q[1]) ** 2),
                   math.sqrt((p[0] - q[0]) ** 2              + (HEIGHT - abs(p[1] - q[1])) ** 2),
                   math.sqrt((WIDTH - abs(p[0] - q[0])) ** 2 + (HEIGHT - abs(p[1] - q[1])) ** 2))
    else:
        # return simple (Euclidian) distance
        # (this is only used for missile/rock distance calculation for collision)
        return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

def norm(p):
    # return the norm of vector p
    return math.sqrt(p[0] ** 2 + p[1] ** 2)

def sign(x):
    # return the sign of x
    if x > 0:
        return  1
    elif x < 0:
        return -1
    else:
        return  0

##################################################################

# Ship class
class Ship:
    def __init__(self, pos, vel, angle, image, info):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = 0.0
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        return

    def draw(self, canvas):
        if self.thrust:
            # thrust => use second image (with thrust flames)
            center = (self.image_center[0] + self.image_size[0], self.image_center[1])
        else:
            # no thrust => use first image (without thrust flames)
            center = (self.image_center[0], self.image_center[1])
        canvas.draw_image(self.image, center, self.image_size, self.pos, self.image_size, self.angle)
        if self.thrust and sound_on:
            ship_thrust_sound.play()
        else:
            ship_thrust_sound.pause()
            ship_thrust_sound.rewind()
        return

    def update(self):
        self.angle += self.angle_vel
        if self.thrust:
            # manage acceleration
            vect = angle_to_vector(self.angle)
            self.vel[0] += SHIP_ACCELERATION * vect[0]
            self.vel[1] += SHIP_ACCELERATION * vect[1]
            # respect speed limit for ship
            if self.get_speed() > VELOCITY_MAX_SHIP:
                self.vel[0] = VELOCITY_MAX_SHIP * vect[0]
                self.vel[1] = VELOCITY_MAX_SHIP * vect[1]
        else:
            # deceleration through friction
            self.vel[0] *= (1.0 - SPACE_FRICTION)
            self.vel[1] *= (1.0 - SPACE_FRICTION)
        # update position + remain within canvas (modulo WIDTH and HEIGHT)
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT
        return

    def get_speed(self):
        # returns speed of ship
        return norm(self.vel)

    def get_angle(self):
        # returns angle of ship
        return self.angle

    def get_position(self):
        # return position of ship
        return self.pos

    def get_radius(self):
        # return radius of ship
        return self.radius

    def get_mass(self):
        # return mass of ship (for consistancy only, mass of the ship is irrelevant but cannot be zero)
        return 1.0

    def shoot(self):
        # shoot one missile from ship
        global missile_group
        vect = angle_to_vector(self.angle)
        # initial position is: top of the ship
        pos = (self.pos[0] + self.radius * vect[0],
               self.pos[1] + self.radius * vect[1])
        # initial velocity is: speed of ship + VELOCITY_MISSILE + bonus for speed of ship
        # Note: the ship is not necessarily oriented in the direction of its speed
        bonus = 1.0 + 1.5 * self.get_speed() / VELOCITY_MAX_SHIP
        vel = (self.vel[0] + VELOCITY_MISSILE * vect[0] * bonus,
               self.vel[1] + VELOCITY_MISSILE * vect[1] * bonus)
        # angle: is the same as the ship
        vect = angle_to_vector(self.angle)
        a_missile = Sprite(pos, vel, 0.0, self.angle, 0.0, missile_image, missile_info, missile_sound)
        missile_group.add(a_missile)
        return

# declare global variable 'my_ship'
my_ship = Ship([WIDTH // 2, HEIGHT // 2], [0, 0], -math.pi / 2.0, ship_image, ship_info)


##################################################################
# Sprite class
class Sprite:
    def __init__(self, pos, vel, mass, ang, ang_vel, image, info, sound = None):
        self.pos = [pos[0], pos[1]]
        self.vel = [vel[0], vel[1]]
        self.mass = mass
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound and sound_on:
            sound.rewind()
            sound.play()
        return

    def get_position(self):
        # return position of sprite
        return self.pos

    def get_mass(self):
        # return mass of sprite
        return self.mass

    def get_velocity(self):
        # return velocity of sprite
        return self.vel

    def get_radius(self):
        # return radius of sprite
        return self.radius

    def collide(self, other_object):
        # return True if self and other_object collide
        if self.mass == 0.0 or other_object.get_mass() == 0.0:
            # use euclidian distance if one of the object is a missile (for quicker calculation)
            # missiles are the only Sprite with zero mass
            return (dist(self.get_position(), other_object.get_position(), False) <= self.get_radius() + other_object.get_radius())
        else:
            return (dist(self.get_position(), other_object.get_position())        <= self.get_radius() + other_object.get_radius())

    def draw(self, canvas):
        self.age += 1
        canvas.draw_image(self.image, self.image_center, self.image_size, self.pos, self.image_size, self.angle)
        return

    def is_dead(self):
        return (self.age > self.lifespan)

    def update(self):
        # update angle
        self.angle += self.angle_vel
        # update speed: if mass != 0, Sprite is gravitationally attracted to the ship
        if self.get_mass() > 0.0:
            # define a normalized vector self -> my_ship
            vect = (my_ship.get_position()[0] - self.pos[0],
                    my_ship.get_position()[1] - self.pos[1])
            n = norm(vect)
            vect = (vect[0] / n, vect[1] / n)
            # calculate Newtonian gravity
            gravity_pull = SHIP_GRAVITY_PULL * self.mass / dist_squared(my_ship.get_position(), self.get_position())
            self.vel[0] += vect[0] * gravity_pull
            self.vel[1] += vect[1] * gravity_pull
        # update position + remain within canvas
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT
        return

##################################################################


# Explosion class
# NOTE: The draw method of this class contains '.remove()'

class Explosion:
    def __init__(self, pos, scale, image, info, sound = None):
        self.pos = [pos[0], pos[1]]
        self.age = 0
        self.scale = scale
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound and sound_on:
            sound.rewind()
            sound.play()
        return

    def draw(self, canvas):
        global explosion_group
        center = (self.image_center[0] + self.age * self.image_size[0], self.image_center[1])
        output = [self.image_size[0] * self.scale, self.image_size[1] * self.scale]
        canvas.draw_image(self.image, center, self.image_size, self.pos, output, 0)
        self.age += 1
        if self.age > self.lifespan:
            explosion_group.remove(self)
        return

##################################################################


# Text class (write temporary information on the screen)
# NOTE: the draw method of this class contains '.remove()'

class Text:
    def __init__(self, text, line, lifespan):
        self.text = text
        self.y = line
        self.age = 0
        self.lifespan = lifespan
        return

    def draw(self, canvas):
        global text_group
        message_size = frame.get_canvas_textwidth(self.text, 40)
        canvas.draw_text(self.text, ((WIDTH - message_size) // 2, self.y), 40, "Red")
        self.age += 1
        if self.age > self.lifespan:
            text_group.remove(self)
        return

##################################################################


# button managed functions

def music_handler(flag = 1):
    # toggle background music on/off
    global music_on
    if flag == 1:
        music_on = not music_on
    if music_on:
        music_button.set_text("[m]usic = ON")
        soundtrack.rewind()
        soundtrack.play()
    else:
        music_button.set_text("[m]usic = OFF")
        soundtrack.pause()
    return

def sound_handler(flag = 1):
    # toggle sound on/off
    global sound_on
    if flag == 1:
        sound_on = not sound_on
    if sound_on:
        sound_button.set_text("[s]ound = ON")
    else:
        sound_button.set_text("[s]ound = OFF")
    return

def bounce_handler(flag = 1):
    # toggle bounce mode true/false
    global bounce_mode
    if flag == 1:
        bounce_mode = not bounce_mode
    if bounce_mode:
        bounce_button.set_text("[b]ounce = ON")
    else:
        bounce_button.set_text("[b]ounce = OFF")
    return

##################################################################

# helper functions for keyboard managed functions

def fire_missile(flag):
    if flag == 1:
        if len(missile_group) < MISSILE_MAX_NUMBER:
            my_ship.shoot()
    return

def ship_thrust(flag):
    my_ship.thrust = (flag == 1)
    return

def ship_rotate_left(flag):
    ship_rotate(flag, -1)
    return

def ship_rotate_right(flag):
    ship_rotate(flag, 1)
    return

def ship_rotate(flag, direction):
    # flag == 1 -> rotate the ship: direction ==  1 -> right
    #                               direction == -1 -> left
    # flag == 0 -> stop rotation if the ship was turning in the relevant direction
    # for example: Left Down / Right Down / Left Up -> does not stop rotation
    if flag == 1:
        # key down
        my_ship.angle_vel = direction * SHIP_ANGLE_INCREMENT
    else:
        # key up
        if sign(my_ship.angle_vel) == direction:
            my_ship.angle_vel = 0
    return

def hyperspace(flag):
    global score
    if flag == 1:
        if score < 100:
            text_group.add(Text("NO CREDIT FOR HYPERSPACE", 70, 30))
        else:
            # put the ship outside of the screen (so it cannot be destroyed during calculation)
            old_pos = my_ship.pos
            my_ship.pos = [WIDTH + my_ship.get_radius() + 1, HEIGHT + my_ship.get_radius() + 1]
            # calculate the distance of all the HYPER_GRID points to their respective nearest rock
            distance_to_rock = []
            for i in range(0, len(HYPER_GRID)):
                d_min = float('inf')
                for rock in list(rock_group):
                    d = dist(HYPER_GRID[i], rock.get_position())
                    if d < d_min:
                        d_min = d
                distance_to_rock.append(d_min)
            # calculate point within HYPER_GRID further from all the rocks
            d_max = 0.0
            hyper_point = -1
            for i in range(0, len(distance_to_rock)):
                if distance_to_rock[i] > d_max:
                    d_max = distance_to_rock[i]
                    hyper_point = i
            # hyper_point is the index in HYPER_GRID where the ship will emerge
            if dist(HYPER_GRID[hyper_point], my_ship.get_position()) < (SHIP_SECURITY_PERIMETER / 2.0) * my_ship.get_radius():
                text_group.add(Text("POSITION CANNOT BE IMPROVED", 70, 30))
                my_ship.pos = old_pos
            else:
                text_group.add(Text("** HYPERSPACE **", 70, 30))
                my_ship.pos[0] = HYPER_GRID[hyper_point][0]
                my_ship.pos[1] = HYPER_GRID[hyper_point][1]
                my_ship.vel[0] = 0.0
                my_ship.vel[1] = 0.0
                my_ship.angle = -math.pi / 2.0
                clean_area_around_ship()
                score -= 100
                if sound_on:
                    # insert 'hyperspace sound' sound here...
                    pass
    return

# keyboard functions

key_inputs = {"space": fire_missile,
              "up":    ship_thrust,
              "left":  ship_rotate_left,
              "right": ship_rotate_right,
              "h":     hyperspace,
              "b":     bounce_handler,
              "m":     music_handler,
              "s":     sound_handler}

def key_down_handler(key):
    global game_in_play
    exception = False
    if game_in_play == 4:
        if key == 13:  # <Enter> key
            game_init()
            game_in_play = 2
    elif game_in_play != 2:
        # the game is resumed from non play status on any key except b, m, s (configuration button)
        if key != simplegui.KEY_MAP["b"] and key != simplegui.KEY_MAP["m"] and key != simplegui.KEY_MAP["s"]:
            game_in_play = 2
        else:
            exception = True
    elif key == 27:    # <Esc> key
        game_in_play = 3
    # No 'else:' used here, so that the key pressed
    # to un-pause the game is handled immediately...
    if game_in_play == 2 or exception:
        for i in key_inputs:
            if key == simplegui.KEY_MAP[i]:
                key_inputs[i](1)
    return

def key_up_handler(key):
    for i in key_inputs:
        if key == simplegui.KEY_MAP[i]:
            key_inputs[i](0)
    return

##################################################################

def game_init():
    # initialize variables for a new game
    global score, lives, time, ship_stillness, my_ship, rock_group, missile_group, explosion_group, text_group
    score = 0
    lives = MAX_LIVES
    time = 0
    ship_stillness = 0.0
    if music_on:
        soundtrack.rewind()
        soundtrack.play()
    # initialize ship
    my_ship = Ship([WIDTH // 2, HEIGHT // 2], [0, 0], -math.pi / 2.0, ship_image, ship_info)
    # initialize rock set
    rock_group = set()
    # initialize missile set
    missile_group = set()
    # initialize explosion set
    explosion_group = set()
    # initialiaze text set
    text_group = set()
    return

def update_score(increase_score):
    # update scores, and add 1 life every 2.000 points
    global score, lives
    old_score = score
    score += increase_score
    if (old_score // 2000) != (score // 2000):
        # x2.000 points crossed!
        lives += 1
        text_group.add(Text("** EXTRA LIFE! **", 110, 30))
    return

def rock_spawner():
    # timer handler that spawns a rock
    # this function is called every 1 second and is used to increase the score due to survival rate
    global rock_group, ship_stillness
    if game_in_play == 2:
        # increase score from +1 (at speed = 0) to +10 (at speed = VELOCITY_MAX_SHIP)
        speed_ratio = 9.0 * my_ship.get_speed() / VELOCITY_MAX_SHIP
        update_score(1 + round(speed_ratio))
        # update ship stillness
        if speed_ratio >= 2.0:
            ship_stillness = 0.0
        elif speed_ratio >= 1.0:
            if ship_stillness < 15.0:
                ship_stillness += 0.5
            else:
                ship_stillness -= 1.0
        else:
            ship_stillness += 1.0
    if len(rock_group) < ROCK_MAX_NUMBER and game_in_play == 2:
        # generate a rock (from a random side of the canvas only / never from the middle)
        overlap = True
        while overlap:
            # rules for ship_stillness penalty:
            #  0 to 15 = nothing
            # 15 to 25 = rock spawn towards ship
            # 25 to 35 = rock spawn towards ship from behind
            # 35 to 45 = rock spawn towards ship from behind + at increased spin
            # 45 to 60 = rock spawn towards ship from behind + at increased spin + at maximum velocity
            # above 60 = rock spawn towards ship from behind + at maximum spin   + at maximum velocity
            #
            # random speed between VELOCITY_MIN_ROCK and VELOCITY_MAX_ROCK
            if ship_stillness > 45.0:
                velocity = VELOCITY_MAX_ROCK
            else:
                velocity = VELOCITY_MIN_ROCK + random.random() * (VELOCITY_MAX_ROCK - VELOCITY_MIN_ROCK)
            if ship_stillness > 25.0:
                angle = my_ship.get_angle() % (2.0 * math.pi)
                if math.pi / 4.0 <= angle <= 3.0 * math.pi / 4.0:
                    center = (random.randint(0, WIDTH - 1), 0)
                elif 3.0 * math.pi / 4.0 <= angle <= 5.0 * math.pi / 4.0:
                    center = (WIDTH - 1, random.randint(0, HEIGHT - 1))
                elif 5.0 * math.pi / 4.0 <= angle <= 7.0 * math.pi / 4.0:
                    center = (random.randint(0, WIDTH - 1), HEIGHT - 1)
                else:
                    center = (0, random.randint(0, HEIGHT - 1))
            else:
                if random.choice([0, 1]) == 0:
                    center = (0, random.randint(0, HEIGHT - 1))
                else:
                    center = (random.randint(0, WIDTH - 1), 0)
            # random trajectory angle between 0 and 2 * PI
            # though generated on left or top side, the rock can enter from right or bottom side, depending on angle:
            # also, adjust angle to target ship after 15 seconds of stillness
            if ship_stillness > 15.0:
                s = my_ship.get_position()
                angle = (s[0] - center[0], s[1] - center[1])
                n = norm(angle)
                angle = (angle[0] / n, angle[1] / n)
            else:
                angle = angle_to_vector(random.random() * 2.0 * math.pi)
            velocity_vect = (angle[0] * velocity, angle[1] * velocity)
            # random rotation between ROTATION_MIN_ROCK and ROTATION_MAX_ROCK turns per
            # second, increasing with the score (min = +15% every 5.000 points / max = +30%)
            spin_min = ROTATION_MIN_ROCK * (1.0 + 0.15 * (score / 5000.0))
            spin_max = ROTATION_MAX_ROCK * (1.0 + 0.30 * (score / 5000.0))
            if ship_stillness > 60.0:
                spin_min = spin_max
            elif ship_stillness > 35.0:
                spin_min = (spin_max + spin_min) / 2.0
            rotation = random.choice([-1, 1]) * (spin_min + random.random() * (spin_max - spin_min)) * (2.0 * math.pi / 60.0)
            # mass of rock is proportional to its spin rate
            mass = abs(rotation)
            new_rock = Sprite(center, velocity_vect, mass, 0.0, rotation, asteroid_image, asteroid_info)
            # Overlap rules for rock generation:
            # a new rock cannot be too close from the ship (not within SHIP_SECURITY_PERIMETER ship radius)
            # a new rock cannot overlap an existing rock if bounce_mode == True
            overlap = False
            if dist(new_rock.get_position(), my_ship.get_position()) <= SHIP_SECURITY_PERIMETER * my_ship.get_radius():
                overlap = True
            if bounce_mode and not overlap:
                for rock in list(rock_group):
                    if new_rock.collide(rock):
                        overlap = True
                        break
        rock_group.add(new_rock)
    return

def bounce_rock(m1, v1, m2, v2):
    # elastic collision between:
    # rock #1: mass m1 (float) and speed v1 (tuple (v_x, v_y))
    # rock #2: mass m1 (float) and speed v2 (tuple (v_x, v_y))

    # some math and comments for elastic collision equations can be found at:
    # http://batesvilleinschools.com/physics/apphynet/Dynamics/Collisions/elastic_deriv.htm

    # Ref2 is the referential where ball #2 is fixed before the collision
    v1_ref2 = (v1[0] - v2[0], v1[1] - v2[1])

    # after choc, in Ref2
    v1_after_ref2 = (((m1 - m2) / (m1 + m2)) * v1_ref2[0],
                     ((m1 - m2) / (m1 + m2)) * v1_ref2[1])
    v2_after_ref2 = (2.0 * m1 / (m1 + m2) * v1_ref2[0],
                     2.0 * m1 / (m1 + m2) * v1_ref2[1])

    # back to initial referential
    v1_after = (v1_after_ref2[0] + v2[0],
                v1_after_ref2[1] + v2[1])
    v2_after = (v2_after_ref2[0] + v2[0],
                v2_after_ref2[1] + v2[1])

    return (v1_after, v2_after)

def group_collide(group, sprite):
    # test for collision between all members of 'group' (group of sprites) vs. 'sprite' (one sprite)
    g = set()
    num_collision = 0
    for member in list(group):
        if member.collide(sprite):
            num_collision += 1
            g.add(member)
            # explosion is centered on 'member' (not 'sprite')
            new_explosion = Explosion(member.get_position(), 1, explosion_image1, explosion_info, explosion_sound)
            explosion_group.add(new_explosion)
    group.difference_update(g)
    return num_collision

def group_group_collide(group1, group2):
    # test for collision between all members of 'group1' (group of sprites) vs. 'group2' (group of sprites)
    # group1 -> missiles
    # group2 -> rocks
    g1 = set()
    num_collision = 0
    for member1 in list(group1):
        n = group_collide(group2, member1)
        if n > 0:
            g1.add(member1)
            num_collision += n
    group1.difference_update(g1)
    return num_collision

def clean_area_around_ship():
    # eliminate all rocks whithin SHIP_SECURITY_PERIMETER radius of the ship
    # (no points added to score)
    global rock_group
    for rock in list(rock_group):
        if dist(rock.get_position(), my_ship.get_position()) <= SHIP_SECURITY_PERIMETER * my_ship.get_radius():
            # the rocks within ship perimeter explode with a different explosion (scaled 30%) image & no sound & no score
            new_explosion = Explosion(rock.get_position(), 0.30, explosion_image2, explosion_info)
            explosion_group.add(new_explosion)
            rock_group.remove(rock)
    return

##################################################################

# update canvas

def help_display(canvas, offset):
    # help screen (display)

    if offset == 2:
        color = "Black"
        color_special = color
    elif offset == 1:
        color = "Blue"
        color_special = "White"
    else:
        color = "White"
        color_special = "Red"

    canvas.draw_text("<Left arrow>",  (50+offset, 130+offset), 40, color)
    canvas.draw_text("<Right arrow>", (50+offset, 180+offset), 40, color)
    canvas.draw_text("<Up arrow>",    (50+offset, 230+offset), 40, color)
    canvas.draw_text("<Space bar>",   (50+offset, 280+offset), 40, color)
    canvas.draw_text("<Esc>",         (50+offset, 330+offset), 40, color)
    canvas.draw_text("<H>",           (50+offset, 380+offset), 40, color)

    canvas.draw_text("turn ship counter-clockwise", (325+offset, 130+offset), 40, color)
    canvas.draw_text("turn ship clockwise",         (325+offset, 180+offset), 40, color)
    canvas.draw_text("accelerate ship forward",     (325+offset, 230+offset), 40, color)
    canvas.draw_text("fire missile",                (325+offset, 280+offset), 40, color)
    canvas.draw_text("pause game",                  (325+offset, 330+offset), 40, color)
    canvas.draw_text("hyperspace",                  (325+offset, 380+offset), 40, color)

    canvas.draw_text("(Transport & stop ship in a 'safer' place. Cost 100 points)", (325+offset, 410+offset), 20, color)

    # bounce message from left to right of the canvas
    if game_in_play == 1:
        message = "welcome to Asteroids!"
    elif game_in_play == 4:
        message = "game over!"
    else:
        message = "== game paused =="
    pos1 = (WIDTH - frame.get_canvas_textwidth(message, 40))
    pos2 = time % pos1
    if (time // pos1) % 2 == 0:
        pos = pos2
    else:
        pos = pos1 - pos2
    canvas.draw_text(message, (pos+offset, 70+offset), 40, color_special)

    if game_in_play == 1:
        canvas.draw_text("== Press any key to start the game ==",   (100+offset, 460+offset), 40, color_special)
    elif game_in_play == 4:
        canvas.draw_text("== Press [Enter] to start a new game ==", ( 90+offset, 460+offset), 40, color_special)
    else:
        canvas.draw_text("== Press any key to resume the game ==",  ( 95+offset, 460+offset), 40, color_special)

    canvas.draw_text("Each rock destroyed = +50 points", (95+offset, 500+offset), 20, color)
    canvas.draw_text("Survival bonus = from +1 (at low speed) to +10 points (at high speed) per second", (95+offset, 525+offset), 20, color)
    canvas.draw_text("Extra life every 2,000 points!", (95+offset, 550+offset), 20, color)

    canvas.draw_text("Heavier rocks spin faster - Rotation increases with time - The ship exerts gravitational pull", (40+offset, 580+offset), 20, color)

    return

def process_sprite_group(canvas, group, update):
    # update and draw each sprite in the group
    dead = set()
    for sprite in list(group):
        if update:
            sprite.update()
            if sprite.is_dead():
                dead.add(sprite)
        sprite.draw(canvas)
    group.difference_update(dead)
    return

def process_rock_collision(group):
    # handle collision rock-rock
    g = list(group)
    for rock1 in range(0, len(g)):
        for rock2 in range(rock1+1, len(g)):
            if g[rock1].collide(g[rock2]):
                # elastic collision between rock1 & rock2. Because mass1 != mass 2, after the collision
                # the speed of 1 rock may be over VELOCITY_MAX_ROCK. This is intentionally not adjusted!
                new_vel = bounce_rock(g[rock1].get_mass(), g[rock1].get_velocity(), g[rock2].get_mass(), g[rock2].get_velocity())
                g[rock1].vel[0], g[rock1].vel[1] = new_vel[0][0], new_vel[0][1]
                g[rock2].vel[0], g[rock2].vel[1] = new_vel[1][0], new_vel[1][1]
                if sound_on:
                    # insert 'rock bouncing off one another' sound here...
                    pass

def process_explosion(canvas):
    # display explosions
    for explosion in list(explosion_group):
        explosion.draw(canvas)
    return

def process_text(canvas):
    # display text
    for text in list(text_group):
        text.draw(canvas)
    return

def help(canvas):
    # help screen / text is shaded in different colors for 3D illusion
    # display text 1st shade (black)
    help_display(canvas, 2)
    # display text 2nd shade (blue)
    help_display(canvas, 1)
    # display text 3rd shade (white)
    help_display(canvas, 0)
    return

def draw(canvas):
    global time, lives, game_in_play, ship_stillness

    # animate background
    time += 1
    center = debris_info.get_center()
    size = debris_info.get_size()
    wtime = (time / 8.0) % center[0]
    canvas.draw_image(nebula_image, nebula_info.get_center(), nebula_info.get_size(), [WIDTH // 2, HEIGHT // 2], [WIDTH, HEIGHT])
    canvas.draw_image(debris_image, [center[0] - wtime, center[1]], [size[0] - 2 * wtime, size[1]],
                                [WIDTH / 2 + 1.25 * wtime, HEIGHT // 2], [WIDTH - 2.5 * wtime, HEIGHT])
    canvas.draw_image(debris_image, [size[0] - wtime, center[1]], [2 * wtime, size[1]],
                                [1.25 * wtime, HEIGHT // 2], [2.5 * wtime, HEIGHT])

    if game_in_play != 2:

        # draw ship and sprites (game is not in play -> not started or paused)
        process_sprite_group(canvas, rock_group, False)
        process_sprite_group(canvas, missile_group, False)
        process_explosion(canvas)
        my_ship.draw(canvas)
        help(canvas)

    elif lives < 0:

        # game has ended ('Live = 0' has been played => lives = -1)
        game_in_play = 4
        process_sprite_group(canvas, rock_group, False)
        process_sprite_group(canvas, missile_group, False)
        process_explosion(canvas)
        my_ship.draw(canvas)
        help(canvas)

    else:

        # draw ship and sprites (game is in play -> normal mode)

        # process rocks
        process_sprite_group(canvas, rock_group, True)
        # handle rock collisions
        if bounce_mode:
            process_rock_collision(rock_group)

        # process missiles
        process_sprite_group(canvas, missile_group, True)

        # update ship
        my_ship.update()
        my_ship.draw(canvas)

        # check if the ship has hit a rock
        if group_collide(rock_group, my_ship) > 0:
            # the ship explodes with a large explosion (scaled 4x) image & no sound
            new_explosion = Explosion(my_ship.get_position(), 4, explosion_image1, explosion_info)
            explosion_group.add(new_explosion)
            clean_area_around_ship()
            # stop ship
            my_ship.vel = [0.0, 0.0]
            if sound_on:
                explosion_sound.rewind()
                explosion_sound.play()
            # lose 1 life but score 50 points...
            lives -= 1
            ship_stillness = 0.0
            update_score(50)
            # indicative display (0.5 second)
            text_group.add(Text("** SHIP DESTROYED! **", 150, 30))

        # check if a missile has hit a rock
        hit = group_group_collide(missile_group, rock_group)
        update_score(50 * hit)

        # explosions
        process_explosion(canvas)

    # display informational text
    process_text(canvas)

    # display number of lives (number & visual information), score, and ship stillness light
    if lives == 1:
        message_lives = "1 life"
    else:
        message_lives = str(max(lives, 0)) + " lives"
    canvas.draw_text(message_lives, (10, 25), 25, "White")

    for i in range(0, lives):
        canvas.draw_image(ship_image, ship_info.get_center(), ship_info.get_size(), [95 + i*25, 20], [30, 30], -math.pi/2)

    message_score = "Score:  " + str(int(score)) + "  "
    message_size = frame.get_canvas_textwidth(message_score, 25)
    canvas.draw_text(message_score, (WIDTH - 10 - message_size, 25), 25, "White")

    if ship_stillness >= 40.0:
        r = 255
        g = 0
        if ship_stillness % 2 == 1:
            # makes light blink each second
            r = -1
    else:
        # creates a gradient color from green to red
        if ship_stillness < 20:
            r = int((255 * ship_stillness) / 20)
            g = 255
        else:
            r = 255
            g = int((255 * (40 - ship_stillness)) / 20)
    if r >= 0:
        color = "rgb(" + str(r) + ", " + str(g) + ", 0)"
        canvas.draw_circle((WIDTH - 10, 16), 5, 1, color, color)

    return

##################################################################

# initialize frame
frame = simplegui.create_frame("Asteroids", WIDTH, HEIGHT)
if sound_on:
    soundtrack.rewind
    soundtrack.play()

# register handlers
frame.set_draw_handler(draw)
frame.set_keydown_handler(key_down_handler)
frame.set_keyup_handler(key_up_handler)
frame.set_draw_handler(draw)

music_button = frame.add_button("", music_handler, 125)
music_on = not music_on
music_handler()

sound_button = frame.add_button("", sound_handler, 125)
sound_on = not sound_on
sound_handler()

bounce_button = frame.add_button("", bounce_handler, 125)
bounce_mode = not bounce_mode
bounce_handler()

# initialize timer rock_spawner() every 1 second
timer = simplegui.create_timer(1000.0, rock_spawner)

# get things rolling
game_init()
timer.start()
frame.start()
