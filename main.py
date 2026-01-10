import pygame
import sys

# Импорты из ядра
from core.config import WIDTH, HEIGHT, FPS, COLOR_BG
from core.asset_manager import AssetManager
from core.scene_manager import SceneManager

# Импорты сцен
from scenes.game_scene import GameScene
from scenes.menu_scene import MenuScene

def main():
    # 1. Инициализация Pygame и окна
    pygame.init()
    # Инициализация звука должна быть до загрузки ресурсов
    try:
        pygame.mixer.init()
    except Exception as e:
        print(f"Ошибка инициализации звука: {e}")

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("Bloodbound ascent - Refactored")
    clock = pygame.time.Clock()

    # 2. Загрузка ресурсов через синглтон AssetManager
    # Это загрузит шрифты, картинки и музыку один раз при старте
    asset_manager = AssetManager()
    asset_manager.load_resources()

    # 3. Создание менеджера сцен
    scene_manager = SceneManager()

    # 4. Запуск стартовой сцены (ТЕПЕРЬ МЕНЮ)
    start_scene = MenuScene(scene_manager)
    scene_manager.switch_to(start_scene)

    # 5. Главный игровой циклы
    running = True
    while running:
        # Расчет дельты времени (в секундах) для независимости физики от FPS
        dt = clock.tick(FPS) / 1000.0

        # Сбор событий Pygame
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        # --- Делегирование управления активной сцене ---
        
        # Обработка ввода (клавиши, клики)
        scene_manager.handle_input(events)
        
        # Обновление логики сцены
        scene_manager.update(dt)
        
        # Отрисовка сцены
        # Можно предварительно очистить экран цветом фона
        screen.fill(COLOR_BG) 
        scene_manager.draw(screen)

        pygame.display.flip()

    # Корректный выход
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()