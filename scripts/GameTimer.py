import pygame

class GameTimer:
    def __init__(self):
        self.start_ticks = None
        self.paused_ticks = 0
        self.pause_start_ticks = None
        self.is_running = False
        self.is_paused = False
        self.current_time = 0
        self.final_time = 0
        self.has_started = False
        self.highlight = False
        
        # Timer display settings
        self.display_font = None
        self.normal_color = (255, 255, 255)
        self.highlight_color = (255, 255, 0)
        self.shadow_color = (0, 0, 0, 180)
        self.use_shadow = True
        self.shadow_offset = (2, 2)
    
    def start(self):
        """Start the timer only if it hasn't been started yet"""
        if not self.has_started:
            # Use pygame's ticks for better performance with the game loop
            self.start_ticks = pygame.time.get_ticks()
            self.is_running = True
            self.has_started = True
    
    def update(self):
        """Update the current time"""
        if self.is_running and not self.is_paused:
            current_ticks = pygame.time.get_ticks()
            self.current_time = (current_ticks - self.start_ticks - self.paused_ticks) / 1000.0
    
    def pause(self):
        """Pause the timer"""
        if self.is_running and not self.is_paused:
            self.pause_start_ticks = pygame.time.get_ticks()
            self.is_paused = True
    
    def resume(self):
        """Resume the timer"""
        if self.is_running and self.is_paused:
            current_ticks = pygame.time.get_ticks()
            self.paused_ticks += current_ticks - self.pause_start_ticks
            self.is_paused = False
    
    def stop(self):
        """Stop the timer and save the final time"""
        if self.is_running:
            self.update()  # Make sure we have the latest time
            self.is_running = False
            self.final_time = self.current_time
            return self.final_time
        return 0
    
    def reset(self):
        """Reset the timer"""
        self.start_ticks = None
        self.paused_ticks = 0
        self.pause_start_ticks = None
        self.is_running = False
        self.is_paused = False
        self.current_time = 0
        self.final_time = 0
        self.has_started = False
        self.highlight = False
    
    def toggle_highlight(self):
        """Toggle highlighting of the timer"""
        self.highlight = not self.highlight
    
    def format_time(self, time_value):
        """Format time as MM:SS.ms"""
        minutes = int(time_value // 60)
        seconds = int(time_value % 60)
        milliseconds = int((time_value % 1) * 1000)
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    
    def get_formatted_current_time(self):
        """Get the formatted current time"""
        return self.format_time(self.current_time)
    
    def get_formatted_final_time(self):
        """Get the formatted final time"""
        return self.format_time(self.final_time)
    
    def set_font(self, font):
        """Set the font used for displaying the timer"""
        self.display_font = font
    
    def set_colors(self, normal_color=(255, 255, 255), highlight_color=(255, 255, 0)):
        """Set the colors used for displaying the timer"""
        self.normal_color = normal_color
        self.highlight_color = highlight_color
    
    def toggle_shadow(self, use_shadow=True, shadow_color=(0, 0, 0, 180), offset=(2, 2)):
        """Toggle and configure text shadow for better visibility"""
        self.use_shadow = use_shadow
        self.shadow_color = shadow_color
        self.shadow_offset = offset
    
    def render(self, surface, position, font=None):
        if font:
            self.display_font = font
        
        if not self.display_font:
            return
            
        # Determine which time to show (current or final)
        time_str = self.get_formatted_final_time() if not self.is_running else self.get_formatted_current_time()
        
        # Choose color based on highlight state
        color = self.highlight_color if self.highlight else self.normal_color
        
        # Render with shadow for better visibility
        if self.use_shadow:
            shadow_text = self.display_font.render(time_str, True, self.shadow_color)
            shadow_pos = (position[0] + self.shadow_offset[0], position[1] + self.shadow_offset[1])
            surface.blit(shadow_text, shadow_pos)
        
        # Render the main text
        timer_text = self.display_font.render(time_str, True, color)
        surface.blit(timer_text, position)