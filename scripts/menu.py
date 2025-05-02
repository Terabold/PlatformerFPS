import pygame
import random
import os
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG
from scripts.utils import load_sounds
from scripts.utils import MenuScreen
from scripts.GameManager import game_state_manager

class Menu:
    def __init__(self, screen):
        self.sfx = {
            'click': load_sounds('click'),
            'music': pygame.mixer.Sound('data/sfx/music/music.mp3')
            }
        self.played_music = False
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        self.player_type = 0  
        self.selected_map = None  
        self.display_size = DISPLAY_SIZE
        self.font_path = FONT

        self.player_type = game_state_manager.player_type
        self.selected_map = game_state_manager.selected_map

        pygame.font.init()

        self.button_props = {
            'padding': 30,
            'height': 80,
            'min_width': 300,  
            'text_padding': 40  
        }

        self.main_menu = MainMenuScreen(self)
        self.options_menu = OptionsMenuScreen(self)
        self.map_menu = MapSelectionScreen(self)
        self.active_menu = self.main_menu
        
        self.main_menu.enable()

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
        if self.options_menu.enabled:
            self.options_menu.disable()
        elif self.map_menu.enabled:
            self.map_menu.disable()
        self.main_menu.enable()
        self.active_menu = self.main_menu

    def _return_to_options(self):
        self.map_menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu
        
    def _handle_escape(self):
        if self.active_menu == self.options_menu:
            # If on options menu, go back to main menu
            self._return_to_main()
        elif self.active_menu == self.map_menu:
            # If on map selection, go back to options
            self._return_to_options()

    def _set_player_type(self, value):
        self.player_type = value
        # Immediately update global state
        game_state_manager.player_type = value
        if self.options_menu.enabled:
            self.options_menu.update_player_type_text()

    def edit_maps(self):
        game_state_manager.setState('editor')
        
    def _select_map(self, map_file):
        self.selected_map = os.path.join('data', 'maps', map_file)
        # Immediately update global state  
        game_state_manager.selected_map = self.selected_map
        
        # After selecting a map, proceed to game directly since options are already set
        self.play_game()

    def play_game(self):
        game_state_manager.setState('game')

    def quit_game(self):
        pygame.time.delay(300)
        pygame.quit()
        exit()
        
    def train_ai_unavailable(self):
        self.main_menu.flash_train_ai_button()
        # Just play the click sound for feedback
        self._play_sound('click')

    # def play_music(self):
    #     if not self.played_music:
    #         self.sfx['music'].set_volume(0.1)  
    #         self.sfx['music'].play(-1)
    #         self.played_music = True

    # def stop_music(self):
    #     if self.played_music:
    #         self.sfx['music'].stop()
    #         self.played_music = False

    def run(self):
        self.screen.blit(self.background, (0, 0))

        # self.play_music()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                # self.stop_music()
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Changed to use the new escape handler
                    self._handle_escape()

        pygame.time.Clock().tick(20)  

        self.active_menu.update(events)
        self.active_menu.draw(self.screen)


class MainMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Super Terboy"
        self.enabled = True
        self.train_ai_button_index = 2  # Track index of TRAIN AI button
        self.flash_timer = 0
        self.is_flashing = False
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['PLAY', 'EDIT', 'TRAIN AI', 'QUIT']
        button_actions = [
            self.parent._show_options_menu,  # Play now goes to options first
            self.parent.edit_maps,
            self.parent.train_ai_unavailable,  # Training AI is not available
            self.parent.quit_game
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            300
        )
    
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
        
        if self.is_flashing and self.train_ai_button_index < len(self.button_manager.buttons):
            button = self.button_manager.buttons[self.train_ai_button_index]
            glow_color = (255, 60, 60)  # soft red
            glow_size = 3

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

        center_x = self.parent.display_size[0] // 2

        def toggle_player_type():
            # new_type = 1 - self.parent.player_type
            self.parent._set_player_type(0) # set new_type when ai available (reminder)
            self.flash_player_type_button()

        self.button_manager.create_centered_button_list(
            ["CONTINUE", f"Player Type: {self.player_types[self.parent.player_type]}", "BACK"],
            [self.parent._show_map_selection, toggle_player_type, self.parent._return_to_main],
            center_x,
            300
        )

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
        if self.is_flashing and self.player_type_button_index < len(self.button_manager.buttons):
            button = self.button_manager.buttons[self.player_type_button_index]
            flash_surface = pygame.Surface((button.rect.width, button.rect.height), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, 150))  # Semi-transparent red
            surface.blit(flash_surface, (button.rect.x, button.rect.y))

    def update_player_type_text(self):
        # Future logic for live label update
        # if self.button_manager.buttons:
        #     self.button_manager.buttons[1].text = f"Player Type: {self.player_types[self.parent.player_type]}"
        pass

    def enable(self):
        super().enable()
        # self.update_player_type_text()



class MapSelectionScreen(MenuScreen):
    def load_maps(self):
        maps_dir = 'data/maps'
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        self.map_numbers = [str(i+1) for i in range(len(self.map_files))]

    def initialize(self):
        self.title = "Select a Map"
        self.load_maps()
        maps_dir = 'data/maps'   
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        self.map_numbers = [str(i+1) for i in range(len(self.map_files))]
        
        columns = 5
        button_width = 200
        padding = self.button_manager.padding
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (self.parent.display_size[0] - grid_width) // 2
        
        def select_map(index):
            map_file = self.map_files[index]
            self.parent._select_map(map_file)
        
        actions = [lambda i=i: select_map(i) for i in range(len(self.map_files))]
        
        self.button_manager.create_grid_buttons(
            self.map_numbers,
            actions,
            columns,
            start_x,
            300,
            button_width
        )
        
        center_x = self.parent.display_size[0] // 2
        rows = (len(self.map_files) + columns - 1) // columns
        back_y = 200 + (rows + 1) * (self.button_manager.button_height + padding)
        
        # Changed BACK to go to options instead of main menu
        self.button_manager.create_centered_button_list(
            ["BACK"], 
            [self.parent._return_to_options], 
            center_x, 
            back_y
        )

        # Add "RELOAD MAPS" button
        self.button_manager.create_button(
            "RELOAD",
            self.reload_maps,  # Use the class method directly
            DISPLAY_SIZE[0] - 350,  # Center the button
            50,
            300
        )

    def reload_maps(self):
        self.button_manager.clear()  # Clear all existing buttons
        self.initialize()           # Re-initialize the screen to reload the maps
