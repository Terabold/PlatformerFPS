import sys
import pygame
from scripts.environment import Environment
from scripts.constants import *

class Game:
    def __init__(self, display, clock):
        self.display = display
        self.clock = clock
        self.environment = None
        
    def initialize_environment(self):
        self.environment = Environment(self.display, self.clock)

    def run(self):
        if not self.environment:
            self.initialize_environment()
            
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:  
                    self.environment.debug_mode = not self.environment.debug_mode  
                    print(f"Debug mode: {'ON' if self.environment.debug_mode else 'OFF'}")
        
        if self.environment.menu:
            self.environment.process_menu_events(events)
        else:
            self.environment.process_human_input(events)
        
        self.environment.update()
        self.environment.render()