import os
import pygame
from scripts.constants import *

BASE_IMG_PATH = 'data/images/'

def load_image(path, scale = None, remove_color = (0, 0, 0)):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    if remove_color is not None: img.set_colorkey(remove_color)
    if scale is not None:
        img = pygame.transform.scale(img, scale)
    return img

def load_sounds(path, volume=0.05):  
    sounds = []
    full_path = 'data/sfx/' + path
    for snd_name in sorted(os.listdir(full_path)):
        if snd_name.endswith('.mp3'):
            sound = pygame.mixer.Sound(os.path.join(full_path, snd_name))
            sound.set_volume(volume)  # Set the volume here
            sounds.append(sound)
    return sounds

def load_images(path, scale = None, remove_color = (0, 0, 0)):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name, scale, remove_color))
    return images

def draw_debug_info(game, surface, offset):
    # Draw player rect
    player_rect = game.player.rect()
    pygame.draw.rect(
        surface, 
        (255, 0, 0),  
        (player_rect.x - offset[0], player_rect.y - offset[1], 
         player_rect.width, player_rect.height), 
        2
    )
    
    # Get visible area only
    visible_start_x = offset[0] // game.tilemap.tile_size
    visible_end_x = (offset[0] + surface.get_width()) // game.tilemap.tile_size + 1
    visible_start_y = offset[1] // game.tilemap.tile_size
    visible_end_y = (offset[1] + surface.get_height()) // game.tilemap.tile_size + 1
    
    # Limit debug drawing to visible spikes only
    for x in range(visible_start_x, visible_end_x):
        for y in range(visible_start_y, visible_end_y):
            loc = f"{x};{y}"
            if loc in game.tilemap.tilemap:
                tile = game.tilemap.tilemap[loc]
                if tile['type'] == 'spikes':
                    # Draw tile outline
                    pygame.draw.rect(
                        surface,
                        (255, 192, 203),
                        (tile['pos'][0] * game.tilemap.tile_size - offset[0],
                         tile['pos'][1] * game.tilemap.tile_size - offset[1],
                         game.tilemap.tile_size, game.tilemap.tile_size),
                        1
                    )
                    
                    # Get spike rect
                    spike_rect = game.tilemap.get_spike_rect_with_rotation(tile)
                    
                    # Draw spike hitbox
                    pygame.draw.rect(
                        surface,
                        (255, 255, 0),
                        (spike_rect.x - offset[0], spike_rect.y - offset[1],
                         spike_rect.width, spike_rect.height),
                        2
                    )
                    
                    # Show rotation value (only if really needed)
                    if game.show_rotation_values:  # Add this flag to your game class
                        rotation = tile.get('rotation', 0)
                        debug_font = pygame.font.Font(FONT, 10)
                        rotation_text = debug_font.render(f"{rotation}°", True, (255, 255, 255))
                        surface.blit(rotation_text, (
                            tile['pos'][0] * game.tilemap.tile_size - offset[0] + 2,
                            tile['pos'][1] * game.tilemap.tile_size - offset[1] + 2
                        ))
    
    # Draw interactive rects around player (limit to a smaller area)
    player_pos = game.player.pos
    interactive_rects = game.tilemap.interactive_rects_around(player_pos)
    
    for rect_data in interactive_rects:
        rect, tile_info = rect_data
        color = (255, 255, 0) if tile_info[0] == 'spikes' else (0, 255, 0) if tile_info[0] == 'finish' else (0, 0, 255)
        
        pygame.draw.rect(
            surface,
            color,
            (rect.x - offset[0], rect.y - offset[1],
             rect.width, rect.height),
            2
        )
        
        # Draw center dot only if needed
        pygame.draw.circle(
            surface,
            (255, 165, 0),
            (rect.centerx - offset[0], rect.centery - offset[1]),
            3
        )
    
    # Show debug status
    debug_font = pygame.font.Font(FONT, 20)
    debug_text = debug_font.render("Debug: Hitboxes Visible", True, (0, 255, 0))
    surface.blit(debug_text, (10, 80))

def update_camera_with_box(player, scroll, display_width, display_height):
    box_width = 200
    box_height = 250
    
    box_left = scroll[0] + (display_width / 2) - (box_width / 2)
    box_right = box_left + box_width
    box_top = scroll[1] + (display_height * 0.8) - (box_height / 2) - 100
    box_bottom = box_top + box_height
    
    player_x = player.rect().centerx
    player_y = player.rect().centery
    
    target_x = scroll[0]
    target_y = scroll[1]
    
    if player_x < box_left:
        target_x = scroll[0] - (box_left - player_x)
    elif player_x > box_right:
        target_x = scroll[0] + (player_x - box_right)
    
    if player_y < box_top:
        target_y = scroll[1] - (box_top - player_y)
    elif player_y > box_bottom:
        target_y = scroll[1] + (player_y - box_bottom)
    
    scroll[0] += (target_x - scroll[0]) / 15
    scroll[1] += (target_y - scroll[1]) / 10
    
    return scroll
class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]
    
def UIsize(size):
    return int(DISPLAY_SIZE[0] * size // 100)