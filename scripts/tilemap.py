import json

import pygame
from scripts.constants import PHYSICS_TILES, AUTOTILE_TYPES, INTERACTIVE_TILES, SPIKE_SIZE

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2, 
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone'}
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
    
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
        
        # Convert dict keys to a list before iteration to avoid RuntimeError
        tilemap_keys = list(self.tilemap.keys())
        for loc in tilemap_keys:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                match = tile.copy()
                # Check if pos is a tuple and convert to list if necessary
                if isinstance(match['pos'], tuple):
                    match['pos'] = list(match['pos'])
                else:
                    match['pos'] = match['pos'].copy()
                match['pos'][0] *= self.tile_size
                match['pos'][1] *= self.tile_size
                matches.append(match)
                if not keep:
                    del self.tilemap[loc]
        
        # Return the matches list
        return matches

    def save(self, path):
        # First check if there are multiple spawners and keep only one if needed
        spawner_tiles = self.extract([('spawners', 0), ('spawners', 1)], keep=True)
        if len(spawner_tiles) > 1:
            # Remove all spawners first
            self.extract([('spawners', 0), ('spawners', 1)], keep=False)
            # Then add back only the first one
            spawner = spawner_tiles[0]
            if 'pos' in spawner:
                pos = spawner['pos'].copy()
                # Convert back to tile coordinates if it was scaled
                if len(str(pos[0]).split('.')) == 1:  # Integer check
                    pos[0] = pos[0] // self.tile_size
                    pos[1] = pos[1] // self.tile_size
                
                tile_loc = f"{int(pos[0])};{int(pos[1])}"
                self.tilemap[tile_loc] = {
                    'type': spawner['type'], 
                    'variant': spawner['variant'], 
                    'pos': [int(pos[0]), int(pos[1])]
                }
        
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'offgrid': self.offgrid_tiles}, f, indent=4)
        f.close()
        
    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        
        self.tilemap = map_data['tilemap']
        #self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
        
        # Ensure only one spawner is present after loading
        spawner_tiles = self.extract([('spawners', 0), ('spawners', 1)], keep=True)
        if len(spawner_tiles) > 1:
            # Remove all spawners
            self.extract([('spawners', 0), ('spawners', 1)], keep=False)
            # Add back only the first one
            spawner = spawner_tiles[0]
            if 'pos' in spawner:
                pos = spawner['pos'].copy()
                # Convert back to tile coordinates
                if len(str(pos[0]).split('.')) == 1:  # Integer check
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
    
    def interactive_rects_around(self, pos):
        tiles = []
        for tile in self.tiles_around(pos):
            if tile['type'].split()[0] in INTERACTIVE_TILES:
                match tile['type'].split()[0]:
                    case 'finish':
                        tiles.append((pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size), (tile['type'].split()[0], tile['variant'])))
                    case 'spike':
                        colrect = pygame.Rect(
                            self.tile_size * tile['pos'][0], 
                            self.tile_size * tile['pos'][1], 
                            int(self.tile_size*SPIKE_SIZE[0]), 
                            int(self.tile_size*SPIKE_SIZE[1])
                        )
                        colrect.center = (
                            self.tile_size * tile['pos'][0] + self.tile_size//2, 
                            self.tile_size * tile['pos'][1] + self.tile_size//2
                        )
                        tiles.append((colrect, (tile['type'], tile['variant'])))
                    # case 'orb':
                    #     tiles.append((pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size), (tile['type'], tile['variant'])))
        return tiles
    
    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0), zoom = 10):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
            
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))