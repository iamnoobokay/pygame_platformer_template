# PERLIN NOISE: generating random terrain

import pygame
import sys
import random

from pygame.locals import *
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.set_num_channels(64)
clock = pygame.time.Clock()

pygame.display.set_caption("Pygame Window")
WINDOW_SIZE = (600, 400)

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
display = pygame.Surface((300, 200))
TILE_SIZE = 16
grass_image = pygame.image.load('grass.png')
dirt_image = pygame.image.load('dirt.png')
plant_image = pygame.image.load('plant.png').convert()
plant_image.set_colorkey((255, 255, 255))

tile_index = {1: grass_image, 2: dirt_image, 3: plant_image}

jump_sound = pygame.mixer.Sound('jump.wav')
grass_sounds = [pygame.mixer.Sound(
    'grass_0.wav'), pygame.mixer.Sound('grass_1.wav')]
grass_sounds[0].set_volume(0.2)
grass_sounds[1].set_volume(0.2)
pygame.mixer.music.load('music.wav')
pygame.mixer.music.play(-1)

# generating a chunk of tiles ? DAFAQ ?
CHUNK_SIZE = 8


def generate_chunk(x, y):
    chunk_data = []
    for y_pos in range(CHUNK_SIZE):
        for x_pos in range(CHUNK_SIZE):
            target_x = x*CHUNK_SIZE + x_pos
            target_y = y * CHUNK_SIZE + y_pos
            tile_type = 0  # nothing
            if target_y > 10:
                tile_type = 2  # dirt
            elif target_y == 10:
                tile_type = 1  # grass
            elif target_y == 9:
                if random.randint(1, 5) == 1:
                    tile_type = 3  # plant
            if tile_type != 0:
                chunk_data.append([[target_x, target_y], tile_type])
    return chunk_data


# animation frames are stored in dictionary below
global animation_frames
animation_frames = {}


# function to load animation based on frame duration
def load_animation(path, frame_durations):
    global animation_frames
    animation_name = path.split('/')[-1]
    animation_frame_data = []
    n = 0
    for frame in frame_durations:
        animation_frame_id = animation_name + '_' + str(n)
        img_loc = path + "/" + animation_frame_id + '.png'
        animation_image = pygame.image.load(img_loc).convert()
        animation_image.set_colorkey((255, 255, 255))
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data

# changing action when key is pressed


def change_action(action_var, frame, new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var, frame


# generate animations, store in database dictionary
animation_database = {}
animation_database['run'] = load_animation('player_animations/run', [7, 7])
animation_database['idle'] = load_animation(
    'player_animations/idle', [7, 7, 40])
player_action = 'idle'
player_frame = 0
player_flip = False
grass_sound_timer = 0

# load the map
game_map = {}

moving_right = False
moving_left = False

# initial player location
player_location = [50, 50]
# initial player y momentum
player_y_momentum = 0
# air timer to prevent double jumps
air_timer = 0
# scroll functionality, dont understand fully.
true_scroll = [0, 0]

# player_rect = pygame.Rect(
# player_location[0], player_location[1], player_image.get_width(), player_image.get_height())

# rectangle bounding the player
player_rect = pygame.Rect(100, 100, 5, 13)

# these are the parallax objects in a list, rendered behind the game screen
background_objects = [[0.25, [120, 10, 70, 400]], [0.25, [280, 30, 40, 400]], [
    0.5, [30, 40, 40, 400]], [0.5, [130, 90, 100, 400]], [0.5, [300, 80, 120, 400]]]


# collison test code
def collision_test(rect, tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list


def move(rect, movement, tiles):
    collision_types = {'top': False, 'bottom': False,
                       'right': False, 'left': False}
    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True

    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True
    return rect, collision_types
# end collision test code


# main game loop
while True:
    # game screen color
    display.fill((146, 244, 255))

    # this is for scroll. scroll 0 and scroll 1 are converted into ints so that the pixels dont tear. dont understand it
    true_scroll[0] += (player_rect.x - true_scroll[0] - 152)/20
    true_scroll[1] += (player_rect.y - true_scroll[1] - 106)/20
    scroll = true_scroll.copy()
    scroll[0] = int(scroll[0])
    scroll[1] = int(scroll[1])

    # this is grass sound timer, grass sound is played only when the timer reaches 0
    if grass_sound_timer > 0:
        grass_sound_timer -= 1

    # this is the main parallax rectangle. it is static
    pygame.draw.rect(display, (7, 80, 75), pygame.Rect(0, 120, 300, 80))

    # the building objects in the parallax being rendered
    for background_object in background_objects:
        obj_rect = pygame.Rect(background_object[1][0]-scroll[0] * background_object[0],
                               background_object[1][1]-scroll[1] * background_object[0], background_object[1][2], background_object[1][3])
        if background_object[0] == 0.5:
            pygame.draw.rect(display, (14, 222, 150), obj_rect)
        else:
            pygame.draw.rect(display, (9, 91, 85), obj_rect)

    # displaying the tiles
    tile_rects = []
    # tile rendering
    for y in range(3):
        for x in range(4):
            target_x = x - 1 + int(round(scroll[0] / (CHUNK_SIZE * 16)))
            target_y = y - 1 + int(round(scroll[1] / (CHUNK_SIZE * 16)))
            target_chunk = str(target_x) + ";" + str(target_y)
            if target_chunk not in game_map:
                game_map[target_chunk] = generate_chunk(target_x, target_y)
            for tile in game_map[target_chunk]:
                display.blit(
                    tile_index[tile[1]], (tile[0][0]*16 - scroll[0], tile[0][1] * 16 - scroll[1]))
                if tile[1] in [1, 2]:
                    tile_rects.append(
                        pygame.Rect(tile[0][0] * 16, tile[0][1] * 16, 16, 16))
    # player movement handler
    player_movement = [0, 0]
    if moving_right:
        player_movement[0] += 2
    if moving_left:
        player_movement[0] -= 2
    player_movement[1] += player_y_momentum
    player_y_momentum += 0.2
    if player_y_momentum > 3:
        player_y_momentum = 3

    # player animation handler
    if player_movement[0] > 0:
        player_action, player_frame = change_action(
            player_action, player_frame, 'run')
        player_flip = False
    if player_movement[0] == 0:
        player_action, player_frame = change_action(
            player_action, player_frame, 'idle')
    if player_movement[0] < 0:
        player_action, player_frame = change_action(
            player_action, player_frame, 'run')
        player_flip = True
    player_rect, collisions = move(player_rect, player_movement, tile_rects)
    if collisions['bottom']:
        player_y_momentum = 0
        air_timer = 0
        if player_movement[0] != 0:
            if grass_sound_timer == 0:
                grass_sound_timer = 30
                random.choice(grass_sounds).play()
    else:
        air_timer += 1
    if collisions['top']:
        player_y_momentum = 0
    player_frame += 1
    if (player_frame >= len(animation_database[player_action])):
        player_frame = 0
    player_img_id = animation_database[player_action][player_frame]
    player_image = animation_frames[player_img_id]
    display.blit(pygame.transform.flip(player_image, player_flip, False), (player_rect.x -
                 scroll[0], player_rect.y - scroll[1]))

    # key bindings
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_w:
                pygame.mixer.music.fadeout(1000)
            if event.key == K_e:
                pygame.mixer.music.play(-1)
            if event.key == K_RIGHT:
                moving_right = True
            if event.key == K_LEFT:
                moving_left = True
            if event.key == K_UP:
                if air_timer < 6:
                    jump_sound.play()
                    player_y_momentum = -5
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                moving_right = False
            if event.key == K_LEFT:
                moving_left = False

    # tick rate and surface rendering
    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    pygame.display.update()
    clock.tick(60)

# test_rect = pygame.Rect(100, 100, 100, 50)

# if player_location[1] > WINDOW_SIZE[1]-player_image.get_height():
#     player_y_momentum = -player_y_momentum
# else:
#     player_y_momentum += 0.2
# player_location[1] += player_y_momentum
# print(player_location[1])
# if moving_right == True:
#     player_location[0] += 4
# if moving_left == True:
#     player_location[0] -= 4
# if player_rect.colliderect(test_rect):
#     pygame.draw.rect(screen, (255, 0, 0), test_rect)
# else:
#     pygame.draw.rect(screen, (0, 0, 0), test_rect)
