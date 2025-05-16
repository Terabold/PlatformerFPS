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
        
        self.background = pygame.image.load(MENUBG).convert()
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        
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
        # Create a new map with default parameters
        # Generate a new map ID
        self.map_menu.showing_edit_page = True
        
        # Get the next available map number
        next_id = "1"
        if self.map_menu.map_files:
            try:
                map_ids = [int(f.split('.')[0]) for f in self.map_menu.map_files if f.split('.')[0].isdigit()]
                if map_ids:
                    next_id = str(max(map_ids) + 1)
            except:
                pass
                
        self.map_menu.selected_map_id = next_id
        self.map_menu.title = f"Creating Map #{next_id}"
        self.map_menu.initialize_edit_page()

    def start_editor(self, map_file):
        self.editor = Editor(self, map_file)  
        self.editor_active = True

    def quit_editor(self):
        # Check if we're coming from the editor and the map menu has a selected map
        if self.editor_active and self.map_menu.selected_map_id:
            # Return to edit page of current map
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Changed to match back button functionality
                    if self.map_menu.showing_edit_page:
                        # If on edit page, return to map list
                        self.map_menu.return_to_map_list()
                    else:
                        # Otherwise quit to main menu
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
        
        # Set up fonts for this screen
        info_font_size = int(DISPLAY_SIZE[1] * 0.02)  
        detail_font_size = int(DISPLAY_SIZE[1] * 0.025)  
        title_font_size = int(DISPLAY_SIZE[1] * 0.045)
        self.info_font = pygame.font.Font(FONT, info_font_size)
        self.detail_font = pygame.font.Font(FONT, detail_font_size)
        self.title_font = pygame.font.Font(FONT, title_font_size)
        
        # Store the selected map
        self.selected_map_id = None
        
        # Flag to show the edit page for a map
        self.showing_edit_page = False
        
        # Text input fields
        self.text_inputs = {}
        
        # Define difficulty options and colors
        self.difficulty_options = ['easy', 'normal', 'hard', 'expert', 'insane']
        self.selected_difficulty = 0  # Index in difficulty_options
        
        self.difficulty_colors = {
            'easy': (0, 255, 0),
            'normal': (255, 255, 0),
            'hard': (255, 165, 0),
            'expert': (255, 0, 0),
            'insane': (128, 0, 128),
        }
        
        # Save confirmation variables
        self.show_save_confirmation = False
        self.save_time = 0
        
        # Load metadata
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
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
            
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        
        def get_map_number(filename):
            try:
                return int(filename.split('.')[0])
            except ValueError:
                return float('inf')
                
        self.map_files.sort(key=get_map_number)
        
        maps_per_page = self.UI_CONSTANTS.get('MAPS_PER_PAGE', 20)  # Default to 20 if not defined
        self.total_pages = (len(self.map_files) + maps_per_page - 1) // maps_per_page
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
            
        self.map_numbers = [str(index) for index in range(len(self.map_files))]
    
    def recreate_buttons(self):
        self.clear_buttons()
        
        maps_per_page = self.UI_CONSTANTS.get('MAPS_PER_PAGE', 20)  # Default to 20 if not defined
        start_index = self.current_page * maps_per_page
        end_index = min(start_index + maps_per_page, len(self.map_files))
        
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        button_width = int(DISPLAY_SIZE[0] * 0.1)  
        padding = self.UI_CONSTANTS['BUTTON_SPACING']
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (DISPLAY_SIZE[0] - grid_width) // 2
        
        # Create actions for each map button
        actions = []
        for i in range(len(current_page_files)):
            map_index = start_index + i
            map_id = self.map_files[map_index].split('.')[0]
            actions.append(lambda idx=map_id: self.show_edit_page(idx))
            
        self.create_grid_buttons(
            current_page_numbers,
            actions,
            start_x,
            int(DISPLAY_SIZE[1] * 0.25),
            button_width
        )
        
        middle_y = DISPLAY_SIZE[1] * 0.37
        
        # Back button to editor map selection
        back_x = int(DISPLAY_SIZE[0] * 0.02)
        back_y = int(DISPLAY_SIZE[1] * 0.02)
        back_width = int(DISPLAY_SIZE[0] * 0.08)
        self.create_button("←", self.return_to_editor_menu, back_x, back_y, back_width)
        
        # Add Map button - restored from original code
        new_map_x = int(DISPLAY_SIZE[0] * 0.75)  
        new_map_y = int(DISPLAY_SIZE[1] * 0.15)  
        new_map_width = int(DISPLAY_SIZE[0] * 0.1)  
        self.create_button("Add", self.menu.create_new_map, new_map_x, new_map_y, new_map_width)
        
        # Navigation buttons for pages
        if self.current_page > 0:
            prev_x = int(DISPLAY_SIZE[0] * 0.12)
            nav_button_width = int(DISPLAY_SIZE[0] * 0.09)
            self.create_button("◀", self.previous_page, prev_x, middle_y, nav_button_width)
        
        if self.current_page < self.total_pages - 1:
            next_x = int(DISPLAY_SIZE[0] * 0.8)
            nav_button_width = int(DISPLAY_SIZE[0] * 0.09)
            self.create_button("▶", self.next_page, next_x, middle_y, nav_button_width)
        
        # Page counter
        if self.total_pages > 1:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            center_x = DISPLAY_SIZE[0] // 2
            page_y = DISPLAY_SIZE[1] * 0.68
            page_width = int(DISPLAY_SIZE[0] * 0.25)
            self.create_button(page_info, lambda: None, center_x - (page_width // 2), page_y, page_width)
    
    def initialize_edit_page(self):
        self.clear_buttons()
        
        # Back button
        back_x = int(DISPLAY_SIZE[0] * 0.02)
        back_y = int(DISPLAY_SIZE[1] * 0.02)
        back_width = int(DISPLAY_SIZE[0] * 0.08)
        self.create_button("←", self.return_to_map_list, back_x, back_y, back_width)
        
        # Define panel dimensions for reference
        panel_width = int(DISPLAY_SIZE[0] * 0.8)
        panel_height = int(DISPLAY_SIZE[1] * 0.6)
        panel_x = (DISPLAY_SIZE[0] - panel_width) // 2
        panel_y = DISPLAY_SIZE[1] * 0.15
        
        # Create save button with blue background - positioned at bottom center-left inside panel
        save_x = panel_x + int(panel_width * 0.25) - int(DISPLAY_SIZE[0] * 0.1)
        save_y = panel_y + panel_height - int(DISPLAY_SIZE[1] * 0.12)
        save_width = int(DISPLAY_SIZE[0] * 0.27)
        self.create_button("Save Changes", self.save_map_metadata, save_x, save_y, save_width, 	(30,144,255))
        
        # Create edit button with green background - positioned at bottom center-right inside panel
        edit_x = panel_x + int(panel_width * 0.75) - int(DISPLAY_SIZE[0] * 0.1)
        edit_y = panel_y + panel_height - int(DISPLAY_SIZE[1] * 0.12)
        edit_width = int(DISPLAY_SIZE[0] * 0.2)
        self.create_button("Edit Map", self.edit_selected_map, edit_x, edit_y, edit_width, (40, 180, 40))
        
        # Create difficulty cycling buttons
        self.create_difficulty_buttons()
        
        # Create text input fields
        self.create_text_inputs()
    
    def create_difficulty_buttons(self):
        button_width = int(DISPLAY_SIZE[0] * 0.03)
        
        # Adjusted Y position (lower to fit better between buttons)
        button_y = DISPLAY_SIZE[1] * 0.44  # Lowered from 0.4
        
        # Position difficulty on the right side
        right_x = DISPLAY_SIZE[0] * 0.75  # Moved from center to right side
        
        # Left difficulty button - positioned to the left of the difficulty text
        diff_left_x = right_x - int(DISPLAY_SIZE[0] * 0.09) - button_width
        self.create_button("◀", self.previous_difficulty, diff_left_x, button_y, button_width)
        
        # Right difficulty button - positioned to the right of the difficulty text
        diff_right_x = right_x + int(DISPLAY_SIZE[0] * 0.09)
        self.create_button("▶", self.next_difficulty, diff_right_x, button_y, button_width)
    
    def create_text_inputs(self):
        panel_width = int(DISPLAY_SIZE[0] * 0.8)
        panel_x = (DISPLAY_SIZE[0] - panel_width) // 2
        
        # Define input field positions and sizes
        input_width = int(DISPLAY_SIZE[0] * 0.5)
        input_height = int(DISPLAY_SIZE[1] * 0.05)
        
        # Map name input - lowered position
        name_y = DISPLAY_SIZE[1] * 0.33  # Lowered from 0.3
        name_rect = pygame.Rect(
            DISPLAY_SIZE[0] // 2 - input_width // 2,
            name_y,
            input_width,
            input_height
        )
        
        # Creator input - lowered position
        creator_y = DISPLAY_SIZE[1] * 0.44  # Lowered from 0.4 to match difficulty position
        creator_rect = pygame.Rect(
            panel_x + int(DISPLAY_SIZE[0] * 0.05),
            creator_y,
            int(input_width * 0.6),
            input_height
        )
        
        # Clear previous inputs
        self.text_inputs = {}
        
        # Get current map data
        map_data = {}
        if self.selected_map_id in self.map_metadata:
            map_data = self.map_metadata[self.selected_map_id]
        
        # Create text input fields
        self.text_inputs['name'] = TextInput(
            name_rect, 
            self.detail_font, 
            self.menu, 
            max_chars=30, 
            placeholder="Enter map name..."
        )
        self.text_inputs['name'].text = map_data.get('name', "")

        self.text_inputs['creator'] = TextInput(
            creator_rect, 
            self.detail_font, 
            self.menu, 
            max_chars=20, 
            placeholder="Creator name..."
        )
        self.text_inputs['creator'].text = map_data.get('creator', "")
        # Set the difficulty
        current_difficulty = map_data.get('difficulty', 'normal')
        if current_difficulty in self.difficulty_options:
            self.selected_difficulty = self.difficulty_options.index(current_difficulty)
        else:
            self.selected_difficulty = 1  # Default to normal
    
    def edit_selected_map(self):
        self.menu._play_sound('click')
        map_filename = f"{self.selected_map_id}.json"  # Get just the filename
        map_path = f"data/maps/{map_filename}"  # Full path
        
        # Find the actual file in map_files list to match the original code's expectations
        for map_file in self.map_files:
            if map_file == map_filename:
                self.menu._select_map(map_file)  # Pass the filename as in the original code
                return
                
        # Fallback if file not found in list (new map)
        self.menu._select_map(map_path)
    
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
        self.menu.quit_editor()  # This should properly call the parent's method to quit
    
    def save_map_metadata(self):
        self.menu._play_sound('click')
        
        # Create or update metadata for this map
        if self.selected_map_id not in self.map_metadata:
            self.map_metadata[self.selected_map_id] = {}
        
        # Update with new values from text inputs
        self.map_metadata[self.selected_map_id].update({
            'path': f"data/maps/{self.selected_map_id}.json",
            'name': self.text_inputs['name'].text,
            'creator': self.text_inputs['creator'].text,
            'difficulty': self.difficulty_options[self.selected_difficulty],
        })
        
        # Keep existing best_time if present
        if 'best_time' not in self.map_metadata[self.selected_map_id]:
            self.map_metadata[self.selected_map_id]['best_time'] = None
        
        # Save to file
        if self.save_metadata():
            # Show save confirmation message
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
        
        # Update text inputs if on edit page
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
        # Draw panel and other background elements first
        center_x = DISPLAY_SIZE[0] // 2
        shadow_offset = max(1, int(2 * (DISPLAY_SIZE[1] / 1080)))
        
        # Draw the background panel
        panel_width = int(DISPLAY_SIZE[0] * 0.8)
        panel_height = int(DISPLAY_SIZE[1] * 0.6)
        panel_x = center_x - panel_width // 2
        panel_y = DISPLAY_SIZE[1] * 0.15
        
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        surface.blit(panel, (panel_x, panel_y))
        
        # Draw "Editing Map #number" inside the panel
        edit_title = f"Editing Map #{self.selected_map_id}"
        render_text_with_shadow(
            surface,
            edit_title,
            self.title_font,
            (255, 255, 160),  # Gold/yellow color
            center_x,
            panel_y + int(DISPLAY_SIZE[1] * 0.05),  # Position inside panel
            shadow_offset,
            True
        )
        
        # Draw buttons on top of the panel now
        super().draw(surface)
        
        # Draw field labels and other content after buttons
        name_label_y = DISPLAY_SIZE[1] * 0.30  # Lowered from 0.27
        render_text_with_shadow(
            surface,
            "Map Name:",
            self.detail_font,
            (200, 200, 255),
            center_x,
            name_label_y,
            shadow_offset,
            True
        )
        
        creator_label_x = panel_x + int(DISPLAY_SIZE[0] * 0.05)
        creator_label_y = DISPLAY_SIZE[1] * 0.41  # Lowered from 0.37
        render_text_with_shadow(
            surface,
            "Creator:",
            self.detail_font,
            (200, 200, 255),
            creator_label_x,
            creator_label_y,
            shadow_offset,
            False  # Left-aligned
        )
        
        # Draw difficulty label
        difficulty_label_y = DISPLAY_SIZE[1] * 0.44  # Lowered from 0.37
        right_x = DISPLAY_SIZE[0] * 0.75  # Right side position
        render_text_with_shadow(
            surface,
            "Difficulty:",
            self.detail_font,
            (200, 200, 255),
            right_x,
            difficulty_label_y,
            shadow_offset,
            True
        )

        # Draw current difficulty
        current_difficulty = self.difficulty_options[self.selected_difficulty]
        diff_color = self.difficulty_colors.get(current_difficulty.lower(), (200, 200, 200))

        diff_text_y = DISPLAY_SIZE[1] * 0.48

        render_text_with_shadow(
            surface,
            current_difficulty.upper(),
            self.detail_font,
            diff_color,
            right_x,
            diff_text_y,
            shadow_offset,
            True
        )
        
        # Draw text input fields
        for input_field in self.text_inputs.values():
            input_field.draw(surface)
        
        # Draw save confirmation if recently saved
        if self.show_save_confirmation:
            current_time = pygame.time.get_ticks()
            if current_time - self.save_time < 2000:  # Show for 2 seconds
                confirm_y = panel_y + panel_height - int(DISPLAY_SIZE[1] * 0.2)  # Moved up
                
                confirm_text = "Metadata saved successfully!"
                
                # Semi-transparent background
                text_width = self.detail_font.size(confirm_text)[0] + int(DISPLAY_SIZE[0] * 0.1)
                text_height = int(DISPLAY_SIZE[1] * 0.05)
                confirm_bg = pygame.Surface((text_width, text_height), pygame.SRCALPHA)
                confirm_bg.fill((0, 0, 0, 100))
                
                surface.blit(confirm_bg, (center_x - text_width // 2, confirm_y - text_height // 2))
                
                render_text_with_shadow(
                    surface,
                    confirm_text,
                    self.detail_font,
                    (100, 255, 100),
                    center_x,
                    confirm_y,
                    shadow_offset,
                    True
                )
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
            
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.current_rotation = 0
        self.ongrid = True
        
        self.movement = [False, False, False, False]  
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        
        
        self.show_save_message = False
        self.save_message_timer = 0
        self.save_message_duration = 80  

        
        self.font = pygame.font.SysFont(FONT, 16)
        self.save_font = pygame.font.SysFont(FONT, 32)
        
        
        if map_file:
            try:
                self.tilemap.load(os.path.join('data/maps', map_file))
            except FileNotFoundError:
                pass

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
        self.scroll[0] = (self.scroll[0] + DISPLAY_SIZE[0]//2) // self.tilemap.tile_size * new_tile_size - DISPLAY_SIZE[0]//2
        self.scroll[1] = (self.scroll[1] + DISPLAY_SIZE[1]//2) // self.tilemap.tile_size * new_tile_size - DISPLAY_SIZE[1]//2
        self.tilemap.tile_size = new_tile_size
        self.assets = self.reload_assets()
    
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
        current_tile_type = self.tile_list[self.tile_group]
        
        
        if self.ongrid and self.clicking:
            
            if current_tile_type == 'spawners' and self.count_spawners() > 0:
                self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False)
            
            
            tile_data = {
                'type': current_tile_type,
                'variant': self.tile_variant,
                'pos': tile_pos
            }
            
            
            if current_tile_type == 'spikes':
                tile_data['rotation'] = self.current_rotation
                
            
            self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = tile_data
        
        
        elif not self.ongrid and self.clicking:
            if current_tile_type == 'spawners' and self.count_spawners() > 0:
                return
                
            if current_tile_type not in PHYSICS_TILES:
                tile_pos = ((mpos[0] + self.scroll[0]) / self.tilemap.tile_size, 
                           (mpos[1] + self.scroll[1]) / self.tilemap.tile_size)
                
                tile_data = {
                    'type': current_tile_type,
                    'variant': self.tile_variant,
                    'pos': tile_pos
                }
                
                
                if current_tile_type == 'spikes':
                    tile_data['rotation'] = self.current_rotation
                    
                self.tilemap.offgrid_tiles.append(tile_data)
                
    def save_map(self):
        directory = 'data/maps'
        if not os.path.exists(directory):
            os.makedirs(directory)  
    
        if self.current_map_file:
            file_path = os.path.join(directory, self.current_map_file)
            self.tilemap.save(file_path)
            saved_map_name = self.current_map_file
        else:
            next_filename = find_next_numeric_filename(directory, extension='.json')            
            file_path = os.path.join(directory, next_filename)
            
            self.tilemap.save(file_path)

            self.current_map_file = next_filename
            saved_map_name = next_filename
        
        self.show_save_message = True
        self.save_message_timer = 0
        self.saved_map_name = saved_map_name        
        
        if not pygame.key.get_pressed()[pygame.K_o]:
            self.menu.return_to_menu()

    def handle_tile_removal(self, tile_pos, mpos):
        if self.right_clicking:
            
            tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
            if tile_loc in self.tilemap.tilemap:
                del self.tilemap.tilemap[tile_loc]
            
            
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
        for x in range(0, DISPLAY_SIZE[0], self.tilemap.tile_size):
            offset_x = x - self.scroll[0] % self.tilemap.tile_size
            pygame.draw.line(
                self.display, (50, 50, 50), 
                (offset_x, 0), (offset_x, DISPLAY_SIZE[1])
            )
            
        for y in range(0, DISPLAY_SIZE[1], self.tilemap.tile_size):
            offset_y = y - self.scroll[1] % self.tilemap.tile_size
            pygame.draw.line(
                self.display, (50, 50, 50), 
                (0, offset_y), (DISPLAY_SIZE[0], offset_y)
            )
    
    def handle_mouse_events(self, event, tile_pos, mpos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  
                if self.ctrl:
                    self.rotate_spike_at_position(tile_pos)
                else:
                    self.clicking = True
            
            elif event.button == 3:  
                self.right_clicking = True
                
            
            elif event.button == 4:  
                if self.shift:
                    
                    current_type = self.tile_list[self.tile_group]
                    self.tile_variant = (self.tile_variant - 1) % len(self.assets[current_type])
                else:
                    
                    self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                    self.tile_variant = 0
                    self.current_rotation = 0
                    
            elif event.button == 5:  
                if self.shift:
                    
                    current_type = self.tile_list[self.tile_group]
                    self.tile_variant = (self.tile_variant + 1) % len(self.assets[current_type]) 
                else:
                    
                    self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                    self.tile_variant = 0
                    self.current_rotation = 0

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.clicking = False
            elif event.button == 3:
                self.right_clicking = False
    
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
                    self.setZoom(self.zoom+1)
                            
            elif event.key == pygame.K_DOWN:
                if self.zoom > 1:
                    self.setZoom(self.zoom-1)
        
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
        self.scroll[0] += (self.movement[1] - self.movement[0]) * 8  
        self.scroll[1] += (self.movement[3] - self.movement[2]) * 8  
        return (int(self.scroll[0]), int(self.scroll[1]))
        
    def draw_save_notification(self):
        if self.show_save_message:
            
            overlay = pygame.Surface((DISPLAY_SIZE[0], 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            
            overlay_y = (DISPLAY_SIZE[1] - overlay.get_height()) // 2
            self.display.blit(overlay, (0, overlay_y))
            
            save_text = self.save_font.render(f"Map saved: {self.saved_map_name}", True, (255, 255, 255))
            text_x = (DISPLAY_SIZE[0] - save_text.get_width()) // 2
            text_y = overlay_y + (overlay.get_height() - save_text.get_height()) // 2
            self.display.blit(save_text, (text_x, text_y))
            
            self.save_message_timer += 1
            if self.save_message_timer >= self.save_message_duration:
                self.show_save_message = False
    
    def draw_ui(self, current_tile_img):
        
        self.display.blit(current_tile_img, (5, 5))
        
        spawner_count = self.count_spawners()
        spawner_text = self.font.render(f"Spawners: {spawner_count}/1", True, (255, 255, 255))
        self.display.blit(spawner_text, (5, 40))
        
        current_type = self.tile_list[self.tile_group]
        tile_info = self.font.render(f"Type: {current_type} ({self.tile_variant})", True, (255, 255, 255))
        self.display.blit(tile_info, (5, 60))
        
        
        if current_type == 'spikes':
            rotation_info = self.font.render(f"Rotation: {self.current_rotation}°", True, (255, 255, 255))
            self.display.blit(rotation_info, (5, 80))
            
            controls_info = self.font.render("R: Rotate spike | Ctrl+Click: Rotate placed spike", True, (255, 255, 255))
            self.display.blit(controls_info, (5, 100))
        
        
        if self.current_map_file:
            file_info = self.font.render(f"Editing: {self.current_map_file}", True, (255, 255, 255))
            self.display.blit(file_info, (5, DISPLAY_SIZE[1] - 50))
        else:
            new_map_info = self.font.render("Creating new map", True, (255, 255, 255))
            self.display.blit(new_map_info, (5, DISPLAY_SIZE[1] - 50))
        
        
        menu_info = self.font.render("ESC: Return to Menu | O: Save Map", True, (255, 255, 255))
        self.display.blit(menu_info, (5, DISPLAY_SIZE[1] - 30))
        
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            self.display.fill((20, 20, 20))
            
            self.draw_grid()
            
            render_scroll = self.update_scroll()
            
            self.tilemap.render(self.display, offset=render_scroll, zoom=self.zoom)
            
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            
            if self.tile_list[self.tile_group] == 'spikes':
                current_tile_img = pygame.transform.rotate(current_tile_img, self.current_rotation)
            
            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), 
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size)
            )
            
            if self.ongrid:
                self.display.blit(
                    current_tile_img, 
                    (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], 
                    tile_pos[1] * self.tilemap.tile_size - self.scroll[1])
                )
            else:
                self.display.blit(current_tile_img, mpos)
            
            self.handle_tile_placement(tile_pos, mpos)
            self.handle_tile_removal(tile_pos, mpos)
            
            self.draw_ui(current_tile_img)
            
            self.draw_save_notification()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.handle_keyboard_events(event):
                    return 
                
                self.handle_mouse_events(event, tile_pos, mpos)
            
            pygame.display.update()
            clock.tick(FPS)