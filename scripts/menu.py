import pygame
import pygame_menu
import sys
import random
from scripts.gameStateManager import game_state_manager
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG, WHITE, MENUTXTCOLOR
from scripts.utils import load_sounds

class Menu:
    def __init__(self, screen):
        self.sfx = {'click': load_sounds('click')}
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        self.background = pygame.transform.scale(self.background, DISPLAY_SIZE)

        pygame.font.init()

        title_font = pygame.font.Font(FONT, 85)
        widget_font = pygame.font.Font(FONT, 50)

        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(20, 30))

        my_theme = pygame_menu.themes.Theme(
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

        self.menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='',
            theme=my_theme,
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

        self.menu.add.button('PLAY', button_click_with_sound(self.play_game))
        self.menu.add.button('Train AI', button_click_with_sound(self.train_ai))
        self.menu.add.button('QUIT', button_click_with_sound(self.quit_game))  # Works now ✅

    def play_game(self):
        game_state_manager.setState('game')

    def train_ai(self):
        pass

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

        self.menu.update(events)
        self.menu.draw(self.screen)

