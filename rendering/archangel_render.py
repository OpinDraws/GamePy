import pygame
import math
import random
from .core import (
    get_bezier_points, 
    solve_ik_2joint, 
    draw_bone_segment,
    draw_alpha_polygon,
    draw_alpha_circle
)
# !!! ИМПОРТ НОВЫХ ФУНКЦИЙ ТЕЛА И РУК ИЗ MONSTER_FLO.PY !!!
# Добавьте draw_detailed_hand в импорт
from .monster_flo import (
    draw_arm_upper_humanoid,
    draw_arm_lower_humanoid,
    draw_humanoid_head_minimal,
    draw_pear_chest,
    draw_joint,
    draw_archangel_torso,
    draw_detailed_hand,
    draw_detailed_hand_palm,
    draw_detailed_hand_fingers,
    draw_archangel_hood # <-- ДОБАВЬТЕ ЭТО
)
from .hair_system import draw_hair_layer_back, draw_hair_layer_front

# --- Цветовая палитра ---
C_WHITE_BASE = (240, 245, 255, 255)      
C_WHITE_SHADOW = (180, 190, 210, 150)    
C_WHITE_HIGHLIGHT = (255, 255, 255, 200) 

C_INK = (15, 10, 20) # Контур

C_WING_DEEP = (100, 120, 150, 255)       
C_WING_MID = (160, 180, 210, 255)        
C_WING_TIP = (230, 240, 255, 255)        

C_GOLD_DARK = (180, 140, 20, 255)        
C_GOLD_BRIGHT = (255, 215, 50, 255)      
C_GOLD_GLOW = (255, 230, 100, 100)       
C_GOLD_ORNAMENT = (210, 180, 50) 
C_GOLD_BELT = (230, 195, 60, 255) # Новый цвет для пояса

C_CYAN_DEEP = (0, 100, 150, 255)         
C_CYAN_BRIGHT = (50, 200, 255, 255)      
C_CYAN_GLOW = (100, 255, 255, 150)       
C_SPEAR_SHAFT = (60, 70, 80)             
C_SPEAR_HIGHLIGHT = (120, 130, 140)      
C_SPEAR_SHADOW = (40, 50, 60)            

C_SKIN = (250, 240, 235, 255)            
C_SKIN_SHADOW = (220, 200, 190, 150)     
C_SKIN_HIGHLIGHT = (255, 245, 240, 150) 

# *** ДОБАВЛЕНЫ КРАСНЫЕ ЦВЕТА ДЛЯ ФАЗЫ 2 ***
C_RED_BRIGHT = (255, 50, 50, 255)
C_RED_GLOW = (255, 100, 100, 150)
C_RED_DEEP = (150, 0, 0, 255) 
C_DASH_INDICATOR_FILL = (255, 215, 0, 50)   
C_DASH_INDICATOR_BORDER = (255, 255, 100)   

# Новые цвета для волос
C_BLONDE_BASE = (255, 235, 160, 255)   # Яркий золотистый блонд
C_BLONDE_SHADOW = (210, 180, 90, 255)  # Темно-золотой для объема и заднего плана
C_BLONDE_HIGHLIGHT = (255, 250, 200, 200) # Блики


# --- НОВЫЕ ЦВЕТА ДЛЯ ОДЕЖДЫ ---
C_CLOTH_BASE = (245, 250, 255, 255)      # Основной белый цвет ткани
C_CLOTH_SHADOW = (200, 210, 230, 255)    # Тень на ткани (голубовато-серая)
C_CLOTH_OUTLINE = (100, 110, 130)        # Цвет контура для ткани (не черный, а темно-серый)
C_GOLD_BELT_BASE = (210, 170, 40, 255)   # Основа золотого пояса/брони
C_GOLD_BELT_HIGHLIGHT = (255, 220, 80, 255) # Блик на золоте

# --- Хелперы ---

def rotate_point(point, angle_rad, center):
    s, c = math.sin(angle_rad), math.cos(angle_rad)
    temp_x = point[0] - center.x
    temp_y = point[1] - center.y
    new_x = temp_x * c - temp_y * s
    new_y = temp_x * s + temp_y * c
    return pygame.math.Vector2(new_x + center.x, new_y + center.y)

def draw_outline(surface, points, width=2, closed=True):
    if len(points) < 2: return
    # Убеждаемся, что точки это кортежи
    points_tuple = [(p.x, p.y) if isinstance(p, pygame.math.Vector2) else p for p in points]
    pygame.draw.lines(surface, C_INK, closed, points_tuple, width)

# --- Отрисовка знака Smite (КРЕСТ) ---
def draw_smite_sign(surface, center, progress, is_phase_two=False):
    sign_pos = center + (0, -100)
    FADE_IN_END = 0.1
    fade_in = min(1.0, progress / FADE_IN_END)
    FADE_OUT_START = 0.7 
    if progress > FADE_OUT_START:
        t = (progress - FADE_OUT_START) / (1.0 - FADE_OUT_START)
        fade_out = 1.0 - (t * t) 
    else:
        fade_out = 1.0
        
    base_alpha_mult = min(fade_in, fade_out) 
    pulse = 1.0
    if progress <= FADE_OUT_START:
        pulse = (math.sin(pygame.time.get_ticks() * 0.015) * 0.2 + 0.9)
        
    alpha = int(255 * base_alpha_mult * pulse) 
    if alpha <= 5: return

    use_red = is_phase_two and progress > 0.3
    
    current_color_bright = C_RED_BRIGHT
    current_color_glow = C_RED_GLOW

    if not use_red:
        current_color_bright = C_CYAN_BRIGHT
        current_color_glow = C_CYAN_GLOW

    glow_alpha = int(alpha * 0.5)
    
    draw_alpha_circle(surface, current_color_glow[:3] + (glow_alpha,), sign_pos, 20 * base_alpha_mult)
    bar_color = current_color_bright[:3] + (alpha,)
    
    w, h = 4, 24
    v_rect = [
        sign_pos + (-w/2, -h/2),
        sign_pos + (w/2, -h/2),
        sign_pos + (w/2, h/2),
        sign_pos + (-w/2, h/2)
    ]
    draw_alpha_polygon(surface, bar_color, [(p.x, p.y) for p in v_rect])
    
    w2, h2 = 16, 4
    h_rect = [
        sign_pos + (-w2/2, -h2/2),
        sign_pos + (w2/2, -h2/2),
        sign_pos + (w2/2, h2/2),
        sign_pos + (-w2/2, h2/2)
    ]
    draw_alpha_polygon(surface, bar_color, [(p.x, p.y) for p in h_rect])


def draw_spear_projectile(surface, center_pos, angle_deg, alpha=255):
    angle_rad = math.radians(angle_deg)
    spear_dir = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))
    tip_center = pygame.math.Vector2(center_pos) + spear_dir * 10
    
    base_alpha_mult = alpha / 255.0
    c_cyan_glow_a = C_CYAN_GLOW[:3] + (int(C_CYAN_GLOW[3] * base_alpha_mult * 0.5),)
    c_cyan_bright_a = C_CYAN_BRIGHT[:3] + (int(C_CYAN_BRIGHT[3] * base_alpha_mult),)
    c_cyan_deep_a = C_CYAN_DEEP[:3] + (int(C_CYAN_DEEP[3] * base_alpha_mult),)
    
    tip_perp = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 6 
    tip_poly = [
        (tip_center + spear_dir * 20).xy, 
        (tip_center - spear_dir * 5 - tip_perp).xy, 
        (tip_center - spear_dir * 2).xy, 
        (tip_center - spear_dir * 5 + tip_perp).xy  
    ]
    
    draw_alpha_circle(surface, c_cyan_glow_a, tip_center.xy, 15)
    draw_alpha_polygon(surface, c_cyan_bright_a, [tip_poly[0], tip_poly[1], tip_poly[3]])
    draw_alpha_polygon(surface, c_cyan_deep_a, [tip_poly[1], tip_poly[2], tip_poly[3]])
    
    shaft_start = tip_center - spear_dir * 2
    shaft_end = tip_center - spear_dir * 60
    
    num_segments = 5
    
    for i in range(num_segments):
        progress_start = i / num_segments
        progress_end = (i + 0.5) / num_segments
        p_start = shaft_start.lerp(shaft_end, progress_start)
        p_end = shaft_start.lerp(shaft_end, progress_end)
        perp_vec = pygame.math.Vector2(-spear_dir.y, spear_dir.x)
        time_offset = math.sin(pygame.time.get_ticks() * 0.015 + i * 2) * 1.5 * base_alpha_mult
        p1 = p_start + perp_vec * (2 + time_offset)
        p2 = p_end + perp_vec * (-2 - time_offset)
        line_color = c_cyan_bright_a
        pygame.draw.line(surface, line_color, p1.xy, p2.xy, 2)
    
    pygame.draw.line(surface, c_cyan_bright_a, shaft_start.xy, shaft_end.xy, 1)

# --- КИСТИ (Используются заглушки для совместимости с Vector2) ---

def draw_hand_fist(surface, pos, color, is_left_hand=True, angle_deg=0):
    radius = 8
    draw_alpha_circle(surface, color, pos.xy, radius)
    pygame.draw.circle(surface, C_INK, (int(pos.x), int(pos.y)), radius, 1)

def draw_hand_holding_spear(surface, hand_pos, spear_segment_start, spear_segment_end, is_left_hand=True, angle_deg=0):
    spear_vec = (spear_segment_end - spear_segment_start).normalize()
    perp_vec = pygame.math.Vector2(-spear_vec.y, spear_vec.x)
    
    finger_mass_start_local = hand_pos + spear_vec * -2 + perp_vec * 2
    finger_mass_end_local = hand_pos + spear_vec * 9 + perp_vec * 3
    pygame.draw.line(surface, C_SKIN, finger_mass_start_local.xy, finger_mass_end_local.xy, 7) 
    pygame.draw.line(surface, C_INK, finger_mass_start_local.xy, finger_mass_end_local.xy, 1)

def draw_arm_sleeve_only(surface, shoulder_pos, elbow_pos, hand_pos, bend_right=True, is_left_hand=True):
    # Теперь передаем C_SKIN вместо C_WHITE_BASE
    draw_arm_upper_humanoid(surface, shoulder_pos, elbow_pos, is_left_hand, C_SKIN, C_INK)
    # 0.5 - это фактор мускулистости, C_SKIN - цвет кожи
    draw_arm_lower_humanoid(surface, elbow_pos, hand_pos, is_left_hand, 0.5, C_SKIN, C_INK)


def calculate_ik_points(shoulder_pos, hand_pos, bend_right=True):
    len_upper = 24
    len_fore = 22
    # IK-функция ожидает КОРТЕЖИ (x, y) и возвращает КОРТЕЖИ
    elbow_pos_vec, hand_ik_pos_vec = solve_ik_2joint(shoulder_pos.xy, hand_pos.xy, len_upper, len_fore, bend_right=bend_right)
    # Возвращает Vector2
    return pygame.math.Vector2(shoulder_pos), pygame.math.Vector2(elbow_pos_vec), pygame.math.Vector2(hand_ik_pos_vec)

# --- Основные функции отрисовки (остальные) ---

def draw_dash_telegraph(surface, start_pos, target_pos, progress):
    GROWTH_PHASE = 0.85 
    max_circle_radius = 180 
    arrow_width = 100
    gap_from_boss = 50        
    gap_from_circle = 50      
    
    if progress < GROWTH_PHASE:
        local_p = progress / GROWTH_PHASE
        t = 1 - (1 - local_p) ** 3
        current_circle_r = max_circle_radius * t
        arrow_growth_t = t
        alpha_mult = 1.0
    else:
        current_circle_r = max_circle_radius
        arrow_growth_t = 1.0
        local_p = (progress - GROWTH_PHASE) / (1.0 - GROWTH_PHASE)
        alpha_mult = 1.0 - local_p

    fill_color = C_DASH_INDICATOR_FILL[:3] + (int(C_DASH_INDICATOR_FILL[3] * alpha_mult),)
    border_color = C_DASH_INDICATOR_BORDER[:3] + (int(255 * alpha_mult),)

    if current_circle_r > 1:
        draw_alpha_circle(surface, fill_color, target_pos, int(current_circle_r))
        draw_outline_circle(surface, target_pos, current_circle_r, border_color)

    start_vec = pygame.math.Vector2(start_pos)
    target_vec = pygame.math.Vector2(target_pos)
    diff = target_vec - start_vec
    dist = diff.length()
    
    if dist < 1: return
    
    direction = diff.normalize()
    perp = pygame.math.Vector2(-direction.y, direction.x) 
    total_arrow_len = dist - gap_from_boss - (gap_from_circle + max_circle_radius)
    
    if total_arrow_len > 0:
        current_arrow_len = total_arrow_len * arrow_growth_t
        p_base = start_vec + direction * gap_from_boss
        p_tip = p_base + direction * current_arrow_len
        
        head_size = 40 
        
        if current_arrow_len < head_size:
            poly_points = [
                (p_base + perp * (arrow_width / 2)).xy,
                (p_base - perp * (arrow_width / 2)).xy,
                (p_tip - perp * (arrow_width / 2)).xy,
                (p_tip + perp * (arrow_width / 2)).xy,
            ]
        else:
            p_neck = p_tip - direction * head_size
            
            poly_points = [
                (p_base + perp * (arrow_width / 2)).xy,         
                (p_base - perp * (arrow_width / 2)).xy,          
                (p_neck - perp * (arrow_width / 2)).xy,          
                (p_neck - perp * (arrow_width / 2 + 20)).xy,     
                p_tip.xy,                                      
                (p_neck + perp * (arrow_width / 2 + 20)).xy,     
                (p_neck + perp * (arrow_width / 2)).xy           
            ]
            
        draw_alpha_polygon(surface, fill_color, poly_points)
        if alpha_mult > 0.1:
            pygame.draw.lines(surface, border_color, True, poly_points, 3)

def draw_outline_circle(surface, center, radius, color):
    """Вспомогательная функция для рисования прозрачного кольца"""
    target_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (int(radius), int(radius)), int(radius), 3)
    surface.blit(shape_surf, target_rect)

def draw_layered_wing(surface, root_pos, angle_deg, scale, time_ticks, flip=False, movement_tilt_x=0.0, alpha=255):
    if alpha <= 0: return
    
    def apply_alpha(col, a):
        if len(col) == 4: return col[:3] + (int(col[3] * (a/255)),)
        return col + (a,)

    color_deep = apply_alpha(C_WING_DEEP, alpha)
    color_mid = apply_alpha(C_WING_MID, alpha)
    color_tip = apply_alpha(C_WING_TIP, alpha)

    angle_rad = math.radians(angle_deg)
    breath = math.sin(time_ticks * 0.03) * 0.1
    side_mult = 1 if not flip else -1
    
    drag_angle = -movement_tilt_x * 0.5 
    tip_angle = angle_rad + (0.5 * side_mult) + (breath * 0.5 * side_mult) + drag_angle
    end_pos = root_pos + pygame.math.Vector2(math.cos(tip_angle), math.sin(tip_angle)) * scale * 3.0
    
    ctrl_angle = angle_rad + (1.6 * side_mult) + drag_angle
    ctrl_dist = scale * 1.5 
    control_pos = root_pos + pygame.math.Vector2(math.cos(ctrl_angle), math.sin(ctrl_angle)) * ctrl_dist
    
    spine_points_tuples = get_bezier_points(root_pos.xy, end_pos.xy, control_pos.xy, segments=16)
    spine_points = [pygame.math.Vector2(p) for p in spine_points_tuples]

    layers = [
        (color_deep, 1.2, 0),    
        (color_mid, 1.0, -2),    
        (color_tip, 0.7, -4)     
    ]

    for color, width_mult, y_offset in layers:
        poly_points = []
        for i, p in enumerate(spine_points):
            if i < len(spine_points) - 1:
                tangent = (spine_points[i+1] - p).normalize()
            else:
                tangent = (p - spine_points[i-1]).normalize()
            normal = pygame.math.Vector2(-tangent.y, tangent.x) * side_mult
            t = i / len(spine_points)
            width = scale * (0.8 + math.sin(t * math.pi) * 0.5) * width_mult
            top_pt = p + normal * (width * 0.3) + pygame.math.Vector2(0, y_offset)
            poly_points.append(top_pt.xy) 

        for i in range(len(spine_points) - 1, -1, -1):
            p = spine_points[i]
            if i < len(spine_points) - 1:
                tangent = (spine_points[i+1] - p).normalize()
            else:
                tangent = (p - spine_points[i-1]).normalize()
            normal = pygame.math.Vector2(-tangent.y, tangent.x) * side_mult
            t = i / len(spine_points)
            width = scale * (0.8 + math.sin(t * math.pi) * 0.8) * width_mult
            
            is_feather_tip = (i % 3 == 0) 
            tooth_len = width
            if is_feather_tip and i > 2: 
                tooth_len *= 1.4 
            
            bot_pt = p - normal * tooth_len - tangent * (scale * 0.3) + pygame.math.Vector2(0, y_offset)
            poly_points.append(bot_pt.xy) 
            
        draw_alpha_polygon(surface, color, poly_points)
        if alpha > 100 and color == color_tip:
             draw_outline(surface, poly_points, width=1)

# --- УДАЛЕНА НОВАЯ/УДАЛЕННАЯ ФУНКЦИЯ ДЛЯ ОТРИСОВКИ НОГ ---
# Эта функция теперь окончательно перенесена в monster_flo.py и вызывается оттуда.

# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ДЛЯ ПЛАТЬЯ (ТОЛЬКО ЮБКА И ПОЯС) ---
# Вставьте эту функцию в boss_flo.py

# В boss_flo.py

# В boss_flo.py

# В boss_flo.py

# Убедитесь, что эта вспомогательная функция есть в файле (или импортирована):
def get_cubic_point(t, p0, p1, p2, p3):
    """Возвращает точку на кубической кривой (для S-изгибов)."""
    u = 1 - t
    tt, uu = t * t, u * u
    uuu, ttt = uu * u, tt * t
    # p0..p3 должны быть Vector2 или иметь перегрузку операций, 
    # иначе нужно расписывать по x/y (здесь предполагаем Vector2)
    return uuu * p0 + 3 * uu * t * p1 + 3 * u * tt * p2 + ttt * p3

def get_cubic_curve_points(p0, p1, p2, p3, segments=16):
    """Генерирует список точек для полигона."""
    res = []
    # Конвертируем в Vector2 для удобства, если переданы кортежи
    v0, v1, v2, v3 = map(pygame.math.Vector2, [p0, p1, p2, p3])
    for i in range(segments + 1):
        res.append(get_cubic_point(i / segments, v0, v1, v2, v3))
    return res

# --- ОСНОВНАЯ ФУНКЦИЯ ---

def draw_flowing_dress(surface, body_center, time_ticks):
    """
    Версия 7:
    - Порядок: Центр -> Бока -> Пояс.
    - Лайн центральной панели в 2 раза тоньше (1px).
    - Сохранена форма "песочных часов" и S-изгибы боков.
    """
    cy = body_center.y
    cx = body_center.x
    
    # --- АНИМАЦИЯ ---
    sway_y = math.sin(time_ticks * 0.05) * 3 
    sway_x = math.cos(time_ticks * 0.04) * 2
    tip_wave = math.sin(time_ticks * 0.06) * 8
    
    # --- КОНСТАНТЫ ---
    BELT_Y = cy + 5                 
    SKIRT_LENGTH = 150              
    
    # Цвета
    COLOR_CLOTH = (240, 245, 255, 255) 
    COLOR_SHADOW = (200, 210, 230, 255) 
    COLOR_GOLD = (230, 195, 60, 255)    

    # Настройки пояса (нужны для расчета координат других частей)
    belt_height = 6
    belt_width = 17
    
    # ==========================================
    # СЛОЙ 1: ЦЕНТРАЛЬНАЯ ПАНЕЛЬ (Теперь рисуется ПЕРВОЙ)
    # ==========================================
    # Форма: Песочные часы (узкий верх -> тонкая талия -> клеш)
    
    PANEL_WIDTH_TOP = 11
    PANEL_WIDTH_BOTTOM = 15
    panel_len = SKIRT_LENGTH * 0.85
    panel_top_y = BELT_Y + belt_height/2
    panel_bottom_y = panel_top_y + panel_len
    
    # Ширина сужения (талии ленты)
    W_TOP = 7      
    W_PINCH = 3    
    W_BOT = 14     

    # Точки
    p_tl = pygame.math.Vector2(cx - W_TOP, panel_top_y)
    p_tr = pygame.math.Vector2(cx + W_TOP, panel_top_y)
    p_bl = pygame.math.Vector2(cx - W_BOT + sway_x, panel_bottom_y + sway_y)
    p_br = pygame.math.Vector2(cx + W_BOT + sway_x, panel_bottom_y + sway_y)

    # Кривые сужения
    ctrl_l_pinch = pygame.math.Vector2(cx - W_PINCH, panel_top_y + 60)
    ctrl_l_low = pygame.math.Vector2(cx - W_PINCH, panel_bottom_y - 40)
    curve_l = get_cubic_curve_points(p_tl, ctrl_l_pinch, ctrl_l_low, p_bl, segments=12)
    
    ctrl_r_pinch = pygame.math.Vector2(cx + W_PINCH, panel_top_y + 60)
    ctrl_r_low = pygame.math.Vector2(cx + W_PINCH, panel_bottom_y - 40)
    curve_r = get_cubic_curve_points(p_tr, ctrl_r_pinch, ctrl_r_low, p_br, segments=12)
    
    panel_poly = [(p.x, p.y) for p in curve_l] + [(p.x, p.y) for p in curve_r[::-1]]
    
    # Отрисовка панели
    draw_alpha_polygon(surface, COLOR_CLOTH, panel_poly)
    
    # Внутренний инсет
    inset_poly = []
    for p in panel_poly:
        px, py = p
        vx = px - cx
        factor = 0.6 if abs(vx) > 5 else 0.3
        inset_x = cx + vx * factor
        inset_poly.append((inset_x, py))
        
    draw_outline(surface, inset_poly, width=1, closed=True)
    # ИЗМЕНЕНИЕ: Лайн теперь шириной 1 (было 2)
    draw_outline(surface, panel_poly, width=1, closed=True)


    # ==========================================
    # СЛОЙ 2: S-ОБРАЗНАЯ ЮБКА (Боковые полы)
    # ==========================================
    # Рисуются ПОВЕРХ центральной панели (если есть перекрытие)
    
    skirt_waist_y = BELT_Y + 4
    skirt_bottom_y = BELT_Y + SKIRT_LENGTH + 10 
    waist_attach_x = 16 

    # --- ЛЕВАЯ СТОРОНА ---
    l_waist = pygame.math.Vector2(cx - waist_attach_x, skirt_waist_y)
    l_tip = pygame.math.Vector2(cx - 85 + sway_x * 1.5 + tip_wave, skirt_bottom_y + sway_y)
    l_inner_gap = pygame.math.Vector2(cx - 30 + sway_x, skirt_bottom_y - 15 + sway_y) 

    l_ctrl_thigh = pygame.math.Vector2(cx - 20, BELT_Y + 80) 
    l_ctrl_flare = pygame.math.Vector2(cx - 95, BELT_Y + 110)
    l_curve_outer = get_cubic_curve_points(l_waist, l_ctrl_thigh, l_ctrl_flare, l_tip, segments=15)
    
    l_ctrl_hem = l_tip.lerp(l_inner_gap, 0.5) + pygame.math.Vector2(0, -10)
    l_curve_hem = get_bezier_points(l_tip.xy, l_inner_gap.xy, l_ctrl_hem.xy, 6)
    
    l_waist_inner = pygame.math.Vector2(cx - 5, skirt_waist_y)
    l_ctrl_leg = pygame.math.Vector2(cx - 15, BELT_Y + 60)
    l_curve_inner = get_bezier_points(l_inner_gap.xy, l_waist_inner.xy, l_ctrl_leg.xy, 8)
    
    poly_l = [(p.x, p.y) for p in l_curve_outer + l_curve_hem[1:] + l_curve_inner[1:]]
    draw_alpha_polygon(surface, COLOR_SHADOW, poly_l)
    draw_outline(surface, poly_l, width=1, closed=True)
    
    # --- ПРАВАЯ СТОРОНА ---
    r_waist = pygame.math.Vector2(cx + waist_attach_x, skirt_waist_y)
    r_tip = pygame.math.Vector2(cx + 85 + sway_x * 1.5 - tip_wave, skirt_bottom_y + sway_y)
    r_inner_gap = pygame.math.Vector2(cx + 30 + sway_x, skirt_bottom_y - 15 + sway_y)
    
    r_ctrl_thigh = pygame.math.Vector2(cx + 20, BELT_Y + 80)
    r_ctrl_flare = pygame.math.Vector2(cx + 95, BELT_Y + 110)
    r_curve_outer = get_cubic_curve_points(r_waist, r_ctrl_thigh, r_ctrl_flare, r_tip, segments=15)
    
    r_ctrl_hem = r_tip.lerp(r_inner_gap, 0.5) + pygame.math.Vector2(0, -10)
    r_curve_hem = get_bezier_points(r_tip.xy, r_inner_gap.xy, r_ctrl_hem.xy, 6)
    
    r_waist_inner = pygame.math.Vector2(cx + 5, skirt_waist_y)
    r_ctrl_leg = pygame.math.Vector2(cx + 15, BELT_Y + 60)
    r_curve_inner = get_bezier_points(r_inner_gap.xy, r_waist_inner.xy, r_ctrl_leg.xy, 8)
    
    poly_r = [(p.x, p.y) for p in r_curve_outer + r_curve_hem[1:] + r_curve_inner[1:]]
    draw_alpha_polygon(surface, COLOR_SHADOW, poly_r)
    draw_outline(surface, poly_r, width=1, closed=True)

    # Декор складки (тонкие линии)
    f_start = l_waist + pygame.math.Vector2(5, 10)
    f_end = l_tip + pygame.math.Vector2(15, -30)
    f_pts = get_cubic_curve_points(f_start, f_start + pygame.math.Vector2(0, 50), f_end + pygame.math.Vector2(10, -50), f_end, 8)
    pygame.draw.aalines(surface, (180, 190, 210), False, [(p.x, p.y) for p in f_pts])
    
    f_start_r = r_waist + pygame.math.Vector2(-5, 10)
    f_end_r = r_tip + pygame.math.Vector2(-15, -30)
    f_pts_r = get_cubic_curve_points(f_start_r, f_start_r + pygame.math.Vector2(0, 50), f_end_r + pygame.math.Vector2(-10, -50), f_end_r, 8)
    pygame.draw.aalines(surface, (180, 190, 210), False, [(p.x, p.y) for p in f_pts_r])


    # ==========================================
    # СЛОЙ 3: ЗОЛОТОЙ ПОЯС (Рисуется ПОСЛЕДНИМ)
    # ==========================================
    belt_poly = [
        (cx - belt_width, BELT_Y - belt_height / 2),
        (cx + belt_width, BELT_Y - belt_height / 2),
        (cx + belt_width + 2, BELT_Y + belt_height / 2),
        (cx - belt_width - 2, BELT_Y + belt_height / 2)
    ]
    draw_alpha_polygon(surface, COLOR_GOLD, belt_poly)
    draw_outline(surface, belt_poly, width=1, closed=True)
    pygame.draw.line(surface, (255, 230, 100), (cx - belt_width + 2, BELT_Y - 2), (cx + belt_width - 2, BELT_Y - 2), 1)

# --- ВАЖНО: ДОБАВЬТЕ ЭТУ ФУНКЦИЮ В НАЧАЛО ФАЙЛА, ЕСЛИ ЕЕ НЕТ ---
def get_cubic_curve(p0, p1, p2, p3, segments=20):
    """Генерация точек для кубической кривой Безье (для более сложных изгибов)."""
    res = []
    for i in range(segments+1):
        t = i / segments
        u = 1 - t
        tt, uu = t * t, u * u
        uuu, ttt = uu * u, tt * t
        p = uuu * p0 + 3 * uu * t * p1 + 3 * u * tt * p2 + ttt * p3
        res.append(p)
    return res


def draw_back_hair(surface, head_center, time_ticks):
    """Рисует только заднюю часть волос (фон)."""
    # Вся логика перенесена в hair_system.py
    draw_hair_layer_back(surface, head_center, time_ticks)

# *** draw_body_and_hair ТЕПЕРЬ ВОЗВРАЩАЕТ АНИМИРОВАННЫЕ КООРДИНАТЫ ***
def draw_body_and_front_hair(surface, body_center, shoulder_l, shoulder_r, time_ticks, death_pose_factor=0.0, target_pos=None, elbow_l_pos=None, elbow_r_pos=None):
    # ... (код расчета цветов и координат без изменений) ...
    """
    Рисует тело, голову и ПЕРЕДНИЕ волосы.
    Задние волосы удалены, чтобы рисовать их отдельным слоем.
    """
    # --- 0. ПЕРЕМЕННЫЕ ЦВЕТОВ ---
    C_BLONDE_BASE = (255, 235, 160, 255)       
    C_BLONDE_SHADOW = (210, 180, 90, 255)      
    C_BLONDE_HIGHLIGHT = (255, 250, 200, 200)  

    cx, cy = body_center.xy

    # --- 1. РАСЧЕТ КООРДИНАТ ---
    death_factor_ease = death_pose_factor * death_pose_factor
    base_shoulder_y = cy - 31
    shoulder_lift = math.sin(time_ticks * 0.05) * 1.5
    shoulder_lift = shoulder_lift * (1.0 - death_factor_ease) + (5.0) * death_factor_ease
    current_shoulder_y = base_shoulder_y + shoulder_lift - 10
    head_y = current_shoulder_y - 33
    head_center = pygame.math.Vector2(cx, head_y)

    # --- УДАЛЕНО: ОТРИСОВКА ВОЛОС СЗАДИ ---
    # Теперь вызывается отдельно через draw_back_hair

    # --- 3. ОТРИСОВКА ТЕЛА, ЛИЦА И НОГ ---
   # ВЫЗОВ draw_archangel_torso ТЕПЕРЬ С ЛОКТЯМИ:
    anim_shoulder_l, anim_shoulder_r, real_head_center = draw_archangel_torso(
        surface, 
        body_center, 
        shoulder_l, 
        shoulder_r, 
        time_ticks, 
        death_pose_factor, 
        C_SKIN, 
        C_SKIN_SHADOW, 
        C_INK,
        target_pos=target_pos,
        elbow_l=elbow_l_pos, # !!!
        elbow_r=elbow_r_pos  # !!!
    )
    
    head_center = real_head_center

    draw_hair_layer_front(surface, head_center, time_ticks)
    
    return anim_shoulder_l, anim_shoulder_r, head_center


def draw_ornate_halo(surface, center, time_ticks):
    halo_pos = center + (0, -125)
    radius_x = 55
    radius_y = 12
    rot = time_ticks * 0.01
    
    draw_alpha_circle(surface, C_GOLD_GLOW, halo_pos.xy, radius_x)
    rect_outer = pygame.Rect(halo_pos.x - radius_x, halo_pos.y - radius_y, radius_x*2, radius_y*2)
    pygame.draw.ellipse(surface, C_GOLD_BRIGHT, rect_outer, 3)
    rect_inner = pygame.Rect(halo_pos.x - radius_x*0.7, halo_pos.y - radius_y*0.7, radius_x*1.4, radius_y*1.4)
    pygame.draw.ellipse(surface, C_GOLD_DARK, rect_inner, 1)
    for i in range(8):
        angle = i * (math.pi * 2 / 8) + rot
        sx = math.cos(angle) * radius_x
        sy = math.sin(angle) * radius_y
        spike_start = halo_pos + pygame.math.Vector2(sx, sy)
        spike_end = halo_pos + pygame.math.Vector2(sx * 1.3, sy * 1.3 - 8) 
        pygame.draw.line(surface, C_GOLD_BRIGHT, spike_start.xy, spike_end.xy, 2)

# ... (draw_archangel_boss и _draw_archangel_internal - без существенных изменений, кроме использования новых функций)

def draw_archangel_boss(surface, center_pos, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress=0.0, shield_animation_progress=0.0, is_phase_two=False, wing_spread_factor=0.0, is_transitioning=False, transition_pose_factor=0.0, movement_tilt_x=0.0, alpha=255, is_final_attack=False, death_params=None, dash_prep_progress=0.0, dash_target_pos=None): 
    if alpha <= 0: return
    if death_params is None: death_params = {}
    
    if dash_target_pos is not None and dash_prep_progress > 0:
        draw_dash_telegraph(surface, center_pos, dash_target_pos, dash_prep_progress)

    surf_w, surf_h = 600, 600
    temp_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
    local_center = pygame.math.Vector2(surf_w // 2, surf_h // 2)
    
    _draw_archangel_internal(
        temp_surf, 
        local_center, 
        time_ticks, 
        spear_animation_progress, 
        is_mist_active, 
        mist_timer, 
        fixed_target_pos, 
        smite_vfx_progress, 
        shield_animation_progress, 
        is_phase_two, 
        wing_spread_factor, 
        is_transitioning, 
        transition_pose_factor, 
        movement_tilt_x, 
        is_final_attack, 
        death_params
    )
    
    if alpha < 255:
        temp_surf.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    dest_pos = (center_pos[0] - surf_w // 2, center_pos[1] - surf_h // 2)
    surface.blit(temp_surf, dest_pos)

def _draw_archangel_internal(surface, draw_pos, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress, shield_animation_progress, is_phase_two, wing_spread_factor, is_transitioning, transition_pose_factor, movement_tilt_x, is_final_attack, death_params):
    
    hover_amp = 8
    if is_transitioning: hover_amp = 12
    hover = math.sin(time_ticks * 0.04) * hover_amp
    draw_pos = draw_pos + pygame.math.Vector2(0, hover - 30)

    # Параметры смерти
    death_pose_factor = death_params.get('pose_factor', 0.0)
    death_item_alpha = death_params.get('item_alpha', 255)
    death_wing_alpha = death_params.get('wing_alpha', 255)
    death_wing_offset = death_params.get('wing_offset', 0.0)
    death_light_scale = death_params.get('light_scale', 0.0)
    death_flash_alpha = death_params.get('flash_alpha', 0) 

    # --- 0. СВЕТ НАКОПЛЕНИЯ ---
    if death_light_scale > 0:
        light_radius = 150 * death_light_scale
        pulse = 1.0 + 0.1 * math.sin(time_ticks * 0.2)
        draw_alpha_circle(surface, (255, 220, 150, int(100 * death_light_scale)), draw_pos.xy, light_radius * 1.5 * pulse)
        draw_alpha_circle(surface, (255, 255, 200, int(150 * death_light_scale)), draw_pos.xy, light_radius * pulse)
        if death_light_scale > 0.5:
            for i in range(8):
                angle = time_ticks * 0.05 + i * (math.pi / 4)
                ray_end = draw_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * (light_radius * 2)
                ray_color = (255, 255, 255, int(100 * (death_light_scale - 0.5) * 2))
                pygame.draw.line(surface, ray_color, draw_pos.xy, ray_end.xy, 4)

    # --- 1. КРЫЛЬЯ (САМЫЙ НИЖНИЙ СЛОЙ) ---
    shoulder_height = -62 
    wing_shift_l = pygame.math.Vector2(-death_wing_offset, 0)
    wing_shift_r = pygame.math.Vector2(death_wing_offset, 0)
    wing_root = draw_pos + (0, shoulder_height)
    spread_angle_offset = -30 * wing_spread_factor 
    
    draw_layered_wing(surface, wing_root + wing_shift_l, 230 + spread_angle_offset, 50, time_ticks, flip=False, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha) 
    draw_layered_wing(surface, wing_root + wing_shift_r, -50 - spread_angle_offset, 50, time_ticks, flip=True, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha)  
    draw_layered_wing(surface, draw_pos + (0, shoulder_height + 20) + wing_shift_l, 200 + spread_angle_offset, 70, time_ticks + 10, flip=False, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha) 
    draw_layered_wing(surface, draw_pos + (0, shoulder_height + 20) + wing_shift_r, -20 - spread_angle_offset, 70, time_ticks + 10, flip=True, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha)  
    
    # --- 2. РАСЧЕТ КООРДИНАТ ТЕЛА ---
    cx, cy = draw_pos.xy
    base_shoulder_y = cy - 31
    death_factor_ease = death_pose_factor * death_pose_factor
    shoulder_lift = math.sin(time_ticks * 0.05) * 1.5
    shoulder_lift = shoulder_lift * (1.0 - death_factor_ease) + (5.0) * death_factor_ease
    shoulder_roll_x = 0 * (1.0 - death_factor_ease) + (10.0) * death_factor_ease
    shoulder_y = base_shoulder_y + shoulder_lift - 10
    
    # Координаты головы (нужны для задних волос)
    head_y = shoulder_y - 33
    head_center_math = pygame.math.Vector2(cx, head_y)

    # Координаты плеч
    SHOULDER_WIDTH_BODY = 7.0
    joint_offset = SHOULDER_WIDTH_BODY + 9.0
    calc_shoulder_l = pygame.math.Vector2(cx - joint_offset - shoulder_roll_x, shoulder_y)
    calc_shoulder_r = pygame.math.Vector2(cx + joint_offset + shoulder_roll_x, shoulder_y)

    # --- 3. ЗАДНИЕ ВОЛОСЫ (РИСУЕМ ДО РУК!) ---
    draw_back_hair(surface, head_center_math, time_ticks)

    # --- 4. ВЕРХНИЕ РУКИ (БИЦЕПСЫ) ---
    is_arms_in_transition = transition_pose_factor > 0.001
    arm_data = calculate_arm_logic(
        draw_pos, calc_shoulder_l, calc_shoulder_r, time_ticks, 
        spear_animation_progress, shield_animation_progress, 
        is_arms_in_transition, transition_pose_factor, death_pose_factor
    )
    draw_arms_upper_layer(surface, arm_data)

    _, elbow_l_calc, _, _, _ = arm_data["l"]
    _, elbow_r_calc, _ = arm_data["r"]

    # --- 5. ТЕЛО И ПЕРЕДНИЕ ВОЛОСЫ ---
    shoulder_width_base = 22
    shoulder_l_base = draw_pos + (-shoulder_width_base, shoulder_height)
    shoulder_r_base = draw_pos + (shoulder_width_base, shoulder_height)

    anim_shoulder_l, anim_shoulder_r, anim_head_center = draw_body_and_front_hair(
        surface, 
        draw_pos, 
        shoulder_l_base, 
        shoulder_r_base, 
        time_ticks, 
        death_pose_factor=death_pose_factor,
        target_pos=fixed_target_pos,
        elbow_l_pos=elbow_l_calc, # !!! Передаем рассчитанный локоть Л
        elbow_r_pos=elbow_r_calc  # !!! Передаем рассчитанный локоть П
    )
    


   
    
    draw_ornate_halo(surface, anim_head_center, time_ticks) 

    draw_flowing_dress(surface, draw_pos, time_ticks)
    
    # --- 6. НИЖНИЕ РУКИ (ПРЕДПЛЕЧЬЯ + ОРУЖИЕ) ---
    draw_arms_lower_layer(surface, arm_data, time_ticks, is_final_attack, is_arms_in_transition, transition_pose_factor, death_item_alpha)

    # --- VFX ---
    if smite_vfx_progress > 0.0: 
        draw_smite_sign(surface, draw_pos.xy, smite_vfx_progress, is_phase_two) 

    if death_flash_alpha > 0:
        draw_alpha_circle(surface, (255, 255, 255, death_flash_alpha), draw_pos.xy, 150)
        draw_alpha_circle(surface, (255, 255, 200, int(death_flash_alpha * 0.5)), draw_pos.xy, 200)

# --- НОВЫЕ ФУНКЦИИ ДЛЯ РАЗДЕЛЬНОЙ ОТРИСОВКИ РУК ---

def calculate_arm_logic(body_center, shoulder_l, shoulder_r, time_ticks, spear_prog, shield_prog, is_trans, trans_factor, death_factor):
    """
    Только математика: рассчитывает координаты локтей и кистей для обеих рук.
    Возвращает словарь с координатами.
    """
    arm_bob_y = math.sin(time_ticks * 0.05) * -2 
    arm_bob_x = math.cos(time_ticks * 0.04) * 2
    
    # --- ЛЕВАЯ РУКА (КОПЬЕ) ---
    DEATH_HAND_POS_L = pygame.math.Vector2(-100, -80) 
    REST_POS = pygame.math.Vector2(-80, -10) 
    RAISED_POS = pygame.math.Vector2(-70, -95) 
    TRANSITION_SPEAR_POS = pygame.math.Vector2(-90, -110)
    
    smooth_progress = 1 - (1 - spear_prog)**3 
    target_pos_base = REST_POS.lerp(RAISED_POS, smooth_progress)
    if is_trans: target_pos_base = target_pos_base.lerp(TRANSITION_SPEAR_POS, trans_factor)
    if death_factor > 0: target_pos_base = target_pos_base.lerp(DEATH_HAND_POS_L, death_factor)

    hand_l_pos = body_center + target_pos_base + pygame.math.Vector2(-arm_bob_x, arm_bob_y) 
    # IK расчет
    shoulder_l_pos, elbow_l_pos, hand_l_ik_pos = calculate_ik_points(shoulder_l, hand_l_pos, bend_right=True)

    # Угол копья
    DEFAULT_SPEAR_ANGLE = -90  
    RAISED_SPEAR_ANGLE = -130 
    TRANSITION_SPEAR_ANGLE = -100 
    current_angle = DEFAULT_SPEAR_ANGLE + (RAISED_SPEAR_ANGLE - DEFAULT_SPEAR_ANGLE) * smooth_progress
    if is_trans: current_angle = current_angle * (1.0 - trans_factor) + TRANSITION_SPEAR_ANGLE * trans_factor
    if death_factor > 0: current_angle = current_angle * (1.0 - death_factor) + (-45) * death_factor

    # --- ПРАВАЯ РУКА (ЩИТ) ---
    DEATH_HAND_POS_R = pygame.math.Vector2(100, -80)
    arm_bob_x_r = math.cos(time_ticks * 0.04) * -2 
    hand_r_rest_pos = pygame.math.Vector2(30, 0) 
    hand_r_bash_pos = pygame.math.Vector2(5, -25) 
    TRANSITION_HAND_POS = pygame.math.Vector2(80, -10)
    
    t = shield_prog
    shield_smooth = t * t * (3 - 2 * t)
    current_hand_pos_local = hand_r_rest_pos.lerp(hand_r_bash_pos, shield_smooth)
    if is_trans: current_hand_pos_local = current_hand_pos_local.lerp(TRANSITION_HAND_POS, trans_factor)
    if death_factor > 0: current_hand_pos_local = current_hand_pos_local.lerp(DEATH_HAND_POS_R, death_factor)

    hand_r_pos = body_center + current_hand_pos_local + pygame.math.Vector2(arm_bob_x_r, arm_bob_y)
    # IK расчет
    shoulder_r_pos, elbow_r_pos, hand_r_ik_pos = calculate_ik_points(shoulder_r, hand_r_pos, bend_right=False)

    return {
        "l": (shoulder_l_pos, elbow_l_pos, hand_l_ik_pos, current_angle, smooth_progress),
        "r": (shoulder_r_pos, elbow_r_pos, hand_r_ik_pos)
    }

def draw_arms_upper_layer(surface, arm_data):
    """
    Слой 1: Рисуем только плечи (бицепсы) от плечевого сустава до локтя.
    Рисуется ПОЗАДИ тела.
    """
    # Левый бицепс
    s_l, e_l, _, _, _ = arm_data["l"]
    # Рисуем только верхнюю часть (C_INK - контур, C_SKIN - кожа)
    draw_arm_upper_humanoid(surface, s_l, e_l, True, C_SKIN, C_INK)
    
    # Правый бицепс
    s_r, e_r, _ = arm_data["r"]
    draw_arm_upper_humanoid(surface, s_r, e_r, False, C_SKIN, C_INK)

# В файле boss_flo.py

def draw_arms_lower_layer(surface, arm_data, time_ticks, use_red_glow, is_trans, trans_factor, item_alpha):
    """
    Слой 2: Рисуем предплечья, кисти и оружие.
    ДЛЯ ЛЕВОЙ РУКИ: Ладонь -> Копье (со смещением в хват) -> Пальцы.
    """
    # --- ЛЕВАЯ СТОРОНА (Копье) ---
    _, elbow_l, hand_l, angle, prog = arm_data["l"]
    
    # 1. Предплечье
    draw_arm_lower_humanoid(surface, elbow_l, hand_l, True, 0.5, C_SKIN, C_INK)
    
    # Расчет БАЗОВОГО угла руки (от локтя к запястью)
    vec_l = hand_l - elbow_l
    base_arm_angle_l = math.atan2(vec_l.y, vec_l.x)

    # === ИЗМЕНЕНИЯ ЗДЕСЬ ===
    
    # 1. Настройка силы наклона:
    # Увеличили угол до -55 градусов (было меньше), чтобы кисть гнулась сильнее.
    MAX_TILT_DEG = -65.0  

    # 2. Настройка динамики ("В конце сильнее"):
    # Возводим prog в степень (например, 2.5). 
    # Это значит: в начале анимации наклон почти не меняется, 
    # а на последних 20% пути происходит основной доворот.
    # Если prog = 0.5 -> offset_factor = 0.17 (мало)
    # Если prog = 1.0 -> offset_factor = 1.0 (полный наклон)
    tilt_curve = math.pow(max(0, prog), 2.5) 
    
    hand_rotation_offset_rad = math.radians(MAX_TILT_DEG * tilt_curve)
    final_hand_angle_l = base_arm_angle_l + hand_rotation_offset_rad
    # ========================

    # 2. ЛАДОНЬ (Задний план кисти)
    flip_hand_l = True
    # Передаем новый угол final_hand_angle_l
    palm_data_l = draw_detailed_hand_palm(surface, hand_l, final_hand_angle_l, is_left=True, 
                                          color=C_SKIN, outline_color=C_INK, 
                                          grip_factor=0.95, scale=0.45, 
                                          flip_vertical=flip_hand_l)

    # 3. КОПЬЕ
    spear_angle_rad = math.radians(angle)
    spear_dir = pygame.math.Vector2(math.cos(spear_angle_rad), math.sin(spear_angle_rad)).normalize()
    
    # --- РАСЧЕТ ТОЧКИ ХВАТА (С учетом нового угла) ---
    mid_palm_pos = pygame.math.Vector2(palm_data_l[0]) 
    
    # Считаем вектор направления самой кисти ПОСЛЕ поворота
    hand_dir_final = pygame.math.Vector2(math.cos(final_hand_angle_l), math.sin(final_hand_angle_l))
    perp_dir_final = pygame.math.Vector2(-hand_dir_final.y, hand_dir_final.x)
    
    # Корректируем точку хвата, чтобы копье "сидело" в повернутой руке
    # (числа можно чуть подправить: *3 - вдоль пальцев, * -2 - вглубь ладони)
    grip_adjustment = hand_dir_final * 3 + perp_dir_final * (-2 if flip_hand_l else 2)
    
    spear_anchor = mid_palm_pos + grip_adjustment

    if item_alpha > 5:
        _draw_spear_visuals(surface, spear_anchor, spear_dir, time_ticks, prog, is_trans, trans_factor, use_red_glow, item_alpha)

    # 4. ПАЛЬЦЫ (Передний план)
    draw_detailed_hand_fingers(surface, palm_data_l, is_left=True, 
                               color=C_SKIN, outline_color=C_INK, 
                               grip_factor=0.95, scale=0.45, 
                               flip_vertical=flip_hand_l)

    # --- ПРАВАЯ СТОРОНА (Без изменений) ---
    _, elbow_r, hand_r = arm_data["r"]
    draw_arm_lower_humanoid(surface, elbow_r, hand_r, False, 0.5, C_SKIN, C_INK)
    vec_r = hand_r - elbow_r
    arm_angle_r = math.atan2(vec_r.y, vec_r.x)
    draw_detailed_hand(surface, hand_r, arm_angle_r, is_left=False, 
                       color=C_SKIN, outline_color=C_INK, 
                       grip_factor=1.0, scale=0.45, flip_vertical=False)
    if item_alpha > 5:
        _draw_shield_visuals(surface, hand_r, item_alpha)


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Вынесли визуализацию предметов, чтобы не загромождать) ---
def _draw_spear_visuals(surface, hand_pos, spear_dir, time_ticks, progress, is_trans, trans_factor, use_red_glow, item_alpha):
    spear_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    glow_active = max(0.0, progress)
    if is_trans: glow_active = trans_factor 
    energy_pulse = math.sin(time_ticks * 0.1) * 0.05 + 0.95
    glow_alpha = int(150 * glow_active * energy_pulse) 
    
    spear_top = hand_pos + spear_dir * 75
    spear_bottom = hand_pos - spear_dir * 85
    pygame.draw.line(spear_surf, C_SPEAR_SHADOW, spear_top.xy, spear_bottom.xy, 7)
    pygame.draw.line(spear_surf, C_SPEAR_SHAFT, spear_top.xy, spear_bottom.xy, 5)
    pygame.draw.line(spear_surf, C_SPEAR_HIGHLIGHT, (spear_top + pygame.math.Vector2(1.5, -1.5)).xy, (spear_bottom + pygame.math.Vector2(1.5, -1.5)).xy, 2)

    if use_red_glow:
        glow_color_bright = C_RED_BRIGHT
        glow_color_deep = C_RED_DEEP
        glow_color_ambient = C_RED_GLOW
    else:
        glow_color_bright = C_CYAN_BRIGHT
        glow_color_deep = C_CYAN_DEEP
        glow_color_ambient = C_CYAN_GLOW

    if glow_alpha > 0:
        num_cuts = 4
        perp_vec = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 3
        for i in range(num_cuts):
            segment_len = (spear_bottom - spear_top).length()
            progress_offset = (time_ticks * 0.05 + i * 1.5) % 1.0 
            p_start_base = spear_bottom.lerp(spear_top, progress_offset)
            p_end_base = spear_bottom.lerp(spear_top, (progress_offset + 0.2) % 1.0) 
            for j in range(3):
                twist_mult = math.sin(time_ticks * 0.1 + i) * 0.5 
                p_start = p_start_base + perp_vec * (0.5 + twist_mult) * (j / 2)
                p_end = p_end_base + perp_vec * (-0.5 - twist_mult) * (j / 2)
                color = glow_color_bright[:3] + (glow_alpha // (j + 1) // 2,)
                pygame.draw.line(spear_surf, color, p_start.xy, p_end.xy, 5 - j * 1)
    
    guard_pos = spear_top - spear_dir * 5
    draw_alpha_circle(spear_surf, C_GOLD_ORNAMENT, guard_pos.xy, 5)
    pygame.draw.circle(spear_surf, C_INK, (int(guard_pos.x), int(guard_pos.y)), 5, 1)

    tip_center = spear_top + spear_dir * 10
    tip_perp = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 12
    tip_poly = [
        (tip_center + spear_dir * 30).xy, 
        (tip_center - spear_dir * 10 - tip_perp).xy, 
        (tip_center - spear_dir * 5).xy, 
        (tip_center - spear_dir * 10 + tip_perp).xy
    ]
    
    draw_alpha_circle(spear_surf, glow_color_ambient[:3] + (glow_alpha,), tip_center.xy, 35)
    draw_alpha_polygon(spear_surf, glow_color_bright, [tip_poly[0], tip_poly[1], tip_poly[3]])
    draw_alpha_polygon(spear_surf, glow_color_deep, [tip_poly[1], tip_poly[2], tip_poly[3]])
    draw_outline(spear_surf, tip_poly, width=1)
    
    if item_alpha < 255:
        spear_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
    
    surface.blit(spear_surf, (0,0))

def _draw_shield_visuals(surface, hand_pos, item_alpha):
    shield_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shield_offset = pygame.math.Vector2(5, 0) 
    shield_center = hand_pos + shield_offset
    draw_alpha_circle(shield_surf, C_GOLD_DARK, shield_center.xy, 30)
    draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center.xy, 24)
    pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 30, 2)
    for i in range(8):
        angle = i * (math.pi * 2 / 8)
        end = shield_center + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 24
        pygame.draw.line(shield_surf, C_GOLD_DARK, shield_center.xy, end.xy, 2)
    draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center.xy, 8)
    pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 8, 1)
    if item_alpha < 255:
        shield_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shield_surf, (0,0))