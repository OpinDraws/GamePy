import pygame
import math
from .core import get_bezier_points, draw_alpha_polygon, draw_alpha_circle

# --- Палитра ---
C_SKIN = (250, 240, 235)
C_SKIN_SHADOW = (220, 200, 195)
C_HAIR_BASE = (245, 245, 255) 
C_HAIR_SHADOW = (205, 205, 220)
C_ARMOR_DARK = (60, 60, 75)
C_ARMOR_LIGHT = (100, 100, 115)
C_GOLD_HALO = (255, 220, 50)
C_INK = (30, 25, 40)

def draw_bezier_line(surface, color, p1, p2, control, width=2):
    """Рисует плавную линию Безье"""
    points = get_bezier_points(p1, p2, control, segments=20)
    pygame.draw.lines(surface, color, False, [(p.x, p.y) for p in points], width)

def draw_archangel_portrait(surface, center, size=100):
    cx, cy = center
    # Базовые параметры
    head_c = pygame.math.Vector2(cx, cy + size * 0.05)
    scale = size / 75.0 

    # --- ФОН И НИМБ ---
    pygame.draw.circle(surface, (30, 30, 40), center, size)
    pygame.draw.circle(surface, (70, 70, 90), center, size, 3)
    
    halo_rect = pygame.Rect(0, 0, 85 * scale, 12 * scale)
    halo_rect.center = (head_c.x, head_c.y - 38 * scale)
    pygame.draw.ellipse(surface, C_GOLD_HALO, halo_rect, 2)

    # ==========================================
    # 1. ЗАДНИЕ ВОЛОСЫ (Фон)
    # ==========================================
    bh_top_w = 50
    bh_bottom_w = 70
    back_hair_poly = [
        head_c + pygame.math.Vector2(-bh_top_w, -35) * scale,
        head_c + pygame.math.Vector2(-bh_bottom_w, 85) * scale,
        head_c + pygame.math.Vector2(bh_bottom_w, 85) * scale,
        head_c + pygame.math.Vector2(bh_top_w, -35) * scale,
    ]
    draw_alpha_polygon(surface, C_HAIR_SHADOW, back_hair_poly)

    # ==========================================
    # 2. ШЕЯ И ДОСПЕХИ
    # ==========================================
    neck_rect = pygame.Rect(0, 0, 16 * scale, 30 * scale)
    neck_rect.center = (head_c.x, head_c.y + 40 * scale)
    pygame.draw.rect(surface, C_SKIN_SHADOW, neck_rect)
    
    # Воротник (ИСПРАВЛЕНО: добавлены Vector2)
    collar_pts = [
        head_c + pygame.math.Vector2(-20, 38) * scale, 
        head_c + pygame.math.Vector2(-30, 5) * scale, 
        head_c + pygame.math.Vector2(30, 5) * scale, 
        head_c + pygame.math.Vector2(20, 38) * scale
    ]
    draw_alpha_polygon(surface, C_ARMOR_LIGHT, collar_pts)
    pygame.draw.lines(surface, C_INK, False, [(p.x, p.y) for p in collar_pts[:3]], 2)

    # ==========================================
    # 3. ЛИЦО
    # ==========================================
    chin_offset = pygame.math.Vector2(0, 46)
    jaw_start_x, jaw_start_y = 24, 8
    ctrl_x, ctrl_y = 14, 42 

    P_chin = head_c + chin_offset * scale
    P_start_l = head_c + pygame.math.Vector2(-jaw_start_x, jaw_start_y) * scale
    P_ctrl_l  = head_c + pygame.math.Vector2(-ctrl_x, ctrl_y) * scale
    P_start_r = head_c + pygame.math.Vector2(jaw_start_x, jaw_start_y) * scale
    P_ctrl_r  = head_c + pygame.math.Vector2(ctrl_x, ctrl_y) * scale

    forehead_taper = 0.9 
    forehead_h = -30
    P_forehead_l = head_c + pygame.math.Vector2(-jaw_start_x * forehead_taper, forehead_h) * scale
    P_forehead_r = head_c + pygame.math.Vector2(jaw_start_x * forehead_taper, forehead_h) * scale

    jaw_line_l = get_bezier_points(P_start_l, P_chin, P_ctrl_l, segments=15)
    jaw_line_r = get_bezier_points(P_chin, P_start_r, P_ctrl_r, segments=15)
    
    face_poly = jaw_line_l + jaw_line_r + [P_forehead_r, P_forehead_l]
    draw_alpha_polygon(surface, C_SKIN, face_poly)
    pygame.draw.lines(surface, C_INK, False, [(p.x, p.y) for p in jaw_line_l + jaw_line_r], 2)

    # ЧЕРТЫ ЛИЦА
    eye_y = 14
    for side in [-1, 1]:
        p1 = head_c + pygame.math.Vector2(6 * side, eye_y) * scale
        p2 = head_c + pygame.math.Vector2(16 * side, eye_y) * scale
        pc = head_c + pygame.math.Vector2(11 * side, eye_y + 5) * scale
        draw_bezier_line(surface, C_INK, p1, p2, pc, 2)

    nose_pos = head_c + pygame.math.Vector2(0, 25) * scale
    draw_alpha_circle(surface, C_SKIN_SHADOW, nose_pos, 1.5 * scale)
    
    # Линия рта (ИСПРАВЛЕНО: добавлены Vector2)
    pygame.draw.line(surface, C_INK, 
                     head_c + pygame.math.Vector2(-3, 35) * scale, 
                     head_c + pygame.math.Vector2(3, 35) * scale, 1)

    # ==========================================
    # 4. ПЕРЕДНИЕ ВОЛОСЫ
    # ==========================================
    
    # Боковые пряди
    hime_start_y = -32
    hime_tip = pygame.math.Vector2(32, 65)
    hime_ctrl = pygame.math.Vector2(58, 5)

    for side in [-1, 1]:
        start_pt = head_c + pygame.math.Vector2(5 * side, hime_start_y) * scale
        tip_pt = head_c + pygame.math.Vector2(hime_tip.x * side, hime_tip.y) * scale
        ctrl_pt = head_c + pygame.math.Vector2(hime_ctrl.x * side, hime_ctrl.y) * scale
        
        outer_curve = get_bezier_points(start_pt, tip_pt, ctrl_pt, segments=20)
        
        template_pt = head_c + pygame.math.Vector2(22 * side, -5) * scale
        hair_poly = outer_curve + [template_pt, start_pt]
        
        draw_alpha_polygon(surface, C_HAIR_BASE, hair_poly)
        pygame.draw.lines(surface, C_INK, False, [(p.x, p.y) for p in outer_curve], 2)

    # Челка
    bang_start = head_c + pygame.math.Vector2(0, -38) * scale
    bang_end_vec = pygame.math.Vector2(22, -2)
    bang_ctrl_vec = pygame.math.Vector2(12, -18)

    for side in [-1, 1]:
        end_pt = head_c + pygame.math.Vector2(bang_end_vec.x * side, bang_end_vec.y) * scale
        ctrl_pt = head_c + pygame.math.Vector2(bang_ctrl_vec.x * side, bang_ctrl_vec.y) * scale
        draw_bezier_line(surface, C_INK, bang_start, end_pt, ctrl_pt, 2)