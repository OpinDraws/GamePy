import pygame
import random
import math
# WIDTH и HEIGHT из конфига больше не используются для размера фона, 
# так как карта теперь больше экрана.

# --- ПАЛИТРА ПЕЩЕРЫ ---
C_CAVE_FLOOR = (20, 15, 25)       # Основной цвет пола (темно-фиолетовый)
C_STONE_DARK = (15, 10, 20)       # Тень камней
C_STONE_LIGHT = (35, 30, 45)      # Светлые грани камней
C_DIRT = (10, 5, 10)              # Грязь/Трещины
C_GLOW_HINT = (40, 30, 60)        # Еле заметное свечение магической руды

def generate_cave_background():
    """
    Генерирует текстуру фона для ВСЕЙ карты.
    Размеры карты: 50x90 тайлов (2000x3600 пикселей).
    Добавляем небольшой запас для тряски экрана.
    """
    map_width = 2000
    map_height = 3600 # (50 босс + 15 коридор + 25 старт) * 40
    
    w = map_width + 40
    h = map_height + 40
    
    surface = pygame.Surface((w, h))
    surface.fill(C_CAVE_FLOOR)
    
    # 1. ТЕКСТУРА ЗЕМЛИ (Шум)
    # Увеличили количество точек, так как карта стала больше
    for _ in range(15000):
        x = random.randint(0, w)
        y = random.randint(0, h)
        color = C_DIRT
        pygame.draw.circle(surface, color, (x, y), 1)

    # 2. КАМНИ
    # Тоже увеличили количество
    for _ in range(1000):
        x = random.randint(0, w)
        y = random.randint(0, h)
        w_rock = random.randint(10, 40)
        h_rock = random.randint(5, 20) 
        
        # Тень камня
        rect_shadow = pygame.Rect(x - w_rock//2 + 2, y - h_rock//2 + 2, w_rock, h_rock)
        pygame.draw.ellipse(surface, C_STONE_DARK, rect_shadow)
        
        # Сам камень
        rect_rock = pygame.Rect(x - w_rock//2, y - h_rock//2, w_rock, h_rock)
        pygame.draw.ellipse(surface, C_STONE_LIGHT, rect_rock)

    # 3. ТРЕЩИНЫ
    for _ in range(30):
        start_x = random.randint(0, w)
        start_y = random.randint(0, h)
        points = [(start_x, start_y)]
        curr_x, curr_y = start_x, start_y
        
        steps = random.randint(5, 15)
        for _ in range(steps):
            angle = random.uniform(0, 6.28)
            length = random.randint(10, 50)
            curr_x += math.cos(angle) * length
            curr_y += math.sin(angle) * length
            points.append((curr_x, curr_y))
            
        if len(points) > 1:
            pygame.draw.lines(surface, C_DIRT, False, points, 3)

    # 4. ЦЕНТРАЛЬНАЯ ЗОНА (КРУГ НА АРЕНЕ БОССА)
    # Комната босса находится в самом верху (Y=0...2000).
    # Она квадратная (2000x2000).
    # Идеальный центр комнаты: X=1000, Y=1000.
    center = (1000, 1000)
    
    # Рисуем декоративные круги
    for i in range(3):
        r = 250 + i * 60 # Радиус побольше для эпичности
        pygame.draw.circle(surface, C_DIRT, center, r, 4)
    
    # 5. ВИНЬЕТКА (Глобальная, на всю карту)
    # Создаем градиент
    grad_size = 512
    gradient = pygame.Surface((grad_size, grad_size), pygame.SRCALPHA)
    for y in range(grad_size):
        for x in range(grad_size):
            dist = math.sqrt((x - grad_size/2)**2 + (y - grad_size/2)**2) / (grad_size/1.42)
            dist = min(1.0, dist)
            alpha = int(200 * (dist ** 3)) # Чуть прозрачнее в центре
            gradient.set_at((x, y), (0, 0, 0, alpha))
            
    # Растягиваем виньетку на всю огромную карту
    vignette = pygame.transform.smoothscale(gradient, (w, h))
    surface.blit(vignette, (0, 0))

    return surface