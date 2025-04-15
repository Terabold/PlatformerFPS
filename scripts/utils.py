import os

import pygame
from constants import FONT
BASE_IMG_PATH = 'data/images/'

def load_image(path, scale = None, remove_color = (0, 0, 0)):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    if remove_color is not None: img.set_colorkey(remove_color)
    if scale is not None:
        img = pygame.transform.scale(img, scale)
    return img

def load_images(path, scale = None, remove_color = (0, 0, 0)):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name, scale, remove_color))
    return images
        

class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]
    

class Text():
    def __init__(self, text, pos, color = (0,0,0), size = 50, font = FONT):
        font = pygame.font.Font(font, size)
        self.text = font.render(text, True, color)
        self.text_rect = self.text.get_rect(center=pos)

    def blit(self, display):
        display.blit(self.text, self.text_rect)
    

class Button:
    def __init__(self, text = '', background_color = (255, 255, 255), button_type = '', hover=True, scale_factor=1.2):
        # Store the Text object
        self.text = text
        self.background_color = background_color
        self.type = button_type
        self.hover_enabled = hover
        self.scale_factor = scale_factor
        
        # Get the rect from the text object
        self.rect = self.text.text_rect.copy()
        
        # Create slightly larger rectangle for better clickable area
        self.padding = 10  # pixels of padding around text
        self.hover_rect = pygame.Rect(
            self.rect.x - self.padding,
            self.rect.y - self.padding,
            self.rect.width + (self.padding * 2),
            self.rect.height + (self.padding * 2)
        )
        
        # Store original surfaces for scaling
        self.original_text_surface = self.text.text
        
        # Pre-calculate the scaled text for hover effect
        scaled_width = int(self.original_text_surface.get_width() * self.scale_factor)
        scaled_height = int(self.original_text_surface.get_height() * self.scale_factor)
        self.scaled_text_surface = pygame.transform.scale(
            self.original_text_surface, 
            (scaled_width, scaled_height)
        )
        
        # Pre-calculate the scaled hover rect
        hover_width = int(self.hover_rect.width * self.scale_factor)
        hover_height = int(self.hover_rect.height * self.scale_factor)
        center_x, center_y = self.hover_rect.center
        self.scaled_hover_rect = pygame.Rect(
            center_x - hover_width // 2,
            center_y - hover_height // 2,
            hover_width,
            hover_height
        )
        
        # Track mouse button state
        self.mouse_pressed = False
        self.mouse_released = False
        
        # Debug flag - set to True to see collision boxes
        self.debug = False

    def update(self, mouse_pressed=None, mouse_released=None):
        # This method should be called every frame before rendering
        # Update mouse position check
        
        self.mouse_pos = pygame.mouse.get_pos()
        
        # Update mouse button state if provided
        if mouse_pressed is not None:
            self.mouse_pressed = mouse_pressed
        if mouse_released is not None:
            self.mouse_released = mouse_released
        
    def is_hovered(self):
        # Use the hover_rect (with padding) for better hit detection
        return self.hover_rect.collidepoint(self.mouse_pos)
    
    def is_clicked(self):
        """Returns True if the button was clicked (pressed and released while hovering)"""
        return self.is_hovered() and self.mouse_released

    def blit(self, display):
        # Always update mouse position before rendering
        self.update()
        
        # Check if we're hovering
        hovering = self.is_hovered() and self.hover_enabled
        
        if hovering:
            # Draw hover state
            pygame.draw.rect(display, self.background_color, self.scaled_hover_rect)
            
            # Center the scaled text in the scaled rect
            scaled_text_rect = self.scaled_text_surface.get_rect(center=self.scaled_hover_rect.center)
            display.blit(self.scaled_text_surface, scaled_text_rect)
        else:
            # Draw normal state
            pygame.draw.rect(display, self.background_color, self.hover_rect)
            display.blit(self.original_text_surface, self.rect)
        
        # Debug visualization
        if self.debug:
            # Draw collision detection box in red
            pygame.draw.rect(display, (255, 0, 0), self.hover_rect, 1)
            # Draw a dot at mouse position
            pygame.draw.circle(display, (0, 255, 0), self.mouse_pos, 3)