import sys
import pygame
import pygame_menu
import random
from scripts.gameStateManager import game_state_manager
from scripts.utils import load_image, load_images, Animation, UIsize, load_sounds, draw_debug_info, update_camera_with_box
from scripts.player import Player
from scripts.tilemap import Tilemap
from scripts.humanagent import InputHandler
from scripts.constants import *

DEBUG_HITBOXES = True

class Game:
    def __init__(self, display, clock):
        self.display = display
        self.clock = clock
        self.menu_active = False
        self.keys = {'left': False, 'right': False, 'jump': False}
        pygame.font.init()

        self.input_handler = InputHandler()
        
        self.tilemap = Tilemap(self, tile_size = TILE_SIZE)
        self.tilemap.load('map.json')
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)

        self.death_sound_played = False
        self.finish_sound_played = False

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
            'death': load_sounds('death'),
            'jump': load_sounds('jump'),
            'collide': load_sounds('wallcollide'),
            'finish': load_sounds('level_complete'),
            'click': load_sounds('click'),
        }

        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        self.default_pos = self.pos[0]['pos'] if self.pos else [10, 10]
        self.player = Player(self, self.default_pos, PLAYERS_SIZE, self.sfx)

        self.buffer_time = 0
        
        self.scroll = [0, 0]
        self.fps_font = pygame.font.Font(None, 36)
        self.debug_hitboxes = False
        
        title_font = pygame.font.Font(FONT, UIsize(2))
        widget_font = pygame.font.Font(FONT, UIsize(2))
        
        self.menu_theme = pygame_menu.themes.Theme(
            background_color=(0, 0, 0, 128),  
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
            height=DISPLAY_SIZE[1] // 2,
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

        self.countdeathframes = 0

    def resume_game(self):
        self.menu_active = False
        
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()
        
    def reset(self):
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countdeathframes = 0
        self.player.reset()
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.menu_active = False
        self.input_handler = InputHandler()


    def run(self):
        self.display.blit(self.assets['background'], (0, 0))

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:  
                    global DEBUG_HITBOXES
                    DEBUG_HITBOXES = not DEBUG_HITBOXES
                    print(f"Debug mode: {'ON' if DEBUG_HITBOXES else 'OFF'}")
                if event.key == pygame.K_ESCAPE:
                    self.menu_active = not self.menu_active

        self.keys, self.buffer_times = self.input_handler.process_events(events, self.menu_active)

        self.buffer_time = self.buffer_times['jump']
        
        update_camera_with_box(self.player, self.scroll, DISPLAY_SIZE[0], DISPLAY_SIZE[1])
        render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
        self.tilemap.render(self.display, offset=render_scroll)

        if DEBUG_HITBOXES and not self.menu_active:
            draw_debug_info(self, self.display, render_scroll)  
            fps = self.clock.get_fps()
            fps_text = self.fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 0))
            self.display.blit(fps_text, (10, 10))

        self.player.update(self.tilemap, self.keys)
        self.player.render(self.display, offset=render_scroll)
    
        if self.player.death: 
            self.countdeathframes += 1
            if not self.death_sound_played:
                random.choice(self.sfx['death']).play()
                self.death_sound_played = True
            if self.countdeathframes >= 40:
                self.menu_active = True
                menu = self.death_menu

        elif self.player.finishLevel:
            if not self.finish_sound_played:
                random.choice(self.sfx['finish']).play()
                self.finish_sound_played = True
            self.menu_active = True
            menu = self.level_complete_menu
        elif self.menu_active:
            menu = self.pause_menu
        
        if self.menu_active:
            menu.update(events)
            menu.draw(self.display)