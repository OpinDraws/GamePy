import pygame
import os

# --- ПУТИ К ФАЙЛАМ ---
# Получаем абсолютный путь к папке, где лежит этот config.py (папка core)
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
# Получаем корневую папку проекта (на уровень выше core)
BASE_DIR = os.path.dirname(CORE_DIR)
# Путь к папке с ассетами
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# Инициализируем дисплей, чтобы узнать разрешение экрана
# (Примечание: лучше вынести это из конфига в будущем, но пока оставим для совместимости)
if not pygame.display.get_init():
    pygame.display.init()

WIDTH, HEIGHT = 1900, 1020
# Если нужно реальное разрешение монитора, можно раскомментировать:
# info = pygame.display.Info()
# WIDTH, HEIGHT = info.current_w, info.current_h

FPS = 60
TILE_SIZE = 40

# --- Цветовая Палитра (Gothic Neon) ---
COLOR_BG = (15, 10, 20)          # Очень темный фиолетово-черный
COLOR_GRID = (30, 20, 40)        # Тусклая сетка

# Вампир
COLOR_VAMPIRE_SKIN = (240, 240, 255) # Мертвецки бледный
COLOR_VAMPIRE_CLOAK = (20, 20, 25)   # Почти черный плащ
COLOR_VAMPIRE_ACCENT = (180, 0, 50)  # Кровавый красный

# Монстры
COLOR_MONSTER_BODY = (40, 0, 60)     # Темно-фиолетовая плоть
COLOR_MONSTER_OUTLINE = (100, 0, 150)# Неоновый фиолетовый контур
COLOR_MONSTER_EYE = (255, 200, 0)    # Желтые глаза
COLOR_MONSTER_GLOW = (150, 0, 200)   

# Снаряды
COLOR_BLOOD_CORE = (255, 200, 200)
COLOR_BLOOD_TRAIL = (200, 0, 0)

COLOR_PARTICLE = (200, 200, 200)


COLOR_PM_BODY = (80, 40, 140)
COLOR_PM_BODY_DARK = (40, 10, 80)
COLOR_PM_EYE = (255, 140, 20)
COLOR_PM_PUPIL = (20, 0, 0)

# --- Группы Спрайтов ---
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
particles = pygame.sprite.Group()