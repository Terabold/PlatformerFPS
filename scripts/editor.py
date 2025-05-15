import sys
import pygame
import os
import random
from scripts.utils import load_images, load_image, find_next_numeric_filename, MenuScreen, load_sounds
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
        self.start_editor(None)

    def start_editor(self, map_file):
        self.editor = Editor(self, map_file)  
        self.editor_active = True

    def quit_editor(self):
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
                    self.quit_editor()

        self.map_menu.update(events)
        self.map_menu.draw(self.screen)

class EditorMapSelectionScreen(MenuScreen):
    def __init__(self, menu, title="Edit a Map"):
        super().__init__(menu, title)
        self.current_page = 0
        self.total_pages = 0
        self.map_files = []
        self.map_numbers = []

    def initialize(self):
        self.title = "Edit a Map"
        self.load_maps()
        self.create_map_buttons()
        
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
        
        maps_per_page = 20
        self.total_pages = (len(self.map_files) + maps_per_page - 1) // maps_per_page
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        self.map_numbers = [str(index) for index in range(len(self.map_files))]
    
    def create_map_buttons(self):
        self.clear_buttons()
        
        maps_per_page = 20
        
        start_index = self.current_page * maps_per_page
        end_index = min(start_index + maps_per_page, len(self.map_files))
        
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        button_width = int(DISPLAY_SIZE[0] * 0.1)  
        padding = self.UI_CONSTANTS['BUTTON_SPACING']
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (DISPLAY_SIZE[0] - grid_width) // 2
        
        
        actions = [lambda i=i: self.menu._select_map(self.map_files[start_index + i]) 
                  for i in range(len(current_page_files))]
        
        self.create_grid_buttons(
            current_page_numbers,
            actions,
            start_x,
            int(DISPLAY_SIZE[1] * 0.25),  
            button_width
        )
        
        middle_y = DISPLAY_SIZE[1] * 0.37  
        
        back_x = int(DISPLAY_SIZE[0] * 0.02)  
        back_y = int(DISPLAY_SIZE[1] * 0.02)  
        back_width = int(DISPLAY_SIZE[0] * 0.08)  
        self.create_button("←", self.menu.quit_editor, back_x, back_y, back_width)
        
        
        new_map_x = int(DISPLAY_SIZE[0] * 0.75)  
        new_map_y = int(DISPLAY_SIZE[1] * 0.15)  
        new_map_width = int(DISPLAY_SIZE[0] * 0.1)  
        self.create_button("Add", self.menu.create_new_map, new_map_x, new_map_y, new_map_width)
        
        if self.current_page > 0:
            prev_x = int(DISPLAY_SIZE[0] * 0.12)  
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  
            self.create_button("◀", self.previous_page, prev_x, middle_y, nav_button_width)
        
        if self.current_page < self.total_pages - 1:
            next_x = int(DISPLAY_SIZE[0] * 0.8)  
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  
            self.create_button("▶", self.next_page, next_x, middle_y, nav_button_width)
         
        if self.total_pages > 1:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            center_x = DISPLAY_SIZE[0] // 2
            page_y = DISPLAY_SIZE[1] * 0.7  
            page_width = int(DISPLAY_SIZE[0] * 0.25)  
            
            self.create_button(page_info, lambda: None, center_x - (page_width // 2), page_y, page_width)
    
    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.create_map_buttons()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.create_map_buttons()
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