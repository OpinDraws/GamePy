import pygame
import math
import random
from .core import draw_organic_polygon, apply_sketchy_style, get_bezier_cubic_point, get_bezier_cubic_derivative
from core.config import COLOR_PM_BODY, COLOR_PM_BODY_DARK, COLOR_PM_EYE, COLOR_PM_PUPIL

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



# rendering/monsters.py

# ... (импорты)

# 1. Обновляем сигнатуру главной функции (добавляем front_tentacle_spread)
def draw_procedural_monster_v2(surface, pos, anim_time, body_radius, vertex_offsets, angle_left, angle_right, front_pos, scale=1.0, tentacle_spread=1.0, tentacle_extension=0.0, front_tentacle_spread=1.0, strike_tentacle_data=None):
    cx, cy = pos
    
    levitation = math.sin(anim_time) * (5 * scale)
    draw_cy = cy + levitation - (20 * scale)
    
    tentacle_y = draw_cy + body_radius * 0.5
    
    # --- НОВОЕ: ОТРИСОВКА БОЕВОГО ЩУПАЛЬЦА (Слой сзади - рисуем первым) ---
    if strike_tentacle_data:
        # Данные должны содержать p2 и p3 (середину и кончик)
        s_p2 = strike_tentacle_data.get('p2')
        s_p3 = strike_tentacle_data.get('p3')
        if s_p2 and s_p3:
            # Рисуем большое щупальце (scale * 2.5)
            # p0 (база) всегда в центре тела
            _draw_front_tentacle(
                surface, (cx, tentacle_y), 0, anim_time, cx, draw_cy, 
                scale * 1.5, # Размер в 2.5 раза больше
                override_p2=s_p2, 
                override_p3=s_p3
            )
    # ----------------------------------------------------------------------

    lift_left = (math.sin(angle_left) + 1) / 2
    lift_right = (math.sin(angle_right) + 1) / 2
    
    _draw_ribbon_tentacle(surface, (cx - 30 * scale * tentacle_spread, tentacle_y), -1, lift_left, anim_time, cx, draw_cy, scale, tentacle_spread, tentacle_extension)
    _draw_ribbon_tentacle(surface, (cx + 30 * scale * tentacle_spread, tentacle_y), 1, lift_right, anim_time, cx, draw_cy, scale, tentacle_spread, tentacle_extension)

    _draw_pm_body(surface, cx, draw_cy, anim_time, body_radius, vertex_offsets, scale)
    _draw_pm_eye(surface, cx, draw_cy, scale)
    
    _draw_front_tentacle(surface, (cx, tentacle_y + 33 * scale), front_pos, anim_time, cx, draw_cy, scale, spread_factor=front_tentacle_spread)



# --- Вспомогательные функции рендера ---

def _draw_ribbon_polygon(surface, p0, p1, p2, p3, base_thickness, round_start=False):
    full_poly = []
    
    deriv0 = get_bezier_cubic_derivative(0, p0, p1, p2, p3)
    angle_start = math.atan2(deriv0[1], deriv0[0])
    
    steps = 20
    
    if round_start:
        right_angle = angle_start + math.pi / 2
        cap_steps = 8
        for i in range(cap_steps + 1):
            t_cap = i / cap_steps
            current_angle = right_angle + math.pi * t_cap 
            cx = p0[0] + base_thickness * math.cos(current_angle)
            cy = p0[1] + base_thickness * math.sin(current_angle)
            full_poly.append((cx, cy))

    left_side = []
    right_side = []

    for i in range(steps + 1):
        t = i / steps
        center = get_bezier_cubic_point(t, p0, p1, p2, p3)
        deriv = get_bezier_cubic_derivative(t, p0, p1, p2, p3)
        length = math.hypot(deriv[0], deriv[1])
        if length == 0: length = 1
        
        nx, ny = deriv[1] / length, -deriv[0] / length
        thickness = base_thickness * (1 - t**2)
        
        left_side.append((center[0] + nx * thickness, center[1] + ny * thickness))
        right_side.append((center[0] - nx * thickness, center[1] - ny * thickness))

    full_poly.extend(left_side)
    full_poly.extend(right_side[::-1])

    pygame.draw.polygon(surface, COLOR_PM_BODY, full_poly)
    pygame.draw.polygon(surface, COLOR_PM_BODY_DARK, full_poly, 3)

def _draw_ribbon_tentacle(surface, start_pos, side_factor, lift_offset, time, base_x, base_y, scale, spread_factor=1.0, extension_offset=0.0):
    p0 = start_pos
    
    sway_amp = (5 * scale) * spread_factor
    sway_x = math.sin(time + abs(side_factor)) * sway_amp
    
    # X: Spread (Мультипликативное сжатие ширины)
    base_spread = 95 * scale
    spread = base_spread * side_factor * spread_factor
    
    lift_amplitude = 35 * scale
    vertical_shift = lift_offset * lift_amplitude 

    # Y: Extension (Аддитивное удлинение/укорачивание)
    # Мы распределяем offset: чем ниже точка, тем сильнее она сдвигается.
    # Это сохраняет привязку к телу (p0) и двигает кончик (p3).
    
    # Точка 1: 30% от смещения
    y1 = base_y + (140 * scale) + (extension_offset * 0.3) - vertical_shift * 0.3
    
    # Точка 2: 70% от смещения
    y2 = base_y + (20 * scale) + (extension_offset * 0.7) - vertical_shift
    
    # Точка 3 (Кончик): 100% от смещения
    y3 = base_y + (45 * scale) + extension_offset - vertical_shift

    p1 = (base_x + spread * 0.8, y1)
    p2 = (base_x + spread * 1.5 + sway_x, y2)
    p3 = (base_x + spread * 1.8 + sway_x, y3)

    # Толщина
    thickness = 29 * scale
    # Если сильно сжимаем, чуть уменьшаем толщину, чтобы не было "каши"
    if extension_offset < -50:
        thickness *= 0.8

    _draw_ribbon_polygon(surface, p0, p1, p2, p3, base_thickness=thickness, round_start=False)


#140 20 45
def _draw_front_tentacle(surface, start_pos, side_factor, time, base_x, base_y, scale, spread_factor=1.0, override_p2=None, override_p3=None):
    p0 = start_pos
    
    # Если переданы конкретные координаты (для атаки), используем их
    if override_p2 is not None and override_p3 is not None:
        p1 = (p0[0], p0[1] + 50 * scale) # Первый сустав немного вниз от тела
        p2 = override_p2
        p3 = override_p3
        # Более толстое основание для огромного щупальца
        thickness = 40 * scale 
    else:
        # Стандартная процедурная анимация (покачивание)
        sway = math.sin(time * 0.6 + abs(side_factor)) * (5 * scale) * spread_factor
        spread = 60 * side_factor * scale * spread_factor
        
        p1 = (base_x + spread * 0.5, base_y + 100 * scale)
        p2 = (base_x + spread * 1.5 + sway, base_y + 20 * scale)
        p3 = (base_x + spread * 2.0 + sway, base_y + 50 * scale)
        thickness = 32 * scale

    _draw_ribbon_polygon(surface, p0, p1, p2, p3, base_thickness=thickness, round_start=True)

#100 -29 -60
def _draw_pm_body(surface, cx, cy, time, radius, vertex_offsets, scale):
    n = len(vertex_offsets)
    # Амплитуда дыхания тоже масштабируется
    r_anim = radius + math.sin(time * 2) * (3 * scale)
    rot = math.sin(time * 0.5) * 0.05
    
    vertices = []
    for i in range(n):
        angle = (2 * math.pi * i / n) - (math.pi / 2) + rot
        r = r_anim + vertex_offsets[i]
        vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        
    smooth_poly = []
    for i in range(n):
        curr, next_v = vertices[i], vertices[(i+1)%n]
        for j in range(4):
            t = j / 4
            px = curr[0] * (1-t) + next_v[0] * t
            py = curr[1] * (1-t) + next_v[1] * t
            smooth_poly.append((px, py))
            
    pygame.draw.polygon(surface, COLOR_PM_BODY, smooth_poly)
    pygame.draw.polygon(surface, COLOR_PM_BODY_DARK, smooth_poly, 4)

def _draw_pm_eye(surface, cx, cy, scale):
    lid_h_radius = 60 * scale
    lid_w_radius = 35 * scale
    shape_power = 1.5 

    lid_points = []
    steps = 30
    for i in range(steps):
        theta = 2 * math.pi * i / steps
        c = math.cos(theta)
        s = math.sin(theta)
        sign_c = 1 if c >= 0 else -1
        sign_s = 1 if s >= 0 else -1
        x = cx + lid_w_radius * sign_c * (abs(c) ** shape_power)
        y = cy + lid_h_radius * sign_s * (abs(s) ** shape_power)
        lid_points.append((x, y))

    pygame.draw.polygon(surface, COLOR_PM_BODY, lid_points)
    pygame.draw.polygon(surface, COLOR_PM_BODY_DARK, lid_points, max(1, int(8 * scale)))

    eye_points = []
    rx = 25 * scale
    ry = 38 * scale
    for i in range(steps):
        theta = 2 * math.pi * i / steps
        x = cx + rx * math.cos(theta)
        y = cy + ry * math.sin(theta)
        eye_points.append((x, y))
        
    pygame.draw.polygon(surface, COLOR_PM_EYE, eye_points)
    pygame.draw.polygon(surface, COLOR_PM_BODY_DARK, eye_points, max(1, int(3 * scale)))
    
    # Зрачок
    pupil_w = 6 * scale
    pupil_h = 24 * scale
    pygame.draw.ellipse(surface, COLOR_PM_PUPIL, (cx - pupil_w/2, cy - 12 * scale, pupil_w, pupil_h))