import pygame
from scripts.constants import DISPLAY_SIZE, FPS
from scripts.game import Game
from scripts.menu import Menu
from scripts.gameStateManager import game_state_manager

class Engine:

    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Super Terboy')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        self.game = Game(self.display, self.clock)
        self.menu = Menu(self.display)

        self.state = {'game': self.game, 'menu': self.menu}

    def run(self):
        while True:
            self.state[game_state_manager.getState()].run()
            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    Engine().run()
