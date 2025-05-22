import sys
import pygame
import os
import random
import json
from scripts.utils import load_images, load_image, find_next_numeric_filename, MenuScreen, load_sounds, TextInput, render_text_with_shadow
from scripts.tilemap import Tilemap
from scripts.constants import TILE_SIZE, DISPLAY_SIZE, FPS, PHYSICS_TILES, FONT, MENUBG, calculate_ui_constants
from scripts.GameManager import game_state_manager

class EditorMenu:
    def __init__(self, display):
        self.screen = display
        self.sfx = {'click': load_sounds('click')}
        
        self.background = pygame.transform.scale(
            pygame.image.load(MENUBG).convert(), 
            DISPLAY_SIZE
        )
        
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        self.selected_map = None
        self.editor_active = False
        self.editor = None
        self.map_menu = EditorMapSelectionScreen(self)
        self.map_menu.enable()

    def _play_sound(self, sound_key):
        if sound_key in self.sfx:
            random.choice(self.sfx[sound_key]).play()

    def _select_map(self, map_file):
        self.selected_map = map_file
        self.start_editor(map_file)

    def create_new_map(self):
        self.map_menu.showing_edit_page = True
        
        # Simplified next ID calculation
        next_id = "1"
        if self.map_menu.map_files:
            map_ids = [int(f.split('.')[0]) for f in self.map_menu.map_files 
                      if f.split('.')[0].isdigit()]
            if map_ids:
                next_id = str(max(map_ids) + 1)
                
        self.map_menu.selected_map_id = next_id
        self.map_menu.title = f"Creating Map #{next_id}"
        self.map_menu.initialize_edit_page()

    def start_editor(self, map_file):
        self.editor = Editor(self, map_file)  
        self.editor_active = True

    def quit_editor(self):
        if self.editor_active and self.map_menu.selected_map_id:
            self.editor_active = False
            self.editor = None
            self.map_menu.showing_edit_page = True
            self.map_menu.initialize_edit_page()
        else:
            game_state_manager.setState('menu')

    def return_to_menu(self):
        self.editor_active = False
        self.editor = None
        self.map_menu = EditorMapSelectionScreen(self)
        self.map_menu.enable()

    def run(self):
        if self.editor_active:
            self.editor.run()
            return

        self.screen.blit(self.background, (0, 0))
            
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.map_menu.showing_edit_page:
                    self.map_menu.return_to_map_list()
                else:
                    self.quit_editor()

        self.map_menu.update(events)
        self.map_menu.draw(self.screen)

class EditorMapSelectionScreen(MenuScreen):
    def __init__(self, menu, title="Map Selection"):
        super().__init__(menu, title)
        self.current_page = 0
        self.total_pages = 0
        self.map_files = []
        self.map_numbers = []
        self.map_metadata = {}
        
        # Consolidated font setup
        self.fonts = {
            'info': pygame.font.Font(FONT, int(DISPLAY_SIZE[1] * 0.02)),
            'detail': pygame.font.Font(FONT, int(DISPLAY_SIZE[1] * 0.025)),
            'title': pygame.font.Font(FONT, int(DISPLAY_SIZE[1] * 0.045))
        }
        
        self.selected_map_id = None
        self.showing_edit_page = False
        self.text_inputs = {}
        
        # Difficulty system
        self.difficulty_options = ['easy', 'normal', 'hard', 'expert', 'insane']
        self.selected_difficulty = 0
        self.difficulty_colors = {
            'easy': (0, 255, 0), 'normal': (255, 255, 0), 'hard': (255, 165, 0),
            'expert': (255, 0, 0), 'insane': (128, 0, 128)
        }
        
        # Save confirmation
        self.show_save_confirmation = False
        self.save_time = 0
        
        self.load_metadata()
        
    def load_metadata(self):
        try:
            with open('metadata.json', 'r') as f:
                self.map_metadata = json.load(f)
        except Exception as e:
            print(f"Error loading metadata.json: {e}")
            self.map_metadata = {}
            
    def save_metadata(self):
        self.load_metadata()
        try:
            with open('metadata.json', 'w') as f:
                json.dump(self.map_metadata, f, indent=2)
            print("Metadata saved successfully!")
            return True
        except Exception as e:
            print(f"Error saving metadata.json: {e}")
            return False
    
    def initialize(self):
        if self.showing_edit_page:
            self.initialize_edit_page()
        else:
            self.title = "Map Selection"
            self.load_maps()
            self.recreate_buttons()
            
    def load_maps(self):
        maps_dir = 'data/maps'
        os.makedirs(maps_dir, exist_ok=True)
            
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        self.map_files.sort(key=lambda f: int(f.split('.')[0]) if f.split('.')[0].isdigit() else float('inf'))
        
        maps_per_page = self.UI_CONSTANTS.get('MAPS_PER_PAGE', 20)
        self.total_pages = (len(self.map_files) + maps_per_page - 1) // maps_per_page
        self.current_page = min(self.current_page, max(0, self.total_pages - 1))
        self.map_numbers = [str(i) for i in range(len(self.map_files))]
    
    def recreate_buttons(self):
        self.clear_buttons()
        
        maps_per_page = self.UI_CONSTANTS.get('MAPS_PER_PAGE', 20)
        start_index = self.current_page * maps_per_page
        end_index = min(start_index + maps_per_page, len(self.map_files))
        
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        button_width = int(DISPLAY_SIZE[0] * 0.1)
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        padding = self.UI_CONSTANTS['BUTTON_SPACING']
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (DISPLAY_SIZE[0] - grid_width) // 2
        
        # Create grid buttons
        actions = [lambda idx=self.map_files[start_index + i].split('.')[0]: self.show_edit_page(idx) 
                  for i in range(len(current_page_files))]
            
        self.create_grid_buttons(
            current_page_numbers, actions, start_x, 
            int(DISPLAY_SIZE[1] * 0.25), button_width
        )
        
        # Navigation and control buttons
        self._create_navigation_buttons()
        
    def _create_navigation_buttons(self):
        # Back button
        self.create_button("←", self.return_to_editor_menu, 
                          int(DISPLAY_SIZE[0] * 0.02), int(DISPLAY_SIZE[1] * 0.02), 
                          int(DISPLAY_SIZE[0] * 0.08))
        
        # Add Map button
        self.create_button("Add", self.menu.create_new_map, 
                          int(DISPLAY_SIZE[0] * 0.75), int(DISPLAY_SIZE[1] * 0.15), 
                          int(DISPLAY_SIZE[0] * 0.1))
        
        # Page navigation
        middle_y = DISPLAY_SIZE[1] * 0.37
        nav_width = int(DISPLAY_SIZE[0] * 0.09)
        
        if self.current_page > 0:
            self.create_button("◀", self.previous_page, int(DISPLAY_SIZE[0] * 0.12), middle_y, nav_width)
        
        if self.current_page < self.total_pages - 1:
            self.create_button("▶", self.next_page, int(DISPLAY_SIZE[0] * 0.8), middle_y, nav_width)
        
        # Page counter
        if self.total_pages > 1:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            page_width = int(DISPLAY_SIZE[0] * 0.25)
            self.create_button(page_info, lambda: None, 
                             DISPLAY_SIZE[0] // 2 - page_width // 2, 
                             DISPLAY_SIZE[1] * 0.68, page_width)
    
    def initialize_edit_page(self):
        self.clear_buttons()
        
        panel_width = int(DISPLAY_SIZE[0] * 0.8)
        panel_height = int(DISPLAY_SIZE[1] * 0.6)
        panel_x = (DISPLAY_SIZE[0] - panel_width) // 2
        panel_y = DISPLAY_SIZE[1] * 0.15
        
        # Back button
        self.create_button("←", self.return_to_map_list, 
                          int(DISPLAY_SIZE[0] * 0.02), int(DISPLAY_SIZE[1] * 0.02), 
                          int(DISPLAY_SIZE[0] * 0.08))
        
        # Action buttons
        button_y = panel_y + panel_height - int(DISPLAY_SIZE[1] * 0.12)
        
        self.create_button("Save Changes", self.save_map_metadata, 
                          panel_x + int(panel_width * 0.25) - int(DISPLAY_SIZE[0] * 0.1),
                          button_y, int(DISPLAY_SIZE[0] * 0.27), (30, 144, 255))
        
        self.create_button("Edit Map", self.edit_selected_map, 
                          panel_x + int(panel_width * 0.75) - int(DISPLAY_SIZE[0] * 0.1),
                          button_y, int(DISPLAY_SIZE[0] * 0.2), (40, 180, 40))
        
        self.create_difficulty_buttons()
        self.create_text_inputs()
    
    def create_difficulty_buttons(self):
        button_width = int(DISPLAY_SIZE[0] * 0.03)
        button_y = DISPLAY_SIZE[1] * 0.44
        right_x = DISPLAY_SIZE[0] * 0.75
        
        self.create_button("◀", self.previous_difficulty, 
                          right_x - int(DISPLAY_SIZE[0] * 0.09) - button_width, 
                          button_y, button_width)
        
        self.create_button("▶", self.next_difficulty, 
                          right_x + int(DISPLAY_SIZE[0] * 0.09), 
                          button_y, button_width)
    
    def create_text_inputs(self):
        input_width = int(DISPLAY_SIZE[0] * 0.5)
        input_height = int(DISPLAY_SIZE[1] * 0.05)
        panel_x = (DISPLAY_SIZE[0] - int(DISPLAY_SIZE[0] * 0.8)) // 2
        
        # Get current map data
        map_data = self.map_metadata.get(self.selected_map_id, {})
        
        # Name input
        name_rect = pygame.Rect(DISPLAY_SIZE[0] // 2 - input_width // 2, 
                               DISPLAY_SIZE[1] * 0.33, input_width, input_height)
        
        # Creator input
        creator_rect = pygame.Rect(panel_x + int(DISPLAY_SIZE[0] * 0.05), 
                                  DISPLAY_SIZE[1] * 0.44, 
                                  int(input_width * 0.6), input_height)
        
        self.text_inputs = {
            'name': TextInput(name_rect, self.fonts['detail'], self.menu, 
                            max_chars=30, placeholder="Enter map name..."),
            'creator': TextInput(creator_rect, self.fonts['detail'], self.menu, 
                               max_chars=20, placeholder="Creator name...")
        }
        
        # Set existing values
        self.text_inputs['name'].text = map_data.get('name', "")
        self.text_inputs['creator'].text = map_data.get('creator', "")
        
        # Set difficulty
        current_difficulty = map_data.get('difficulty', 'normal')
        self.selected_difficulty = (self.difficulty_options.index(current_difficulty) 
                                  if current_difficulty in self.difficulty_options else 1)
    
    def edit_selected_map(self):
        self.menu._play_sound('click')
        map_filename = f"{self.selected_map_id}.json"
        
        for map_file in self.map_files:
            if map_file == map_filename:
                self.menu._select_map(map_file)
                return
                
        self.menu._select_map(f"data/maps/{map_filename}")
    
    def show_edit_page(self, map_id):
        self.menu._play_sound('click')
        self.selected_map_id = map_id
        self.showing_edit_page = True
        self.title = ""
        self.initialize_edit_page()
    
    def return_to_map_list(self):
        self.menu._play_sound('click')
        self.showing_edit_page = False
        self.initialize()
    
    def return_to_editor_menu(self):
        self.menu._play_sound('click')
        self.menu.quit_editor()
    
    def save_map_metadata(self):
        self.menu._play_sound('click')
        
        if self.selected_map_id not in self.map_metadata:
            self.map_metadata[self.selected_map_id] = {}
        
        self.map_metadata[self.selected_map_id].update({
            'path': f"data/maps/{self.selected_map_id}.json",
            'name': self.text_inputs['name'].text,
            'creator': self.text_inputs['creator'].text,
            'difficulty': self.difficulty_options[self.selected_difficulty],
        })
        
        if 'best_time' not in self.map_metadata[self.selected_map_id]:
            self.map_metadata[self.selected_map_id]['best_time'] = None
        
        if self.save_metadata():
            self.show_save_confirmation = True
            self.save_time = pygame.time.get_ticks()
        
    def next_difficulty(self):
        self.selected_difficulty = (self.selected_difficulty + 1) % len(self.difficulty_options)
    
    def previous_difficulty(self):
        self.selected_difficulty = (self.selected_difficulty - 1) % len(self.difficulty_options)
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.recreate_buttons()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.recreate_buttons()
    
    def update(self, events):
        super().update(events)
        
        if self.showing_edit_page:
            for input_field in self.text_inputs.values():
                for event in events:
                    input_field.handle_event(event)
                input_field.update()
    
    def draw(self, surface):
        if self.showing_edit_page:
            self.draw_edit_page(surface)
        else:            
            super().draw(surface)   
    
    def draw_edit_page(self, surface):
        center_x = DISPLAY_SIZE[0] // 2
        shadow_offset = max(1, int(2 * (DISPLAY_SIZE[1] / 1080)))
        
        # Background panel
        panel_width = int(DISPLAY_SIZE[0] * 0.8)
        panel_height = int(DISPLAY_SIZE[1] * 0.6)
        panel_x = center_x - panel_width // 2
        panel_y = DISPLAY_SIZE[1] * 0.15
        
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        surface.blit(panel, (panel_x, panel_y))
        
        # Title
        edit_title = f"Editing Map #{self.selected_map_id}"
        render_text_with_shadow(surface, edit_title, self.fonts['title'], (255, 255, 160),
                               center_x, panel_y + int(DISPLAY_SIZE[1] * 0.05), shadow_offset, True)
        
        # Draw buttons
        super().draw(surface)
        
        # Labels and content
        self._draw_labels_and_content(surface, shadow_offset, center_x, panel_x)
        
        # Text inputs
        for input_field in self.text_inputs.values():
            input_field.draw(surface)
        
        # Save confirmation
        self._draw_save_confirmation(surface, shadow_offset, center_x, panel_y, panel_height)
    
    def _draw_labels_and_content(self, surface, shadow_offset, center_x, panel_x):
        # Map name label
        render_text_with_shadow(surface, "Map Name:", self.fonts['detail'], (200, 200, 255),
                               center_x, DISPLAY_SIZE[1] * 0.30, shadow_offset, True)
        
        # Creator label
        render_text_with_shadow(surface, "Creator:", self.fonts['detail'], (200, 200, 255),
                               panel_x + int(DISPLAY_SIZE[0] * 0.05), DISPLAY_SIZE[1] * 0.41, shadow_offset, False)
        
        # Difficulty section
        right_x = DISPLAY_SIZE[0] * 0.75
        render_text_with_shadow(surface, "Difficulty:", self.fonts['detail'], (200, 200, 255),
                               right_x, DISPLAY_SIZE[1] * 0.44, shadow_offset, True)

        current_difficulty = self.difficulty_options[self.selected_difficulty]
        diff_color = self.difficulty_colors.get(current_difficulty.lower(), (200, 200, 200))

        render_text_with_shadow(surface, current_difficulty.upper(), self.fonts['detail'], diff_color,
                               right_x, DISPLAY_SIZE[1] * 0.48, shadow_offset, True)
    
    def _draw_save_confirmation(self, surface, shadow_offset, center_x, panel_y, panel_height):
        if self.show_save_confirmation:
            current_time = pygame.time.get_ticks()
            if current_time - self.save_time < 2000:
                confirm_y = panel_y + panel_height - int(DISPLAY_SIZE[1] * 0.2)
                confirm_text = "Metadata saved successfully!"
                
                text_width = self.fonts['detail'].size(confirm_text)[0] + int(DISPLAY_SIZE[0] * 0.1)
                text_height = int(DISPLAY_SIZE[1] * 0.05)
                confirm_bg = pygame.Surface((text_width, text_height), pygame.SRCALPHA)
                confirm_bg.fill((0, 0, 0, 100))
                
                surface.blit(confirm_bg, (center_x - text_width // 2, confirm_y - text_height // 2))
                render_text_with_shadow(surface, confirm_text, self.fonts['detail'], (100, 255, 100),
                                       center_x, confirm_y, shadow_offset, True)
            else:
                self.show_save_confirmation = False

class Editor:
    def __init__(self, menu, map_file=None):
        self.menu = menu
        pygame.init()
        pygame.display.set_caption('editor')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        
        self.zoom = 10
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        self.scroll = [0, 0]
        self.current_map_file = map_file
        
        self.assets = self.reload_assets()
        self.background_image = load_image('background/background.png', scale=DISPLAY_SIZE)
        self.rotated_assets = {}
        
        # Menu system
        self.menu_width = 170
        self.menu_scroll = [0, 0, 0]
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.current_rotation = 0
        self.ongrid = True
        
        self.tile_type_thumbs = self.generate_tile_type_thumbs()
        
        # Input states - simplified
        self.movement = [False] * 4
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        
        # Save notification
        self.show_save_message = False
        self.save_message_timer = 0
        self.save_message_duration = 80
        
        # Fonts
        self.font = pygame.font.SysFont(FONT, 16)
        self.save_font = pygame.font.SysFont(FONT, 32)
        
        # Load map if provided
        if map_file:
            try:
                self.tilemap.load(os.path.join('data/maps', map_file))
            except FileNotFoundError:
                pass

    def generate_tile_type_thumbs(self):
        thumbs = {}
        for tile_type in self.tile_list:
            thumb_surf = pygame.Surface((100, 24), pygame.SRCALPHA)
            variants = self.assets[tile_type]
            
            if isinstance(variants, dict):
                variant_items = list(variants.items())[:4]
                for i, (variant_key, img) in enumerate(variant_items):
                    thumb_surf.blit(pygame.transform.scale(img, (24, 24)), (i * 24, 0))
            else:
                for i, img in enumerate(variants[:4]):
                    thumb_surf.blit(pygame.transform.scale(img, (24, 24)), (i * 24, 0))
            thumbs[tile_type] = thumb_surf
        return thumbs

    def get_rotated_image(self, tile_type, variant, rotation):
        key = f"{tile_type}_{variant}_{rotation}"
        
        if key not in self.rotated_assets:
            original = self.assets[tile_type][variant]
            self.rotated_assets[key] = pygame.transform.rotate(original, rotation)
        
        return self.rotated_assets[key]
    
    def reload_assets(self):
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)
        assets = {
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/finish', scale=IMGscale),
            'ores': load_images('tiles/ores', scale=IMGscale),
            'weather': load_images('tiles/weather', scale=IMGscale),
            'kill': load_images('tiles/kill', scale=IMGscale),
            'nether': load_images('tiles/nether', scale=IMGscale),
            'wood': load_images('tiles/wood', scale=IMGscale),
            'wool': load_images('tiles/wool', scale=IMGscale),
        }
        self.rotated_assets = {}
        return assets
    
    def setZoom(self, zoom):
        self.zoom = int(zoom)
        new_tile_size = int(TILE_SIZE * self.zoom // 10)
        
        # Simplified zoom calculation
        center_offset_x = DISPLAY_SIZE[0] // 2
        center_offset_y = DISPLAY_SIZE[1] // 2
        
        self.scroll[0] = ((self.scroll[0] + center_offset_x) // self.tilemap.tile_size * 
                         new_tile_size - center_offset_x)
        self.scroll[1] = ((self.scroll[1] + center_offset_y) // self.tilemap.tile_size * 
                         new_tile_size - center_offset_y)
        
        self.tilemap.tile_size = new_tile_size
        self.assets = self.reload_assets()
        self.tile_type_thumbs = self.generate_tile_type_thumbs()
    
    def count_spawners(self):
        return len(self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=True))
    
    def rotate_spike_at_position(self, pos):
        tile_loc = f"{pos[0]};{pos[1]}"
        if tile_loc in self.tilemap.tilemap:
            tile = self.tilemap.tilemap[tile_loc]
            if tile['type'] == 'spikes':
                current_rot = tile.get('rotation', 0)
                new_rot = (current_rot - 90) % 360
                self.tilemap.tilemap[tile_loc]['rotation'] = new_rot
    
    def handle_tile_placement(self, tile_pos, mpos):
        if not self.clicking:
            return
            
        current_tile_type = self.tile_list[self.tile_group]
        
        # Remove existing spawners if placing new one
        if current_tile_type == 'spawners' and self.count_spawners() > 0:
            self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False)
        
        tile_data = {
            'type': current_tile_type,
            'variant': self.tile_variant,
            'pos': tile_pos if self.ongrid else ((mpos[0] + self.scroll[0]) / self.tilemap.tile_size, 
                                                (mpos[1] + self.scroll[1]) / self.tilemap.tile_size)
        }
        
        if current_tile_type == 'spikes':
            tile_data['rotation'] = self.current_rotation
        
        if self.ongrid:
            self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = tile_data
        elif current_tile_type not in PHYSICS_TILES:
            self.tilemap.offgrid_tiles.append(tile_data)
                
    def save_map(self):
        directory = 'data/maps'
        if not os.path.exists(directory):
            os.makedirs(directory)  
    
        if self.current_map_file:
            filename = os.path.basename(self.current_map_file)  
            file_path = os.path.join(directory, filename)
            self.tilemap.save(file_path)
            saved_map_name = filename
        else:
            next_filename = find_next_numeric_filename(directory, extension='.json')            
            file_path = self.current_map_file
            
            self.tilemap.save(file_path)

            self.current_map_file = next_filename
            saved_map_name = next_filename
        
        self.show_save_message = True
        self.save_message_timer = 0
        self.saved_map_name = saved_map_name        
        
        if not pygame.key.get_pressed()[pygame.K_o]:
            self.menu.return_to_menu()

    def handle_tile_removal(self, tile_pos, mpos):
        if not self.right_clicking:
            return
            
        # Remove grid tile
        tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
        if tile_loc in self.tilemap.tilemap:
            del self.tilemap.tilemap[tile_loc]
        
        # Remove offgrid tiles
        for tile in self.tilemap.offgrid_tiles.copy():
            tile_img = self.assets[tile['type']][tile['variant']]
            tile_r = pygame.Rect(
                tile['pos'][0] * self.tilemap.tile_size - self.scroll[0], 
                tile['pos'][1] * self.tilemap.tile_size - self.scroll[1], 
                tile_img.get_width(), tile_img.get_height()
            )
            if tile_r.collidepoint(mpos):
                self.tilemap.offgrid_tiles.remove(tile)
    
    def draw_grid(self):
        # Simplified grid drawing
        tile_size = self.tilemap.tile_size
        
        # Vertical lines
        start_x = -self.scroll[0] % tile_size
        for x in range(start_x, DISPLAY_SIZE[0], tile_size):
            pygame.draw.line(self.display, (50, 50, 50), (x, 0), (x, DISPLAY_SIZE[1]))
            
        # Horizontal lines
        start_y = -self.scroll[1] % tile_size
        for y in range(start_y, DISPLAY_SIZE[1], tile_size):
            pygame.draw.line(self.display, (50, 50, 50), (0, y), (DISPLAY_SIZE[0], y))
    
    def handle_mouse_events(self, event, tile_pos, mpos):
        in_menu = mpos[0] < self.menu_width
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if in_menu:
                    self.handle_menu_click(mpos)
                elif self.ctrl:
                    self.rotate_spike_at_position(tile_pos)
                else:
                    self.clicking = True
            elif event.button == 3 and not in_menu:  # Right click
                self.right_clicking = True
            elif event.button in [4, 5]:  # Scroll
                self.handle_scroll(event.button, mpos, in_menu)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.clicking = False
            elif event.button == 3:
                self.right_clicking = False
    
    def handle_scroll(self, button, mpos, in_menu):
        scroll_up = button == 4
        
        if in_menu:
            if mpos[1] < 120:  # Tile types section
                self.menu_scroll[0] += -1 if scroll_up else 1
            else:  # Variants section
                scroll_index = 1 if self.shift else 2
                if scroll_up:
                    self.menu_scroll[scroll_index] = max(0, self.menu_scroll[scroll_index] - 1)
                else:
                    self.menu_scroll[scroll_index] += 1
        elif self.shift:
            # Change variant
            current_type = self.tile_list[self.tile_group]
            variants = self.get_variants(current_type)
            self.tile_variant = ((self.tile_variant + (-1 if scroll_up else 1)) % len(variants))
        else:
            # Change tile type
            self.tile_group = ((self.tile_group + (-1 if scroll_up else 1)) % len(self.tile_list))
            self.tile_variant = 0
            self.current_rotation = 0
    
    def get_variants(self, tile_type):
        variants = self.assets[tile_type]
        return list(variants.keys()) if isinstance(variants, dict) else list(range(len(variants)))
    
    def handle_menu_click(self, mpos):
        if mpos[1] < 120:  # Tile type selection
            for i in range(min(4, len(self.tile_list))):
                lookup_i = (self.menu_scroll[0] + i) % len(self.tile_list)
                thumb_rect = pygame.Rect(5, 5 + i * 30, 100, 24)
                
                if thumb_rect.collidepoint(mpos):
                    self.tile_group = lookup_i
                    self.tile_variant = 0
                    self.menu_scroll[1] = self.menu_scroll[2] = 0
                    break
        else:  # Variant selection
            current_type = self.tile_list[self.tile_group]
            variants = self.get_variants(current_type)
            variants_per_row = 4
            
            for y_index in range(10):
                for x_index in range(variants_per_row):
                    variant_x = x_index + self.menu_scroll[1]
                    variant_y = y_index + self.menu_scroll[2]
                    variant_index = variant_y * variants_per_row + variant_x
                    
                    if variant_index >= len(variants):
                        continue
                    
                    tile_rect = pygame.Rect(5 + x_index * 34, 125 + y_index * 34, 30, 30)
                    
                    if tile_rect.collidepoint(mpos):
                        self.tile_variant = variants[variant_index]
                        return
    
    def handle_keyboard_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.movement[0] = True
            elif event.key == pygame.K_d:
                self.movement[1] = True
            elif event.key == pygame.K_w:
                self.movement[2] = True
            elif event.key == pygame.K_s:
                self.movement[3] = True
            elif event.key == pygame.K_g:
                self.ongrid = not self.ongrid
            elif event.key == pygame.K_o:
                self.save_map()
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = True
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = True
            elif event.key == pygame.K_ESCAPE:
                self.menu.return_to_menu()
                return True
            elif event.key == pygame.K_r and self.tile_list[self.tile_group] == 'spikes':
                self.current_rotation = (self.current_rotation + 90) % 360
            elif event.key == pygame.K_UP:
                if self.zoom < 20:
                    self.setZoom(self.zoom + 1)
            elif event.key == pygame.K_DOWN:
                if self.zoom > 1:
                    self.setZoom(self.zoom - 1)
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                self.movement[0] = False
            elif event.key == pygame.K_d:
                self.movement[1] = False
            elif event.key == pygame.K_w:
                self.movement[2] = False
            elif event.key == pygame.K_s:
                self.movement[3] = False
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = False
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = False
        
        return False
        
    def update_scroll(self):
        self.scroll[0] += (self.movement[1] - self.movement[0]) * 14
        self.scroll[1] += (self.movement[3] - self.movement[2]) * 14  
        return (int(self.scroll[0]), int(self.scroll[1]))
        
    def draw_save_notification(self):
        if not self.show_save_message:
            return
            
        overlay = pygame.Surface((DISPLAY_SIZE[0], 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        
        overlay_y = (DISPLAY_SIZE[1] - 80) // 2
        self.display.blit(overlay, (0, overlay_y))
        
        save_text = self.save_font.render(f"Map saved: {self.saved_map_name}", True, (255, 255, 255))
        text_x = (DISPLAY_SIZE[0] - save_text.get_width()) // 2
        text_y = overlay_y + (80 - save_text.get_height()) // 2
        self.display.blit(save_text, (text_x, text_y))
        
        self.save_message_timer += 1
        if self.save_message_timer >= self.save_message_duration:
            self.show_save_message = False
    
    def draw_menu(self):
        menu_surf = pygame.Surface((self.menu_width, DISPLAY_SIZE[1]), pygame.SRCALPHA)
        menu_surf.fill((0, 40, 60, 180))
        
        # Draw dividers
        pygame.draw.line(menu_surf, (0, 80, 120), (0, 120), (self.menu_width, 120))
        pygame.draw.line(menu_surf, (0, 80, 120), (self.menu_width - 1, 0), (self.menu_width - 1, DISPLAY_SIZE[1]))
        
        # Draw tile type thumbnails
        self._draw_tile_types(menu_surf)
        
        # Draw variants
        self._draw_variants(menu_surf)
        
        self.display.blit(menu_surf, (0, 0))
    
    def _draw_tile_types(self, menu_surf):
        for i in range(min(4, len(self.tile_list))):
            lookup_i = (self.menu_scroll[0] + i) % len(self.tile_list)
            tile_type = self.tile_list[lookup_i]
            thumb = self.tile_type_thumbs[tile_type]
            
            if lookup_i == self.tile_group:
                pygame.draw.rect(menu_surf, (100, 100, 255, 100), pygame.Rect(4, 4 + i * 30, 102, 26))
            
            menu_surf.blit(thumb, (5, 5 + i * 30))
            
            type_text = pygame.font.SysFont(FONT, 20).render(tile_type, True, (200, 200, 200))
            menu_surf.blit(type_text, (109, 9 + i * 30))
    
    def _draw_variants(self, menu_surf):
        current_type = self.tile_list[self.tile_group]
        variants = self.get_variants(current_type)
        variants_per_row = 4
        
        for y_index in range(10):
            for x_index in range(variants_per_row):
                variant_x = x_index + self.menu_scroll[1]
                variant_y = y_index + self.menu_scroll[2]
                variant_index = variant_y * variants_per_row + variant_x
                
                if variant_index >= len(variants):
                    continue
                
                variant = variants[variant_index]
                tile_img = self.assets[current_type][variant]
                
                if variant == self.tile_variant:
                    pygame.draw.rect(menu_surf, (255, 255, 100, 100), 
                                    pygame.Rect(4 + x_index * 34, 124 + y_index * 34, 32, 32))
                
                # Don't show rotation in menu for spikes
                display_img = (pygame.transform.scale(tile_img, (30, 30)) 
                             if current_type != 'spikes' or self.current_rotation == 0
                             else pygame.transform.scale(self.get_rotated_image(current_type, variant, 0), (30, 30)))
                
                menu_surf.blit(display_img, (5 + x_index * 34, 125 + y_index * 34))

    def draw_ui(self, current_tile_img):
        ui_x = self.menu_width + 5
        
        ui_elements = [
            f"Spawners: {self.count_spawners()}/1",
            f"Type: {self.tile_list[self.tile_group]} ({self.tile_variant})",
            f"Grid: {'On' if self.ongrid else 'Off'} (G to toggle)"
        ]
        
        for i, text in enumerate(ui_elements):
            rendered = self.font.render(text, True, (255, 255, 255))
            self.display.blit(rendered, (ui_x, 5 + i * 20))
        
        # Rotation info for spikes
        if self.tile_list[self.tile_group] == 'spikes':
            rotation_text = self.font.render(f"Rotation: {self.current_rotation}° (R to rotate)", True, (255, 255, 255))
            self.display.blit(rotation_text, (ui_x, 65))
        
        # File info
        file_text = (f"Editing: {self.current_map_file}" if self.current_map_file 
                    else "Creating new map")
        file_rendered = self.font.render(file_text, True, (255, 255, 255))
        self.display.blit(file_rendered, (ui_x, DISPLAY_SIZE[1] - 50))
        
        # Controls
        controls = self.font.render("ESC: Return to Menu | O: Save Map", True, (255, 255, 255))
        self.display.blit(controls, (ui_x, DISPLAY_SIZE[1] - 30))
        
    def run(self):
        while True:
            self.display.fill((20, 20, 20))
            
            render_scroll = self.update_scroll()
            
            # Draw grid and tilemap
            self.draw_grid()
            self.tilemap.render(self.display, offset=render_scroll, zoom=self.zoom)
            
            # Get current tile and mouse position
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            
            if self.tile_list[self.tile_group] == 'spikes':
                current_tile_img = pygame.transform.rotate(current_tile_img, self.current_rotation)
            
            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), 
                       int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            # Show tile preview and handle placement/removal outside menu
            if mpos[0] >= self.menu_width:
                if self.ongrid:
                    self.display.blit(current_tile_img, 
                                    (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], 
                                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
                else:
                    self.display.blit(current_tile_img, mpos)
            
                self.handle_tile_placement(tile_pos, mpos)
                self.handle_tile_removal(tile_pos, mpos)
            
            # Draw UI elements
            self.draw_menu()
            self.draw_ui(current_tile_img)
            self.draw_save_notification()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.handle_keyboard_events(event):
                    return 
                
                self.handle_mouse_events(event, tile_pos, mpos)
            
            pygame.display.update()
            self.clock.tick(FPS)