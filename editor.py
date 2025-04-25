import sys

import pygame

from scripts.utils import load_images, load_image
from scripts.tilemap import Tilemap
from scripts.constants import TILE_SIZE, DISPLAY_SIZE, FPS, PHYSICS_TILES

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('editor')
        self.display = pygame.display.set_mode(DISPLAY_SIZE)
        self.zoom = 10
        self.clock = pygame.time.Clock()
        
        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)

        self.assets = self.reload_assets()
        self.background_image = load_image('background.png', scale=DISPLAY_SIZE)
        
        self.movement = [False, False, False, False]
            
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass
        
        self.scroll = [0, 0]
        
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True

        self.font = pygame.font.SysFont('Arial', 16)

    def reload_assets(self):
        IMGscale = (self.tilemap.tile_size, self.tilemap.tile_size)
        return {
            'decor': load_images('tiles/decor', scale=IMGscale),
            'grass': load_images('tiles/grass', scale=IMGscale),
            'stone': load_images('tiles/stone', scale=IMGscale),
            'spawners': load_images('tiles/spawners', scale=IMGscale),
            'spikes': load_images('tiles/spikes', scale=IMGscale),
            'finish': load_images('tiles/Checkpoint', scale=IMGscale),
            'ores': load_images('tiles/ores', scale=IMGscale),
            'hardened_clay': load_images('tiles/hardened clay', scale=IMGscale),
            'weather': load_images('tiles/weather', scale=IMGscale),
        }
    
    def count_spawners(self):
        return len(self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=True))
        
    def run(self):
        while True:
            self.display.fill((20, 20, 20))
            for x in range(0, DISPLAY_SIZE[0], self.tilemap.tile_size):
                pygame.draw.line(self.display, (50, 50, 50), (x - self.scroll[0] % self.tilemap.tile_size, 0), (x - self.scroll[0] % self.tilemap.tile_size, DISPLAY_SIZE[1]))
            for y in range(0, DISPLAY_SIZE[1], self.tilemap.tile_size):
                pygame.draw.line(self.display, (50, 50, 50), (0, y - self.scroll[1] % self.tilemap.tile_size), (DISPLAY_SIZE[0], y - self.scroll[1] % self.tilemap.tile_size))
            
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 8
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 8
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            self.tilemap.render(self.display, offset=render_scroll, zoom=self.zoom)
            
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)
            
            # Handle spawner placement logic - only allow one spawner
            if self.clicking and self.ongrid:
                if self.tile_list[self.tile_group] == 'spawners':
                    # If placing a spawner, remove any existing spawners first
                    existing_spawners = self.count_spawners()
                    if existing_spawners > 0:
                        self.tilemap.extract([('spawners', 0), ('spawners', 1)], keep=False)
                
                # Now add the new tile
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos}
        

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] * self.tilemap.tile_size - self.scroll[0], tile['pos'][1] * self.tilemap.tile_size - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            
            # Display current tile and spawner count info
            self.display.blit(current_tile_img, (5, 5))
            
            # Show spawner count
            spawner_count = self.count_spawners()
            spawner_text = self.font.render(f"Spawners: {spawner_count}/1", True, (255, 255, 255))
            self.display.blit(spawner_text, (5, 40))
            
            # Display current tile group/variant
            tile_info = self.font.render(f"Type: {self.tile_list[self.tile_group]} ({self.tile_variant})", True, (255, 255, 255))
            self.display.blit(tile_info, (5, 60))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            tile_type = self.tile_list[self.tile_group]
                            if tile_type == 'spawners' and self.count_spawners() > 0:
                                pass
                            elif (tile_type not in PHYSICS_TILES):
                                tile_pos = ((mpos[0] + self.scroll[0]) / self.tilemap.tile_size, (mpos[1] + self.scroll[1]) / self.tilemap.tile_size)
                                self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': tile_pos})
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')
                    if event.key in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                        self.shift = True
                    if event.key == pygame.K_UP:
                        if self.zoom < 20:
                            self.zoom += 1
                            self.zoom = int(self.zoom)
                            self.tilemap.tile_size = int(TILE_SIZE * self.zoom // 10)
                            self.assets = self.reload_assets()
                    if event.key == pygame.K_DOWN:
                        if self.zoom > 1:
                            self.zoom -= 1
                            self.zoom = int(self.zoom)
                            self.tilemap.tile_size = int(TILE_SIZE * self.zoom // 10)
                            self.assets = self.reload_assets()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key not in {pygame.K_LSHIFT, pygame.K_RSHIFT}:
                        self.shift = False
            
            pygame.display.update()
            self.clock.tick(FPS)

Editor().run()