import pygame
import random
import os
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG
from scripts.utils import load_sounds
from scripts.utils import MenuScreen

class Menu:
    def __init__(self, screen):
        self.sfx = {'click': load_sounds('click')}
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        self.player_type = 0  
        self.selected_map = None  
        self.display_size = DISPLAY_SIZE
        self.font_path = FONT

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

    def _show_map_selection(self):
        self.main_menu.disable()
        self.map_menu.enable()
        self.active_menu = self.map_menu

    def _show_options_menu(self):
        if self.map_menu.enabled:
            self.map_menu.disable()
        else:
            self.main_menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu

    def _return_to_main(self):
        self.map_menu.disable()
        self.main_menu.enable()
        self.active_menu = self.main_menu

    def _return_to_map_selection(self):
        self.options_menu.disable()
        self.map_menu.enable()
        self.active_menu = self.map_menu

    def _set_player_type(self, value):
        self.player_type = value
        if self.options_menu.enabled:
            self.options_menu.update_player_type_text()
        
    def _select_map(self, map_file):
        self.selected_map = map_file
        self._show_options_menu()

    def play_game(self):
        from scripts.GameManager import game_state_manager
        game_state_manager.player_type = self.player_type
        
        if self.selected_map:
            game_state_manager.selected_map = self.selected_map
            
        game_state_manager.setState('game')

    def quit_game(self):
        pygame.time.delay(300)
        pygame.quit()
        exit()

    def run(self):
        self.screen.blit(self.background, (0, 0))
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.time.Clock().tick(30)  

        self.active_menu.update(events)
        self.active_menu.draw(self.screen)


class MainMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Super Terboy"
        self.enabled = True
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['PLAY', 'TRAIN AI', 'QUIT']
        button_actions = [
            self.parent._show_map_selection,
            self.parent._show_options_menu,
            self.parent.quit_game
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            300
        )


class MapSelectionScreen(MenuScreen):
    def initialize(self):
        self.title = "Select a Map"
        
        maps_dir = 'data/maps'   
        self.map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
        self.map_numbers = [str(i+1) for i in range(len(self.map_files))]
        
        columns = 5
        button_width = 200
        padding = self.button_manager.padding
        
        grid_width = columns * (button_width + padding) - padding
        start_x = (self.parent.display_size[0] - grid_width) // 2
        
        actions = [lambda i=i: self.parent._select_map(self.map_files[i]) for i in range(len(self.map_files))]
        
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
        
        self.button_manager.create_centered_button_list(
            ["BACK"], 
            [self.parent._return_to_main], 
            center_x, 
            back_y
        )


class OptionsMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Options"
        
        self.player_types = ['PL', 'AI']
        
        center_x = self.parent.display_size[0] // 2
        
        def toggle_player_type():
            new_type = 1 - self.parent.player_type
            self.parent._set_player_type(new_type)
        
        self.button_manager.create_centered_button_list(
            [f"Player Type: {self.player_types[self.parent.player_type]}", "START GAME", "BACK"],
            [toggle_player_type, self.parent.play_game, self.parent._return_to_map_selection],
            center_x,
            300
        )
    
    def update_player_type_text(self):
        if self.button_manager.buttons:
            self.button_manager.buttons[0].text = f"Player Type: {self.player_types[self.parent.player_type]}"

    def enable(self):
        super().enable()
        
        if self.button_manager.buttons:
            self.button_manager.buttons[0].text = f"Player Type: {self.player_types[self.parent.player_type]}"