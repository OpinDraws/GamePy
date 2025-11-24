import pygame
import math
import random
from .core import draw_alpha_circle

# Цвета портала
C_PORTAL_CORE = (255, 255, 220)
C_PORTAL_INNER = (255, 215, 50)
C_PORTAL_OUTER = (218, 165, 32)
C_PORTAL_GLOW = (255, 120, 50)

def draw_divine_portal(surface, center, progress, time_ticks):
    """
    Рисует ОГРОМНЫЙ божественный портал.
    """
    if progress <= 0: return

    cx, cy = center
    # УВЕЛИЧИЛИ РАЗМЕР: Базовый радиус был 120, стал 220
    base_radius = 220 * progress 
    
    # 1. Основное свечение (Glow) - пульсирует
    pulse = math.sin(time_ticks * 0.1) * 0.05 + 0.95
    glow_radius = base_radius * 1.6 * pulse
    
    # Внешняя аура
    draw_alpha_circle(surface, (*C_PORTAL_GLOW[:3], 40), center, glow_radius)
    draw_alpha_circle(surface, (*C_PORTAL_OUTER[:3], 60), center, base_radius * 1.3)

    # 2. Вращающиеся магические круги
    num_rings = 4
    for i in range(num_rings):
        # Кольца разного размера
        ring_radius = base_radius * (0.9 - i * 0.15)
        # Вращение в разные стороны
        direction = -1 if i % 2 == 0 else 1
        angle_offset = time_ticks * (0.02 * (i + 1) * direction)
        
        # Рисуем кольцо из сегментов
        points = []
        segments = 12 + i * 4
        for j in range(segments + 1): # +1 чтобы замкнуть
            angle = angle_offset + (j / segments) * math.pi * 2
            # Сплющиваем Y (умножаем на 0.3), чтобы портал выглядел как диск в небе (перспектива)
            px = cx + math.cos(angle) * ring_radius
            py = cy + math.sin(angle) * ring_radius * 0.3 
            points.append((px, py))
            
        if len(points) > 2:
            # Золотые линии
            pygame.draw.lines(surface, C_PORTAL_INNER, False, points, 3)

    # 3. Ядро портала (Яркий эллипс в центре)
    # Оно должно быть очень ярким, откуда выходит босс
    rect_core = pygame.Rect(0, 0, base_radius * 1.5, base_radius * 0.5)
    rect_core.center = center
    pygame.draw.ellipse(surface, (*C_PORTAL_CORE, 255), rect_core)
    
    # Белый центр
    rect_center = pygame.Rect(0, 0, base_radius * 0.8, base_radius * 0.3)
    rect_center.center = center
    pygame.draw.ellipse(surface, (255, 255, 255, 255), rect_center)

    # 4. Лучи света (God Rays) вниз
    if progress > 0.3:
        num_rays = 10
        for i in range(num_rays):
            angle_phase = i * (math.pi * 2 / num_rays)
            ray_w = base_radius * (0.5 + 0.5 * math.sin(time_ticks * 0.05 + angle_phase))
            
            # Лучи идут вниз конусом
            start_pos = (cx + math.cos(angle_phase)*base_radius*0.2, cy)
            end_pos = (cx + math.cos(angle_phase)*base_radius*0.8, cy + base_radius * 3)
            
            width = int(8 * progress)
            alpha_ray = int(50 * (1 - abs(math.sin(time_ticks * 0.02 + i))))
            
            # Рисуем луч (нужна поверхность с прозрачностью для линии, если хотим красиво)
            # Упрощенно рисуем линию
            color = (*C_PORTAL_CORE[:3], alpha_ray)
            # Pygame draw line не поддерживает альфу напрямую, но draw_alpha_polygon да
            # Обойдемся простым вариантом для скорости или используем существующий polygon
            pass