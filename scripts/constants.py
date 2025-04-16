import tkinter as tk
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
DISPLAY_SIZE = (screen_width, screen_height-60)

FPS = 60

TILE_SIZE = DISPLAY_SIZE[0] // 40 # tilemap tile size

PLAYER_SPEED = 1   *TILE_SIZE/36 # added per frame
JUMP_SPEED = 15  *TILE_SIZE/36 # initial jump velocity
WALLSLIDE_SPEED = 1  *TILE_SIZE/36 # the speed in which the player will slide off a wall
WALLJUMP_X_SPEED = 20  *TILE_SIZE/36 # the x velocity of the player when jumpingoff of a wall
WALLJUMP_Y_SPEED = 15  *TILE_SIZE/36 # the y velocity of the player when jumpingoff of a wall
GRAVITY_UP = 0.6   *TILE_SIZE/36 # subtracted from y velocity every frame when player going up
GRAVITY_DOWN = 0.3  *TILE_SIZE/36 # subtracted from y velocity every frame when player going down
ACCELERAION = 0.02  *TILE_SIZE/36 # friction with the ground on the x axis when starting to move, between 0 and 1 (0 < Acc < 1)
DECCELARATION = 0.1   *TILE_SIZE/36 # friction with the ground on the x axis when stopping to move, between 0 and 1 (0 < Acc < 1)
MAX_X_SPEED = 15   *TILE_SIZE/36 # x axis speed limit
MAX_Y_SPEED = 20   *TILE_SIZE/36 # y axis speed limit

PLAYER_BUFFER = 5 # amount of frame buffer

PLAYER_POS = (50, 50) # player position when the level start
PLAYERS_SIZE = (TILE_SIZE, TILE_SIZE) # size of actual player hitbox
PLAYERS_IMAGE_SIZE = (PLAYERS_SIZE[0], PLAYERS_SIZE[1]) # size of the player image

PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}
INTERACTIVE_TILES = {'spikes', 'finish'}
SPIKE_SIZE = (1, 0.3)

FONT = None # deafult font for text and buttons

EDITOR_SCROLL_SPEED = 10 # how fast you can move in the editor using WASD

RECT = 'data\images\Rect.png'
MENUBG = r'data\images\backgroundmenu.jpeg'

MENUTXTCOLOR = (186,248,186)
WHITE = (255, 255, 255)