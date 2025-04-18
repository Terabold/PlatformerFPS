import pygame
import pygame_menu
import sys
from scripts.gameStateManager import game_state_manager
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG, WHITE, MENUTXTCOLOR

class Menu:
    def __init__(self, screen):
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
            title_offset=(DISPLAY_SIZE[0]/4, 20),  
            widget_font=widget_font,
            widget_font_color=MENUTXTCOLOR,
            widget_margin=(0, 30),
            widget_selection_effect=selection_effect 
        )
  
        self.menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='Super Terboy',
            theme=my_theme,
            center_content=True,
            mouse_motion_selection=True,
        )
        
        self.menu.add.button('PLAY', self.play_game)
        self.menu.add.button('Train AI', self.train_ai)
        self.menu.add.button('QUIT', pygame_menu.events.EXIT)
    
    def play_game(self):
        game_state_manager.setState('game')
        
    def train_ai(self):
        pass
        
    def run(self):
        self.screen.blit(self.background, (0, 0))
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        self.menu.update(events)
        self.menu.draw(self.screen)