import pygame
import pygame_menu
import sys
import random
from scripts.GameManager import game_state_manager
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG, WHITE, MENUTXTCOLOR
from scripts.utils import load_sounds

class Menu:
    def __init__(self, screen):
        self.sfx = {'click': load_sounds('click')}
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)
        self.player_type = 0  # Default player type

        pygame.font.init()

        # Create themes and base menu
        self._setup_theme()
        self._create_main_menu()
        self._create_options_menu()

        self.active_menu = self.menu

    def _setup_theme(self):
        title_font = pygame.font.Font(FONT, 85)
        widget_font = pygame.font.Font(FONT, 50)
        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(20, 30))

        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 0),
            title_background_color=(0, 0, 0, 0),
            title_font=title_font,
            title_font_color=WHITE,
            title_offset=(DISPLAY_SIZE[0] / 4, 20),
            widget_font=widget_font,
            widget_font_color=MENUTXTCOLOR,
            widget_margin=(0, 30),
            widget_selection_effect=selection_effect
        )

    def _create_main_menu(self):
        self.menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        def button_click_with_sound(action_func):
            def wrapper():
                random.choice(self.sfx['click']).play()
                if callable(action_func):
                    return action_func()
                else:
                    return action_func
            return wrapper

        self.menu.add.button('PLAY', button_click_with_sound(self._show_options_menu))
        self.menu.add.button('TRAIN AI', button_click_with_sound(self._show_options_menu))
        self.menu.add.button('QUIT', button_click_with_sound(self.quit_game))

    def _create_options_menu(self):
        self.options_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        def button_click_with_sound(action_func):
            def wrapper(*args):
                random.choice(self.sfx['click']).play()
                if callable(action_func):
                    return action_func(*args)
                else:
                    return action_func
            return wrapper

        self.options_menu.add.selector(
            'Player Type: ',
            [('Human', 0), ('AI', 1)],
            onchange=button_click_with_sound(self._set_player_type)
        )
        
        self.options_menu.add.button('START GAME', button_click_with_sound(self.play_game))
        self.options_menu.add.button('BACK', button_click_with_sound(self._return_to_main))

    def _show_options_menu(self):
        self.menu.disable()
        self.options_menu.enable()
        self.active_menu = self.options_menu

    def _return_to_main(self):
        self.options_menu.disable()
        self.menu.enable()
        self.active_menu = self.menu

    def _set_player_type(self, _, value):
        self.player_type = value

    def play_game(self):
        game_state_manager.player_type = self.player_type
        game_state_manager.setState('game')

    def quit_game(self):
        pygame.time.delay(300)
        pygame.quit()
        sys.exit()

    def run(self):
        self.screen.blit(self.background, (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        shadow_offset = (4, 4)
        title_font = pygame.font.Font(FONT, 85)
        title_text = 'Super Terboy'

        shadow_surf = title_font.render(title_text, True, (0, 0, 0))
        title_surf = title_font.render(title_text, True, (160, 111, 78))

        title_pos = (DISPLAY_SIZE[0] // 4, 20)
        self.screen.blit(shadow_surf, (title_pos[0] + shadow_offset[0], title_pos[1] + shadow_offset[1]))
        self.screen.blit(title_surf, title_pos)
            
        self.active_menu.update(events)
        self.active_menu.draw(self.screen)