import pygame
import math
import random
from .core import draw_organic_polygon, apply_sketchy_style

# --- ПАЛИТРА ---
C_BODY = (40, 0, 60)
C_OUTLINE = (35, 0, 50) 

C_MAW_VOID = (5, 0, 10) 
C_TEETH = (180, 170, 160)

C_EYE_SCLERA = (40, 10, 50) 
C_EYE_IRIS = (255, 180, 0)  
C_EYE_PUPIL = (0, 0, 0)     
C_EYE_GLOW = (255, 100, 0)  

C_PUPIL = C_EYE_PUPIL 

def draw_eldritch_horror(surface, center, body_parts, tentacles, anim_offset, head_dir, pupil_dir):
    # 1. Щупальца (Гладкие)
    for points in tentacles:
        _draw_tentacle_strip(surface, points, 14, C_BODY, C_OUTLINE)
        
    # 2. Связки
    for i in range(1, len(body_parts)):
        part = body_parts[i]
        parent_idx = part.get('parent_idx', 0) 
        parent = body_parts[parent_idx]
        p_start = center + parent['offset']
        p_end = center + part['offset']
        thickness = int(part['radius'] * 1.2)
        pygame.draw.line(surface, C_BODY, p_start, p_end, thickness)

    look_angle = math.atan2(head_dir.y, head_dir.x)
    
    # 3. Придаточные сегменты
    for i in range(len(body_parts)-1, 0, -1):
        part = body_parts[i]
        float_offset = pygame.math.Vector2(math.sin(pygame.time.get_ticks()*0.002 + i)*0.5, 0)
        pos = center + part['offset'] + float_offset
        _draw_flesh_blob(surface, pos, part, look_angle, head_dir, pupil_dir)

    # 4. ГОЛОВА
    head = body_parts[0]
    pulse = math.sin(pygame.time.get_ticks() * 0.005 + head['pulse_phase']) * 0.5
    r = head['radius'] + pulse
    
    poly_points = _generate_noisy_polygon(center, r, 16, head['seed'], intensity=3.0)
    draw_organic_polygon(surface, C_BODY, poly_points, C_OUTLINE)
    
    # ПАСТЬ (Ниже и дальше)
    maw_offset = head_dir * (r * 0.5) + pygame.math.Vector2(0, r * 0.6) 
    maw_pos = center + maw_offset
    maw_size = r * 0.55
    
    _draw_poly_crescent_maw(surface, maw_pos, maw_size, head_dir)
    
    # ГЛАЗА
    eye_spacing = r * 0.9 
    eye_lift = pygame.math.Vector2(-head_dir.y, head_dir.x) * eye_spacing
    
    forehead_pos = center + head_dir * (r * 0.1) + pygame.math.Vector2(0, -r * 0.65)
    
    eye_pos_l = forehead_pos - eye_lift * 0.5
    eye_pos_r = forehead_pos + eye_lift * 0.5
    
    _draw_old_god_eye(surface, eye_pos_l, 10, head_dir, pupil_dir) 
    _draw_old_god_eye(surface, eye_pos_r, 10, head_dir, pupil_dir)


def _draw_flesh_blob(surface, pos, part, look_angle, head_dir, pupil_dir):
    pulse = math.sin(pygame.time.get_ticks() * 0.005 + part['pulse_phase']) * 0.5
    r = part['radius'] + pulse
    
    poly_points = _generate_noisy_polygon(pos, r, 11, part['seed'], intensity=2.5)
    draw_organic_polygon(surface, C_BODY, poly_points, C_OUTLINE)
    
    for eye in part['eyes']:
        eye_ang = look_angle + eye['angle']
        dist = min(eye['dist'], r * 0.6) 
        eye_offset = pygame.math.Vector2(math.cos(eye_ang), math.sin(eye_ang)) * dist
        safe_size = min(eye['size'], r * 0.4)
        
        _draw_old_god_eye(surface, pos + eye_offset, safe_size, head_dir, pupil_dir)


def _generate_noisy_polygon(center, radius, num_points, seed_offset, intensity=3.0):
    points = []
    for i in range(num_points):
        angle = (i / num_points) * math.pi * 2
        noise1 = math.sin(pygame.time.get_ticks() * 0.004 + i * 2 + seed_offset) * intensity
        noise2 = math.cos(i * 3.5 + seed_offset) * (intensity * 0.8)
        r = radius + noise1 + noise2
        px = center.x + math.cos(angle) * r
        py = center.y + math.sin(angle) * r
        points.append((px, py))
    return points

def _draw_tentacle_strip(surface, points, width_start, color, outline):
    if len(points) < 2: return
    left, right = [], []
    num = len(points)
    for i in range(num):
        p = points[i]
        if i < num - 1: tangent = points[i+1] - p
        else: tangent = p - points[i-1]
        if tangent.length() == 0: continue
        tangent = tangent.normalize()
        normal = pygame.math.Vector2(-tangent.y, tangent.x)
        t = i / num
        w = width_start * (1 - t**1.2)
        w = max(1, w)
        left.append(p + normal * w * 0.5)
        right.append(p - normal * w * 0.5)
    poly = left + right[::-1]
    pygame.draw.polygon(surface, outline, poly) 
    pygame.draw.polygon(surface, color, poly)

def _draw_old_god_eye(surface, center, size, head_dir, pupil_dir):
    """Глаз."""
    pygame.draw.circle(surface, (30, 0, 40), (int(center.x), int(center.y)), int(size + 3))
    pygame.draw.circle(surface, C_EYE_SCLERA, (int(center.x), int(center.y)), int(size))
    
    offset = pupil_dir * (size * 0.3) 
    iris_pos = center + offset
    pygame.draw.circle(surface, C_EYE_IRIS, (int(iris_pos.x), int(iris_pos.y)), int(size * 0.7))
    pygame.draw.circle(surface, C_EYE_GLOW, (int(iris_pos.x), int(iris_pos.y)), int(size * 0.4))
    
    pupil_pos = iris_pos + pupil_dir * (size * 0.1)
    p_w = size * 0.25
    p_h = size * 0.85
    pupil_rect = pygame.Rect(0, 0, p_w, p_h)
    pupil_rect.center = (pupil_pos.x, pupil_pos.y)
    pygame.draw.ellipse(surface, C_EYE_PUPIL, pupil_rect)
    
    # Бровь (Дуга над глазом)
    right_vec = pygame.math.Vector2(-head_dir.y, head_dir.x) * (size * 1.4)
    top_center = center + pygame.math.Vector2(0, -size * 1.4) # Выше
    
    b_left = top_center - right_vec * 0.8 + pygame.math.Vector2(0, size*0.3)
    b_right = top_center + right_vec * 0.8 + pygame.math.Vector2(0, size*0.3)
    b_mid = top_center 
    
    pygame.draw.lines(surface, C_OUTLINE, False, [b_left, b_mid, b_right], 2)

def _draw_poly_crescent_maw(surface, center, radius, look_dir):
    """Полумесяц."""
    points = []
    steps = 10
    
    for i in range(steps + 1):
        t = i / steps 
        angle_deg = -100 + t * 200 
        v = look_dir.rotate(angle_deg)
        p = center + v * radius
        points.append(p)
        
    for i in range(steps, -1, -1):
        t = i / steps
        angle_deg = -100 + t * 200
        v = look_dir.rotate(angle_deg)
        inner_r = radius * 0.7
        offset_c = center + look_dir * (radius * 0.4)
        p = offset_c + v * inner_r
        points.append(p)
        
    pygame.draw.polygon(surface, C_MAW_VOID, points)
    
    for i in range(0, len(points), 2):
        p_base = points[i]
        to_c = (center + look_dir * (radius*0.2) - pygame.math.Vector2(p_base)).normalize()
        tooth_len = random.uniform(3, 6)
        p_tip = pygame.math.Vector2(p_base) + to_c * tooth_len
        
        perp = pygame.math.Vector2(-to_c.y, to_c.x) * 1.5
        t1 = p_base + perp
        t2 = p_base - perp
        
        pygame.draw.polygon(surface, C_TEETH, [t1, t2, p_tip])