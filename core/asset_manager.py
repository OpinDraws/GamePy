import pygame
import os
from core.config import ASSETS_DIR

class AssetManager:
    _instance = None

    def __new__(cls):
        """Реализация паттерна Singleton: гарантирует, что существует только один экземпляр."""
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        # Хранилища ресурсов
        self.fonts = {}
        self.images = {}
        self.sounds = {}
        
        # Флаг успешной загрузки музыки
        self.music_loaded = False
        
        self.initialized = True

    def load_resources(self):
        """Загружает все необходимые ресурсы игры."""
        print("--- AssetManager: Загрузка ресурсов... ---")
        self._load_fonts()
        self._load_images()
        self._load_music()
        print("--- AssetManager: Загрузка завершена ---")

    def _load_fonts(self):
        try:
            # Пытаемся найти красивые шрифты с засечками
            serif_path = pygame.font.match_font('cambria, georgia, timesnewroman, serif')
            
            # Шрифт имени босса (Жирный)
            font_boss_name = pygame.font.Font(serif_path, 28)
            font_boss_name.set_bold(True)
            self.fonts['boss_name'] = font_boss_name
            
            # Шрифт титула босса (Курсив)
            font_boss_title = pygame.font.Font(serif_path, 18)
            font_boss_title.set_italic(True)
            self.fonts['boss_title'] = font_boss_title
            
            # Обычный UI шрифт
            self.fonts['ui_main'] = pygame.font.SysFont("Arial", 18)
            
        except Exception as e:
            print(f"Ошибка загрузки шрифтов: {e}. Использую стандартные.")
            self.fonts['boss_name'] = pygame.font.SysFont(None, 28)
            self.fonts['boss_title'] = pygame.font.SysFont(None, 18)
            self.fonts['ui_main'] = pygame.font.SysFont(None, 18)

    def _load_images(self):
        # --- Иконка Босса ---
        icon_path = os.path.join(ASSETS_DIR, 'boss_icon.jpg')
        try:
            img = pygame.image.load(icon_path).convert()
            img = pygame.transform.smoothscale(img, (80, 80))
            img = pygame.transform.flip(img, True, False) # Отражаем, как было в main.py
            self.images['boss_icon'] = img
        except Exception as e:
            print(f"Внимание: Не удалось загрузить {icon_path} ({e}). Создаю заглушку.")
            # Создаем фиолетовый квадрат-заглушку
            surf = pygame.Surface((80, 80))
            surf.fill((50, 0, 50))
            self.images['boss_icon'] = surf

    def _load_music(self):
        music_path = os.path.join(ASSETS_DIR, 'boss_theme.mp3')
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)
                self.music_loaded = True
                print("Музыка успешно загружена.")
            except Exception as e:
                print(f"Ошибка загрузки музыки: {e}")
                self.music_loaded = False
        else:
            print(f"Файл музыки не найден: {music_path}")
            self.music_loaded = False

    # --- Геттеры (Getters) ---

    def get_font_boss_name(self):
        return self.fonts.get('boss_name')

    def get_font_boss_title(self):
        return self.fonts.get('boss_title')

    def get_font_ui(self):
        return self.fonts.get('ui_main')

    def get_boss_icon(self):
        return self.images.get('boss_icon')

    # Методы управления музыкой
    def play_music(self):
        if self.music_loaded and not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(loops=-1, fade_ms=4000)