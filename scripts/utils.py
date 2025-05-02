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

def find_next_numeric_filename(directory, extension='.json'):
    existing_files = os.listdir(directory)
    numeric_names = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit() and f.endswith(extension)]
    next_number = max(numeric_names, default=-1) + 1
    return f"{next_number}{extension}"

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
    box_height = 55
    
    box_left = scroll[0] + (display_width / 2) - (box_width / 2)
    box_right = box_left + box_width
    box_top = scroll[1] + (display_height / 1.8) - (box_height / 2) 
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

from pygame import Rect

class ButtonManager:
    def __init__(self, font, button_height=80, min_width=300, text_padding=40, padding=30):
        self.font = font
        self.button_height = button_height
        self.min_width = min_width
        self.text_padding = text_padding
        self.padding = padding
        self.buttons = []
        self.selected_index = None
        
    def calculate_button_size(self, text):
        text_surf = self.font.render(text, True, (255, 255, 255))
        width = text_surf.get_width() + self.text_padding
        
        if width < self.min_width:
            width = self.min_width
            
        return width, self.button_height
    
    def create_button(self, text, action, x, y, width=None):
        if width is None:
            width, _ = self.calculate_button_size(text)
            
        button = Button(
            Rect(x, y, width, self.button_height),
            text,
            action,
            self.font,
            self.min_width,
            self.text_padding
        )
        
        self.buttons.append(button)
        return button
    
    def create_centered_button_list(self, button_texts, button_actions, start_x, start_y):
        max_width = self.min_width
        
        for text in button_texts:
            width, _ = self.calculate_button_size(text)
            max_width = max(max_width, width)
        
        centered_x = start_x - (max_width // 2)
        
        for i, (text, action) in enumerate(zip(button_texts, button_actions)):
            y_pos = start_y + i * (self.button_height + self.padding)
            self.create_button(text, action, centered_x, y_pos, max_width)
    
    def create_grid_buttons(self, texts, actions, columns, start_x, start_y, fixed_width=None):
        if fixed_width is None:
            fixed_width = self.min_width
            
        for i, (text, action) in enumerate(zip(texts, actions)):
            row = i // columns
            col = i % columns
            
            button_x = start_x + col * (fixed_width + self.padding)
            button_y = start_y + row * (self.button_height + self.padding)
            
            self.create_button(text, action, button_x, button_y, fixed_width)
    
    def update(self, mouse_pos):
        self.selected_index = None
        
        for i, button in enumerate(self.buttons):
            button.selected = button.is_hovered(mouse_pos)
            if button.selected:
                self.selected_index = i
    
    def handle_events(self, events, sound_callback=None):
        for button in self.buttons:
            if button.handle_events(events, sound_callback):
                return True
        return False
    
    def draw(self, surface):
        for button in self.buttons:
            button.draw(surface)
    
    def clear(self):
        self.buttons = []
        self.selected_index = None

class Button:
    def __init__(self, rect, text, action, font, min_width=300, text_padding=40):
        self.rect = rect
        self.text = text
        self.action = action
        self.font = font
        self.min_width = min_width
        self.text_padding = text_padding
        self.selected = False
        
    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface, highlight_color=(255, 215, 0)):
        # Add shadow behind the button
        shadow_offset = 4
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Change shadow color based on hover state
        shadow_color = (255, 255, 255, 90) if self.selected else (0, 0, 0, 90)
        shadow_surface.fill(shadow_color)

        surface.blit(shadow_surface, (self.rect.x + shadow_offset, self.rect.y + shadow_offset))
        
        # Button background with improved colors
        button_color = (100, 120, 255, 200) if self.selected else (80, 80, 120, 180)
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        button_surface.fill(button_color)
        surface.blit(button_surface, (self.rect.x, self.rect.y))
        
        # Text with shadow effect
        text_shadow = self.font.render(self.text, True, (0, 0, 0, 180))
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        
        # Position text with shadow offset
        text_x = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        
        # Draw text shadow slightly offset
        surface.blit(text_shadow, (text_x + 2, text_y + 2))
        surface.blit(text_surf, (text_x, text_y))
        
        # Draw highlight border if selected
        if self.selected:
            glow_color = (200, 230, 255)  # clean white glow
            glow_size = 3 # number of glow layers

            for i in range(glow_size, 0, -1):
                alpha = 60 - i * 10  # fade out each outer layer
                glow_rect = self.rect.inflate(i * 4, i * 4)
                glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)

                pygame.draw.rect(
                    glow_surface,
                    (*glow_color, alpha),
                    glow_surface.get_rect(),
                    border_radius=6  # nice soft corners
                )

                surface.blit(glow_surface, (
                    self.rect.x - i * 2,
                    self.rect.y - i * 2
                ))


    
    def handle_events(self, events, sound_callback=None):
        if self.selected:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if sound_callback:
                        sound_callback('click')
                    self.action()
                    return True
        return False


class MenuScreen:
    def __init__(self, parent, title="Menu"):
        self.parent = parent
        self.screen = parent.screen
        self.background = parent.background
        self.font = pygame.font.Font(parent.font_path, 40)
        self.title_font = pygame.font.Font(parent.font_path, 70)
        self.enabled = False
        self.title = title
        
        self.button_manager = ButtonManager(
            self.font,
            parent.button_props['height'],
            parent.button_props['min_width'],
            parent.button_props['text_padding'],
            parent.button_props['padding']
        )
        
        self.initialize()
    
    def initialize(self):
        pass
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
    
    def update(self, events):
        if not self.enabled:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        self.button_manager.update(mouse_pos)
        
        self.button_manager.handle_events(events, self.parent._play_sound)
    
    def draw(self, surface):
        if not self.enabled:
            return
            
        # Create title text with shadow effect
        title_shadow = self.title_font.render(self.title, True, (0, 0, 0))
        title_text = self.title_font.render(self.title, True, (255, 255, 255))
        
        title_x = (self.parent.display_size[0] - title_text.get_width()) // 2
        title_y = (self.parent.display_size[1] - title_text.get_height()) // 7
        
        # Draw shadow with offset
        surface.blit(title_shadow, (title_x + 4, title_y + 4))
        # Draw main text
        surface.blit(title_text, (title_x, title_y))
        
        self.button_manager.draw(surface)