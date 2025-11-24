import pygame
import math
from .core import solve_ik_2joint, draw_organic_polygon, draw_bone_segment

# --- ПАЛИТРА ---
SKIN_PALE = (245, 240, 250)
SKIN_SHADE = (200, 190, 210)
CLOTH_MAIN = (25, 20, 30) 
CLOTH_ACCENT = (140, 10, 40) 
GOLD = (200, 180, 50)
HAIR_COLOR = (15, 15, 20)

# *** ИЗМЕНЕНИЕ: Добавлен alpha_mult с значением по умолчанию 1.0 ***
def draw_vampire_advanced(surface, center, angle, walk_cycle, vel_vector, cape_points, alpha_mult=1.0):
    
    # *** НОВОЕ: Устанавливаем общую прозрачность для всей поверхности ***
    # Это позволяет реализовать мигание при неуязвимости.
    alpha_value = int(255 * alpha_mult)
    surface.set_alpha(alpha_value)

    cx, cy = center
    
    facing_right = 90 < angle < 270
    dir_sk = 1 if facing_right else -1
    is_moving = vel_vector.length() > 0.1
    
    # --- 1. СКЕЛЕТ ---
    bounce = abs(math.sin(walk_cycle)) * 4 if is_moving else 0
    
    # Точки привязки
    hip_pos = pygame.math.Vector2(cx, cy - 20 + bounce)
    waist_pos = hip_pos + pygame.math.Vector2(0, -12)
    chest_pos = waist_pos + pygame.math.Vector2(0, -18)
    neck_base = chest_pos + pygame.math.Vector2(0, -8)
    head_pos = neck_base + pygame.math.Vector2(2 * dir_sk, -10) 
    
    shoulder_w = 14
    shoulder_l = chest_pos + pygame.math.Vector2(-shoulder_w, 0)
    shoulder_r = chest_pos + pygame.math.Vector2(shoulder_w, 0)

    # --- 2. НОГИ (IK) ---
    ground_y = cy + 30
    foot_targets = []
    phases = [walk_cycle, walk_cycle + math.pi]
    
    for phase in phases:
        c_x, c_y = math.cos(phase), math.sin(phase)
        step_x = c_x * 24 * dir_sk
        lift = max(0, -c_y) * 12
        target = pygame.math.Vector2(hip_pos.x + step_x, ground_y - lift)
        if is_moving: target.x -= vel_vector.x * 3
        foot_targets.append(target)
        
    if facing_right:
        idx_back, idx_front = 1, 0
        shoulder_front, shoulder_back = shoulder_l, shoulder_r
    else:
        idx_back, idx_front = 0, 1
        shoulder_front, shoulder_back = shoulder_r, shoulder_l

    # ========= СЛОИ ОТРИСОВКИ (Z-ORDER) =========

    # 1. Задняя нога
    _draw_leg(surface, hip_pos, foot_targets[idx_back], 20, 22, facing_right, is_back=True)

    # 2. Плащ (Задний план)
    if len(cape_points) > 2:
        cape_poly = []
        cape_poly.append(shoulder_l + pygame.math.Vector2(0, -5))
        cape_poly.append(shoulder_r + pygame.math.Vector2(0, -5))
        for i, p in enumerate(cape_points):
            w = 20 * (1 - (i/len(cape_points))**0.7)
            cape_poly.append((p.x + w, p.y))
        for i in range(len(cape_points)-1, -1, -1):
            p = cape_points[i]
            w = 20 * (1 - (i/len(cape_points))**0.7)
            cape_poly.append((p.x - w, p.y))
        draw_organic_polygon(surface, (50, 5, 15), cape_poly, (20, 0, 0))

    # 3. ВОРОТНИК (Теперь РИСУЕТСЯ ЗА ГОЛОВОЙ)
    # Это исправляет проблему "черного квадрата" на лице
    col_h = 22
    col_poly = [
        (shoulder_l.x, shoulder_l.y),
        (shoulder_l.x + 4, shoulder_l.y - col_h), 
        (shoulder_r.x - 4, shoulder_r.y - col_h), 
        (shoulder_r.x, shoulder_r.y)
    ]
    draw_organic_polygon(surface, CLOTH_MAIN, col_poly)
    # Красная подкладка воротника
    inner_col = [
        (shoulder_l.x + 2, shoulder_l.y),
        (shoulder_l.x + 5, shoulder_l.y - col_h + 2), 
        (shoulder_r.x - 5, shoulder_r.y - col_h + 2), 
        (shoulder_r.x - 2, shoulder_r.y)
    ]
    draw_organic_polygon(surface, (100, 10, 30), inner_col)

    # 4. Торс и Жилет
    pelvis_poly = [
        (hip_pos.x - 9, hip_pos.y), (hip_pos.x + 9, hip_pos.y),
        (waist_pos.x + 10, waist_pos.y), (waist_pos.x - 10, waist_pos.y)
    ]
    draw_organic_polygon(surface, CLOTH_MAIN, pelvis_poly)
    
    torso_poly = [
        (waist_pos.x - 10, waist_pos.y), (waist_pos.x + 10, waist_pos.y),
        (shoulder_r.x, shoulder_r.y), (shoulder_l.x, shoulder_l.y)
    ]
    draw_organic_polygon(surface, CLOTH_MAIN, torso_poly)
    
    vest_poly = [
        (waist_pos.x, waist_pos.y + 5),
        (shoulder_r.x - 5, shoulder_r.y + 2),
        (shoulder_l.x + 5, shoulder_l.y + 2)
    ]
    draw_organic_polygon(surface, CLOTH_ACCENT, vest_poly)

    # 5. Голова и Лицо (Теперь рисуется ПОВЕРХ воротника)
    draw_bone_segment(surface, neck_base, head_pos, SKIN_PALE, 7, 7)
    _draw_anime_head(surface, head_pos, angle, dir_sk)

    # 6. Передняя нога
    _draw_leg(surface, hip_pos, foot_targets[idx_front], 20, 22, facing_right, is_back=False)

    # 7. Руки
    arm_back_angle = math.radians(100 + math.sin(walk_cycle)*20)
    _draw_arm(surface, shoulder_back, arm_back_angle, 14, 13, CLOTH_MAIN, SKIN_PALE)
    
    aim_rad = math.radians(angle - 5*dir_sk)
    _draw_arm(surface, shoulder_front, aim_rad, 14, 13, CLOTH_MAIN, SKIN_PALE, has_magic=True)

def _draw_anime_head(surface, center, angle, dir_sk):
    # Контур лица
    chin_y = 8
    width = 8
    height_up = 9
    
    face_poly = [
        (center.x - width * dir_sk, center.y - height_up),
        (center.x + (width-2) * dir_sk, center.y - height_up),
        (center.x + (width+1) * dir_sk, center.y),
        (center.x + 2 * dir_sk, center.y + chin_y),
        (center.x - (width-2) * dir_sk, center.y + chin_y - 3),
        (center.x - width * dir_sk, center.y)
    ]
    draw_organic_polygon(surface, SKIN_PALE, face_poly, SKIN_SHADE)
    
    # Черты лица (если не спиной)
    if not (80 < angle < 100 or 260 < angle < 280):
        face_off = pygame.math.Vector2(3 * dir_sk, 0)
        eye_pos = center + face_off + pygame.math.Vector2(0, -1)
        
        # Глаз
        eye_rect = [
            (eye_pos.x - 1*dir_sk, eye_pos.y - 3),
            (eye_pos.x + 3*dir_sk, eye_pos.y - 1),
            (eye_pos.x - 1*dir_sk, eye_pos.y + 1)
        ]
        pygame.draw.polygon(surface, (240, 240, 240), eye_rect)
        pygame.draw.circle(surface, (200, 0, 0), (int(eye_pos.x + 1*dir_sk), int(eye_pos.y - 1)), 1)
        
        # Волосы (Челка)
        hair_front = [
            (center.x - 8*dir_sk, center.y - 8),
            (center.x + 6*dir_sk, center.y - 6),
            (center.x + 8*dir_sk, center.y + 2),
            (center.x + 2*dir_sk, center.y - 4)
        ]
        draw_organic_polygon(surface, HAIR_COLOR, hair_front)

    # Волосы сзади
    hair_back = [
        (center.x - 6*dir_sk, center.y - 8),
        (center.x - 10*dir_sk, center.y + 6),
        (center.x - 4*dir_sk, center.y + 14),
        (center.x + 4*dir_sk, center.y - 2)
    ]
    draw_organic_polygon(surface, HAIR_COLOR, hair_back)

def _draw_leg(surface, hip, target, l1, l2, facing_right, is_back):
    knee, ankle = solve_ik_2joint(hip, target, l1, l2, bend_right=facing_right)
    col = CLOTH_MAIN if not is_back else (15, 10, 15)
    draw_bone_segment(surface, hip, knee, col, 9, 7)
    draw_bone_segment(surface, knee, ankle, col, 7, 5)
    boot_toe = ankle + pygame.math.Vector2(6 if facing_right else -6, 2)
    pygame.draw.polygon(surface, (10, 10, 10), [(ankle.x-2, ankle.y), (ankle.x+2, ankle.y), (boot_toe.x, boot_toe.y+2), (boot_toe.x, boot_toe.y-2)])

def _draw_arm(surface, shoulder, angle, l1, l2, color, skin, has_magic=False):
    elbow = shoulder + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * l1
    hand_angle = angle + math.radians(15)
    hand = elbow + pygame.math.Vector2(math.cos(hand_angle), math.sin(hand_angle)) * l2
    draw_bone_segment(surface, shoulder, elbow, color, 8, 6)
    draw_bone_segment(surface, elbow, hand, color, 6, 4)
    pygame.draw.circle(surface, skin, (int(hand.x), int(hand.y)), 3)
    if has_magic:
        pygame.draw.circle(surface, (255, 50, 50), (int(hand.x), int(hand.y)), 4)