from scripts.constants import *
import random
import pygame

class Player:
    def __init__(self, game, pos, size, sfx):
        self.game = game
        self.start_pos = pos
        self.size = size
        self.sfx = sfx
        self._initialize()

    def _initialize(self):
        self.pos = list(self.start_pos)
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.air_time = 5
        self.grounded = False
        self.facing_right = True
        self.jump_available = True  # Single flag to control jump availability
        self.action = ''
        self.death = False 
        self.finishLevel = False 
        self.respawn = False
        self.was_colliding_wall = False
        self.wall_contact_time = 0
        self.wall_momentum_active = False
        self.set_action('run')

    def reset(self):
        self._initialize()
        #self.game.scroll = list(self.start_pos).copy()
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['player/' + self.action].copy()
    
    def update(self, tilemap, keys, countdeathframes):
        self.animation.update()

        if tilemap.is_below_map(self.pos):
            self.death = True
            self.velocity = [0, 0]
            self.set_action('death')
            return 

        if countdeathframes > 40 or self.finishLevel:
            return 
        
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        if not self.death and not self.finishLevel:
            self.velocity[0] += (int(keys['right']) - int(keys['left'])) * PLAYER_SPEED
            x_acceleration = (1 - DECCELARATION) if int(keys['right']) - int(keys['left']) == 0 else (1 - ACCELERAION)
            self.velocity[0] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[0] * x_acceleration))

            gravity = GRAVITY_DOWN if self.velocity[1] > 0 and not keys['jump'] else GRAVITY_UP
            self.velocity[1] = max(-MAX_Y_SPEED, min(MAX_Y_SPEED, self.velocity[1] + gravity))
        else:
            self.velocity[0] = 0    
            self.velocity[1] = 0
            
        self.pos[0] += self.velocity[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if self.velocity[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        self.pos[1] += self.velocity[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if self.velocity[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if self.velocity[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        entity_rect = self.rect()
        for rect, tile_info in tilemap.interactive_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                tile_type = tile_info[0]
                if tile_type in ['spikes', 'saws', 'kill']:
                    self.death = True 
                    self.velocity = [0, 0]
                    self.set_action('death')
                    return
                elif tile_type == 'finish':
                    self.finishLevel = True

        if keys['right'] and not keys['left']:
            self.facing_right = True
        elif keys['left'] and not keys['right']:
            self.facing_right = False

        if self.collisions['right'] or self.collisions['left']:
            self.velocity[0] = 0
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        # Check if we just hit a wall this frame
        now_colliding_wall = self.collisions['left'] or self.collisions['right']
        if now_colliding_wall and not self.was_colliding_wall:  
            random.choice(self.sfx['collide']).play()
        self.was_colliding_wall = now_colliding_wall

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
        self.grounded = self.air_time <= 4

        if self.death:
            self.set_action('death') 
        elif (self.collisions['left'] or self.collisions['right']) and self.velocity[1] > 0 and not self.grounded:
            self.set_action('wallslide')
        elif (self.collisions['left'] or self.collisions['right']):
            self.set_action('wallcollide')
        elif abs(self.velocity[0]) > 0.5:
            self.set_action('run')
        elif self.velocity[1] < 1 and not self.grounded:
            self.set_action('jump')  
        elif self.velocity[1] > 1 and not self.grounded:
            self.set_action('fall')  
        else:
            self.set_action('idle')
        
        # Reset jump availability when key is released
        if not keys['jump']:
            self.jump_available = True
        
        # Handle jumps - Only if jump is available and key is pressed
        elif keys['jump'] and self.jump_available:
            self.jump_available = False
            
            # Wall jump logic
            if not self.grounded and (self.collisions['left'] or self.collisions['right']):
                self.velocity[1] = -WALLJUMP_Y_SPEED
                if self.collisions['right']: self.velocity[0] = -WALLJUMP_X_SPEED
                if self.collisions['left']: self.velocity[0] = WALLJUMP_X_SPEED
                random.choice(self.sfx['jump']).play()  # Play jump sound directly
            
            # Regular jump logic
            elif self.grounded and self.game.buffer_time <= PLAYER_BUFFER:
                self.velocity[1] = -JUMP_SPEED
                self.air_time = 5
                self.grounded = False
                random.choice(self.sfx['jump']).play()
        
        # Wall slide, wall slide momentum logic
        if not self.grounded and (self.collisions['left'] or self.collisions['right']):
            if not self.was_colliding_wall:
                self.wall_contact_time = 0
                if self.velocity[1] < 0:
                    self.wall_momentum_active = True
            
            self.wall_contact_time += 1
            
            if self.wall_momentum_active and self.wall_contact_time <= WALL_MOMENTUM_FRAMES:
                self.velocity[1] *= WALL_MOMENTUM_PRESERVE
            else:
                self.wall_momentum_active = False
                if self.velocity[1] > 0:  
                    self.velocity[1] = min(WALLSLIDE_SPEED, self.velocity[1])
        
        # Cut jump short if key released
        if not keys['jump'] and self.velocity[1] < 0:
            self.velocity[1] = 0
        
    def render(self, surf, offset=(0, 0)):
        # Get the original image
        image = self.animation.img()
        
        # Flip the image horizontally if facing left
        if not self.facing_right:
            image = pygame.transform.flip(image, True, False)
        
        # Get the rectangle of the rotated image
        image_rect = image.get_rect(center=(self.pos[0] + self.size[0] // 2 - offset[0],
                                                self.pos[1] + self.size[1] // 2 - offset[1]))
        # Draw the rotated image
        surf.blit(image, image_rect)
        