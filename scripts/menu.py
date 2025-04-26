import pygame
import random
import pygame_menu
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG, MENUTXTCOLOR, WHITE
from scripts.utils import load_sounds


class Menu:
    def __init__(self, screen):
        self.sfx = {'click': load_sounds('click')}
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        self.player_type = 0  # Default player type

        pygame.font.init()

        # Create themes and base menus
        self._setup_theme()
        self.main_menu = self._create_main_menu()
        self.options_menu = self._create_options_menu()

        self.active_menu = self.main_menu

    def _setup_theme(self):
        title_font = pygame.font.Font(FONT, 85)
        widget_font = pygame.font.Font(FONT, 50)

        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(20, 30))
        selection_effect.color = (255, 215, 0) 

        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 0), 
            title_background_color=(0, 0, 0, 0),
            title_font=title_font,
            title_font_color=WHITE,
            title_offset=(DISPLAY_SIZE[0] / 4, 20),
            widget_font=widget_font,
            widget_font_color=(255, 255, 255),  
            widget_margin=(0, 30),
            widget_selection_effect=selection_effect,
            selection_color=(160, 111, 78), 
        )

    def _play_sound(self, sound_key):
        if sound_key in self.sfx:
            random.choice(self.sfx[sound_key]).play()

    def _create_main_menu(self):
        menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        menu.add.button('PLAY', self._menu_action(self._show_options_menu))
        menu.add.button('TRAIN AI', self._menu_action(self._show_options_menu))
        menu.add.button('QUIT', self._menu_action(self.quit_game))

        return menu

    def _create_options_menu(self):
        menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        menu.add.selector(
            'Player Type: ',
            [('Human', 0), (' AI  ', 1)],
            onchange=self._menu_action(self._set_player_type)
        )
        menu.add.button('START GAME', self._menu_action(self.play_game))
        menu.add.button('BACK', self._menu_action(self._return_to_main))

        return menu

    def _menu_action(self, action_func):
        def wrapper(*args):
            self._play_sound('click')
            if callable(action_func):
                return action_func(*args)
            return action_func
        return wrapper

    def _show_options_menu(self):
        self.main_menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu

    def _return_to_main(self):
        self.options_menu.disable()
        self.main_menu.enable()
        self.active_menu = self.main_menu

    def _set_player_type(self, _, value):
        self.player_type = value

    def play_game(self):
        from scripts.GameManager import game_state_manager
        game_state_manager.player_type = self.player_type
        game_state_manager.setState('game')

    def quit_game(self):
        pygame.time.delay(300)
        pygame.quit()
        exit()

    def run(self):
        # Only draw background once when entering the menu, not every frame
        self.screen.blit(self.background, (0, 0))
        
        # Pre-render the title and shadow only once
        shadow_offset = (4, 4)
        title_font = pygame.font.Font(FONT, 85)
        title_text = 'Super Terboy'

        shadow_surf = title_font.render(title_text, True, (0, 0, 0))
        title_surf = title_font.render(title_text, True, MENUTXTCOLOR)

        title_pos = (DISPLAY_SIZE[0] // 4, DISPLAY_SIZE[1] // 6)
        self.screen.blit(shadow_surf, (title_pos[0] + shadow_offset[0], title_pos[1] + shadow_offset[1]))
        self.screen.blit(title_surf, title_pos)
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        pygame.time.Clock().tick(30)  

        self.active_menu.update(events)
        self.active_menu.draw(self.screen)