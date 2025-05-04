import pygame
import random
import os
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG    
from scripts.utils import load_sounds, MenuScreen
from scripts.GameManager import game_state_manager
from scripts.utils import calculate_ui_constants

class Menu:
    def __init__(self, screen):
        pygame.font.init()
        
        self.screen = screen
        self.sfx = {
            'click': load_sounds('click'),
            'music': pygame.mixer.Sound('data/sfx/music/music.mp3')
        }  
        self.played_music = False
        
        # Calculate UI constants based on screen size
        self.UI_CONSTANTS = calculate_ui_constants(DISPLAY_SIZE)
        
        # Load and scale background
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        
        # Initialize state
        self.player_type = game_state_manager.player_type
        self.selected_map = game_state_manager.selected_map
        
        # Create menu screens
        self.main_menu = MainMenuScreen(self)
        self.options_menu = OptionsMenuScreen(self)
        self.map_menu = MapSelectionScreen(self)
        
        # Start with main menu active
        self.active_menu = None
        self.main_menu.enable()
        self.active_menu = self.main_menu
        
    def _play_sound(self, sound_key):
        if sound_key in self.sfx:
            random.choice(self.sfx[sound_key]).play()
            
    def _show_options_menu(self):
        self.main_menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu

    def _show_map_selection(self):
        self.options_menu.disable()
        self.map_menu.enable()
        self.active_menu = self.map_menu

    def _return_to_main(self):
        if self.active_menu == self.options_menu:
            self.options_menu.disable()
        elif self.active_menu == self.map_menu:
            self.map_menu.disable()
        self.main_menu.enable()
        self.active_menu = self.main_menu

    def _return_to_options(self):
        self.map_menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu
        
    def _handle_escape(self):
        if self.active_menu == self.options_menu:
            self._return_to_main()
        elif self.active_menu == self.map_menu:
            self._return_to_options()

    def _set_player_type(self, value):
        self.player_type = value
        game_state_manager.player_type = value

    def edit_maps(self):
        game_state_manager.setState('editor')
        
    def _select_map(self, map_file):
        self.selected_map = os.path.join('data', 'maps', map_file)
        game_state_manager.selected_map = self.selected_map
        self.play_game()

    def play_game(self):
        game_state_manager.setState('game')

    def quit_game(self):
        pygame.time.delay(300)
        pygame.quit()
        exit()
        
    def train_ai_unavailable(self):
        if isinstance(self.active_menu, MainMenuScreen):
            self.active_menu.flash_train_ai_button()
        self._play_sound('click')

    def run(self):
        self.screen.blit(self.background, (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()

        pygame.time.Clock().tick(20)  

        self.active_menu.update(events)
        self.active_menu.draw(self.screen)


class MainMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Super Terboy"
        self.train_ai_button_index = 2
        self.flash_timer = 0
        self.is_flashing = False
        
        self.clear_buttons()
        center_x = DISPLAY_SIZE[0] // 2
        
        button_texts = ['PLAY', 'EDIT', 'TRAIN AI', 'QUIT']
        button_actions = [
            self.menu._show_options_menu,
            self.menu.edit_maps,
            self.menu.train_ai_unavailable,
            self.menu.quit_game
        ]
        
        # Use relative positioning instead of fixed coordinates
        start_y = int(DISPLAY_SIZE[1] * 0.3)  # 30% down from top
        
        self.create_centered_button_list(button_texts, button_actions, center_x, start_y)
    
    def flash_train_ai_button(self):
        self.is_flashing = True
        self.flash_timer = 0
    
    def update(self, events):
        super().update(events)
        
        if self.is_flashing:
            self.flash_timer += 1
            if self.flash_timer > 5: 
                self.is_flashing = False
    
    def draw(self, surface):
        super().draw(surface)
        
        if self.is_flashing and len(self.buttons) > self.train_ai_button_index:
            button = self.buttons[self.train_ai_button_index]
            glow_color = (255, 60, 60)  # soft red
            glow_size = int(3 * (DISPLAY_SIZE[0] / 1920))  # Scale glow with screen size

            for i in range(glow_size, 0, -1):
                alpha = 120 - i * 15
                glow_rect = button.rect.inflate(i * 4, i * 4)
                glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                
                pygame.draw.rect(
                    glow_surface,
                    (*glow_color, alpha),
                    glow_surface.get_rect(),
                    border_radius=6
                )
                surface.blit(glow_surface, (
                    button.rect.x - i * 2,
                    button.rect.y - i * 2
                ))

class OptionsMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Options"
        self.player_types = ['PL', 'AI']
        self.player_type_button_index = 1
        self.flash_timer = 0
        self.is_flashing = False

        self.clear_buttons()
        center_x = DISPLAY_SIZE[0] // 2

        def toggle_player_type():
            self.menu._set_player_type(0)  # set player type to 0 (when AI available this would toggle)
            self.flash_player_type_button()

        # Use relative positioning
        start_y = int(DISPLAY_SIZE[1] * 0.3)  # 30% down from top
        
        self.create_centered_button_list(
            ["CONTINUE", f"Player Type: {self.player_types[self.menu.player_type]}"],
            [self.menu._show_map_selection, toggle_player_type],
            center_x,
            start_y
        )

        # Back button - position relative to screen size
        back_x = int(DISPLAY_SIZE[0] * 0.02)  # 2% from left
        back_y = int(DISPLAY_SIZE[1] * 0.02)  # 2% from top
        back_width = int(DISPLAY_SIZE[0] * 0.08)  # 8% of screen width
        
        self.create_button("←", self.menu._return_to_main, back_x, back_y, back_width)

    def flash_player_type_button(self):
        self.is_flashing = True
        self.flash_timer = 0

    def update(self, events):
        super().update(events)
        if self.is_flashing:
            self.flash_timer += 1
            if self.flash_timer > 5:
                self.is_flashing = False

    def draw(self, surface):
        super().draw(surface)
        if self.is_flashing and len(self.buttons) > self.player_type_button_index:
            button = self.buttons[self.player_type_button_index]
            glow_color = (255, 60, 60)  # soft red
            glow_size = int(3 * (DISPLAY_SIZE[0] / 1920))  # Scale with screen size

            for i in range(glow_size, 0, -1):
                alpha = 120 - i * 15
                glow_rect = button.rect.inflate(i * 4, i * 4)
                glow_surface = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
                
                pygame.draw.rect(
                    glow_surface,
                    (*glow_color, alpha),
                    glow_surface.get_rect(),
                    border_radius=6
                )
                surface.blit(glow_surface, (
                    button.rect.x - i * 2,
                    button.rect.y - i * 2
                ))


class MapSelectionScreen(MenuScreen):
    def __init__(self, menu, title="Select a Map"):
        super().__init__(menu, title)
        self.current_page = 0
        self.total_pages = 0
        self.map_files = []
        self.map_numbers = []

    def initialize(self):
        self.title = "Select a Map"
        self.load_maps()
        self.recreate_buttons()

    def load_maps(self):
        maps_dir = 'data/maps'
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        
        # Sort map files numerically
        def get_map_number(filename):
            try:
                return int(filename.split('.')[0])
            except ValueError:
                return float('inf')  # Non-numeric names go to the end
                
        self.map_files.sort(key=get_map_number)
        
        self.total_pages = (len(self.map_files) + self.UI_CONSTANTS['MAPS_PER_PAGE'] - 1) // self.UI_CONSTANTS['MAPS_PER_PAGE']
        
        # Ensure current page is valid after reload
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
            
        # Create map numbers for display
        self.map_numbers = [str(i) for i in range(len(self.map_files))]

    def recreate_buttons(self):
        self.clear_buttons()
        
        # Calculate pagination
        start_index = self.current_page * self.UI_CONSTANTS['MAPS_PER_PAGE']
        end_index = min(start_index + self.UI_CONSTANTS['MAPS_PER_PAGE'], len(self.map_files))
        
        # Get maps for current page
        current_page_files = self.map_files[start_index:end_index]
        current_page_numbers = self.map_numbers[start_index:end_index]
        
        # Scale button width with screen size
        button_width = int(DISPLAY_SIZE[0] * 0.1)  # 15% of screen width
        padding = self.UI_CONSTANTS['BUTTON_SPACING']
        columns = self.UI_CONSTANTS['GRID_COLUMNS']
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (DISPLAY_SIZE[0] - grid_width) // 2
        
        # Create map selection buttons
        actions = [lambda i=i: self.menu._select_map(current_page_files[i]) for i in range(len(current_page_files))]
        self.create_grid_buttons(current_page_numbers, actions, start_x, int(DISPLAY_SIZE[1] * 0.25), button_width)
        
        # Relative positions for navigation buttons
        middle_y = DISPLAY_SIZE[1] * 0.37  # 40% down the screen
        
        # Back button - position relative to screen size
        back_x = int(DISPLAY_SIZE[0] * 0.02)  # 2% from left
        back_y = int(DISPLAY_SIZE[1] * 0.02)  # 2% from top
        back_width = int(DISPLAY_SIZE[0] * 0.08)  # 8% of screen width
        
        # Create Previous button if applicable
        if self.current_page > 0:
            prev_x = int(DISPLAY_SIZE[0] * 0.12)  # 5% from left (closer to edge)
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  # 10% of screen width
            self.create_button("◀", self.previous_page, prev_x, middle_y, nav_button_width)
        
        # Next page button - moved further to edge
        if self.current_page < self.total_pages - 1:
            next_x = int(DISPLAY_SIZE[0] * 0.8)  # 85% from left (closer to right edge)
            nav_button_width = int(DISPLAY_SIZE[0] * 0.08)  # 10% of screen width
            self.create_button("▶", self.next_page, next_x, middle_y, nav_button_width)
        
        # Create back button
        self.create_button("←", self.menu._return_to_options, back_x, back_y, back_width)


        # not needed for now 
        # reload_x = int(DISPLAY_SIZE[0] * 0.75)  # 15% from left
        # reload_y = int(DISPLAY_SIZE[1] * 0.15)  # 15% from top
        # reload_width = int(DISPLAY_SIZE[0] * 0.1)  # 15% of screen width (increased)
        # self.create_button("Sync", self.reload_maps, reload_x, reload_y, reload_width)
        
        # Add page info display with relative positioning
        if self.total_pages > 1:
            page_info = f"Page {self.current_page + 1}/{self.total_pages}"
            center_x = DISPLAY_SIZE[0] // 2
            page_y = DISPLAY_SIZE[1] * 0.7  # 70% down the screen
            page_width = int(DISPLAY_SIZE[0] * 0.25)  # 25% of screen width
            
            self.create_button(page_info, lambda: None, center_x - (page_width // 2), page_y, page_width)

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.recreate_buttons()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.recreate_buttons()

    # not needed for now
    # def reload_maps(self):
    #     self.load_maps()
    #     self.recreate_buttons()