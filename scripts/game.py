import sys
import pygame
from scripts.gameStateManager import game_state_manager
from scripts.utils import load_image, load_images, Animation, Text, vh
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.constants import *

class Game:
    def __init__(self, display):

        self.display = display
        self.menu = False
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
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=8),
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=30),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), img_dur=8),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE)),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'checkpoint': load_images('tiles/Checkpoint', scale=IMGscale),
        }
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        self.default_pos = self.pos[0]['pos'] if self.pos else [10, 10]
        self.player = Player(self, self.default_pos, PLAYERS_SIZE)

        self.buffer_time = 0
        
        self.scroll = [0, 0]

    def blitMenu(self, mouse_pressed, mouse_released):
        rect_width, rect_height = DISPLAY_SIZE[0]//2, DISPLAY_SIZE[1]//3*2 
        black_rect = pygame.Surface((rect_width, rect_height), pygame.SRCALPHA)  # enable per-pixel alpha
        black_rect.fill((0, 0, 0, 128))  

        x = (DISPLAY_SIZE[0] - rect_width) // 2
        y = (DISPLAY_SIZE[1] - rect_height) // 2

        self.display.blit(black_rect, (x, y))

        if self.player.finishLevel:
                
                finish_text = Text("Level Complete!", vh(50, 30), color=(255, 255, 255))
                finish_text.blit(self.display)

                for button in self.buttons:

                    if button.type == 'menu':
                        button.set_offset(vh(-10, -5)[0], vh(-10, -5)[1])
                        button.update(mouse_pressed, mouse_released)
                        if button.is_clicked():
                                self.openMenu = False
                                self.reset()
                                game_state_manager.returnToPrevState()
                        button.blit(self.display)

                    if button.type == 'reset':
                        button.update(mouse_pressed, mouse_released)
                        if button.is_clicked():
                                self.openMenu = False
                                self.reset()
                        button.blit(self.display)
        else:

            self.pause_title_text.blit(self.display)

            for button in self.buttons:  

                if button.type == 'menu':
                    button.set_offset(0, 0)
                    button.update(mouse_pressed, mouse_released)
                    if button.is_clicked():
                            self.openMenu = False
                            self.reset()
                            game_state_manager.returnToPrevState()
                    button.blit(self.display)

                if button.type == 'resume':
                    button.update(mouse_pressed, mouse_released)
                    if button.is_clicked():
                            self.openMenu = False
                    button.blit(self.display)

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
                    self.buffer_time = 0

        if self.keys['jump']:
            self.buffer_time += 1
            if self.buffer_time > PLAYER_BUFFER:
                self.buffer_time = PLAYER_BUFFER + 1
            


        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 3 - self.scroll[0]) / 15
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 15
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
        self.clouds.update()
        self.clouds.render(self.display, offset=render_scroll)
            
        self.tilemap.render(self.display, offset=render_scroll)
        
        self.player.update(self.tilemap, self.keys)
        self.player.render(self.display, offset=render_scroll)

        if self.player.death:
            self.player.reset()

        if self.player.finishLevel:
            self.menu = True

        if self.menu: self.blitMenu(False, False)
