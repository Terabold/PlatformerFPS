import pygame
import pygame_menu
import sys
from scripts.gameStateManager import game_state_manager
from scripts.constants import DISPLAY_SIZE, FONT, MENUBG, WHITE, MENUTXTCOLOR

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.background = pygame.image.load(MENUBG)
        
        # Initialize pygame font
        pygame.font.init()
        
        # Create pygame-menu compatible font objects
        title_font = pygame.font.Font(FONT, 85)
        widget_font = pygame.font.Font(FONT, 50)
        
                # Define selection effect first
        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(20, 30))

        # Now create your theme
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
  
        # Main menu
        self.menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1],
            width=DISPLAY_SIZE[0],
            title='Super Terboy',
            theme=my_theme,
            center_content=True,
            mouse_motion_selection=True,
        )
        
        # Add buttons with the same functionality 
        self.menu.add.button('PLAY', self.play_game)
        self.menu.add.button('Train AI', self.train_ai)
        self.menu.add.button('QUIT', pygame_menu.events.EXIT)
    
    def play_game(self):
        game_state_manager.setState('game')
        
    def train_ai(self):
        # Implement your AI training functionality
        pass
        
    def run(self):
        # Draw the background before drawing the menu
        self.screen.blit(self.background, (0, 0))
        
        # Process pygame events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
        # Update and draw the menu
        self.menu.update(events)
        self.menu.draw(self.screen)
        
        pygame.display.update()