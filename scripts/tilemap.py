# tilemap.py
import json
import pygame
from scripts.constants import PHYSICS_TILES, INTERACTIVE_TILES, SPIKE_SIZE

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.lowest_y = 0
        self.map_background = None
    
    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        
        tilemap_keys = list(self.tilemap.keys())
        for loc in tilemap_keys:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                match = tile.copy()
                if isinstance(match['pos'], tuple):
                    match['pos'] = list(match['pos'])
                else:
                    match['pos'] = match['pos'].copy()
                match['pos'][0] *= self.tile_size
                match['pos'][1] *= self.tile_size
                matches.append(match)
                if not keep:
                    del self.tilemap[loc]
        
        return matches

    def save(self, path):
        lowest_y = 0
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            lowest_y = max(lowest_y, tile['pos'][1])

        spawner_tiles = self.extract([('spawners', 0), ('spawners', 1)], keep=True)
        if len(spawner_tiles) > 1:
            self.extract([('spawners', 0), ('spawners', 1)], keep=False)
            spawner = spawner_tiles[0]
            if 'pos' in spawner:
                pos = spawner['pos'].copy()
                if len(str(pos[0]).split('.')) == 1:
                    pos[0] = pos[0] // self.tile_size
                    pos[1] = pos[1] // self.tile_size
                
                tile_loc = f"{int(pos[0])};{int(pos[1])}"
                self.tilemap[tile_loc] = {
                    'type': spawner['type'], 
                    'variant': spawner['variant'], 
                    'pos': [int(pos[0]), int(pos[1])]
                }
        
        f = open(path, 'w')
        json.dump({
            'tilemap': self.tilemap, 
            'offgrid': self.offgrid_tiles,
            'lowest_y': lowest_y,
            'map': self.map_background
        }, f, indent=4)
        f.close()
        
    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
        self.tilemap = map_data['tilemap']
        self.offgrid_tiles = map_data['offgrid']
        self.lowest_y = map_data.get('lowest_y', 0)
        self.map_background = map_data.get('map', None)

        spawner_tiles = self.extract([('spawners', 0), ('spawners', 1)], keep=True)
        if len(spawner_tiles) > 1:
            self.extract([('spawners', 0), ('spawners', 1)], keep=False)
            spawner = spawner_tiles[0]
            if 'pos' in spawner:
                pos = spawner['pos'].copy()
                if len(str(pos[0]).split('.')) == 1:
                    pos[0] = pos[0] // self.tile_size
                    pos[1] = pos[1] // self.tile_size
                
                tile_loc = f"{int(pos[0])};{int(pos[1])}"
                self.tilemap[tile_loc] = {
                    'type': spawner['type'], 
                    'variant': spawner['variant'], 
                    'pos': [int(pos[0]), int(pos[1])]
                }
    
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    def get_spike_rect_with_rotation(self, tile):
        spike_width = int(self.tile_size * SPIKE_SIZE[0])
        spike_height = int(self.tile_size * SPIKE_SIZE[1])
        rotation = tile.get('rotation', 0)
        
        tile_x = tile['pos'][0] * self.tile_size
        tile_y = tile['pos'][1] * self.tile_size
        
        rect_data = {
            0: (tile_x + (self.tile_size - spike_width) // 2,
                tile_y + (self.tile_size - spike_height),
                spike_width, spike_height),
            90: (tile_x + (self.tile_size - spike_height),
                tile_y + (self.tile_size - spike_width) // 2,
                spike_height, spike_width),
            180: (tile_x + (self.tile_size - spike_width) // 2,
                tile_y, spike_width, spike_height),
            270: (tile_x, tile_y + (self.tile_size - spike_width) // 2,
                spike_height, spike_width)
        }
        
        x, y, width, height = rect_data.get(rotation, rect_data[0])
        return pygame.Rect(x, y, width, height)

    def interactive_rects_around(self, pos):
        tiles = []
        for tile in self.tiles_around(pos):
            if tile['type'] in INTERACTIVE_TILES:
                match tile['type']:
                    case 'finish':
                        tiles.append((pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size), (tile['type'], tile['variant'])))
                    case 'spikes':
                        spike_rect = self.get_spike_rect_with_rotation(tile)
                        tiles.append((spike_rect, (tile['type'], tile['variant'])))
                    case 'kill':
                        kill_rect = pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size)
                        tiles.append((kill_rect, (tile['type'], tile['variant'])))
        return tiles
    
    def is_below_map(self, entity_pos, tiles_threshold=2):
        lowest_tile_y = self.lowest_y * self.tile_size
        if entity_pos[1] > lowest_tile_y + (tiles_threshold * self.tile_size):
            return True
        return False

    def render(self, surf, offset=(0, 0), zoom=10):
        # For offgrid tiles
        for tile in self.offgrid_tiles:
            if tile['type'] == 'spikes' and 'rotation' in tile:
                img = self.game.get_rotated_image(tile['type'], tile['variant'], tile['rotation'])
                x = tile['pos'][0] * self.tile_size - offset[0] - (img.get_width() - self.tile_size) // 2
                y = tile['pos'][1] * self.tile_size - offset[1] - (img.get_height() - self.tile_size) // 2
                surf.blit(img, (x, y))
            else:
                surf.blit(self.game.assets[tile['type']][tile['variant']], 
                        (tile['pos'][0] * self.tile_size - offset[0], 
                        tile['pos'][1] * self.tile_size - offset[1]))
                    
        # For grid tiles
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if tile['type'] == 'spikes' and 'rotation' in tile:
                img = self.game.get_rotated_image(tile['type'], tile['variant'], tile['rotation'])
                x_pos = tile['pos'][0] * self.tile_size - offset[0] - (img.get_width() - self.tile_size) // 2
                y_pos = tile['pos'][1] * self.tile_size - offset[1] - (img.get_height() - self.tile_size) // 2
                surf.blit(img, (x_pos, y_pos))
            else:
                surf.blit(self.game.assets[tile['type']][tile['variant']], 
                        (tile['pos'][0] * self.tile_size - offset[0], 
                        tile['pos'][1] * self.tile_size - offset[1]))
    
    def get_background_map(self):
        return self.map_background
    
    def set_background_map(self, map_path):
        self.map_background = map_path
        