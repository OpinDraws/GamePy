import pygame
import math
import random

def solve_ik_2joint(start, target, len1, len2, bend_right=True):
    """Решает задачу IK для двух сегментов."""
    start_vec = pygame.math.Vector2(start)
    target_vec = pygame.math.Vector2(target)
    diff = target_vec - start_vec
    dist = diff.length()
    full_len = len1 + len2
    
    if dist >= full_len:
        direction = diff.normalize()
        return start_vec + direction * len1, start_vec + direction * full_len
    
    try:
        cos_angle = (len1**2 + dist**2 - len2**2) / (2 * len1 * dist)
        angle_a = math.acos(max(-1, min(1, cos_angle)))
    except ValueError:
        angle_a = 0

    base_angle = math.atan2(diff.y, diff.x)
    
    if bend_right: joint_angle = base_angle + angle_a
    else: joint_angle = base_angle - angle_a
        
    joint_pos = start_vec + pygame.math.Vector2(math.cos(joint_angle), math.sin(joint_angle)) * len1
    
    return joint_pos, target_vec

def get_bezier_points(start, end, control, segments=10):
    """
    Генерирует точки квадратичной кривой Безье.
    """
    points = []
    for i in range(segments + 1):
        t = i / segments
        # Формула: (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
        p = (1-t)**2 * start + 2 * (1-t) * t * control + t**2 * end
        points.append(p)
    return points

def apply_sketchy_style(points, intensity=1.0):
    return [(p[0] + random.uniform(-intensity, intensity), 
             p[1] + random.uniform(-intensity, intensity)) for p in points]

def draw_organic_polygon(surface, color, points, outline_color=None):
    if len(points) < 3: return
    pygame.draw.polygon(surface, color, points)
    if not outline_color:
        outline_color = (max(0, color[0]-30), max(0, color[1]-30), max(0, color[2]-30))
    jit_points = apply_sketchy_style(points, 0.6)
    pygame.draw.lines(surface, outline_color, True, jit_points, 1)

def draw_bone_segment(surface, start, end, color, width_start, width_end):
    vec = end - start
    if vec.length() < 1: return
    perp = pygame.math.Vector2(-vec.y, vec.x).normalize()
    p1 = start + perp * (width_start / 2)
    p2 = end + perp * (width_end / 2)
    p3 = end - perp * (width_end / 2)
    p4 = start - perp * (width_start / 2)
    pygame.draw.polygon(surface, color, [p1, p2, p3, p4])
    pygame.draw.circle(surface, color, (int(start.x), int(start.y)), width_start // 2)
    pygame.draw.circle(surface, color, (int(end.x), int(end.y)), width_end // 2)

def draw_alpha_polygon(surface, color, points):
    """Рисует полигон с поддержкой альфа-канала (прозрачности)."""
    if len(points) < 3: return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w, h = int(max_x - min_x), int(max_y - min_y)
    # Проверка на вырожденный полигон
    if w <= 0 or h <= 0: return
    
    shape_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
    pygame.draw.polygon(shape_surf, color, local_points)
    surface.blit(shape_surf, (min_x, min_y))

def draw_alpha_circle(surface, color, center, radius):
    """Рисует круг с поддержкой альфа-канала."""
    radius = int(radius)
    if radius <= 0: return
    target_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)