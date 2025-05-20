import pygame
from scripts.constants import PLAYER_BUFFER

class InputHandler:
    def __init__(self):
        self.keys = {'left': False, 'right': False, 'jump': False}
        self.buffer_times = {'jump': 0}
        
        # Initialize controller support
        pygame.joystick.init()
        self.controllers = []
        self.update_controllers()
        
        # Define controller settings
        self.controller_deadzone = 0.5  # Analog stick deadzone threshold
        
    def update_controllers(self):
        """Detect and initialize all connected controllers"""
        self.controllers = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        for controller in self.controllers:
            controller.init()
        
    def process_events(self, events, menu_active=False):
        # Check if any controllers were connected or disconnected
        for event in events:
            if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
                self.update_controllers()
        
        # Skip gameplay input processing if menu is active
        if menu_active:
            return self.keys, self.buffer_times
                
        for event in events:
            # Keyboard input handling (unchanged)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.keys['right'] = True
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.keys['left'] = True
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.keys['jump'] = True
                        
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.keys['right'] = False
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.keys['left'] = False
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self.keys['jump'] = False
                    self.buffer_times['jump'] = 0
                    
            # Controller button press events
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button (Xbox) / X button (PlayStation)
                    self.keys['jump'] = True
                    
            if event.type == pygame.JOYBUTTONUP:
                if event.button == 0:  # A button (Xbox) / X button (PlayStation)
                    self.keys['jump'] = False
                    self.buffer_times['jump'] = 0
                    
            # Controller hat (D-pad) events
            if event.type == pygame.JOYHATMOTION:
                if event.value[0] == 1:  # Right on D-pad
                    self.keys['right'] = True
                    self.keys['left'] = False
                elif event.value[0] == -1:  # Left on D-pad
                    self.keys['left'] = True
                    self.keys['right'] = False
                elif event.value[0] == 0:  # No horizontal input on D-pad
                    # Only reset if it was set by controller D-pad (not keyboard)
                    if not any(pygame.key.get_pressed()[key] for key in [pygame.K_RIGHT, pygame.K_d, pygame.K_LEFT, pygame.K_a]):
                        self.keys['right'] = False
                        self.keys['left'] = False
        
        # Process continuous controller input (analog sticks)
        if self.controllers:
            for controller in self.controllers:
                # Left analog stick horizontal axis
                left_stick_x = controller.get_axis(0)
                
                # Handle left analog stick for movement
                if left_stick_x > self.controller_deadzone:  # Right on analog stick
                    self.keys['right'] = True
                    self.keys['left'] = False
                elif left_stick_x < -self.controller_deadzone:  # Left on analog stick
                    self.keys['left'] = True
                    self.keys['right'] = False
                elif -0.2 < left_stick_x < 0.2:  # Deadzone - no input
                    # Only reset if it was set by controller (not keyboard)
                    if not any(pygame.key.get_pressed()[key] for key in [pygame.K_RIGHT, pygame.K_d]):
                        self.keys['right'] = False
                    if not any(pygame.key.get_pressed()[key] for key in [pygame.K_LEFT, pygame.K_a]):
                        self.keys['left'] = False
                        
        # Update jump buffer logic
        if self.keys['jump']:
            self.buffer_times['jump'] += 1
            if self.buffer_times['jump'] > PLAYER_BUFFER:
                self.buffer_times['jump'] = PLAYER_BUFFER + 1
                        
        return self.keys, self.buffer_times