import sys

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from constants import *

class Game:
    def __init__(self, display):

        self.display = display

        self.keys = {'left': False, 'right': False, 'jump': False}
        
        self.tilemap = Tilemap(self, tile_size = TILE_SIZE)
        self.tilemap.load('map.json')
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)

        self.assets = {
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'player': load_image('player/player.png', scale=PLAYERS_IMAGE_SIZE),
            'background': load_image('background.png', scale=DISPLAY_SIZE),
            'clouds': load_images('clouds'),
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=4),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE)),
        }
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.player = Player(self, PLAYER_POS, PLAYERS_SIZE)
        
        self.scroll = [0, 0]

    def run(self):
        
        self.display.blit(self.assets['background'], (0, 0))
            
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
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

        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 3 - self.scroll[0]) / 15
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 15
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
        self.clouds.update()
        self.clouds.render(self.display, offset=render_scroll)
            
        self.tilemap.render(self.display, offset=render_scroll)
            
        self.player.update(self.tilemap, self.keys)
        self.player.render(self.display, offset=render_scroll)
