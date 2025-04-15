from constants import *

import pygame

class Player:
    def __init__(self, game, pos, size):
        self.game = game
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.air_time = 0
        self.grounded = False
        
        self.action = ''
        self.anim_offset = (0 ,0)
        self.deg = 0
        self.facing_right = True
        self.set_action('run')
    
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets['player/' + self.action].copy()
        
    def update(self, tilemap, keys):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        self.velocity[0] += (int(keys['right']) - int(keys['left'])) * PLAYER_SPEED
        self.velocity[0] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[0] * (1 - ACCELERAION)))
        self.velocity[1] = max(-MAX_X_SPEED, min(MAX_X_SPEED, self.velocity[1] + GRAVITY))
        if keys['jump'] and self.grounded:
            self.velocity[1] = -JUMP_SPEED
        
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

        if keys['right'] and not keys['left']:
            self.facing_right = True
        elif keys['left'] and not keys['right']:
            self.facing_right = False

        if self.collisions['right'] or self.collisions['left']:
            self.velocity[0] = 0
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0
        self.grounded = self.air_time <= 4

        if self.grounded: self.set_action('run')
        else: self.set_action('jump')
        self.animation.update()
        
    def render(self, surf, offset=(0, 0)):
        # Get the original image
        original_img = self.animation.img()
        
        # Flip the image horizontally if facing left
        if not self.facing_right:
            original_img = pygame.transform.flip(original_img, True, False)
        
        # Rotate the image around its center (if you still want rotation)
        rotated_img = pygame.transform.rotate(original_img, -self.deg)
        
        # Get the rectangle of the rotated image
        rotated_rect = rotated_img.get_rect(center=(self.pos[0] + self.size[0] // 2 - offset[0],
                                                self.pos[1] + self.size[1] // 2 - offset[1]))
        # Draw the rotated image
        surf.blit(rotated_img, rotated_rect)