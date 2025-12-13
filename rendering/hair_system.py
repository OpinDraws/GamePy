import pygame
import math
import random
from .core import draw_alpha_polygon, draw_alpha_circle

# --- ПАЛИТРА ---
C_BLONDE_BASE = (255, 235, 160, 255)       
C_BLONDE_SHADOW = (210, 180, 90, 255)      # Цвет линий текстуры
C_BLONDE_DEEP_SHADOW = (180, 150, 70, 255) 
C_BLONDE_HIGHLIGHT = (255, 250, 200, 200)  
C_INK = (15, 10, 20)                       

# ==========================================
# --- МАТЕМАТИКА ---
# ==========================================

def get_cubic_bezier_normal(t, p0, p1, p2, p3):
    u = 1 - t
    tangent = 3*(u**2)*(p1-p0) + 6*u*t*(p2-p1) + 3*(t**2)*(p3-p2)
    if tangent.length_squared() < 0.001:
        return pygame.math.Vector2(0, 1)
    tangent = tangent.normalize()
    return pygame.math.Vector2(-tangent.y, tangent.x)

def apply_wind_cubic(p_end, p_ctrl1, p_ctrl2, time_ticks, intensity=1.0, phase=0.0):
    sway = math.sin(time_ticks * 0.05 + phase) * 2.5 * intensity
    ripple = math.cos(time_ticks * 0.08 + phase) * 1.5 * intensity
    
    new_end = p_end + pygame.math.Vector2(sway + ripple, sway * 0.2)
    new_c2 = p_ctrl2 + pygame.math.Vector2(sway * 0.5, 0)
    new_c1 = p_ctrl1 + pygame.math.Vector2(sway * 0.1, 0)
    
    return new_end, new_c1, new_c2

def draw_outline(surface, points, width=1, closed=True):
    if len(points) < 2: return
    points_tuple = [(p.x, p.y) if isinstance(p, pygame.math.Vector2) else p for p in points]
    pygame.draw.lines(surface, C_INK, closed, points_tuple, width)

# ==========================================
# --- РЕНДЕР (ТЕКСТУРНЫЕ ЛИНИИ) ---
# ==========================================

def draw_hair_strand_cubic(surface, p0, p1, p2, p3, width_root, width_tip, color_base, color_line, segments=15, blend_root=False):
    p0, p1, p2, p3 = map(pygame.math.Vector2, [p0, p1, p2, p3])
    
    points_left = []
    points_right = []
    tex_offsets = [-0.3, 0.3] 
    tex_lines = [ [] for _ in tex_offsets ]
    
    for i in range(segments + 1):
        t = i / segments
        u = 1 - t
        pos = (u**3)*p0 + 3*(u**2)*t*p1 + 3*u*(t**2)*p2 + (t**3)*p3
        normal = get_cubic_bezier_normal(t, p0, p1, p2, p3)
        
        t_width = t * t 
        current_width = width_root * (1 - t_width) + width_tip * t_width
        
        points_left.append(pos + normal * (current_width / 2))
        points_right.append(pos - normal * (current_width / 2))
        
        for idx, offset_factor in enumerate(tex_offsets):
            offset_pos = pos + normal * (current_width * 0.5 * offset_factor)
            tex_lines[idx].append((offset_pos.x, offset_pos.y))
        
    full_poly = points_left + points_right[::-1]
    poly_tuples = [(p.x, p.y) for p in full_poly]
    
    if len(poly_tuples) < 3: return

    draw_alpha_polygon(surface, color_base, poly_tuples)
    
    for line_pts in tex_lines:
        if len(line_pts) > 1:
            pygame.draw.aalines(surface, color_line, False, line_pts)

    if blend_root:
        pts_l = [(p.x, p.y) for p in points_left]
        pts_r = [(p.x, p.y) for p in points_right]
        if len(pts_l) > 2: pygame.draw.lines(surface, C_INK, False, pts_l[1:], 1)
        if len(pts_r) > 2: pygame.draw.lines(surface, C_INK, False, pts_r[1:], 1)
    else:
        draw_outline(surface, full_poly, width=1, closed=True)

# ==========================================
# --- НАСТРОЙКА ФОРМЫ ---
# ==========================================

def define_archangel_hair_style(head_center, time_ticks):
    hc = pygame.math.Vector2(head_center) + (0, 10)
    
    strands = {
        'top_sides': [], 
        'bangs': []      
    }
    
    # --- 1. ЧЕЛКА ---
    # Левая
    root = hc + (-2, -12) 
    base_c1 = hc + (-6, -30) 
    base_c2 = hc + (-16, -10)
    base_end = hc + (-18, 2) 
    end, c1, c2 = apply_wind_cubic(base_end, base_c1, base_c2, time_ticks, intensity=0.15)
    
    strands['bangs'].append({
        'p0': root, 'p1': c1, 'p2': c2, 'p3': end,
        'w_root': 10, 'w_tip': 2, 
        'c_base': C_BLONDE_BASE, 'c_shadow': C_BLONDE_SHADOW 
    })
    
    # Правая
    root = hc + (2, -12)
    base_c1 = hc + (6, -30) 
    base_c2 = hc + (16, -10)
    base_end = hc + (18, 2)
    end, c1, c2 = apply_wind_cubic(base_end, base_c1, base_c2, time_ticks, intensity=0.15, phase=0.5)
    
    strands['bangs'].append({
        'p0': root, 'p1': c1, 'p2': c2, 'p3': end,
        'w_root': 10, 'w_tip': 2, 
        'c_base': C_BLONDE_BASE, 'c_shadow': C_BLONDE_SHADOW
    })
    
    # --- 2. БОКОВЫЕ ПРЯДИ ---
    # ЛЕВАЯ
    root = hc + (-12, -19) 
    base_c1 = hc + (-30, -5) 
    base_c2 = hc + (-5, 25) 
    base_end = hc + (-25, 15)
    end, c1, c2 = apply_wind_cubic(base_end, base_c1, base_c2, time_ticks, intensity=0.7, phase=0.2)
    strands['top_sides'].append({
        'p0': root, 'p1': c1, 'p2': c2, 'p3': end,
        'w_root': 15, 'w_tip': 4, 
        'c_base': C_BLONDE_BASE, 'c_shadow': C_BLONDE_SHADOW
    })
    
    # ПРАВАЯ
    root = hc + (12, -19) 
    base_c1 = hc + (30, -5) 
    base_c2 = hc + (5, 25) 
    base_end = hc + (25, 15) 
    end, c1, c2 = apply_wind_cubic(base_end, base_c1, base_c2, time_ticks, intensity=0.7, phase=0.7)
    strands['top_sides'].append({
        'p0': root, 'p1': c1, 'p2': c2, 'p3': end,
        'w_root': 15, 'w_tip': 4, 
        'c_base': C_BLONDE_BASE, 'c_shadow': C_BLONDE_SHADOW
    })

    return strands

# ==========================================
# --- ОТРИСОВКА (ИЗМЕНЕН ПОРЯДОК) ---
# ==========================================

def draw_hair_layer_back(surface, head_center, time_ticks):
    crescent_center = pygame.math.Vector2(head_center) + (0, 1)
    radius = 21 
    draw_alpha_circle(surface, C_BLONDE_BASE, crescent_center, radius)
    pygame.draw.circle(surface, C_INK, (int(crescent_center.x), int(crescent_center.y)), int(radius), 1)

def draw_hair_layer_front(surface, head_center, time_ticks):
    hair_data = define_archangel_hair_style(head_center, time_ticks)
    
    # --- ПОРЯДОК ИЗМЕНЕН ---
    
    # 1. Сначала ЧЕЛКА (Bangs) -> Будет ПОД боковыми
    for s in hair_data['bangs']:
        draw_hair_strand_cubic(
            surface, s['p0'], s['p1'], s['p2'], s['p3'], 
            s['w_root'], s['w_tip'], s['c_base'], s['c_shadow']
        )
        
    # 2. Затем БОКОВЫЕ (Sides) -> Будут ПОВЕРХ челки
    for s in hair_data['top_sides']:
        draw_hair_strand_cubic(
            surface, s['p0'], s['p1'], s['p2'], s['p3'], 
            s['w_root'], s['w_tip'], s['c_base'], s['c_shadow'],
            blend_root=True
        )

    # 3. Блик (всегда сверху)
    highlight_pos = pygame.math.Vector2(head_center) + (0, -12)
    for i in range(3):
        y_off = i * 2
        rect = pygame.Rect(highlight_pos.x - 10 + i, highlight_pos.y - 6 + y_off, 20 - i*2, 4)
        pygame.draw.arc(surface, C_BLONDE_HIGHLIGHT[:3], rect, 0.2, 2.9, 1)