import pygame
import random
import math
from core.config import WIDTH, HEIGHT

# --- ПАЛИТРА ПЕЩЕРЫ ---
C_CAVE_FLOOR = (20, 15, 25)       # Основной цвет пола (темно-фиолетовый)
C_STONE_DARK = (15, 10, 20)       # Тень камней
C_STONE_LIGHT = (35, 30, 45)      # Светлые грани камней
C_DIRT = (10, 5, 10)              # Грязь/Трещины
C_GLOW_HINT = (40, 30, 60)        # Еле заметное свечение магической руды

def generate_cave_background():
    """
    Генерирует поверхность пещеры один раз и возвращает Surface.
    Размер делается чуть больше экрана, чтобы при тряске не было черных краев.
    """
    w = WIDTH + 40
    h = HEIGHT + 40
    surface = pygame.Surface((w, h))
    surface.fill(C_CAVE_FLOOR)
    
    # 1. ТЕКСТУРА ЗЕМЛИ (Шум)
    # Рисуем много маленьких точек грязи
    for _ in range(5000):
        x = random.randint(0, w)
        y = random.randint(0, h)
        color = C_DIRT
        pygame.draw.circle(surface, color, (x, y), 1)

    # 2. КАМНИ (Плоские, чтобы дать ощущение пола)
    for _ in range(300):
        x = random.randint(0, w)
        y = random.randint(0, h)
        w_rock = random.randint(10, 40)
        h_rock = random.randint(5, 20) # Более сплюснутые по Y
        
        # Тень камня
        rect_shadow = pygame.Rect(x - w_rock//2 + 2, y - h_rock//2 + 2, w_rock, h_rock)
        pygame.draw.ellipse(surface, C_STONE_DARK, rect_shadow)
        
        # Сам камень
        rect_rock = pygame.Rect(x - w_rock//2, y - h_rock//2, w_rock, h_rock)
        pygame.draw.ellipse(surface, C_STONE_LIGHT, rect_rock)

    # 3. ТРЕЩИНЫ (Линии Безье или ломаные)
    for _ in range(10):
        start_x = random.randint(0, w)
        start_y = random.randint(0, h)
        points = [(start_x, start_y)]
        curr_x, curr_y = start_x, start_y
        
        # Генерируем ломаную линию
        steps = random.randint(5, 15)
        for _ in range(steps):
            angle = random.uniform(0, 6.28)
            length = random.randint(10, 50)
            curr_x += math.cos(angle) * length
            curr_y += math.sin(angle) * length
            points.append((curr_x, curr_y))
            
        if len(points) > 1:
            pygame.draw.lines(surface, C_DIRT, False, points, 3)

    # 4. ЦЕНТРАЛЬНАЯ ЗОНА (Где будет портал)
    # Рисуем еле заметный выжженный круг или руны в центре
    center = (w // 2, h // 2)
    for i in range(3):
        r = 150 + i * 40
        pygame.draw.circle(surface, C_DIRT, center, r, 2)
    
    # 5. ВИНЬЕТКА (Затемнение по краям)
    # Создаем поверхность с per-pixel alpha
    darkness = pygame.Surface((w, h), pygame.SRCALPHA)
    # Заливаем полупрозрачным черным
    darkness.fill((0, 0, 0, 180)) 
    
    # "Вырезаем" прозрачный круг в центре (светлое пятно)
    # Используем режим наложения BLEND_RGBA_SUB (вычитание альфы) или просто рисуем градиент
    # Простой способ: нарисовать много кругов с уменьшающейся прозрачностью от центра
    max_radius = int((w**2 + h**2)**0.5 / 2) + 100
    for r in range(max_radius, 0, -20):
        alpha = int(255 * (r / max_radius)) # Чем больше радиус, тем темнее (больше альфа)
        # Но нам нужно наоборот: в центре прозрачно (alpha=0), по краям темно
        # Поэтому рисуем круги от большого к малому, В ЦЕНТРЕ "прогрызая" тьму?
        # Нет, проще нарисовать "свет" поверх тьмы с особым флагом, но в pygame это сложно.
        pass
    
    # АЛЬТЕРНАТИВНЫЙ СПОСОБ ВИНЬЕТКИ (через smoothscale - быстро и красиво)
    # Создаем маленькую картинку градиента
    grad_size = 256
    gradient = pygame.Surface((grad_size, grad_size), pygame.SRCALPHA)
    for y in range(grad_size):
        for x in range(grad_size):
            # Расстояние от центра (0..1)
            dist = math.sqrt((x - grad_size/2)**2 + (y - grad_size/2)**2) / (grad_size/1.4)
            dist = min(1.0, dist)
            # В центре 0 (прозрачно), с краю 255 (черный)
            alpha = int(255 * (dist ** 2)) # dist^2 делает переход более резким к краям
            gradient.set_at((x, y), (0, 0, 0, alpha))
            
    # Растягиваем градиент на весь экран
    vignette = pygame.transform.smoothscale(gradient, (w, h))
    surface.blit(vignette, (0, 0))

    return surface