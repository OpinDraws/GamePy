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
        
        self.fonts = {}
        self.images = {}
        self.sounds = {} # Для коротких эффектов
        
        # НОВОЕ: Хранилище для музыки (как Sound объекты)
        self.music_assets = {} 
        # НОВОЕ: Текущий канал, на котором играет музыка
        self.music_channel = None 
        
        self.initialized = True

    def load_resources(self):
        """Загружает все необходимые ресурсы игры."""
        print("--- AssetManager: Загрузка ресурсов... ---")
        self._load_fonts()
        self._load_images()
        self._load_music()
        self._load_sounds()  # <--- ДОБАВИТЬ ЭТУ СТРОКУ
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
        # Попробуем загрузить, проверяя расширения
        tracks_to_load = ['boss', 'dungeon']
        
        print("--- Загрузка музыки в память ---")
        for name in tracks_to_load:
            # Сначала пробуем wav (лучше для производительности)
            wav_path = os.path.join(ASSETS_DIR, f"{name}_theme.wav")
            ogg_path = os.path.join(ASSETS_DIR, f"{name}_theme.ogg")
            mp3_path = os.path.join(ASSETS_DIR, f"{name}_theme.mp3")
            
            path_to_use = None
            if os.path.exists(wav_path):
                path_to_use = wav_path
            elif os.path.exists(ogg_path):
                path_to_use = ogg_path
            elif os.path.exists(mp3_path):
                path_to_use = mp3_path
            
            if path_to_use:
                try:
                    sound_obj = pygame.mixer.Sound(path_to_use)
                    # sound_obj.set_volume(0.5) 
                    self.music_assets[name] = sound_obj
                    print(f"Музыка загружена: {name} из {path_to_use}")
                except Exception as e:
                    print(f"Ошибка загрузки {path_to_use}: {e}")
            else:
                print(f"НЕ НАЙДЕН файл музыки для: {name}")

    def play_music(self, track_name, loops=-1, fade_ms=1000):
        """
        Проигрывает музыку без лагов, используя preloaded Sound объекты.
        """
        if track_name not in self.music_assets:
            print(f"Трек {track_name} не найден!")
            return

        # 1. Если музыка уже играет, плавно глушим старую
        if self.music_channel and self.music_channel.get_busy():
            self.music_channel.fadeout(fade_ms)

        # 2. Получаем объект звука
        new_track = self.music_assets[track_name]
        
        # 3. Находим свободный канал или принудительно берем канал (например, канал 0 reserved)
        # Лучше всего использовать play(), он сам найдет свободный канал и вернет его
        self.music_channel = new_track.play(loops=loops, fade_ms=fade_ms)
        
        # Устанавливаем громкость канала (общая громкость музыки)
        if self.music_channel:
            self.music_channel.set_volume(0.5)

    def stop_music(self, fade_ms=1000):
        """Останавливает текущую музыку."""
        if self.music_channel and self.music_channel.get_busy():
            self.music_channel.fadeout(fade_ms)
    # --- Геттеры (Getters) ---

    def get_font_boss_name(self):
        return self.fonts.get('boss_name')

    def get_font_boss_title(self):
        return self.fonts.get('boss_title')

    def get_font_ui(self):
        return self.fonts.get('ui_main')

    def get_boss_icon(self):
        return self.images.get('boss_icon')

   
    def _load_sounds(self):
        # Список: (ключ, имя_файла)
        sound_files = [
            ('tentacle_lunge', 'tentacle_lunge.wav'),
            ('tentacle_strike', 'tentacle_strike.wav'),
            ('brain_spike', 'brain_spike.wav'),
            ('boss_spear', 'boss_spear.wav')
        ]

        for name, filename in sound_files:
            path = os.path.join(ASSETS_DIR, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                    
                    # ИЗМЕНИТЕ ЭТО ЧИСЛО:
                    # 0.4 -> 40% громкости (было в примере)
                    # 0.1 -> 10% громкости (тихо)
                    # 0.05 -> 5% громкости (очень тихо)
                    self.sounds[name].set_volume(0.3) 
                    
                except Exception as e:
                    print(f"Ошибка загрузки звука {filename}: {e}")

    def play_sound(self, name, volume=None):
        """Воспроизводит звук по имени."""
        if name in self.sounds:
            sound = self.sounds[name]
            if volume is not None:
                sound.set_volume(volume)
            sound.play()