import pygame
import random
import os
import json
from scripts.GameManager import game_state_manager
from scripts.constants import *
from scripts.player import Player
from scripts.humanagent import InputHandler
from scripts.tilemap import Tilemap
from scripts.GameTimer import GameTimer
from scripts.utils import (
    load_image, load_images, Animation, load_sounds, 
    draw_debug_info, update_camera_with_box, MenuScreen,
    calculate_ui_constants, scale_font
)

class PauseMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Game Paused"
        self.clear_buttons()
        
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)  # 40% from top
        
        button_texts = ['Resume Game', 'Restart Level', 'Main Menu']
        button_actions = [
            self.menu.resume_game,
            self.menu.reset,
            self.menu.return_to_main
        ]
        
        self.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            start_y
        )

class LevelCompleteMenuScreen(MenuScreen):
    def initialize(self):
        self.title = "Level Complete!"
        self.clear_buttons()
        
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)  # 40% from top
        
        button_texts = ['Next Map', 'Play Again', 'Main Menu']
        button_actions = [
            self.menu.load_next_map,
            self.menu.reset,
            self.menu.return_to_main
        ]
        
        self.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            start_y
        )

class CongratulationsScreen(MenuScreen):
    def initialize(self):
        self.title = "Congratulations!"
        self.clear_buttons()
        
        center_x = self.menu.display_size[0] // 2
        start_y = int(self.menu.display_size[1] * 0.4)  # 40% from top
        
        button_texts = ['Restart Game', 'Main Menu']
        button_actions = [
            self.menu.restart_game,
            self.menu.return_to_main
        ]
        
        self.create_centered_button_list(
            button_texts, 
            button_actions, 
            center_x, 
            start_y
        )

class GameMenu:
    def __init__(self, environment):
        self.environment = environment
        self.screen = environment.display
        self.display_size = DISPLAY_SIZE
        self.font_path = FONT
        
        # Get UI constants based on display size
        self.UI_CONSTANTS = calculate_ui_constants(self.display_size)
        
        # Initialize menu screens
        self.pause_menu = PauseMenuScreen(self, "Game Paused")
        self.level_complete_menu = LevelCompleteMenuScreen(self, "Level Complete!")
        self.congratulations_menu = CongratulationsScreen(self, "Congratulations!")
        
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
    
    def restart_game(self):
        self.environment.restart_game()
        self._play_sound('click')
    
    def show_pause_menu(self):
        self.pause_menu.enable()
        self.level_complete_menu.disable()
        self.congratulations_menu.disable()
        self.active_menu = self.pause_menu
    
    def show_level_complete_menu(self):
        self.pause_menu.disable()
        self.level_complete_menu.enable()
        self.congratulations_menu.disable()
        self.active_menu = self.level_complete_menu
    
    def show_congratulations_menu(self):
        self.pause_menu.disable()
        self.level_complete_menu.disable()
        self.congratulations_menu.enable()
        self.active_menu = self.congratulations_menu
    
    def load_next_map(self):
        self.environment.load_next_map()
    
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
        self.ai_train_mode = ai_train_mode if not self.player_type == 1 else True
        self.display = display
        self.clock = clock
        self.menu = False
        self.rotated_assets = {}
        self.show_rotation_values = False
        
        # Initialize important state variables upfront
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countdeathframes = 0
        self.debug_mode = False
        self.player_finished = False
        self.buffer_time = 0

        # Initialize scroll variable here, before it's used in center_scroll_on_player
        self.scroll = [0, 0]
        self.render_scroll = [0, 0]

        # Initialize font with scaled size based on display
        font_size = scale_font(36, DISPLAY_SIZE)
        pygame.font.init()
        self.fps_font = pygame.font.Font(FONT, font_size)
        
        # Initialize tilemap and load map
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)
        
        # Initialize game timer
        self.initialize_timer()
        
        # Load the current map
        self.load_current_map()
        
        # Initialize input handler
        self.input_handler = InputHandler()
        
        # Initialize game menu with scaled UI
        self.game_menu = GameMenu(self)
    
    def initialize_timer(self):
        self.timer = GameTimer()
        self.movement_started = False
        
        # Timer display settings
        timer_font_size = scale_font(24, DISPLAY_SIZE)
        self.timer_font = pygame.font.Font(FONT, timer_font_size)
        self.timer_color = (255, 255, 255)
        self.timer_highlight_color = (255, 255, 0)
        self.show_timer = True

    def update_timer(self):
        # Start timer on first movement
        if not self.movement_started and (self.keys['left'] or self.keys['right'] or self.keys['jump']):
            self.movement_started = True
            self.timer.start()
        
        # Handle timer pausing based on game state
        if self.menu and not self.timer.is_paused:
            self.timer.pause()
        elif not self.menu and self.timer.is_paused and not self.player.death and not self.player.finishLevel:
            self.timer.resume()
        
        # Stop timer on level completion
        if self.player.finishLevel and self.timer.is_running:
            time = self.timer.stop()
            print('new record:', self.set_map_best_time(time=time))
        
        # Update timer if running
        self.timer.update()

    def render_timer(self):
        if not self.show_timer:
            return
            
        # Position in top right corner with padding
        padding = 10
        timer_pos = (25, padding)
        
        # Use the new direct rendering method
        self.timer.render(self.display, timer_pos, self.timer_font)

    def toggle_timer_highlight(self):
        self.timer.toggle_highlight()

    def toggle_timer_visibility(self):
        self.show_timer = not self.show_timer

    def reset_timer(self):
        self.timer.reset()
        self.movement_started = False
    
    def load_current_map(self):
        map_path = game_state_manager.selected_map
        self.tilemap.load(map_path)
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)

        # Load assets
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
            'nether': load_images('tiles/nether', scale=IMGscale),
            'wood': load_images('tiles/wood', scale=IMGscale),
            'wool': load_images('tiles/wool', scale=IMGscale),       
            'player': load_image('player/player.png', scale=PLAYERS_IMAGE_SIZE),
            'player/run': Animation(load_images('player/run', scale=PLAYERS_IMAGE_SIZE), img_dur=5),
            'player/idle': Animation(load_images('player/idle', scale=PLAYERS_IMAGE_SIZE), img_dur=25),
            'player/wallslide': Animation(load_images('player/wallslide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/wallcollide': Animation(load_images('player/wallcollide', scale=PLAYERS_IMAGE_SIZE), loop=False),
            'player/jump': Animation(load_images('player/jump', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/fall': Animation(load_images('player/fall', scale=PLAYERS_IMAGE_SIZE), img_dur=4, loop=False),
            'player/death': Animation(load_images('player/death', scale=(PLAYERS_IMAGE_SIZE[0]*2, PLAYERS_IMAGE_SIZE[1])), img_dur=6, loop=False),
            'saws': load_images('tiles/saws', scale=IMGscale),
        }
        
        if self.tilemap.get_background_map() is not None:
            self.background = load_image(self.tilemap.get_background_map(), scale=DISPLAY_SIZE, remove_color=None)
        else:
            self.background = load_image('background/background.png', scale=DISPLAY_SIZE, remove_color=None)

        # Load sounds
        self.sfx = {
            'death': load_sounds('death', volume=0.25),
            'jump': load_sounds('jump'),
            'collide': load_sounds('wallcollide'),
            'finish': load_sounds('level_complete'),
            'click': load_sounds('click'),
        }

        # Get spawner positions
        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        
        if not self.pos:
            self.default_pos = [10, 10]
        else:
            self.default_pos = self.pos[0]['pos'].copy()
        
        self.player = Player(self, self.default_pos.copy(), PLAYERS_SIZE, self.sfx)
        
        self.center_scroll_on_player()
        
        # Initialize input state
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
    
    def center_scroll_on_player(self):
        player_rect = self.player.rect()
        display_width = self.display.get_width()
        display_height = self.display.get_height()
        
        self.scroll[0] = player_rect.centerx - display_width // 2
        self.scroll[1] = player_rect.centery - display_height // 2
        
        self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
    
    def reset(self):
        self.death_sound_played = False
        self.finish_sound_played = False
        self.countdeathframes = 0
        self.player.reset()
        
        self.player.pos = self.default_pos.copy()
        
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        self.menu = False
        self.input_handler = InputHandler()
        self.debug_mode = False
        self.buffer_time = 0
        self.player_finished = False
        
        # Reset the timer
        self.reset_timer()
        
        # Re-center the scroll on the player's position
        self.center_scroll_on_player()

    def restart_game(self):
        self.load_map_id(0)

    def load_map_id(self, map_id):
        next_map = f'data/maps/{map_id}.json'
        game_state_manager.selected_map = next_map
        
        # Reset the environment
        self.reset()
        
        # Load the new map
        self.tilemap.load(next_map)
        
        # Update player spawn position
        self.pos = self.tilemap.extract([('spawners', 0), ('spawners', 1)])
        if self.pos:
            # Always use a copy of the position to avoid reference issues
            self.default_pos = self.pos[0]['pos'].copy()
        else:
            self.default_pos = [10, 10]
            
        self.player.pos = self.default_pos.copy()
        
        # Reset the timer for the new map
        self.reset_timer()
        
        # Center the view on the player
        self.center_scroll_on_player()
        
        self.menu = False

    def set_map_best_time(self, time):
        # Get the current map ID
        current_map = game_state_manager.selected_map
        
        # Use proper string splitting that's compatible with both slash types
        current_index = str(os.path.basename(current_map).split('.')[0])

        # Load the map times from the JSON file
        map_times_file = 'metadata.json'
        with open(map_times_file, 'r') as f:
            all_maps_data = json.load(f)
        # Get the time for the current map
        best_times = all_maps_data[current_index]['best_time']

        # new_best_time = best_time == None or time < best_time
        # if new_best_time:
        #     # Update the best time in the JSON file
        #     all_maps_data[current_index]['best_time'] = time
            
        #     # Save the updated data back to the JSON file
        #     with open(map_times_file, 'w') as f:
        #         json.dump(all_maps_data, f, indent=4)

        is_new_record = len(best_times) < 3 or time > min(best_times)
        best_times.append(time)
        best_times = sorted(best_times)[:3]  # Keep only the top 3 times

        all_maps_data[current_index]['best_time'] = best_times
        # Save the updated data back to the JSON file
        with open(map_times_file, 'w') as f:
            json.dump(all_maps_data, f, indent=4)

        return is_new_record
    
    def resume_game(self):
        self.menu = False
        
    def return_to_main(self):
        self.reset()
        game_state_manager.returnToPrevState()

    def is_last_map(self):
        # Get current level index
        current_map = game_state_manager.selected_map
        
        # Use proper string splitting that's compatible with both slash types
        current_index = int(os.path.basename(current_map).split('.')[0])
        
        # Get all maps
        maps_folder = os.path.join('data', 'maps')
        map_files = [f for f in os.listdir(maps_folder) if f.endswith('.json')]
        
        # Return true if this is NOT the last map (i.e., there are more maps to play)
        return current_index < len(map_files) - 1

    def load_next_map(self):
        # Get current map and find next map
        current_map = game_state_manager.selected_map
        if current_map:
                import os
                # Check if we're on the last map
                maps_folder = os.path.join('data', 'maps')
                map_files = sorted([f for f in os.listdir(maps_folder) if f.endswith('.json')])

                # Properly extract the current index from the filename
                current_index = int(os.path.basename(current_map).split('.')[0])
                
                if f'{current_index}.json' in map_files:
                    if current_index < len(map_files) - 1:
                        # Load next map
                        self.load_map_id(current_index + 1)
                else:
                    # Can't find current map, just reset
                    self.reset()
        else:
            self.reset()

    def get_rotated_image(self, tile_type, variant, rotation):
        key = f"{tile_type}_{variant}_{rotation}"
        
        if key not in self.rotated_assets:
            original = self.assets[tile_type][variant]
            self.rotated_assets[key] = pygame.transform.rotate(original, rotation)
        
        return self.rotated_assets[key]
    
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
        # Update the timer first
        self.update_timer()
        
        if self.player.death:
            self.countdeathframes += 1
            if not self.death_sound_played:
                random.choice(self.sfx['death']).play()
                self.death_sound_played = True
            if self.countdeathframes >= 40:
                self.reset()
        
        elif self.player.finishLevel:
            if not self.finish_sound_played:
                random.choice(self.sfx['finish']).play()
                self.finish_sound_played = True
            self.menu = True
            
            if self.is_last_map():
                self.game_menu.show_level_complete_menu()
            else:
                self.game_menu.show_congratulations_menu()
            
        if not self.menu:
            self.player.update(self.tilemap, self.keys, self.countdeathframes)
            update_camera_with_box(self.player, self.scroll, self.display.get_width(), self.display.get_height())
            self.render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

    def render(self):
        self.display.blit(self.background, (0, 0))
        self.tilemap.render(self.display, offset=self.render_scroll)

        if self.debug_mode and not self.menu:
            self.debug_render()

        self.player.render(self.display, offset=self.render_scroll)
        
        # Render the timer
        self.render_timer()
        
        if self.menu:
            # Get the current mouse position every frame to update button hover states
            # This ensures hover effects work in every menu screen
            mouse_pos = pygame.mouse.get_pos()
            if self.game_menu.active_menu:
                for button in self.game_menu.active_menu.buttons:
                    button.selected = button.is_hovered(mouse_pos)
                    
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