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
        self.menu_active = False
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
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=25),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/fall': Animation(load_images('player/fall', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
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
        
        title_font = pygame.font.Font(FONT, UIsize(2))
        widget_font = pygame.font.Font(FONT, UIsize(2))
        
        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 128),  
            title_background_color=(0, 0, 0, 0),
            title_font=title_font,  
            title_font_size=UIsize(2),
            title_font_color=(255, 255, 255),
            title_offset=(100, 20),
            widget_font=widget_font,  
            widget_font_color=(255, 255, 255),
            widget_margin=(0, 20),
        )
        
        selection_effect = pygame_menu.widgets.LeftArrowSelection(arrow_size=(15, 20))
        self.menu_theme.widget_selection_effect = selection_effect
        
        self.pause_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 2.5,
            width=DISPLAY_SIZE[0] // 2,
            title='Game Paused',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.pause_menu.add.label('', font_size=1)
        self.pause_menu.add.button('Resume Game', self.resume_game)
        self.pause_menu.add.button('Restart Level', self.reset)
        self.pause_menu.add.button('Main Menu', self.return_to_main)
        
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

        self.death_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 2.5,
            width=DISPLAY_SIZE[0] // 2,
            title='Game Over',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.death_menu.add.label('', font_size=1)
        self.death_menu.add.button('Restart Level', self.reset)
        self.death_menu.add.button('Main Menu', self.return_to_main)

    def resume_game(self):
        self.menu_active = False
        
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()
        
    def reset(self):
        self.player.reset()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.menu_active = False

    def update_camera_with_box(self):
        box_width = 200
        box_height = 250
        
        box_left = self.scroll[0] + (self.display.get_width() / 2) - (box_width / 2)
        box_right = box_left + box_width
        box_top = self.scroll[1] + (self.display.get_height() *0.8 ) - (box_height / 2) - 100
        box_bottom = box_top + box_height
        
        player_x = self.player.rect().centerx
        player_y = self.player.rect().centery
        
        target_x = self.scroll[0]
        target_y = self.scroll[1]
        
        if player_x < box_left:
            target_x = self.scroll[0] - (box_left - player_x)
        elif player_x > box_right:
            target_x = self.scroll[0] + (player_x - box_right)
        
        if player_y < box_top:
            target_y = self.scroll[1] - (box_top - player_y)
        elif player_y > box_bottom:
            target_y = self.scroll[1] + (player_y - box_bottom)
        
        self.scroll[0] += (target_x - self.scroll[0]) / 15
        self.scroll[1] += (target_y - self.scroll[1]) / 15
        
        screen_box = {
            'left': box_left - self.scroll[0],
            'right': box_right - self.scroll[0],
            'top': box_top - self.scroll[1],
            'bottom': box_bottom - self.scroll[1]
        }
        return screen_box

    def run(self):
        self.display.blit(self.assets['background'], (0, 0))
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.menu_active = not self.menu_active
                
                if not self.menu_active:
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
        
        self.update_camera_with_box()
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
        self.clouds.update()
        self.clouds.render(self.display, offset=render_scroll)
            
        self.tilemap.render(self.display, offset=render_scroll)
        
        if not self.menu_active:
            self.player.update(self.tilemap, self.keys)
            
        self.player.render(self.display, offset=render_scroll)

        if self.player.death:
            self.menu_active = True
            menu = self.death_menu

        elif self.player.finishLevel:
            self.menu_active = True
            menu = self.level_complete_menu
        elif self.menu_active:
            menu = self.pause_menu
        
        if self.menu_active:
            menu.update(events)
            menu.draw(self.display)