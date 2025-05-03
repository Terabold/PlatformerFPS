import sys
import pygame
import os
import random
from scripts.utils import load_images, load_image, find_next_numeric_filename, MenuScreen, load_sounds
from scripts.tilemap import Tilemap
from scripts.constants import TILE_SIZE, DISPLAY_SIZE, FPS, PHYSICS_TILES, FONT, MENUBG
from scripts.GameManager import game_state_manager

class EditorMenu:
    def __init__(self, display):
        self.screen = display
        self.sfx = {'click': load_sounds('click')}
        self.background = pygame.image.load(MENUBG).convert()
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
     
        self.selected_map = None
        self.display_size = DISPLAY_SIZE
        self.font_path = FONT
        self.editor_active = False
        self.editor = None

        self.button_props = {
            'padding': 30,
            'height': 80,
            'min_width': 300,
            'text_padding': 40
        }

        self.map_menu = MapSelectionScreen(self)
        self.map_menu.enable()

    def _play_sound(self, sound_key):
        if sound_key in self.sfx:
            random.choice(self.sfx[sound_key]).play()

    def _select_map(self, map_file):
        self.selected_map = map_file
        self.start_editor(map_file)

    def create_new_map(self):
        self.start_editor(None)

    def start_editor(self, map_file):
        self.editor = Editor(self, map_file)
        self.editor_active = True

    def quit_editor(self):
        # Return to the main menu
        game_state_manager.setState('menu')

    def return_to_menu(self):
        # Return to the map selection screen within the editor
        self.editor_active = False
        self.editor = None
        # Refresh the map menu to show any newly saved maps
        self.map_menu = MapSelectionScreen(self)
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
                    # When pressing escape in the map selection screen of editor,
                    # return to the main menu
                    self.quit_editor()

        self.map_menu.update(events)
        self.map_menu.draw(self.screen)

class MapSelectionScreen(MenuScreen):
    def __init__(self, parent, title="Edit a Map"):
        self.maps_per_page = 20  
        self.current_page = 0  # Start with page 0 (first page)
        super().__init__(parent, title)

    def initialize(self):
        self.title = "Edit a Map"
        
        self.load_maps()
        self.create_map_buttons()
        
    def load_maps(self):
        maps_dir = 'data/maps'
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
            
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        
        # Sort map files numerically
        def get_map_number(filename):
            try:
                return int(filename.split('.')[0])
            except ValueError:
                return float('inf')  # Non-numeric names go to the end
                
        self.map_files.sort(key=get_map_number)
        
        # Calculate total pages
        self.total_pages = (len(self.map_files) + self.maps_per_page - 1) // self.maps_per_page
        
        # Ensure current page is valid
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        # Use the actual filename as the display text for better identification
        self.map_numbers = [str(index + 1) for index in range(len(self.map_files))]
    
    def create_map_buttons(self):
        # Clear existing buttons
        self.button_manager.clear()
        
        # Calculate pagination
        start_index = self.current_page * self.maps_per_page
        end_index = min(start_index + self.maps_per_page, len(self.map_files))
        
        # Get maps for current page
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        columns = 5
        button_width = 200
        padding = self.button_manager.padding
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (self.parent.display_size[0] - grid_width) // 2
        
        # Create actions for selecting maps
        actions = [lambda i=i: self.parent._select_map(self.map_files[start_index + i]) 
                  for i in range(len(current_page_files))]
        
        # Add display labels for current page
        display_labels = current_page_numbers
        
        # Position for the map grid - ensure it's below the title
        grid_start_y = 275  # Adjusted to avoid overlapping with the title
        
        # Create map buttons
        self.button_manager.create_grid_buttons(
            display_labels,
            actions,
            columns,
            start_x,
            grid_start_y,
            button_width
        )
        
        # Calculate the fixed position for navigation arrows
        middle_y = DISPLAY_SIZE[1] / 2 - 100
        
        # Add "Return" button at top left
        return_button_width = 100
        self.button_manager.create_button(
            "←", 
            self.parent.quit_editor, 
            20,  # Left edge with some margin
            20,   # Top edge with some margin
            return_button_width
        )
        
        # Add "New Map" button at top right
        new_button_width = 175
        self.button_manager.create_button(
            "Add", 
            self.parent.create_new_map, 
            start_x,
            grid_start_y - 100,  # Top edge with some margin
            new_button_width
        )
        
        # Previous page button (if not on first page)
        if self.current_page > 0:
            self.button_manager.create_button(
                "◀",
                self.previous_page,
                250,  # Left side
                middle_y,  # Middle of the map grid height
                100
            )
        
        # Next page button (if not on last page)
        if self.current_page < self.total_pages - 1:
            self.button_manager.create_button(
                "▶",
                self.next_page,
                DISPLAY_SIZE[0] - 350,  # Right side
                middle_y,  # Middle of the map grid height
                100
            )
        
        pagebutton_width = 400
        # Add pagination info at bottom center
        if self.total_pages > 1:
            # Page info display
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            center_x = DISPLAY_SIZE[0] // 2
            bottom_y = DISPLAY_SIZE[1] * 0.7  # Bottom with margin
            
            self.button_manager.create_button(
                page_info,
                lambda: None,  # No action for info display
                center_x - pagebutton_width/2,  # Centered
                bottom_y,
                pagebutton_width
            )
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.create_map_buttons()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.create_map_buttons()
            
    def enable(self):
        self.enabled = True
        # Refresh maps when enabling the screen
        self.load_maps()
        self.create_map_buttons()

class Editor:
    def __init__(self, menu, map_file=None):
        self.menu = menu
        pygame.init()
        pygame.display.set_caption('editor')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        
        # Core settings
        self.zoom = 10
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        self.scroll = [0, 0]
        
        # Store the current map file path
        self.current_map_file = map_file
        
        # Asset handling
        self.assets = self.reload_assets()
        self.background_image = load_image('background.png', scale=DISPLAY_SIZE)
        self.rotated_assets = {}
        
        # Tile selection
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.current_rotation = 0
        self.ongrid = True
        
        # Input states
        self.movement = [False, False, False, False]  # Left, Right, Up, Down
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ctrl = False
        
        # Save notification
        self.show_save_message = False
        self.save_message_timer = 0
        self.save_message_duration = 80  

        # UI
        self.font = pygame.font.SysFont(FONT, 16)
        self.save_font = pygame.font.SysFont(FONT, 32)
        
        # Load existing map if available
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
            # 'ores': load_images('tiles/ores', scale=IMGscale),
            'weather': load_images('tiles/weather', scale=IMGscale),
            'kill': load_images('tiles/kill', scale=IMGscale),
            'nether': load_images('tiles/nether', scale=IMGscale),
            'wood': load_images('tiles/wood', scale=IMGscale),
            # 'wool': load_images('tiles/wool', scale=IMGscale),
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
        
        # Handle grid-based placement
        if self.ongrid and self.clicking:
            # Special handling for spawners - only allow one
            if current_tile_type == 'spawners' and self.count_spawners() > 0:
                self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False)
            
            # Create tile data with rotation if needed
            tile_data = {
                'type': current_tile_type,
                'variant': self.tile_variant,
                'pos': tile_pos
            }
            
            # Add rotation for spikes
            if current_tile_type == 'spikes':
                tile_data['rotation'] = self.current_rotation
                
            # Add to tilemap
            self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = tile_data
        
        # Handle off-grid placement
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
                
                # Add rotation for spikes
                if current_tile_type == 'spikes':
                    tile_data['rotation'] = self.current_rotation
                    
                self.tilemap.offgrid_tiles.append(tile_data)
                
    def save_map(self):
        directory = 'data/maps'
        if not os.path.exists(directory):
            os.makedirs(directory)  # Ensure the directory exists
            
        # If editing an existing map, update it directly
        if self.current_map_file:
            self.tilemap.save(os.path.join(directory, self.current_map_file))
            saved_map_name = self.current_map_file
        else:
            # For new maps, create a new file
            next_filename = find_next_numeric_filename(directory, extension='.json')
            self.current_map_file = next_filename  # Update the current map file
            self.tilemap.save(os.path.join(directory, next_filename))
            saved_map_name = next_filename
        
        # Set the save notification
        self.show_save_message = True
        self.save_message_timer = 0
        self.saved_map_name = saved_map_name
        
        # Return to menu immediately if called from elsewhere
        if not pygame.key.get_pressed()[pygame.K_o]:
            self.menu.return_to_menu()

    def handle_tile_removal(self, tile_pos, mpos):
        if self.right_clicking:
            # Remove grid tiles
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
            if event.button == 1:  # Left click
                if self.ctrl:
                    self.rotate_spike_at_position(tile_pos)
                else:
                    self.clicking = True
            
            elif event.button == 3:  # Right click
                self.right_clicking = True
                
            # Mouse wheel for tile selection
            elif event.button == 4:  # Scroll up
                if self.shift:
                    # Change variant
                    current_type = self.tile_list[self.tile_group]
                    self.tile_variant = (self.tile_variant - 1) % len(self.assets[current_type])
                else:
                    # Change tile type
                    self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                    self.tile_variant = 0
                    self.current_rotation = 0
                    
            elif event.button == 5:  # Scroll down
                if self.shift:
                    # Change variant
                    current_type = self.tile_list[self.tile_group]
                    self.tile_variant = (self.tile_variant + 1) % len(self.assets[current_type]) 
                else:
                    # Change tile type
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
            # Movement keys
            if event.key == pygame.K_a:
                self.movement[0] = True
            elif event.key == pygame.K_d:
                self.movement[1] = True
            elif event.key == pygame.K_w:
                self.movement[2] = True
            elif event.key == pygame.K_s:
                self.movement[3] = True
            
            # Feature keys
            elif event.key == pygame.K_g:
                self.ongrid = not self.ongrid
            elif event.key == pygame.K_o:
                self.save_map()
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = True
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = True
            elif event.key == pygame.K_ESCAPE:  # This is the key change
                self.menu.return_to_menu()
                return True  # Indicate we want to exit the editor
            
            # Spike rotation
            elif event.key == pygame.K_r and self.tile_list[self.tile_group] == 'spikes':
                self.current_rotation = (self.current_rotation + 90) % 360
            
            # Zoom controls
            elif event.key == pygame.K_UP:
                if self.zoom < 20:
                    self.setZoom(self.zoom+1)
                            
            elif event.key == pygame.K_DOWN:
                if self.zoom > 1:
                    self.setZoom(self.zoom-1)
        
        elif event.type == pygame.KEYUP:
            # Movement keys
            if event.key == pygame.K_a:
                self.movement[0] = False
            elif event.key == pygame.K_d:
                self.movement[1] = False
            elif event.key == pygame.K_w:
                self.movement[2] = False
            elif event.key == pygame.K_s:
                self.movement[3] = False
            
            # Modifier keys
            elif event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                self.shift = False
            elif event.key in {pygame.K_LCTRL, pygame.K_RCTRL}:
                self.ctrl = False
        
        return False
    
    def update_scroll(self):
        self.scroll[0] += (self.movement[1] - self.movement[0]) * 8  # Horizontal
        self.scroll[1] += (self.movement[3] - self.movement[2]) * 8  # Vertical
        return (int(self.scroll[0]), int(self.scroll[1]))
        
    def draw_save_notification(self):
        if self.show_save_message:
            # Create a semi-transparent background
            overlay = pygame.Surface((DISPLAY_SIZE[0], 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            
            # Position the overlay in the middle of the screen
            overlay_y = (DISPLAY_SIZE[1] - overlay.get_height()) // 2
            self.display.blit(overlay, (0, overlay_y))
            
            # Render and position the text
            save_text = self.save_font.render(f"Map saved: {self.saved_map_name}", True, (255, 255, 255))
            text_x = (DISPLAY_SIZE[0] - save_text.get_width()) // 2
            text_y = overlay_y + (overlay.get_height() - save_text.get_height()) // 2
            self.display.blit(save_text, (text_x, text_y))
            
            # Update timer and check if we should hide the message
            self.save_message_timer += 1
            if self.save_message_timer >= self.save_message_duration:
                self.show_save_message = False
    
    def draw_ui(self, current_tile_img):
        # Show current tile preview
        self.display.blit(current_tile_img, (5, 5))
        
        # Show spawner count
        spawner_count = self.count_spawners()
        spawner_text = self.font.render(f"Spawners: {spawner_count}/1", True, (255, 255, 255))
        self.display.blit(spawner_text, (5, 40))
        
        # Show current tile info
        current_type = self.tile_list[self.tile_group]
        tile_info = self.font.render(f"Type: {current_type} ({self.tile_variant})", True, (255, 255, 255))
        self.display.blit(tile_info, (5, 60))
        
        # Show spike rotation info if applicable
        if current_type == 'spikes':
            rotation_info = self.font.render(f"Rotation: {self.current_rotation}°", True, (255, 255, 255))
            self.display.blit(rotation_info, (5, 80))
            
            controls_info = self.font.render("R: Rotate spike | Ctrl+Click: Rotate placed spike", True, (255, 255, 255))
            self.display.blit(controls_info, (5, 100))
        
        # Show file info
        if self.current_map_file:
            file_info = self.font.render(f"Editing: {self.current_map_file}", True, (255, 255, 255))
            self.display.blit(file_info, (5, DISPLAY_SIZE[1] - 50))
        else:
            new_map_info = self.font.render("Creating new map", True, (255, 255, 255))
            self.display.blit(new_map_info, (5, DISPLAY_SIZE[1] - 50))
        
        # Show menu return info
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
            
            # Draw save notification over everything else
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