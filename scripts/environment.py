import pygame
import random
import pygame_menu
from scripts.GameManager import game_state_manager
from scripts.constants import *
from scripts.player import Player
from scripts.humanagent import InputHandler
from scripts.tilemap import Tilemap
from scripts.utils import load_image, load_images, Animation, UIsize, load_sounds, draw_debug_info, update_camera_with_box
import math
import numpy as np
import sys

class Environment:
    def __init__(self, display, clock, ai_train_mode=False, player_type=0):
        self.ai_train_mode = ai_train_mode
        self.display = display
        self.clock = clock
        self.menu = False

        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        self.tilemap.load('map.json')
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)

        self.assets = {
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'ores': load_images('tiles/ores', scale=IMGscale),
            'hardened_clay': load_images('tiles/hardened clay', scale=IMGscale),
            'weather': load_images('tiles/weather', scale=IMGscale),
            'player': load_image('player/player.png', scale=PLAYERS_IMAGE_SIZE),
            'background': load_image('background.png', scale=DISPLAY_SIZE),
            'clouds': load_images('clouds'),
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=5),
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=25),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/fall': Animation(load_images('player/fall', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/death': Animation(load_images('player/death', scale=(PLAYERS_IMAGE_SIZE[0]*2, PLAYERS_IMAGE_SIZE[1])), img_dur=6, loop=False),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/Checkpoint', scale=IMGscale),
            'saws': load_images('tiles/saws', scale=IMGscale),
        }
        
        self.sfx = {
            'death': load_sounds('death', volume=0.25),
            'jump': load_sounds('jump'),
            'collide': load_sounds('wallcollide'),
            'finish': load_sounds('level_complete'),
            'click': load_sounds('click'),
        }

        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        self.default_pos = self.pos[0]['pos'] if self.pos else [10, 10]
        self.player = Player(self, self.default_pos, PLAYERS_SIZE, self.sfx)

        self.keys = {'left': False, 'right': False, 'jump': False}

        self.buffer_times = {'jump': 0}

        self.reset()
        pygame.font.init()
        self.fps_font = pygame.font.Font(FONT, 36)

        if player_type == 0:
            self.input_handler = InputHandler()
        elif player_type == 1:
            self.input_handler = InputHandler() 

        self.scroll = [0, 0]

        self._setup_menus()
    
    def reset(self):
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countdeathframes = 0
        self.player.reset()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        self.menu = False
        self.input_handler = InputHandler()
        self.debug_mode = False
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countdeathframes = 0
        self.buffer_time = 0
        self.player_finished = False

    def _setup_menus(self):
        title_font = pygame.font.Font(FONT, UIsize(2))
        widget_font = pygame.font.Font(FONT, UIsize(2))
        
        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 175),  
            title_background_color=(0, 0, 0, 0),
            title_font=title_font,  
            title_font_size=UIsize(2),
            title_font_color=(255, 170, 0),
            title_offset=(20, 20),
            widget_font=widget_font,  
            widget_font_color=WHITE,
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

        def button_click_with_sound(action_func):
            def wrapper():
                random.choice(self.sfx['click']).play()
                action_func()
            return wrapper
        self.pause_menu.add.button('Resume Game', button_click_with_sound(self.resume_game))
        self.pause_menu.add.button('Restart Level', button_click_with_sound(self.reset))
        self.pause_menu.add.button('Main Menu', button_click_with_sound(self.return_to_main))
        
        self.level_complete_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 2.5,
            width=DISPLAY_SIZE[0] // 2,
            title='Level Complete!',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.level_complete_menu.add.label('', font_size=1)
        self.level_complete_menu.add.button('Play Again', button_click_with_sound(self.reset))
        self.level_complete_menu.add.button('Main Menu', button_click_with_sound(self.return_to_main))

        self.death_menu = pygame_menu.Menu(
            height=DISPLAY_SIZE[1] // 2.5,
            width=DISPLAY_SIZE[0] // 2,
            title='Game Over',
            theme=self.menu_theme,
            center_content=True,
            mouse_motion_selection=True,
        )

        self.death_menu.add.label('', font_size=1)
        self.death_menu.add.button('Restart Level', button_click_with_sound(self.reset))
        self.death_menu.add.button('Main Menu', button_click_with_sound(self.return_to_main))

    def resume_game(self):
        self.menu = False
        
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()
        

    def get_state(self):
        if self.ai_train_mode:
            # Create a simple state representation for the AI
            # This could include player position, velocity, surrounding tiles, etc.
            player_rect = self.player.rect()
            player_x = player_rect.centerx
            player_y = player_rect.centery
            player_vel_x = self.player.velocity[0]
            player_vel_y = self.player.velocity[1]
            
            # Get nearby physics tiles (platforms)
            physics_tiles = self.tilemap.physics_rects_around(self.player.pos)
            
            # Get nearby interactive tiles (spikes, finish, etc.)
            interactive_tiles = self.tilemap.interactive_rects_around(self.player.pos)
            
            # Create a state dictionary
            state = {
                'player_pos': (player_x, player_y),
                'player_vel': (player_vel_x, player_vel_y),
                'player_grounded': self.player.grounded,
                'player_air_time': self.player.air_time,
                'physics_tiles': physics_tiles,
                'interactive_tiles': interactive_tiles,
                'collisions': self.player.collisions,
                'finished': self.player.finishLevel,
                'dead': self.player.death
            }
            return state
        return None
    
    def set_action(self, action):
        if self.ai_train_mode:
            self.keys = action
            if action['jump']:
                self.buffer_times['jump'] = min(self.buffer_times['jump'] + 1, PLAYER_BUFFER + 1)
            else:
                self.buffer_times['jump'] = 0
                
            self.buffer_time = self.buffer_times['jump']

    def process_human_input(self, events):
        if not self.ai_train_mode:
            self.keys, self.buffer_times = self.input_handler.process_events(events, self.menu)
            self.buffer_time = self.buffer_times['jump']
    
    def update(self):
        if self.player.death:
            self.countdeathframes += 1
            if not self.death_sound_played:
                random.choice(self.sfx['death']).play()
                self.death_sound_played = True
            if self.countdeathframes >= 40:
                self.menu = True
        
        elif self.player.finishLevel:
            if not self.finish_sound_played:
                random.choice(self.sfx['finish']).play()
                self.finish_sound_played = True
            self.menu = True
            
        if not self.menu:
            self.player.update(self.tilemap, self.keys, self.countdeathframes)
            update_camera_with_box(self.player, self.scroll, DISPLAY_SIZE[0], DISPLAY_SIZE[1])
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

    def render(self):
        self.display.blit(self.assets['background'], (0, 0))
        self.tilemap.render(self.display, offset=self.render_scroll)

        if self.debug_mode and not self.menu:
            self.debug_render()

        self.player.render(self.display, offset=self.render_scroll)
        
        # Don't handle menu events here - just draw the menus
        if self.menu:
            if self.player.death and self.countdeathframes >= 40:
                self.death_menu.draw(self.display)
            elif self.player.finishLevel:
                self.level_complete_menu.draw(self.display)
            else:
                self.pause_menu.draw(self.display)


    def process_menu_events(self, events):
        if self.menu:
            if self.player.death and self.countdeathframes >= 40:
                self.death_menu.update(events)
            elif self.player.finishLevel:
                self.level_complete_menu.update(events)
            else:
                self.pause_menu.update(events)


    def debug_render(self):
        draw_debug_info(self, self.display, self.render_scroll)  
        fps = self.clock.get_fps()
        fps_text = self.fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 0))
        self.display.blit(fps_text, (10, 10))