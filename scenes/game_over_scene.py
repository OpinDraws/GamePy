import pygame
import sys
from core.scene_manager import Scene
from core.asset_manager import AssetManager
from core.config import WIDTH, HEIGHT, COLOR_BG

# УБРАЛИ ВЕРХНИЕ ИМПОРТЫ СЦЕН, ЧТОБЫ ИЗБЕЖАТЬ ЦИКЛА

class GameOverScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager()
        self.title_font = self.assets.get_font_boss_name()
        self.ui_font = self.assets.get_font_ui()
        print("Сцена Game Over: Инициализация")

    def enter(self):
        # Останавливаем музыку игры
        self.assets.stop_music()

    def handle_input(self, events):
        # ЛОКАЛЬНЫЙ ИМПОРТ (Здесь разрываем круг)
        from scenes.game_scene import GameScene
        from scenes.menu_scene import MenuScene

        for event in events:
            if event.type == pygame.KEYDOWN:
                # R для рестарта (переход в GameScene)
                if event.key == pygame.K_r:
                    print("Game Over: Перезапуск игры")
                    # Пересоздаем GameScene, чтобы начать игру заново
                    game_scene = GameScene(self.manager)
                    self.manager.switch_to(game_scene)
                # ESC для выхода в меню (переход в MenuScene)
                elif event.key == pygame.K_ESCAPE:
                    print("Game Over: Выход в меню")
                    menu_scene = MenuScene(self.manager)
                    self.manager.switch_to(menu_scene)
    
    def update(self, dt):
        pass

    def draw(self, surface):
        # Заливаем экран темным фоном
        surface.fill(COLOR_BG)
        
        # 1. Текст "YOU DIED"
        title_text = "YOU DIED"
        title_surf = self.title_font.render(title_text, True, (255, 0, 0)) # Ярко-красный
        title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        surface.blit(title_surf, title_rect)
        
        # 2. Текст подсказок
        restart_text = "Нажмите R для рестарта"
        menu_text = "Нажмите ESC для выхода в меню"
        
        restart_surf = self.ui_font.render(restart_text, True, (200, 200, 200))
        menu_surf = self.ui_font.render(menu_text, True, (150, 150, 150))
        
        restart_rect = restart_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        menu_rect = menu_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
        
        surface.blit(restart_surf, restart_rect)
        surface.blit(menu_surf, menu_rect)