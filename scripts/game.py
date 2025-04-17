import sys
import pygame
import pygame_menu
from scripts.gameStateManager import game_state_manager
from scripts.utils import load_image, load_images, Animation, UIsize
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.constants import *

class Game:
    def __init__(self, display):
        self.display = display
        self.menu = False
        self.keys = {'left': False, 'right': False, 'jump': False}
        
        pygame.font.init()
        
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
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE)),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/Checkpoint', scale=IMGscale),
            'saws': load_images('tiles/saws', scale=IMGscale),
        }
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        self.default_pos = self.pos[0]['pos'] if self.pos else [10, 10]
        self.player = Player(self, self.default_pos, PLAYERS_SIZE)

        self.buffer_time = 0
        
        self.scroll = [0, 0]
        
        # Create pygame-menu compatible font objects
        title_font = pygame.font.Font(FONT, UIsize(2))
        widget_font = pygame.font.Font(FONT, UIsize(2))
        
        # Create menu theme
        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 128),  
            title_background_color=(0, 0, 0, 0),
            title_font=title_font,  
            title_font_size=UIsize(2),
            title_font_color=(255, 255, 255),
            title_offset=(DISPLAY_SIZE[0]/4 - 275, 20),
            widget_font=widget_font,  
            widget_font_color=(255, 255, 255),
            widget_margin=(0, 20),
        )
        
        # Configure selection effect
        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(15, 20))
        self.menu_theme.widget_selection_effect = selection_effect
        
        # Initialize pause menu
        self.pause_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 3,
            width=DISPLAY_SIZE[0] // 2,
            title='Game Paused',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.pause_menu.add.label('', font_size=1)
        self.pause_menu.add.button('Resume Game', self.resume_game)
        self.pause_menu.add.button('Main Menu', self.return_to_main)
        
        # Initialize level complete menu
        self.level_complete_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 2,
            width=DISPLAY_SIZE[0] // 2,
            title='Level Complete!',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.level_complete_menu.add.label('', font_size=1)
        self.level_complete_menu.add.button('Play Again', self.reset)
        self.level_complete_menu.add.button('Main Menu', self.return_to_main)
        
        self.current_menu = None

    def resume_game(self):
        self.menu = False
        
    def return_to_main(self):
        self.reset()
        if self.player.finishLevel:
            self.level_complete_menu.disable()
        else:
            self.pause_menu.disable()
        game_state_manager.returnToPrevState()
        
    def reset(self):
        self.player.reset()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.menu = False

    def blitMenu(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and not self.player.finishLevel:
                    self.resume_game()
        
        if self.player.finishLevel:
            current_menu = self.level_complete_menu
        else:
            current_menu = self.pause_menu
            
        if current_menu.is_enabled():
            current_menu.update(events)
            current_menu.draw(self.display)

    def run(self):
        self.display.blit(self.assets['background'], (0, 0))
        events = pygame.event.get()  
        for event in events:
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
                if event.key == pygame.K_ESCAPE:
                    self.menu = True

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
        
        if not self.menu: self.player.update(self.tilemap, self.keys)
        self.player.render(self.display, offset=render_scroll)

        if self.player.death:
            self.player.reset()

        if self.player.finishLevel:
            self.menu = True
            

        if self.menu:
            self.blitMenu(events)
            pygame.display.update()

        pygame.display.update()