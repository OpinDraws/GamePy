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
C_RED_DEEP = (150, 0, 0, 255) # Добавим темный красный для наконечника
C_DASH_INDICATOR_FILL = (255, 215, 0, 50)   # Полупрозрачный желтый
C_DASH_INDICATOR_BORDER = (255, 255, 100)   # Яркий желтый

# --- Хелперы ---

def rotate_point(point, angle_rad, center):
    s, c = math.sin(angle_rad), math.cos(angle_rad)
    temp_x = point[0] - center.x
    temp_y = point[1] - center.y
    new_x = temp_x * c - temp_y * s
    new_y = temp_x * s + temp_y * c
    return pygame.math.Vector2(new_x + center.x, new_y + center.y)

# *** ДОБАВЬТЕ/ПРОВЕРЬТЕ ЭТУ ФУНКЦИЮ ЗДЕСЬ ***
def draw_outline(surface, points, width=2, closed=True):
    if len(points) < 2: return
    pygame.draw.lines(surface, C_INK, closed, points, width)

# --- Отрисовка знака Smite с учетом прогресса ---
# *** ИЗМЕНЕНО: Добавлена смена цвета креста в фазе 2 ***
# --- Отрисовка знака Smite (КРЕСТ) ---
def draw_smite_sign(surface, center, progress, is_phase_two=False):
    """
    Рисует знак атаки над головой босса.
    progress: от 0.0 до 1.0.
    """
    sign_pos = center + (0, -100)
    
    # Fade In: Быстрое появление
    FADE_IN_END = 0.1
    fade_in = min(1.0, progress / FADE_IN_END)
    
    # Fade Out: Более плавное и раннее исчезновение
    FADE_OUT_START = 0.7 
    if progress > FADE_OUT_START:
        t = (progress - FADE_OUT_START) / (1.0 - FADE_OUT_START)
        fade_out = 1.0 - (t * t) # Квадратичное затухание (плавнее)
    else:
        fade_out = 1.0
        
    base_alpha_mult = min(fade_in, fade_out) 
    
    # Пульсация
    pulse = 1.0
    if progress <= FADE_OUT_START:
        pulse = (math.sin(pygame.time.get_ticks() * 0.015) * 0.2 + 0.9)
        
    alpha = int(255 * base_alpha_mult * pulse) 
    
    if alpha <= 5: return

    # Логика цвета
    use_red = is_phase_two and progress > 0.3
    
    current_color_bright = C_RED_BRIGHT if use_red else C_CYAN_BRIGHT
    current_color_glow = C_RED_GLOW if use_red else C_CYAN_GLOW

    glow_alpha = int(alpha * 0.5)
    
    # Свечение
    draw_alpha_circle(surface, current_color_glow[:3] + (glow_alpha,), sign_pos, 20 * base_alpha_mult)
    
    # Рисуем крест ПОЛИГОНАМИ (чтобы цвет точно был правильным и прозрачным)
    bar_color = current_color_bright[:3] + (alpha,)
    
    # Вертикальная палка
    w, h = 4, 24
    v_rect = [
        sign_pos + (-w/2, -h/2),
        sign_pos + (w/2, -h/2),
        sign_pos + (w/2, h/2),
        sign_pos + (-w/2, h/2)
    ]
    draw_alpha_polygon(surface, bar_color, v_rect)
    
    # Горизонтальная палка
    w2, h2 = 16, 4
    h_rect = [
        sign_pos + (-w2/2, -h2/2),
        sign_pos + (w2/2, -h2/2),
        sign_pos + (w2/2, h2/2),
        sign_pos + (-w2/2, h2/2)
    ]
    draw_alpha_polygon(surface, bar_color, h_rect)


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
        tip_center + spear_dir * 20, 
        tip_center - spear_dir * 5 - tip_perp, 
        tip_center - spear_dir * 2, 
        tip_center - spear_dir * 5 + tip_perp  
    ]
    
    draw_alpha_circle(surface, c_cyan_glow_a, tip_center, 15)
    draw_alpha_polygon(surface, c_cyan_bright_a, [tip_poly[0], tip_poly[1], tip_poly[3]])
    draw_alpha_polygon(surface, c_cyan_deep_a, [tip_poly[1], tip_poly[2], tip_poly[3]])
    
    shaft_start = tip_center - spear_dir * 2
    shaft_end = tip_center - spear_dir * 60
    
    num_segments = 5
    shaft_len = (shaft_end - shaft_start).length()
    
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
        pygame.draw.line(surface, line_color, p1, p2, 2)
    
    pygame.draw.line(surface, c_cyan_bright_a, shaft_start, shaft_end, 1)

# --- КИСТИ ---

def draw_hand_fist(surface, pos, color, is_left_hand=True, angle_deg=0):
    angle_rad = math.radians(angle_deg)
    knuckles_w = 10
    knuckles_h = 11
    
    half_w = knuckles_w / 2
    half_h = knuckles_h / 2
    local_corners = [
        pygame.math.Vector2(-half_w, -half_h),
        pygame.math.Vector2(half_w, -half_h),
        pygame.math.Vector2(half_w, half_h),
        pygame.math.Vector2(-half_w, half_h)
    ]
    world_corners = [rotate_point(pos + p, angle_rad, pos) for p in local_corners]
    draw_alpha_polygon(surface, color, world_corners)
    draw_outline(surface, world_corners, width=1)

    down_vec = rotate_point(pos + pygame.math.Vector2(0, 1), angle_rad, pos) - pos
    down_vec = down_vec.normalize()
    for i in range(1, 4):
        offset_x = (knuckles_w / 4) * i - half_w
        start_local = pos + pygame.math.Vector2(offset_x, -half_h + 3)
        start_world = rotate_point(start_local, angle_rad, pos)
        end_world = start_world + down_vec * (knuckles_h - 4)
        pygame.draw.line(surface, (200, 180, 170), start_world, end_world, 1)

    thumb_offset_x = 4 if is_left_hand else -4
    thumb_local_pos = pos + pygame.math.Vector2(thumb_offset_x, 2)
    thumb_world_pos = rotate_point(thumb_local_pos, angle_rad, pos)
    draw_alpha_circle(surface, color, thumb_world_pos, 4)
    pygame.draw.circle(surface, C_INK, (int(thumb_world_pos.x), int(thumb_world_pos.y)), 4, 1)

def draw_hand_holding_spear(surface, hand_pos, spear_segment_start, spear_segment_end, is_left_hand=True, angle_deg=0):
    angle_rad = math.radians(angle_deg)
    spear_vec = (spear_segment_end - spear_segment_start).normalize()
    perp_vec = pygame.math.Vector2(-spear_vec.y, spear_vec.x)
    finger_root_offset_x = 4 if is_left_hand else -4
    
    finger_mass_start_local = hand_pos + spear_vec * -2 + perp_vec * finger_root_offset_x * 0.5
    finger_mass_end_local = hand_pos + spear_vec * 9 + perp_vec * finger_root_offset_x * 0.8
    finger_start_world = rotate_point(finger_mass_start_local, angle_rad, hand_pos)
    finger_end_world = rotate_point(finger_mass_end_local, angle_rad, hand_pos)
    pygame.draw.line(surface, C_SKIN, finger_start_world, finger_end_world, 7) 
    pygame.draw.line(surface, C_INK, finger_start_world, finger_end_world, 1)

    thumb_offset_x = -7 if is_left_hand else 7
    thumb_offset_y = -3 
    thumb_base_local = pygame.math.Vector2(thumb_offset_x * 0.7, thumb_offset_y - 2)
    thumb_tip_local = pygame.math.Vector2(thumb_offset_x * 1.2, thumb_offset_y + 4)
    thumb_points_local = [
        hand_pos + thumb_base_local + perp_vec * (2 if is_left_hand else -2),
        hand_pos + thumb_base_local + perp_vec * (-2 if is_left_hand else 2),
        hand_pos + thumb_tip_local + perp_vec * (-1 if is_left_hand else 1) * 0.5,
        hand_pos + thumb_tip_local + perp_vec * (1 if is_left_hand else -1) * 0.5,
    ]
    draw_alpha_polygon(surface, C_SKIN, [rotate_point(p, angle_rad, hand_pos) for p in thumb_points_local])
    draw_outline(surface, [rotate_point(p, angle_rad, hand_pos) for p in thumb_points_local], width=1)


def draw_arm_sleeve_only(surface, shoulder_pos, elbow_pos, hand_pos, bend_right=True, is_left_hand=True):
    draw_bone_segment(surface, shoulder_pos, elbow_pos, C_WHITE_BASE, 8, 6) 
    draw_bone_segment(surface, elbow_pos, hand_pos, C_WHITE_BASE, 6, 8) 
    vec = (hand_pos - elbow_pos).normalize()
    perp = pygame.math.Vector2(-vec.y, vec.x) * 5 
    cuff_pos = hand_pos - vec * 3
    cuff_start = cuff_pos + perp
    cuff_end = cuff_pos - perp
    pygame.draw.line(surface, C_GOLD_ORNAMENT, cuff_start, cuff_end, 4)
    pygame.draw.line(surface, C_INK, cuff_start, cuff_end, 1)
    
    perp_u = pygame.math.Vector2(-(elbow_pos-shoulder_pos).y, (elbow_pos-shoulder_pos).x).normalize() * 4
    perp_f = pygame.math.Vector2(-(hand_pos-elbow_pos).y, (hand_pos-elbow_pos).x).normalize() * 3 
    pygame.draw.line(surface, C_INK, shoulder_pos + perp_u, elbow_pos + perp_u, 1)
    pygame.draw.line(surface, C_INK, elbow_pos + perp_f, hand_pos + perp_f, 1)
    pygame.draw.line(surface, C_INK, shoulder_pos - perp_u, elbow_pos - perp_u, 1)
    pygame.draw.line(surface, C_INK, elbow_pos - perp_f, hand_pos - perp_f, 1)


def calculate_ik_points(shoulder_pos, hand_pos, bend_right=True):
    len_upper = 24
    len_fore = 22
    elbow_pos, hand_ik_pos = solve_ik_2joint(shoulder_pos, hand_pos, len_upper, len_fore, bend_right=False)
    return shoulder_pos, elbow_pos, hand_ik_pos


# --- Основные функции отрисовки (остальные) ---

def draw_dash_telegraph(surface, start_pos, target_pos, progress):
    """
    Рисует индикатор рывка: растущий круг и вытягивающуюся стрелку.
    start_pos: Экранные координаты босса
    target_pos: Экранные координаты точки назначения
    progress: 0.0 -> 1.0 (время жизни эффекта)
    """
    # Тайминги (на основе 0.7 сек)
    GROWTH_PHASE = 0.85 # Фаза роста
    
    # ИЗМЕНЕНИЕ: Радиус увеличен в 2 раза (было 90 -> стало 180)
    max_circle_radius = 180 
    
    # Параметры стрелки
    arrow_width = 100
    gap_from_boss = 50        # Отступ от босса
    gap_from_circle = 50      # Отступ от края круга
    
    if progress < GROWTH_PHASE:
        # Фаза роста (0.0 -> 0.6 сек)
        local_p = progress / GROWTH_PHASE
        t = 1 - (1 - local_p) ** 3 # Ease Out
        
        current_circle_r = max_circle_radius * t
        
        # Стрелка растет линейно или с тем же easing
        arrow_growth_t = t
        
        alpha_mult = 1.0
    else:
        # Фаза исчезновения (0.6 -> 0.7 сек)
        current_circle_r = max_circle_radius
        arrow_growth_t = 1.0
        
        local_p = (progress - GROWTH_PHASE) / (1.0 - GROWTH_PHASE)
        alpha_mult = 1.0 - local_p

    # Цвета с учетом альфы
    fill_color = C_DASH_INDICATOR_FILL[:3] + (int(C_DASH_INDICATOR_FILL[3] * alpha_mult),)
    border_color = C_DASH_INDICATOR_BORDER[:3] + (int(255 * alpha_mult),)

    # --- 1. РИСУЕМ КРУГ ---
    if current_circle_r > 1:
        # Заливка
        draw_alpha_circle(surface, fill_color, target_pos, int(current_circle_r))
        # Обводка (яркая)
        # Рисуем через pygame.draw.circle (он не поддерживает alpha напрямую для линий, 
        # поэтому рисуем на временной поверхности или используем полигон, но для простоты и скорости:
        draw_outline_circle(surface, target_pos, current_circle_r, border_color)

    # --- 2. РИСУЕМ СТРЕЛКУ ---
    # Векторная математика
    start_vec = pygame.math.Vector2(start_pos)
    target_vec = pygame.math.Vector2(target_pos)
    diff = target_vec - start_vec
    dist = diff.length()
    
    # Защита от деления на ноль
    if dist < 1: return
    
    direction = diff.normalize()
    perp = pygame.math.Vector2(-direction.y, direction.x) # Перпендикуляр для ширины
    
    # Рассчитываем полную длину пути стрелки
    # Dist - (Отступ от босса) - (Отступ от круга) - (Радиус круга)
    # Стрелка должна касаться "зоны" вокруг круга
    total_arrow_len = dist - gap_from_boss - (gap_from_circle + max_circle_radius)
    
    if total_arrow_len > 0:
        current_arrow_len = total_arrow_len * arrow_growth_t
        
        # Точки стрелки
        # Начало (у босса + отступ)
        p_base = start_vec + direction * gap_from_boss
        # Конец (с учетом роста)
        p_tip = p_base + direction * current_arrow_len
        
        # Формируем полигон (Прямоугольник + Треугольный наконечник)
        head_size = 40 # Размер наконечника
        
        # Если стрелка еще слишком короткая для наконечника, рисуем просто прямоугольник
        if current_arrow_len < head_size:
            poly_points = [
                p_base + perp * (arrow_width / 2),
                p_base - perp * (arrow_width / 2),
                p_tip - perp * (arrow_width / 2),
                p_tip + perp * (arrow_width / 2),
            ]
        else:
            # Основание стрелки (прямоугольная часть)
            p_neck = p_tip - direction * head_size
            
            poly_points = [
                p_base + perp * (arrow_width / 2),          # Левый низ
                p_base - perp * (arrow_width / 2),          # Правый низ
                p_neck - perp * (arrow_width / 2),          # Правый верх (перед наконечником)
                p_neck - perp * (arrow_width / 2 + 20),     # Расширение для наконечника
                p_tip,                                      # Острие
                p_neck + perp * (arrow_width / 2 + 20),     # Расширение для наконечника
                p_neck + perp * (arrow_width / 2)           # Левый верх
            ]
            
        # Рисуем стрелку
        draw_alpha_polygon(surface, fill_color, poly_points)
        # Обводка стрелки (яркая)
        if alpha_mult > 0.1:
            pygame.draw.lines(surface, border_color, True, poly_points, 3)

def draw_outline_circle(surface, center, radius, color):
    """Вспомогательная функция для рисования прозрачного кольца"""
    target_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (int(radius), int(radius)), int(radius), 3)
    surface.blit(shape_surf, target_rect)

# *** ИЗМЕНЕНО: Добавлен аргумент movement_tilt_x ***
def draw_layered_wing(surface, root_pos, angle_deg, scale, time_ticks, flip=False, movement_tilt_x=0.0, alpha=255):
    # Если альфа 0, не рисуем
    if alpha <= 0: return
    
    # Хелпер для применения альфы к цвету
    def apply_alpha(col, a):
        if len(col) == 4: return col[:3] + (int(col[3] * (a/255)),)
        return col + (a,)

    # Применяем прозрачность к цветам слоев
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
    
    spine_points = get_bezier_points(root_pos, end_pos, control_pos, segments=16)

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
            poly_points.append(top_pt)

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
            poly_points.append(bot_pt)
            
        draw_alpha_polygon(surface, color, poly_points)
        # Рисуем контур только если крылья достаточно видимы
        if alpha > 100 and color == color_tip:
             draw_outline(surface, poly_points, width=1)

def draw_flowing_dress(surface, body_center, shoulder_l, shoulder_r, time_ticks):
    neck_base_center = body_center + (0, -45)
    bottom_width = 70
    length = 110
    sway = math.sin(time_ticks * 0.04) * 5
    
    hem_l = body_center + pygame.math.Vector2(-bottom_width/2 + sway, length - 30)
    hem_r = body_center + pygame.math.Vector2(bottom_width/2 + sway, length - 30)
    hem_mid = body_center + pygame.math.Vector2(sway, length - 20)
    
    waist_l = pygame.math.Vector2(shoulder_l.x + 5, body_center.y - 20)
    waist_r = pygame.math.Vector2(shoulder_r.x - 5, body_center.y - 20)

    left_side = get_bezier_points(waist_l, hem_l, body_center + pygame.math.Vector2(-bottom_width, 20), 5)
    right_side = get_bezier_points(waist_r, hem_r, body_center + pygame.math.Vector2(bottom_width, 20), 5)
    
    dress_poly = [shoulder_l, neck_base_center, shoulder_r] + right_side + [hem_mid] + left_side[::-1]
    
    draw_alpha_polygon(surface, C_WHITE_BASE, dress_poly)
    fold_center = [neck_base_center + (0, 10), hem_mid + (-10, 0), hem_mid + (10, 0)]
    draw_alpha_polygon(surface, C_WHITE_SHADOW, fold_center)
    
    draw_outline(surface, dress_poly, width=2)
    pygame.draw.line(surface, C_INK, neck_base_center, shoulder_l, 2)
    pygame.draw.line(surface, C_INK, neck_base_center, shoulder_r, 2)

def draw_body_and_hair(surface, body_center, shoulder_l, shoulder_r, time_ticks, death_pose_factor=0.0):
    head_center = body_center + (0, -90)
    
    # Поднимаем голову при смерти (чем больше фактор, тем выше)
    head_offset_y = -5 * death_pose_factor
    head_center.y += head_offset_y
    
    # ... (Весь остальной код внутри этой функции оставляем без изменений) ...
    # Просто скопируй старое тело функции сюда, поменяв только заголовок и добавив head_offset_y
    
    collar_top_y = shoulder_l.y 
    collar_bottom_y = shoulder_l.y + 10
    # ... (дальше стандартный код отрисовки тела) ...
    # Если лень копировать, просто вставь head_center.y += ... после объявления head_center
    
    # (Ниже привожу полный код функции для удобства копирования, чтобы не ошибиться)
    collar_width_bottom = 14
    collar_width_top = 10
    collar_poly = [
        (body_center.x - collar_width_top/2, collar_top_y),
        (body_center.x + collar_width_top/2, collar_top_y),
        (body_center.x + collar_width_bottom/2, collar_bottom_y),
        (body_center.x - collar_width_bottom/2, collar_bottom_y)
    ]
    draw_alpha_polygon(surface, C_WHITE_BASE, collar_poly)
    draw_outline(surface, collar_poly, width=1)

    skin_darker = (230, 220, 215, 255) 
    neck_width = 7
    neck_bottom = collar_top_y + 2
    neck_top = head_center.y + 18
    neck_rect = pygame.Rect(
        body_center.x - neck_width/2,
        neck_top,
        neck_width,
        neck_bottom - neck_top
    )
    pygame.draw.rect(surface, skin_darker, neck_rect)
    pygame.draw.line(surface, C_INK, (neck_rect.left, neck_rect.top), (neck_rect.left, neck_rect.bottom), 1)
    pygame.draw.line(surface, C_INK, (neck_rect.right, neck_rect.top), (neck_rect.right, neck_rect.bottom), 1)

    draw_alpha_circle(surface, C_SKIN_SHADOW, head_center + (0, 18), 6)

    hair_flow = math.sin(time_ticks * 0.05) * 3
    hair_back = [
        head_center + (0, -20), 
        shoulder_l + (hair_flow, 0),
        body_center + (-20, 50), 
        body_center + (20, 50),
        shoulder_r + (hair_flow, 0)
    ]
    draw_alpha_polygon(surface, C_WHITE_SHADOW, hair_back)
    draw_outline(surface, hair_back, width=1)

    face_w = 14 
    face_poly = [
        head_center + (-face_w, -10), 
        head_center + (face_w, -10),
        head_center + (face_w - 1, 4),  
        head_center + (9, 16), 
        head_center + (0, 20), 
        head_center + (-9, 16),
        head_center + (-face_w + 1, 4)
    ]
    draw_alpha_polygon(surface, C_SKIN, face_poly)
    draw_outline(surface, face_poly, width=1)
    
    pygame.draw.circle(surface, C_SKIN, (int(head_center.x), int(head_center.y - 10)), face_w)
    pygame.draw.circle(surface, C_INK, (int(head_center.x), int(head_center.y - 10)), face_w, 1) 
    pygame.draw.circle(surface, C_WHITE_BASE, (int(head_center.x), int(head_center.y - 12)), face_w + 5)
    pygame.draw.circle(surface, C_INK, (int(head_center.x), int(head_center.y - 12)), face_w + 5, 1)
    
    strand_l = get_bezier_points(head_center + (-12, -18), body_center + (-25 + hair_flow, -40), head_center + (-45, 0))
    draw_alpha_polygon(surface, C_WHITE_BASE, strand_l + [head_center + (-16, -5)])
    draw_outline(surface, strand_l + [head_center + (-16, -5)], width=1)
    strand_r = get_bezier_points(head_center + (12, -18), body_center + (25 + hair_flow, -40), head_center + (45, 0))
    draw_alpha_polygon(surface, C_WHITE_BASE, strand_r + [head_center + (16, -5)])
    draw_outline(surface, strand_r + [head_center + (16, -5)], width=1)
    
    bangs = [head_center + (0, -15), head_center + (-4, -6), head_center + (4, -6)]
    draw_alpha_polygon(surface, C_WHITE_BASE, bangs)

def draw_ornate_halo(surface, center, time_ticks):
    halo_pos = center + (0, -125)
    radius_x = 55
    radius_y = 12
    rot = time_ticks * 0.01
    
    draw_alpha_circle(surface, C_GOLD_GLOW, halo_pos, radius_x)
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
        pygame.draw.line(surface, C_GOLD_BRIGHT, spike_start, spike_end, 2)

def draw_archangel_boss(surface, center_pos, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress=0.0, shield_animation_progress=0.0, is_phase_two=False, wing_spread_factor=0.0, is_transitioning=False, transition_pose_factor=0.0, movement_tilt_x=0.0, alpha=255, is_final_attack=False, death_params=None): 
    if alpha <= 0: return
    if death_params is None: death_params = {}
    
    surf_w, surf_h = 600, 600
    temp_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
    local_center = pygame.math.Vector2(surf_w // 2, surf_h // 2)
    
    _draw_archangel_internal(temp_surf, local_center, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress, shield_animation_progress, is_phase_two, wing_spread_factor, is_transitioning, transition_pose_factor, movement_tilt_x, is_final_attack, death_params)
    
    if alpha < 255:
        temp_surf.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    dest_pos = (center_pos[0] - surf_w // 2, center_pos[1] - surf_h // 2)
    surface.blit(temp_surf, dest_pos)

# Переименовали старую функцию draw_archangel_boss в _draw_archangel_internal
# Она делает всю грязную работу по рисованию линий
def _draw_archangel_internal(surface, draw_pos, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress, shield_animation_progress, is_phase_two, wing_spread_factor, is_transitioning, transition_pose_factor, movement_tilt_x, is_final_attack, death_params):
    
    hover_amp = 8
    if is_transitioning: hover_amp = 12
    hover = math.sin(time_ticks * 0.04) * hover_amp
    draw_pos = draw_pos + pygame.math.Vector2(0, hover - 30)

    shoulder_width = 22
    shoulder_height = -62 
    shoulder_l = draw_pos + (-shoulder_width, shoulder_height)
    shoulder_r = draw_pos + (shoulder_width, shoulder_height)
    
    # --- ПАРАМЕТРЫ СМЕРТИ ---
    death_pose_factor = death_params.get('pose_factor', 0.0)
    death_item_alpha = death_params.get('item_alpha', 255)
    death_wing_alpha = death_params.get('wing_alpha', 255)
    death_wing_offset = death_params.get('wing_offset', 0.0)
    death_light_scale = death_params.get('light_scale', 0.0) # НОВОЕ
    death_flash_alpha = death_params.get('flash_alpha', 0)   # НОВОЕ

    # --- 0. СВЕТ НАКОПЛЕНИЯ (Позади босса) ---
    if death_light_scale > 0:
        # Большой светящийся круг сзади
        light_radius = 150 * death_light_scale
        # Пульсация
        pulse = 1.0 + 0.1 * math.sin(time_ticks * 0.2)
        
        # Внешний ореол
        draw_alpha_circle(surface, (255, 220, 150, int(100 * death_light_scale)), draw_pos, light_radius * 1.5 * pulse)
        # Ядро света
        draw_alpha_circle(surface, (255, 255, 200, int(150 * death_light_scale)), draw_pos, light_radius * pulse)
        # Лучи
        if death_light_scale > 0.5:
            for i in range(8):
                angle = time_ticks * 0.05 + i * (math.pi / 4)
                ray_end = draw_pos + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * (light_radius * 2)
                ray_color = (255, 255, 255, int(100 * (death_light_scale - 0.5) * 2))
                pygame.draw.line(surface, ray_color, draw_pos, ray_end, 4)

    # 1. Крылья
    wing_shift_l = pygame.math.Vector2(-death_wing_offset, 0)
    wing_shift_r = pygame.math.Vector2(death_wing_offset, 0)
    wing_root = draw_pos + (0, shoulder_height)
    spread_angle_offset = -30 * wing_spread_factor 
    
    draw_layered_wing(surface, wing_root + wing_shift_l, 230 + spread_angle_offset, 50, time_ticks, flip=False, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha) 
    draw_layered_wing(surface, wing_root + wing_shift_r, -50 - spread_angle_offset, 50, time_ticks, flip=True, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha)  
    draw_layered_wing(surface, draw_pos + (0, shoulder_height + 20) + wing_shift_l, 200 + spread_angle_offset, 70, time_ticks + 10, flip=False, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha) 
    draw_layered_wing(surface, draw_pos + (0, shoulder_height + 20) + wing_shift_r, -20 - spread_angle_offset, 70, time_ticks + 10, flip=True, movement_tilt_x=movement_tilt_x, alpha=death_wing_alpha)  
    
    # 2. Тело
    draw_ornate_halo(surface, draw_pos, time_ticks)
    draw_flowing_dress(surface, draw_pos, shoulder_l, shoulder_r, time_ticks)
    draw_body_and_hair(surface, draw_pos, shoulder_l, shoulder_r, time_ticks, death_pose_factor=death_pose_factor) 
    
    current_spear_prog = spear_animation_progress
    current_shield_prog = shield_animation_progress
    is_arms_in_transition = transition_pose_factor > 0.001
    
    draw_equipment_and_arms_custom(
        surface, draw_pos, shoulder_l, shoulder_r, time_ticks, 
        current_spear_prog, current_shield_prog, 
        is_transitioning=is_arms_in_transition, 
        transition_factor=transition_pose_factor,
        use_red_glow=is_final_attack,
        death_pose_factor=death_pose_factor,
        item_alpha=death_item_alpha
    )
    
    if smite_vfx_progress > 0.0: 
        draw_smite_sign(surface, draw_pos, smite_vfx_progress, is_phase_two)

    # --- 99. ФИНАЛЬНАЯ ВСПЫШКА (Поверх всего) ---
    if death_flash_alpha > 0:
        # Рисуем просто белый круг или заливаем фигуру белым
        # Если нарисовать круг поверх, он перекроет детали. 
        # Это то, что нужно для "исчезновения в свете".
        draw_alpha_circle(surface, (255, 255, 255, death_flash_alpha), draw_pos, 150)
        # Дополнительное сияние
        draw_alpha_circle(surface, (255, 255, 200, int(death_flash_alpha * 0.5)), draw_pos, 200)

# --- ОБНОВЛЕНА СИГНАТУРА: добавлен is_final_attack ---
def draw_archangel_boss(surface, center_pos, time_ticks, spear_animation_progress, is_mist_active, mist_timer, fixed_target_pos, smite_vfx_progress=0.0, shield_animation_progress=0.0, is_phase_two=False, wing_spread_factor=0.0, is_transitioning=False, transition_pose_factor=0.0, movement_tilt_x=0.0, alpha=255, is_final_attack=False, death_params=None, dash_prep_progress=0.0, dash_target_pos=None): 
    if alpha <= 0: return
    if death_params is None: death_params = {}
    
    # 1. ТЕЛЕГРАФ РЫВКА
    if dash_target_pos is not None and dash_prep_progress > 0:
        # Передаем: (Поверхность, Позиция Босса, Позиция Цели, Прогресс)
        draw_dash_telegraph(surface, center_pos, dash_target_pos, dash_prep_progress)

    # ... (Остальной код без изменений) ...
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

# --- ОБНОВЛЕНА СИГНАТУРА: добавлен use_red_glow ---
def draw_equipment_and_arms_custom(surface, body_center, shoulder_l, shoulder_r, time_ticks, spear_animation_progress, shield_animation_progress, is_transitioning=False, transition_factor=0.0, use_red_glow=False, death_pose_factor=0.0, item_alpha=255):
    arm_bob_y = math.sin(time_ticks * 0.05) * -2 
    arm_bob_x = math.cos(time_ticks * 0.04) * 2
    
    # Позиции для смерти (кисти вверх, поза мольбы)
    DEATH_HAND_POS_L = pygame.math.Vector2(-120, -90)
    DEATH_HAND_POS_R = pygame.math.Vector2(120, -90)
    
    # ================== ЛЕВАЯ РУКА (КОПЬЕ) ==================
    REST_POS = pygame.math.Vector2(-80, -10) 
    RAISED_POS = pygame.math.Vector2(-70, -95) 
    TRANSITION_SPEAR_POS = pygame.math.Vector2(-90, -110)
    
    progress = spear_animation_progress
    smooth_progress = 1 - (1 - progress)**3 
    target_pos_base = REST_POS.lerp(RAISED_POS, smooth_progress)
    
    if is_transitioning:
        target_pos_base = target_pos_base.lerp(TRANSITION_SPEAR_POS, transition_factor)
    
    # Интерполяция в позу смерти
    if death_pose_factor > 0:
        target_pos_base = target_pos_base.lerp(DEATH_HAND_POS_L, death_pose_factor)

    hand_l_pos = body_center + target_pos_base + pygame.math.Vector2(-arm_bob_x, arm_bob_y) 
    shoulder_l_pos, elbow_l_pos, hand_l_ik_pos = calculate_ik_points(shoulder_l, hand_l_pos, bend_right=True)

    draw_arm_sleeve_only(surface, shoulder_l_pos, elbow_l_pos, hand_l_ik_pos, bend_right=False)
    
    # --- ВАЖНО: РАСЧЕТ УГЛА ВЫНЕСЕН СЮДА (ДО ПРОВЕРКИ ПРОЗРАЧНОСТИ) ---
    DEFAULT_SPEAR_ANGLE_DEG = -90  
    RAISED_SPEAR_ANGLE_DEG = -130 
    TRANSITION_SPEAR_ANGLE = -100 
    current_angle = DEFAULT_SPEAR_ANGLE_DEG + (RAISED_SPEAR_ANGLE_DEG - DEFAULT_SPEAR_ANGLE_DEG) * smooth_progress
    
    if is_transitioning:
        current_angle = current_angle * (1.0 - transition_factor) + TRANSITION_SPEAR_ANGLE * transition_factor
        
    # При смерти копье наклоняется
    if death_pose_factor > 0:
            current_angle = current_angle * (1.0 - death_pose_factor) + (-45) * death_pose_factor

    spear_angle_rad = math.radians(current_angle)
    spear_dir = pygame.math.Vector2(math.cos(spear_angle_rad), math.sin(spear_angle_rad)).normalize()
    
    # Эти координаты нужны и для отрисовки, и для эффектов
    spear_top = hand_l_ik_pos + spear_dir * 75
    spear_bottom = hand_l_ik_pos - spear_dir * 85

    # --- ОТРИСОВКА КОПЬЯ (ТОЛЬКО ЕСЛИ ВИДНО) ---
    if item_alpha > 5: 
        spear_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        glow_active = max(0.0, progress)
        if is_transitioning: glow_active = transition_factor 
        energy_pulse = math.sin(time_ticks * 0.1) * 0.05 + 0.95
        glow_alpha = int(150 * glow_active * energy_pulse) 
        
        # Рисуем само копье
        pygame.draw.line(spear_surf, C_SPEAR_SHADOW, spear_top, spear_bottom, 7)
        pygame.draw.line(spear_surf, C_SPEAR_SHAFT, spear_top, spear_bottom, 5)
        pygame.draw.line(spear_surf, C_SPEAR_HIGHLIGHT, spear_top + pygame.math.Vector2(1.5, -1.5), spear_bottom + pygame.math.Vector2(1.5, -1.5), 2)

        # Выбор цвета свечения
        if use_red_glow:
            glow_color_bright = C_RED_BRIGHT
            glow_color_deep = C_RED_DEEP
            glow_color_ambient = C_RED_GLOW
        else:
            glow_color_bright = C_CYAN_BRIGHT
            glow_color_deep = C_CYAN_DEEP
            glow_color_ambient = C_CYAN_GLOW

        # Магическое свечение (спираль)
        if glow_alpha > 0:
            num_cuts = 4
            perp_vec = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 3
            for i in range(num_cuts):
                progress_offset = (time_ticks * 0.05 + i * 1.5) % ((spear_bottom - spear_top).length() / 20) / ((spear_bottom - spear_top).length() / 20) 
                p_start_base = spear_bottom.lerp(spear_top, progress_offset)
                p_end_base = spear_bottom.lerp(spear_top, (progress_offset + 0.2) % 1.0) 
                for j in range(3):
                    twist_mult = math.sin(time_ticks * 0.1 + i) * 0.5 
                    p_start = p_start_base + perp_vec * (0.5 + twist_mult) * (j / 2)
                    p_end = p_end_base + perp_vec * (-0.5 - twist_mult) * (j / 2)
                    color = glow_color_bright[:3] + (glow_alpha // (j + 1) // 2,)
                    pygame.draw.line(spear_surf, color, p_start, p_end, 5 - j * 1)
        
        # Гарда
        guard_pos = spear_top - spear_dir * 5
        draw_alpha_circle(spear_surf, C_GOLD_ORNAMENT, guard_pos, 5)
        pygame.draw.circle(spear_surf, C_INK, (int(guard_pos.x), int(guard_pos.y)), 5, 1)

        # Наконечник
        tip_center = spear_top + spear_dir * 10
        tip_perp = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 12
        tip_poly = [
            tip_center + spear_dir * 30, 
            tip_center - spear_dir * 10 - tip_perp, 
            tip_center - spear_dir * 5, 
            tip_center - spear_dir * 10 + tip_perp
        ]
        
        draw_alpha_circle(spear_surf, glow_color_ambient[:3] + (glow_alpha,), tip_center, 35)
        draw_alpha_polygon(spear_surf, glow_color_bright, [tip_poly[0], tip_poly[1], tip_poly[3]])
        draw_alpha_polygon(spear_surf, glow_color_deep, [tip_poly[1], tip_poly[2], tip_poly[3]])
        draw_outline(spear_surf, tip_poly, width=1)
        
        # Применяем прозрачность ко всему копью
        if item_alpha < 255:
            spear_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        
        surface.blit(spear_surf, (0,0))

    # --- КИСТЬ ЛЕВОЙ РУКИ ---
    hand_angle = current_angle + 90
    # Если оружие почти исчезло, рисуем просто кулак
    if item_alpha < 50:
        draw_hand_fist(surface, hand_l_ik_pos, C_SKIN, is_left_hand=True, angle_deg=hand_angle)
    else:
        spear_grip_start = hand_l_ik_pos + spear_dir * -5 
        spear_grip_end = hand_l_ik_pos + spear_dir * 5 
        draw_hand_holding_spear(surface, hand_l_ik_pos, spear_grip_start, spear_grip_end, is_left_hand=True, angle_deg=hand_angle)
    
    # ================== ПРАВАЯ РУКА (ЩИТ) ==================
    arm_bob_x_r = math.cos(time_ticks * 0.04) * -2 
    hand_r_rest_pos = pygame.math.Vector2(30, 0) 
    hand_r_bash_pos = pygame.math.Vector2(5, -25) 
    TRANSITION_HAND_POS = pygame.math.Vector2(80, -10)
    
    t = shield_animation_progress
    shield_smooth = t * t * (3 - 2 * t)
    current_hand_pos_local = hand_r_rest_pos.lerp(hand_r_bash_pos, shield_smooth)
    
    if is_transitioning:
        current_hand_pos_local = current_hand_pos_local.lerp(TRANSITION_HAND_POS, transition_factor)
    
    # Интерполяция в позу смерти
    if death_pose_factor > 0:
        current_hand_pos_local = current_hand_pos_local.lerp(DEATH_HAND_POS_R, death_pose_factor)

    hand_r_pos = body_center + current_hand_pos_local + pygame.math.Vector2(arm_bob_x_r, arm_bob_y)
    shoulder_r_pos, elbow_r_pos, hand_r_ik_pos = calculate_ik_points(shoulder_r, hand_r_pos, bend_right=True)
    
    draw_arm_sleeve_only(surface, shoulder_r_pos, elbow_r_pos, hand_r_ik_pos, bend_right=True)
    draw_hand_fist(surface, hand_r_ik_pos, C_SKIN, is_left_hand=False, angle_deg=10)

    # --- ОТРИСОВКА ЩИТА (С ПРОЗРАЧНОСТЬЮ) ---
    if item_alpha > 5:
        shield_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shield_offset = pygame.math.Vector2(5, 0) 
        shield_center = hand_r_ik_pos + shield_offset
        
        draw_alpha_circle(shield_surf, C_GOLD_DARK, shield_center, 30)
        draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center, 24)
        pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 30, 2)
        
        for i in range(8):
            angle = i * (math.pi * 2 / 8)
            end = shield_center + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 24
            pygame.draw.line(shield_surf, C_GOLD_DARK, shield_center, end, 2)
            
        draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center, 8)
        pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 8, 1)
        
        if item_alpha < 255:
            shield_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        
        surface.blit(shield_surf, (0,0))
    arm_bob_y = math.sin(time_ticks * 0.05) * -2 
    arm_bob_x = math.cos(time_ticks * 0.04) * 2
    
    DEATH_HAND_POS_L = pygame.math.Vector2(-100, -80) # Уменьшил разлет, чтобы не рвались локти
    DEATH_HAND_POS_R = pygame.math.Vector2(100, -80)
    
    # ================== ЛЕВАЯ РУКА (КОПЬЕ) ==================
    REST_POS = pygame.math.Vector2(-80, -10) 
    RAISED_POS = pygame.math.Vector2(-70, -95) 
    TRANSITION_SPEAR_POS = pygame.math.Vector2(-90, -110)
    
    progress = spear_animation_progress
    smooth_progress = 1 - (1 - progress)**3 
    target_pos_base = REST_POS.lerp(RAISED_POS, smooth_progress)
    if is_transitioning: target_pos_base = target_pos_base.lerp(TRANSITION_SPEAR_POS, transition_factor)
    if death_pose_factor > 0: target_pos_base = target_pos_base.lerp(DEATH_HAND_POS_L, death_pose_factor)

    hand_l_pos = body_center + target_pos_base + pygame.math.Vector2(-arm_bob_x, arm_bob_y) 
    shoulder_l_pos, elbow_l_pos, hand_l_ik_pos = calculate_ik_points(shoulder_l, hand_l_pos, bend_right=True)
    draw_arm_sleeve_only(surface, shoulder_l_pos, elbow_l_pos, hand_l_ik_pos, bend_right=False)
    
    DEFAULT_SPEAR_ANGLE_DEG = -90  
    RAISED_SPEAR_ANGLE_DEG = -130 
    TRANSITION_SPEAR_ANGLE = -100 
    current_angle = DEFAULT_SPEAR_ANGLE_DEG + (RAISED_SPEAR_ANGLE_DEG - DEFAULT_SPEAR_ANGLE_DEG) * smooth_progress
    if is_transitioning: current_angle = current_angle * (1.0 - transition_factor) + TRANSITION_SPEAR_ANGLE * transition_factor
    if death_pose_factor > 0: current_angle = current_angle * (1.0 - death_pose_factor) + (-45) * death_pose_factor

    spear_angle_rad = math.radians(current_angle)
    spear_dir = pygame.math.Vector2(math.cos(spear_angle_rad), math.sin(spear_angle_rad)).normalize()

    if item_alpha > 5:
        spear_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        glow_active = max(0.0, progress)
        if is_transitioning: glow_active = transition_factor 
        energy_pulse = math.sin(time_ticks * 0.1) * 0.05 + 0.95
        glow_alpha = int(150 * glow_active * energy_pulse) 
        
        spear_top = hand_l_ik_pos + spear_dir * 75
        spear_bottom = hand_l_ik_pos - spear_dir * 85
        pygame.draw.line(spear_surf, C_SPEAR_SHADOW, spear_top, spear_bottom, 7)
        pygame.draw.line(spear_surf, C_SPEAR_SHAFT, spear_top, spear_bottom, 5)
        pygame.draw.line(spear_surf, C_SPEAR_HIGHLIGHT, spear_top + pygame.math.Vector2(1.5, -1.5), spear_bottom + pygame.math.Vector2(1.5, -1.5), 2)

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
                progress_offset = (time_ticks * 0.05 + i * 1.5) % ((spear_bottom - spear_top).length() / 20) / ((spear_bottom - spear_top).length() / 20) 
                p_start_base = spear_bottom.lerp(spear_top, progress_offset)
                p_end_base = spear_bottom.lerp(spear_top, (progress_offset + 0.2) % 1.0) 
                for j in range(3):
                    twist_mult = math.sin(time_ticks * 0.1 + i) * 0.5 
                    p_start = p_start_base + perp_vec * (0.5 + twist_mult) * (j / 2)
                    p_end = p_end_base + perp_vec * (-0.5 - twist_mult) * (j / 2)
                    color = glow_color_bright[:3] + (glow_alpha // (j + 1) // 2,)
                    pygame.draw.line(spear_surf, color, p_start, p_end, 5 - j * 1)
        
        guard_pos = spear_top - spear_dir * 5
        draw_alpha_circle(spear_surf, C_GOLD_ORNAMENT, guard_pos, 5)
        pygame.draw.circle(spear_surf, C_INK, (int(guard_pos.x), int(guard_pos.y)), 5, 1)
        tip_center = spear_top + spear_dir * 10
        tip_perp = pygame.math.Vector2(-spear_dir.y, spear_dir.x) * 12
        tip_poly = [tip_center + spear_dir * 30, tip_center - spear_dir * 10 - tip_perp, tip_center - spear_dir * 5, tip_center - spear_dir * 10 + tip_perp]
        draw_alpha_circle(spear_surf, glow_color_ambient[:3] + (glow_alpha,), tip_center, 35)
        draw_alpha_polygon(spear_surf, glow_color_bright, [tip_poly[0], tip_poly[1], tip_poly[3]])
        draw_alpha_polygon(spear_surf, glow_color_deep, [tip_poly[1], tip_poly[2], tip_poly[3]])
        draw_outline(spear_surf, tip_poly, width=1)
        
        if item_alpha < 255:
            spear_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(spear_surf, (0,0))

    hand_angle = current_angle + 90
    if item_alpha < 50:
        draw_hand_fist(surface, hand_l_ik_pos, C_SKIN, is_left_hand=True, angle_deg=hand_angle)
    else:
        spear_grip_start = hand_l_ik_pos + spear_dir * -5 
        spear_grip_end = hand_l_ik_pos + spear_dir * 5 
        draw_hand_holding_spear(surface, hand_l_ik_pos, spear_grip_start, spear_grip_end, is_left_hand=True, angle_deg=hand_angle)
    
    # ================== ПРАВАЯ РУКА (ЩИТ) ==================
    arm_bob_x_r = math.cos(time_ticks * 0.04) * -2 
    hand_r_rest_pos = pygame.math.Vector2(30, 0) 
    hand_r_bash_pos = pygame.math.Vector2(5, -25) 
    TRANSITION_HAND_POS = pygame.math.Vector2(80, -10)
    t = shield_animation_progress
    shield_smooth = t * t * (3 - 2 * t)
    current_hand_pos_local = hand_r_rest_pos.lerp(hand_r_bash_pos, shield_smooth)
    if is_transitioning: current_hand_pos_local = current_hand_pos_local.lerp(TRANSITION_HAND_POS, transition_factor)
    if death_pose_factor > 0: current_hand_pos_local = current_hand_pos_local.lerp(DEATH_HAND_POS_R, death_pose_factor)

    hand_r_pos = body_center + current_hand_pos_local + pygame.math.Vector2(arm_bob_x_r, arm_bob_y)
    shoulder_r_pos, elbow_r_pos, hand_r_ik_pos = calculate_ik_points(shoulder_r, hand_r_pos, bend_right=True)
    draw_arm_sleeve_only(surface, shoulder_r_pos, elbow_r_pos, hand_r_ik_pos, bend_right=True)
    draw_hand_fist(surface, hand_r_ik_pos, C_SKIN, is_left_hand=False, angle_deg=10)

    if item_alpha > 5:
        shield_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shield_offset = pygame.math.Vector2(5, 0) 
        shield_center = hand_r_ik_pos + shield_offset
        draw_alpha_circle(shield_surf, C_GOLD_DARK, shield_center, 30)
        draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center, 24)
        pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 30, 2)
        for i in range(8):
            angle = i * (math.pi * 2 / 8)
            end = shield_center + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 24
            pygame.draw.line(shield_surf, C_GOLD_DARK, shield_center, end, 2)
        draw_alpha_circle(shield_surf, C_GOLD_BRIGHT, shield_center, 8)
        pygame.draw.circle(shield_surf, C_INK, (int(shield_center.x), int(shield_center.y)), 8, 1)
        if item_alpha < 255:
            shield_surf.fill((255, 255, 255, item_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(shield_surf, (0,0))