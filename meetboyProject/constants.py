
DISPLAY_SIZE = (1280, 720)
FPS = 60

TILE_SIZE = 36 # tilemap tile size

PLAYER_SPEED = 3 # added per frame
JUMP_SPEED = 13 # initial jump velocity
GRAVITY = 0.6 # subtracted from y velocity every frame
ACCELERAION = 0.05 # friction with the ground on the x axis, between 0 and 1 (0 < Acc < 1)
MAX_X_SPEED = 20 # x axis speed limit
MAX_Y_SPEED = 20 # y axis speed limit


PLAYER_POS = (50, 50) # player position when the level start
PLAYERS_SIZE = (TILE_SIZE, TILE_SIZE) # size of actual player hitbox
PLAYERS_IMAGE_SIZE = (PLAYERS_SIZE[0], PLAYERS_SIZE[1]) # size of the player image

PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

FONT = None # deafult font for text and buttons

EDITOR_SCROLL_SPEED = 10 # how fast you can move in the editor using WASD
