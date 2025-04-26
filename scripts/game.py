import sys
import pygame
from scripts.environment import Environment
from scripts.constants import *
from scripts.GameManager import game_state_manager

class Game:
    def __init__(self, display, clock):
        self.display = display
        self.clock = clock
        player_type = game_state_manager.player_type
        self.environment = Environment(display, clock, player_type=player_type)
        
    def resume_game(self):
        self.environment.resume_game()
        
    def return_to_main(self):
        self.environment.return_to_main()
        
    def reset(self):
        self.environment.reset()

    def run(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:  
                    self.environment.debug_mode = not self.environment.debug_mode  
                    print(f"Debug mode: {'ON' if self.environment.debug_mode else 'OFF'}")
                if event.key == pygame.K_ESCAPE and not self.environment.player.death:
                    self.environment.menu = not self.environment.menu
        
        if self.environment.menu:
            self.environment.process_menu_events(events)
        else:
            self.environment.process_human_input(events)
        
        self.environment.update()
        
        self.environment.render()