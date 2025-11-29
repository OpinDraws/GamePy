import pygame
import math
import random

# --- ПАЛИТРА ---
PURPLE_DARK = (45, 30, 70)
PURPLE_MID = (85, 60, 130)
BLACK = (0, 0, 0)
C_EYE_SCLERA = (40, 10, 50)
C_EYE_IRIS = (255, 180, 0)
C_EYE_PUPIL = (0, 0, 0)
C_EYE_GLOW = (255, 220, 150)
SHADOW_COLOR = (0, 0, 0, 80)

# КОЭФФИЦИЕНТ МАСШТАБА
S = 0.5

def get_bezier_point(t, p0, p1, p2):
    x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
    y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
    return (x, y)

def draw_clipped_leg(target_surface, start_pos, control_pos, end_pos, width_top, width_bottom, color, ground_y, is_outline=False):
    """
    Рисует ногу на временной поверхности, обрезает её по ground_y,
    а затем накладывает результат на целевую поверхность.
    """
    # 1. Создаем временную поверхность размером с целевую
    temp_surf = pygame.Surface(target_surface.get_size(), pygame.SRCALPHA)
    temp_surf.fill((0, 0, 0, 0))

    # 2. Устанавливаем клип на временной поверхности (рисуем только выше ground_y)
    # ground_y - 1, чтобы линия среза была чуть чище
    clip_rect = pygame.Rect(0, 0, temp_surf.get_width(), int(ground_y))
    temp_surf.set_clip(clip_rect)
    
    steps = 20
    points = []
    for i in range(steps + 1):
        t = i / steps
        center = get_bezier_point(t, start_pos, control_pos, end_pos)
        radius = width_top * (1 - t) + width_bottom * t
        pygame.draw.circle(temp_surf, color, (int(center[0]), int(center[1])), int(radius))
        points.append(center)
    
    # 3. Снимаем клип, чтобы нарисовать "подошву" (если нужно)
    temp_surf.set_clip(None)
    
    if is_outline and len(points) > 1:
        final_x = end_pos[0]
        # Рисуем линию ровно на уровне земли
        pygame.draw.line(temp_surf, color, 
                         (final_x - width_bottom, ground_y), 
                         (final_x + width_bottom, ground_y), int(3 * S))

    # 4. Накладываем обрезанную ногу на основную поверхность
    target_surface.blit(temp_surf, (0, 0))


def draw_eye_rhombus(surface, x, y, width, height, pupil_dir):
    # Применяем масштаб к размерам глаза
    w = width * S
    h = height * S
    
    p_top = (x, y - h)
    p_bot = (x, y + h)
    p_left = (x - w, y)
    p_right = (x + w, y)
    
    lineWidth = max(1, int(3 * S))
    pygame.draw.polygon(surface, C_EYE_SCLERA, [p_top, p_right, p_bot, p_left])
    pygame.draw.polygon(surface, BLACK, [p_top, p_right, p_bot, p_left], lineWidth)
    
    scale_eye = 0.65
    iris_w = w * scale_eye
    iris_h = h * scale_eye
    iris_rect = pygame.Rect(x - iris_w, y - iris_h, iris_w * 2, iris_h * 2)
    pygame.draw.ellipse(surface, C_EYE_IRIS, iris_rect)
    
    pupil_offset_x = pupil_dir[0] * (w * 0.3)
    pupil_offset_y = pupil_dir[1] * (h * 0.3)
    
    pupil_w = max(2, 6 * S)
    pupil_h = iris_h * 0.7
    pupil_rect = pygame.Rect(0, 0, pupil_w, pupil_h)
    pupil_rect.center = (x + pupil_offset_x, y + pupil_offset_y)
    pygame.draw.ellipse(surface, C_EYE_PUPIL, pupil_rect)
    
    glow_size = max(1, int(2 * S))
    pygame.draw.circle(surface, C_EYE_GLOW, (int(x + pupil_offset_x + 3*S), int(y + pupil_offset_y - 4*S)), glow_size)

def draw_ground_shadow(surface, x, y, width):
    w = width * S
    h = 6 * S
    shadow_rect = pygame.Rect(x - w - 2*S, y - h/2, w * 2 + 4*S, h)
    s = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(s, SHADOW_COLOR, (0, 0, shadow_rect.width, shadow_rect.height))
    surface.blit(s, shadow_rect.topleft)

def draw_brain_monster(surface, pos, time_tick, look_target_pos, brain_img=None):
    x, y = pos
    
    # Уровень земли - это y координата позиции
    ground_level = y
    
    # Базовая высота тела от земли (масштабированная)
    # В оригинале было около 200 пикселей вверх от земли до центра мозга
    base_height_offset = 200 * S 
    draw_y_center = y - base_height_offset

    # --- АНИМАЦИЯ (амплитуды масштабируются) ---
    breath = math.sin(time_tick * 0.05) * (2 * S)
    body_sway = math.sin(time_tick * 0.02) * (1.5 * S)
    leg_wobble = math.sin(time_tick * 0.08) * (6 * S)
    
    # Взгляд
    if look_target_pos:
        # Глаз находится примерно в центре масс по Y
        eye_center_pos = pygame.math.Vector2(x, draw_y_center)
        aim_vec = look_target_pos - eye_center_pos
        if aim_vec.length_squared() > 0:
            aim_vec = aim_vec.normalize()
            pupil_dir = (aim_vec.x, aim_vec.y)
        else:
            pupil_dir = (0, 0)
    else:
        look_x = math.sin(time_tick * 0.02)
        look_y = math.cos(time_tick * 0.03) * 0.3
        pupil_dir = (look_x, look_y)

    # --- РАЗМЕРЫ (ВСЕ МАСШТАБИРУЕТСЯ НА S) ---
    w_rim = (110 * S) + breath
    h_rim = 40 * S
    rim_thickness = 10 * S
    w_body_top = (100 * S) + breath
    w_body_bot = (50 * S) + breath
    h_body = 120 * S
    
    # Верх и низ фиолетового тела
    body_y_start = draw_y_center - h_body / 2 + (20 * S) # Чуть смещаем вверх относительно центра
    body_y_end = body_y_start + h_body
    
    leg_thin = 8 * S
    leg_thick = 25 * S
    lineWidth = max(1, int(3 * S))
    outline_thin = leg_thin + lineWidth
    outline_thick = leg_thick + lineWidth

    # Смещение ног от центра
    leg_offset_x = 90 * S
    knee_offset_x = 80 * S
    knee_offset_y = 40 * S

    # 1. ТЕНИ
    draw_ground_shadow(surface, x, ground_level, leg_thick)
    draw_ground_shadow(surface, x - leg_offset_x, ground_level, leg_thick)
    draw_ground_shadow(surface, x + leg_offset_x, ground_level, leg_thick)

    # 2. ЗАДНЯЯ НОГА
    p0_back = (x + body_sway, body_y_end)
    p1_back = (x + body_sway + leg_wobble, body_y_end + knee_offset_y)
    p2_back = (x, ground_level)
    
    draw_clipped_leg(surface, p0_back, p1_back, p2_back, outline_thin, outline_thick, BLACK, ground_level, True)
    draw_clipped_leg(surface, p0_back, p1_back, p2_back, leg_thin, leg_thick, PURPLE_DARK, ground_level)

    # 3. ТЕЛО
    p1 = (x - w_body_top / 2 + body_sway, body_y_start)
    p2 = (x + w_body_top / 2 + body_sway, body_y_start)
    p3 = (x + w_body_bot / 2 + body_sway, body_y_end)
    p4 = (x - w_body_bot / 2 + body_sway, body_y_end)
    
    pygame.draw.polygon(surface, PURPLE_MID, [p1, p2, p3, p4])
    pygame.draw.line(surface, BLACK, p1, p4, lineWidth) 
    pygame.draw.line(surface, BLACK, p2, p3, lineWidth) 
    pygame.draw.line(surface, BLACK, p3, p4, lineWidth) 

    # 4. ГЛАЗ (размеры передаем оригинальные, функция сама отмасштабирует)
    eye_x = x + body_sway
    eye_y = body_y_start + h_body * 0.5 
    draw_eye_rhombus(surface, eye_x, eye_y, 28, 42, pupil_dir)

    # 5. ГОЛОВА (ОБОД и МОЗГ)
    # Центр головы чуть выше начала тела
    head_y = body_y_start - (10 * S)

    outer_rect = pygame.Rect(x - w_rim / 2 + body_sway, head_y - h_rim / 2, w_rim, h_rim)
    w_hole = w_rim - (rim_thickness * 2)
    h_hole = h_rim - (rim_thickness * 1.5)
    inner_rect = pygame.Rect(x - w_hole / 2 + body_sway, head_y - h_hole / 2, w_hole, h_hole)

    # Задний фон головы
    pygame.draw.ellipse(surface, PURPLE_MID, outer_rect) 
    pygame.draw.ellipse(surface, BLACK, outer_rect, lineWidth)
    pygame.draw.ellipse(surface, PURPLE_DARK, inner_rect)
    pygame.draw.ellipse(surface, BLACK, inner_rect, max(1, int(2*S)))

    # Мозг
    if brain_img:
        # Картинка уже должна быть отмасштабирована при загрузке
        brain_x = x + body_sway - (brain_img.get_width() / 2)
        # Смещение мозга вверх от обода
        brain_y = head_y - (40 * S) 
        surface.blit(brain_img, (brain_x, brain_y))
    else:
        # Заглушка тоже масштабируется
        pygame.draw.circle(surface, (200, 100, 100), (int(x+body_sway), int(head_y - 20*S)), int(40*S))

    # Передняя часть обода
    start_angle = math.pi
    stop_angle = 2 * math.pi
    pygame.draw.arc(surface, PURPLE_MID, outer_rect, start_angle, stop_angle, int(rim_thickness))
    pygame.draw.arc(surface, BLACK, outer_rect, start_angle, stop_angle, lineWidth)

    # 6. ПЕРЕДНИЕ НОГИ
    # Левая
    l_p0 = (x - w_body_bot/2 + body_sway + (5*S), body_y_end - (5*S))
    l_p1 = (x - knee_offset_x + body_sway - leg_wobble, body_y_end + knee_offset_y) 
    l_p2 = (x - leg_offset_x, ground_level)
    
    draw_clipped_leg(surface, l_p0, l_p1, l_p2, outline_thin, outline_thick, BLACK, ground_level, True)
    draw_clipped_leg(surface, l_p0, l_p1, l_p2, leg_thin, leg_thick, PURPLE_MID, ground_level)

    # Правая
    r_p0 = (x + w_body_bot/2 + body_sway - (5*S), body_y_end - (5*S))
    r_p1 = (x + knee_offset_x + body_sway + leg_wobble, body_y_end + knee_offset_y)
    r_p2 = (x + leg_offset_x, ground_level)
    
    draw_clipped_leg(surface, r_p0, r_p1, r_p2, outline_thin, outline_thick, BLACK, ground_level, True)
    draw_clipped_leg(surface, r_p0, r_p1, r_p2, leg_thin, leg_thick, PURPLE_MID, ground_level)