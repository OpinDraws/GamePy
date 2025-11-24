import pygame
import math
import random

def draw_slash_flurry(surface, center, aim_angle, progress, radius=80):
    """
    Рисует эффект множественных разрезов (Anime/Vergil style).
    progress: от 0.0 до 1.0 (время жизни эффекта)
    """
    # Преобразуем угол в радианы
    rad = math.radians(aim_angle)
    # Вектор направления
    direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
    
    # Центр области удара (смещен вперед от игрока)
    impact_center = pygame.math.Vector2(center) + direction * (radius * 0.6)
    
    # Генератор псевдослучайных чисел на основе прогресса, 
    # чтобы кадры были "дерганными", но стабильными внутри фрейма
    seed = int(progress * 20) 
    rng = random.Random(seed)
    
    # Цвет: от ярко-белого к кроваво-красному и исчезновение
    if progress < 0.2:
        color_core = (255, 255, 255)
        color_glow = (255, 100, 100)
    elif progress < 0.7:
        color_core = (255, 200, 200)
        color_glow = (200, 0, 0)
    else:
        color_core = (100, 0, 0)
        color_glow = (50, 0, 0)
        
    alpha = int(255 * (1 - progress))
    
    # Рисуем "Сферу ударов" - множество линий
    num_slashes = 8
    for i in range(num_slashes):
        # Случайный угол разреза
        slash_angle = rng.uniform(0, math.pi)
        slash_dir = pygame.math.Vector2(math.cos(slash_angle), math.sin(slash_angle))
        
        # Случайное смещение от центра удара
        offset = pygame.math.Vector2(rng.uniform(-20, 20), rng.uniform(-20, 20))
        slash_center = impact_center + offset
        
        # Длина линии
        length = rng.uniform(radius, radius * 1.5)
        p1 = slash_center - slash_dir * (length / 2)
        p2 = slash_center + slash_dir * (length / 2)
        
        # Толщина уменьшается со временем
        width = max(1, int(4 * (1 - progress)))
        
        # Рисуем свечение
        if width > 1:
            pygame.draw.line(surface, (*color_glow, alpha), p1, p2, width + 4)
        # Рисуем ядро
        pygame.draw.line(surface, (*color_core, alpha), p1, p2, width)

    # Рисуем внешний круг ударной волны (искаженный)
    points = []
    for i in range(16):
        angle = (i / 16) * math.pi * 2
        r = radius * (0.5 + progress * 0.5) + rng.uniform(-5, 5)
        px = impact_center.x + math.cos(angle) * r
        py = impact_center.y + math.sin(angle) * r
        points.append((px, py))
        
    if len(points) > 2:
        pygame.draw.lines(surface, (*color_glow, alpha), True, points, 2)