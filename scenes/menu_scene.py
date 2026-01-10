import pygame
import sys
from core.scene_manager import Scene
from core.asset_manager import AssetManager
from core.config import WIDTH, HEIGHT, COLOR_BG

# УБРАЛИ ВЕРХНИЙ ИМПОРТ

class MenuScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager()
        
        self.title_font = self.assets.get_font_boss_name() 
        self.ui_font = self.assets.get_font_ui()

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    print("Меню: Переход в игру")
                    # ЛОКАЛЬНЫЙ ИМПОРТ
                    from scenes.game_scene import GameScene
                    
                    game_scene = GameScene(self.manager)
                    self.manager.switch_to(game_scene)
                
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(COLOR_BG)
        
        title_text = "Bloodbound ascent"
        title_surf = self.title_font.render(title_text, True, (220, 50, 60)) 
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        surface.blit(title_surf, title_rect)
        
        current_time = pygame.time.get_ticks()
        if (current_time // 500) % 2 == 0:
            start_text = "Нажмите ENTER, чтобы начать"
            start_surf = self.ui_font.render(start_text, True, (255, 255, 255))
            start_rect = start_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
            surface.blit(start_surf, start_rect)
            
        quit_text = "ESC - Выход"
        quit_surf = self.ui_font.render(quit_text, True, (100, 100, 100))
        quit_rect = quit_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        surface.blit(quit_surf, quit_rect)