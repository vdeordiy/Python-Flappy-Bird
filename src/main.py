import pygame
from pygame.locals import *
import os
from enum import IntEnum, auto
import itertools
import random


def load_image(name):
    return pygame.image.load(os.path.join(os.path.dirname(__file__), 'images', name))


def load_sound(name):
    return pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), 'sounds', name))


def load_font(name, size):
    return pygame.font.Font(os.path.join(os.path.dirname(__file__), 'fonts', name), size)


class Layer(IntEnum):
    BACKGROUND = auto()
    OBSTACLE = auto()
    GROUND = auto()
    BIRD = auto()
    UI = auto()


class State(IntEnum):
    IDLE = auto()
    FLYING = auto()
    DEAD = auto()


class Event:
    BIRD_ANIMATION = pygame.event.custom_type()
    OBSTACLE_GENERATION = pygame.event.custom_type()
    GAME_OVER = pygame.event.custom_type()
    RESET = pygame.event.custom_type()


class Background(pygame.sprite.Sprite):
    def __init__(self, layer, image: pygame.Surface, topleft, speed):
        super().__init__()
        self._layer = layer
        self.image = image
        self.rect = image.get_rect(topleft=topleft)
        self.speed = speed

    def update(self):
        # Scrolling background effect
        if self.rect.right <= 0:
            self.rect.left = game_width

        if bird.state != State.DEAD:
            self.rect.x -= self.speed


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self._layer = Layer.BIRD
        self.frame: pygame.Surface = next(bird_animation_frames)
        self.image = self.frame.copy()
        self.rect = self.image.get_rect(center=(40, game_height/2))
        self.mask = pygame.mask.from_surface(self.image)
        self.state = State.IDLE
        self.gravity = 0.5
        self.speed = 0

    def animate(self):
        if self.state != State.DEAD:
            self.frame: pygame.Surface = next(bird_animation_frames)

    def update(self):
        self.image = self.frame.copy()
        self.mask = pygame.mask.from_surface(self.image)

        if self.state != State.IDLE:
            # Bird rotation
            angle = max(self.speed * -3.5, -90)
            self.image = pygame.transform.rotozoom(self.image, angle, 1)
            self.mask = pygame.mask.from_surface(self.image)

            if self.rect.bottom < background_image.get_height():
                self.speed += self.gravity
                self.rect.y += pygame.math.clamp(self.speed, -10, 10)

    def flap(self):
        if self.rect.y > 0:
            wing_sound.play()
            self.speed = -10

    def reset(self):
        self.rect.center = (40, game_height/2)
        self.speed = 0


class Obstacle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self._layer = Layer.OBSTACLE
        # Create a blank image and add two pipes to it
        self.image = pygame.Surface((pipe_image.get_width(), pipe_image.get_height()*2 + obstacle_gap), flags=pygame.SRCALPHA)
        self.image.blit(pygame.transform.flip(pipe_image, False, True), (0, 0))
        self.image.blit(pipe_image, (0, self.image.get_height() - pipe_image.get_height()))
        self.mask = pygame.mask.from_surface(self.image)

        # Obstacle random placement
        leeway = (background_image.get_height() - self.image.get_height())/2
        y = random.uniform(-leeway, leeway) + background_image.get_height()/2
        self.rect = self.image.get_rect(center=(game_width + pipe_image.get_width(), y))

        # Reward only one point per obstacle
        self.point_debounce = False

    def update(self):
        if self.rect.right < 0:
            self.kill()

        if bird.state != State.DEAD:
            self.rect.x -= obstacle_speed


class UI(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, center):
        super().__init__()
        self._layer = Layer.UI
        self.image = image
        self.rect = self.image.get_rect(center=center)


# Initialize
pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
pygame.init()
clock = pygame.time.Clock()
run_flag = True
fps = 60
score = 0
obstacle_gap = 140
obstacle_speed = 3

background_image = load_image("background-day.png")
ground_image = load_image("base.png")

game_width = background_image.get_width()
game_height = background_image.get_height() + ground_image.get_height()

screen = pygame.display.set_mode((game_width, game_height))

# Conversion can only happen after pygame.display.set_mode
background_image = background_image.convert()
ground_image = ground_image.convert()
down_flap = load_image("yellowbird-downflap.png").convert_alpha()
mid_flap = load_image("yellowbird-midflap.png").convert_alpha()
up_flap = load_image("yellowbird-upflap.png").convert_alpha()
bird_animation_frames = itertools.cycle([mid_flap, up_flap, mid_flap, down_flap])
pipe_image = load_image("pipe-green.png").convert_alpha()
main_message_image = load_image("message.png").convert_alpha()
game_over_message_image = load_image("gameover.png").convert_alpha()

pygame.display.set_caption("Flappy Bird")
pygame.display.set_icon(up_flap)

hit_sound = load_sound("sfx_hit.wav")
point_sound = load_sound("sfx_point.wav")
point_sound.set_volume(0.2)
wing_sound = load_sound("sfx_wing.wav")

main_font = load_font("04B_19.TTF", 40)

obstacles = pygame.sprite.Group()
sprites = pygame.sprite.LayeredUpdates()
# Create scrolling background effect by using two tiles
sprites.add([
    Background(Layer.BACKGROUND, background_image, (0, 0), 1),
    Background(Layer.BACKGROUND, background_image, (game_width, 0), 1),
    Background(Layer.GROUND, ground_image, (0, background_image.get_height()), obstacle_speed),
    Background(Layer.GROUND, ground_image, (game_width, background_image.get_height()), obstacle_speed),
])

bird = Bird()
main_message = UI(main_message_image, (game_width/2, game_height/2))
game_over_message = UI(game_over_message_image, (game_width/2, game_height/2 - 50))
sprites.add([bird, main_message])

pygame.time.set_timer(Event.BIRD_ANIMATION, 125)
pygame.time.set_timer(Event.OBSTACLE_GENERATION, 1100)

while run_flag:
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == QUIT:
            run_flag = False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.event.post(pygame.event.Event(QUIT))
            elif event.key == K_SPACE:
                pygame.event.post(pygame.event.Event(MOUSEBUTTONDOWN))
            elif event.key == K_r:
                pygame.event.post(pygame.event.Event(Event.RESET))
        elif event.type == Event.BIRD_ANIMATION:
            bird.animate()
        elif event.type == MOUSEBUTTONDOWN:
            if bird.state == State.IDLE:
                bird.state = State.FLYING
                main_message.kill()
                bird.flap()
            elif bird.state == State.FLYING:
                bird.flap()
            elif bird.state == State.DEAD:
                pygame.event.post(pygame.event.Event(Event.RESET))
        elif event.type == Event.GAME_OVER:
            if bird.state != State.DEAD:
                hit_sound.play()
                bird.state = State.DEAD
                sprites.add(game_over_message)
        elif event.type == Event.RESET:
            if bird.state == State.DEAD:
                bird.reset()
                bird.state = State.IDLE
                game_over_message.kill()
                sprites.add(main_message)
                for obstacle in obstacles.sprites():
                    obstacle.kill()
                score = 0
        elif event.type == Event.OBSTACLE_GENERATION:
            if bird.state == State.FLYING:
                obstacle = Obstacle()
                sprites.add(obstacle)
                obstacles.add(obstacle)

    if bird.state == State.FLYING:
        if bird.rect.bottom >= background_image.get_height() or pygame.sprite.spritecollide(bird, obstacles, False, pygame.sprite.collide_mask):
            # Lose condition
            pygame.event.post(pygame.event.Event(Event.GAME_OVER))
        else:
            # Score condition
            collisions = pygame.sprite.spritecollide(bird, obstacles, False, pygame.sprite.collide_rect)
            if collisions:
                obstacle = collisions[0]
                if not obstacle.point_debounce:
                    score += 1
                    point_sound.play()

                obstacle.point_debounce = True

    sprites.draw(screen)
    sprites.update()

    # Draw score
    if bird.state != State.IDLE:
        text = main_font.render(f'{score}', True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(game_width/2, 50)))

    pygame.display.update()

pygame.quit()