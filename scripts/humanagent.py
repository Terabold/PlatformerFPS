import pygame
from scripts.constants import PLAYER_BUFFER
class InputHandler:
    def __init__(self):
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        
    def process_events(self, events, menu_active=False):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if not menu_active:
                    if event.key == pygame.K_d:
                        self.keys['right'] = True
                    if event.key == pygame.K_a:
                        self.keys['left'] = True
                    if event.key == pygame.K_SPACE:
                        self.keys['jump'] = True
                        
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_d:
                    self.keys['right'] = False
                if event.key == pygame.K_a:
                    self.keys['left'] = False
                if event.key == pygame.K_SPACE:
                    self.keys['jump'] = False
                    self.buffer_times['jump'] = 0
        
            if self.keys['jump']:
                self.buffer_times['jump'] += 1
                if self.buffer_times['jump'] > PLAYER_BUFFER:
                    self.buffer_times['jump'] = PLAYER_BUFFER + 1
                                
        return self.keys, self.buffer_times