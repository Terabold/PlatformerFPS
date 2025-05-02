import pygame
import random
import os
from scripts.GameManager import game_state_manager
from scripts.constants import *
from scripts.player import Player
from scripts.humanagent import InputHandler
from scripts.tilemap import Tilemap
from scripts.utils import (
    load_image, load_images, Animation, load_sounds, 
    draw_debug_info, update_camera_with_box, MenuScreen
)


class PauseMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Game Paused"
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['Resume Game', 'Restart Level', 'Main Menu']
        button_actions = [
            self.parent.resume_game,
            self.parent.reset,
            self.parent.return_to_main
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            400
        )

class LevelCompleteMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Level Complete!"
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['Next Map', 'Play Again', 'Main Menu']
        button_actions = [
            self.parent.load_next_map,
            self.parent.reset,
            self.parent.return_to_main
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            400
        )

class CongratulationsScreen(MenuScreen):
    def initialize(self):
        self.title = "Congratulations!"
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['Restart Game', 'Main Menu']
        button_actions = [
            self.parent.restart_game,
            self.parent.return_to_main
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            400
        )
class GameOverMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Game Over"
        
        center_x = self.parent.display_size[0] // 2
        
        button_texts = ['Restart Level', 'Main Menu']
        button_actions = [
            self.parent.reset,
            self.parent.return_to_main
        ]
        
        self.button_manager.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            400
        )

class GameMenu:
    def __init__(self, environment):
        self.environment = environment
        self.screen = environment.display
        self.background = None 
        self.display_size = DISPLAY_SIZE
        self.font_path = FONT
        
        self.button_props = {
            'padding': 30,
            'height': 80,
            'min_width': 300,  
            'text_padding': 40  
        }
        
        self.pause_menu = PauseMenuScreen(self, "Game Paused")
        self.level_complete_menu = LevelCompleteMenuScreen(self, "Level Complete!")
        self.game_over_menu = GameOverMenuScreen(self, "Game Over")
        
        self.active_menu = None
    
    def _play_sound(self, sound_key):
        if sound_key in self.environment.sfx:
            random.choice(self.environment.sfx[sound_key]).play()
    
    def resume_game(self):
        self.environment.menu = False
        self.active_menu = None
        self._play_sound('click')
    
    def reset(self):
        self.environment.reset()
        self._play_sound('click')
    
    def return_to_main(self):
        self.environment.return_to_main()
        self._play_sound('click')
    
    def show_pause_menu(self):
        self.pause_menu.enable()
        self.level_complete_menu.disable()
        self.game_over_menu.disable()
        self.active_menu = self.pause_menu
    
    def show_level_complete_menu(self):
        self.pause_menu.disable()
        self.level_complete_menu.enable()
        self.game_over_menu.disable()
        self.active_menu = self.level_complete_menu
    
    def show_game_over_menu(self):
        self.pause_menu.disable()
        self.level_complete_menu.disable()
        self.game_over_menu.enable()
        self.active_menu = self.game_over_menu
    
    def load_next_map(self):
        pass
    
    def update(self, events):
        if self.active_menu:
            self.active_menu.update(events)
    
    def draw(self, surface):
        if self.active_menu:
            # Create semi-transparent overlay
            overlay = pygame.Surface((self.display_size[0], self.display_size[1]), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 175))  # Semi-transparent black
            surface.blit(overlay, (0, 0))
            
            # Draw active menu
            self.active_menu.draw(surface)

class Environment:
    def __init__(self, display, clock, ai_train_mode=False):
        self.player_type = game_state_manager.player_type
        self.ai_train_mode = ai_train_mode 
        
        if self.player_type == 1:  
            self.ai_train_mode = True
        
        self.display = display
        self.clock = clock
        self.menu = False
        self.rotated_assets = {}
        self.show_rotation_values = False
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        
        # Get the latest map selection
        map_path = game_state_manager.selected_map
        self.tilemap.load(map_path)
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)

        # Rest of initialization continues as before
        self.assets = {          
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/finish', scale=IMGscale),
            'ores': load_images('tiles/ores', scale=IMGscale),
            'weather': load_images('tiles/weather', scale=IMGscale),
            'kill': load_images('tiles/kill', scale=IMGscale),
            # 'nether': load_images('tiles/nether', scale=IMGscale),
            # 'wood': load_images('tiles/wood', scale=IMGscale),
            # 'wool': load_images('tiles/wool', scale=IMGscale),       
            'player': load_image('player/player.png', scale=PLAYERS_IMAGE_SIZE),
            'background': load_image('background.png', scale=DISPLAY_SIZE),
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=5),
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=25),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/fall': Animation(load_images('player/fall', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/death': Animation(load_images('player/death', scale=(PLAYERS_IMAGE_SIZE[0]*2, PLAYERS_IMAGE_SIZE[1])), img_dur=6, loop=False),
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

        if self.player_type == 0:
            self.input_handler = InputHandler()
        elif self.player_type == 1:
            self.input_handler = InputHandler() 

        self.scroll = self.default_pos.copy()

        self.game_menu = GameMenu(self)
    
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

    def resume_game(self):
        self.menu = False
        
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()

    def get_rotated_image(self, tile_type, variant, rotation):
        key = f"{tile_type}_{variant}_{rotation}"
        
        if key not in self.rotated_assets:
            original = self.assets[tile_type][variant]
            self.rotated_assets[key] = pygame.transform.rotate(original, rotation)
        
        return self.rotated_assets[key]
    
    def get_state(self):
        if self.ai_train_mode:
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
            # Handle escape key to toggle pause menu
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if not self.menu and not self.player.death and not self.player.finishLevel:
                        # Open pause menu
                        self.menu = True
                        self.game_menu.show_pause_menu()
                    elif self.menu and not self.player.death and not self.player.finishLevel:
                        # Close pause menu
                        self.menu = False
                        self.game_menu.active_menu = None
                    
            # Continue with normal input processing
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
                self.game_menu.show_game_over_menu()
        
        elif self.player.finishLevel:
            if not self.finish_sound_played:
                random.choice(self.sfx['finish']).play()
                self.finish_sound_played = True
            self.menu = True
            self.game_menu.show_level_complete_menu()
            
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
        
        if self.menu:
            self.game_menu.draw(self.display)

    def process_menu_events(self, events):
        if self.menu:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Handle escape in different menus
                    if self.player.finishLevel:
                        # From level complete menu -> return to main
                        self.return_to_main()
                    elif self.player.death:
                        # From game over menu -> return to main
                        self.return_to_main()
                    else:
                        # From pause menu -> resume game
                        self.menu = False
                        self.game_menu.active_menu = None
            
            self.game_menu.update(events)

    def debug_render(self):
        draw_debug_info(self, self.display, self.render_scroll)  
        fps = self.clock.get_fps()
        fps_text = self.fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 0))
        self.display.blit(fps_text, (10, 10))