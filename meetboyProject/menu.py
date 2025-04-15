import sys

import pygame
from scripts.utils import Text, Button
from gameStateManager import game_state_manager
from constants import DISPLAY_SIZE

class Menu:
    
    def __init__(self, display):

        self.display = display

        test_text = Text('start game', pos = (DISPLAY_SIZE[0]//2, DISPLAY_SIZE[1]//2), size=30)
        test_button = Button(test_text, (0 ,255, 0), 'start_game')

        self.buttons = [test_button]

    def run(self):

        self.display.fill((0, 0, 100))

        mouse_pressed = False
        mouse_released = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pressed = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_released = True

        for button in self.buttons:
            button.update(mouse_pressed, mouse_released)
            if button.is_clicked():
                if button.type == 'start_game':
                    game_state_manager.setState('game')
            button.blit(self.display)
