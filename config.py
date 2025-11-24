import pygame

# --- Экран и Частота обновлений ---
WIDTH, HEIGHT = 1280, 720
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

# --- Группы Спрайтов ---
all_sprites = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
particles = pygame.sprite.Group()