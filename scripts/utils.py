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

# This is a sample of what to add to scripts/utils.py

def render_text_with_shadow(surface, text, font, color, x, y, shadow_offset=1, centered=False):
    text_surface = font.render(text, True, color)
    shadow_surface = font.render(text, True, (0, 0, 0))
    
    if centered:
        text_rect = text_surface.get_rect(center=(x, y))
        shadow_rect = shadow_surface.get_rect(
            center=(x + shadow_offset, y + shadow_offset)
        )
    else:
        text_rect = text_surface.get_rect(topleft=(x, y))
        shadow_rect = shadow_surface.get_rect(
            topleft=(x + shadow_offset, y + shadow_offset)
        )
    
    # Draw shadow first, then text
    surface.blit(shadow_surface, shadow_rect)
    surface.blit(text_surface, text_rect)
    
    return text_rect  # Return rect in case positioning is needed

def scale_position(x_percent, y_percent, display_size):
    return (int(display_size[0] * x_percent), int(display_size[1] * y_percent))

def scale_size(width_percent, height_percent, display_size):
    return (int(display_size[0] * width_percent), int(display_size[1] * height_percent))

def scale_font(base_size, display_size, reference_size=(1920, 1080)):
    # Calculate scaling factor based on the geometric mean of width and height ratios
    width_ratio = display_size[0] / reference_size[0]
    height_ratio = display_size[1] / reference_size[1]
    scale_factor = (width_ratio * height_ratio) ** 0.5
    
    # Apply scaling with limits to prevent extreme sizes
    scaled_size = max(12, min(72, int(base_size * scale_factor)))
    return scaled_size


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

class Button:
    def __init__(self, rect, text, action, font, menu):
        self.rect = rect
        self.text = text
        self.action = action
        self.font = font
        self.menu = menu  # Store reference to menu for access to UI_CONSTANTS
        self.selected = False
        
        # Calculate proportional border radius based on button height
        self.border_radius = max(6, int(rect.height * 0.1))  # 10% of height, minimum 6px
        
        # Calculate shadow offset based on display size
        display_height = pygame.display.get_surface().get_height()
        self.shadow_offset = max(2, int(4 * (display_height / 1080)))
    
    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        # Add shadow behind the button - scaled with display size
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        shadow_color = (255, 255, 255, 90) if self.selected else (0, 0, 0, 90)
        shadow_surface.fill(shadow_color)
        surface.blit(shadow_surface, (self.rect.x + self.shadow_offset, self.rect.y + self.shadow_offset))
        
        # Button background
        button_color = self.menu.UI_CONSTANTS['BUTTON_HOVER_COLOR'] if self.selected else self.menu.UI_CONSTANTS['BUTTON_COLOR']
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        button_surface.fill(button_color)
        surface.blit(button_surface, (self.rect.x, self.rect.y))
        
        # Text with shadow effect - shadow offset scaled with display size
        text_shadow = self.font.render(self.text, True, (0, 0, 0, 180))
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        
        text_x = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        
        # Scale text shadow offset with display size
        text_shadow_offset = max(1, int(2 * pygame.display.get_surface().get_height() / 1080))
        
        surface.blit(text_shadow, (text_x + text_shadow_offset, text_y + text_shadow_offset))
        surface.blit(text_surf, (text_x, text_y))
        
        # Draw highlight border if selected - scale glow with display size
        if self.selected:
            glow_color = self.menu.UI_CONSTANTS['BUTTON_GLOW_COLOR']
            display_width = pygame.display.get_surface().get_width()
            glow_size = max(2, int(3 * (display_width / 1920)))

            for i in range(glow_size, 0, -1):
                alpha = 60 - i * 10
                glow_rect = self.rect.inflate(i * 4, i * 4)
                glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)

                pygame.draw.rect(
                    glow_surface,
                    (*glow_color, alpha),
                    glow_surface.get_rect(),
                    border_radius=self.border_radius
                )

                surface.blit(glow_surface, (
                    self.rect.x - i * 2,
                    self.rect.y - i * 2
                ))

class MenuScreen:
    def __init__(self, menu, title="Menu"):
        self.menu = menu
        self.screen = menu.screen
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        
        # Scale fonts based on display size
        font_size = scale_font(40, DISPLAY_SIZE)
        title_font_size = scale_font(70, DISPLAY_SIZE)
        
        self.font = pygame.font.Font(FONT, font_size)
        self.title_font = pygame.font.Font(FONT, title_font_size)
        self.enabled = False
        self.title = title
        self.buttons = []
        
    def enable(self):
        self.enabled = True
        self.initialize()
    
    def disable(self):
        self.enabled = False
    
    def initialize(self):
        # Override in subclasses
        pass
    
    def update(self, events):
        if not self.enabled:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        
        # Update button hover states
        for button in self.buttons:
            button.selected = button.is_hovered(mouse_pos)
        
        # Handle button clicks
        for button in self.buttons:
            if button.selected:
                for event in events:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.menu._play_sound('click')
                        button.action()
                        return
    
    def draw(self, surface):
        if not self.enabled:
            return
        
        # Draw title with shadow
        title_shadow = self.title_font.render(self.title, True, (0, 0, 0))
        title_text = self.title_font.render(self.title, True, (255, 255, 255))
        
        title_x = (DISPLAY_SIZE[0] - title_text.get_width()) // 2
        title_y = int(DISPLAY_SIZE[1] * 0.1)  # 10% from top
        
        # Scale shadow offset with display size
        shadow_offset = max(2, int(4 * (DISPLAY_SIZE[1] / 1080)))
        
        surface.blit(title_shadow, (title_x + shadow_offset, title_y + shadow_offset))
        surface.blit(title_text, (title_x, title_y))
        
        # Draw all buttons
        for button in self.buttons:
            button.draw(surface)
    
    def clear_buttons(self):
        self.buttons = []
    
    def create_button(self, text, action, x, y, width=None):
        # Calculate button size based on text if width not specified
        if width is None:
            text_surf = self.font.render(text, True, (255, 255, 255))
            width = text_surf.get_width() + self.UI_CONSTANTS['BUTTON_TEXT_PADDING']
            width = max(width, self.UI_CONSTANTS['BUTTON_MIN_WIDTH'])
            
        button = Button(
            pygame.Rect(x, y, width, self.UI_CONSTANTS['BUTTON_HEIGHT']),
            text,
            action,
            self.font,
            self.menu  # Pass menu reference to Button
        )
        
        self.buttons.append(button)
        return button
    
    def create_centered_button_list(self, button_texts, button_actions, center_x, start_y):
        # Calculate the maximum width needed for buttons
        max_width = self.UI_CONSTANTS['BUTTON_MIN_WIDTH']
        for text in button_texts:
            text_surf = self.font.render(text, True, (255, 255, 255))
            width = text_surf.get_width() + self.UI_CONSTANTS['BUTTON_TEXT_PADDING']
            max_width = max(max_width, width)
        
        # Create centered buttons
        left_x = center_x - (max_width // 2)
        for i, (text, action) in enumerate(zip(button_texts, button_actions)):
            y_pos = start_y + i * (self.UI_CONSTANTS['BUTTON_HEIGHT'] + self.UI_CONSTANTS['BUTTON_SPACING'])
            self.create_button(text, action, left_x, y_pos, max_width)
    
    def create_grid_buttons(self, texts, actions, start_x, start_y, fixed_width=None):
        if fixed_width is None:
            fixed_width = self.UI_CONSTANTS['BUTTON_MIN_WIDTH']
            
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        for i, (text, action) in enumerate(zip(texts, actions)):
            row = i // columns
            col = i % columns
            
            button_x = start_x + col * (fixed_width + self.UI_CONSTANTS['BUTTON_SPACING'])
            button_y = start_y + row * (self.UI_CONSTANTS['BUTTON_HEIGHT'] + self.UI_CONSTANTS['BUTTON_SPACING'])
            
            self.create_button(text, action, button_x, button_y, fixed_width)

class TextInput:
    def __init__(self, rect, font, menu, max_chars=20, placeholder="Enter text..."):
        self.rect = rect
        self.font = font
        self.menu = menu
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        self.max_chars = max_chars
        self.placeholder = placeholder
        self.text = ""
        self.active = False  # Whether the input box is selected
        self.border_radius = max(6, int(rect.height * 0.1))
        self.cursor_visible = True
        self.cursor_counter = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click toggles active if clicked inside
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False  # Optional: deactivate on Enter
            elif len(self.text) < self.max_chars:
                if event.unicode.isprintable():
                    self.text += event.unicode

    def update(self):
        # Simple blinking cursor
        self.cursor_counter += 1
        if self.cursor_counter >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_counter = 0

    def draw(self, surface):
        # Background box
        bg_color = self.UI_CONSTANTS['BUTTON_HOVER_COLOR'] if self.active else self.UI_CONSTANTS['BUTTON_COLOR']
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=self.border_radius)

        # Text
        if self.text:
            text_surface = self.font.render(self.text, True, (255, 255, 255))
        else:
            text_surface = self.font.render(self.placeholder, True, (150, 150, 150))

        text_x = self.rect.x + 10
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

        # Cursor
        if self.active and self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y = text_y
            cursor_height = text_surface.get_height()
            pygame.draw.line(surface, (255, 255, 255), (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)
