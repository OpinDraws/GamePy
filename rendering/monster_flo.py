import pygame
import math
import random

# ==========================================
# --- ИМПОРТЫ И ЗАГЛУШКИ ---
# ==========================================
try:
    # Используем правильное имя аргумента outline_color
    from .core import draw_organic_polygon, draw_alpha_circle, get_bezier_points, draw_alpha_polygon
except ImportError:
    # Важно добавить заглушку для draw_alpha_polygon, которая будет нужна для стоп.
    def draw_alpha_polygon(surface, color, points):
        if len(color) == 4: color = color[:3] # Без альфы, так как нет информации о ней
        if len(points) < 3: return
        pygame.draw.polygon(surface, color, points)

    def draw_alpha_circle(surface, color, center, radius):
        s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (int(radius), int(radius)), int(radius))
        surface.blit(s, (int(center[0]-radius), int(center[1]-radius)))

    # ИСПРАВЛЕНО: Теперь заглушка принимает outline_color
    def draw_organic_polygon(surface, color, points, outline_color=None):
        if len(points) < 3: return
        pygame.draw.polygon(surface, color, points)
        if outline_color:
            pygame.draw.aalines(surface, outline_color, True, points)

    def get_bezier_points(p0, p1, control, segments=15):
        points = []
        # ПРИМЕЧАНИЕ: В core.py этот код уже преобразован для Vector2.
        # В этой заглушке оставим кортежи для совместимости с исходным monster_flo.
        for i in range(segments + 1):
            t = i / segments
            x = (1-t)**2 * p0[0] + 2*(1-t)*t * control[0] + t**2 * p1[0]
            y = (1-t)**2 * p0[1] + 2*(1-t)*t * control[1] + t**2 * p1[1]
            points.append(pygame.math.Vector2(x, y)) # ДОБАВЛЕНО: возвращаем Vector2 для совместимости с остальным кодом
        return points

# ==========================================
# --- МАТЕМАТИКА ---
# ==========================================

def get_cubic_point(t, p0, p1, p2, p3):
    u = 1 - t
    tt, uu = t * t, u * u
    uuu, ttt = uu * u, tt * t
    x = uuu * p0[0] + 3 * uu * t * p1[0] + 3 * u * tt * p2[0] + ttt * p3[0]
    y = uuu * p0[1] + 3 * uu * t * p1[1] + 3 * u * tt * p2[1] + ttt * p3[1]
    return pygame.math.Vector2(x, y)

def get_cubic_derivative(t, p0, p1, p2, p3):
    u = 1 - t
    p0, p1, p2, p3 = map(pygame.math.Vector2, [p0, p1, p2, p3])
    tangent = 3*u*u*(p1-p0) + 6*u*t*(p2-p1) + 3*t*t*(p3-p2)
    return tangent

def normalize_vec(vec):
    if vec.length_squared() < 0.001: return pygame.math.Vector2(0, 1)
    return vec.normalize()
    
def generate_segment_geometry(start, end, width_start, width_end):
    vec = pygame.math.Vector2(end) - pygame.math.Vector2(start)
    length = vec.length()
    if length < 0.1: return []
    
    normal = normalize_vec(pygame.math.Vector2(-vec.y, vec.x))
    
    p1 = pygame.math.Vector2(start) + normal * width_start * 0.5
    p2 = pygame.math.Vector2(start) - normal * width_start * 0.5
    p3 = pygame.math.Vector2(end) - normal * width_end * 0.5
    p4 = pygame.math.Vector2(end) + normal * width_end * 0.5
    
    return [p1, p2, p3, p4]

def draw_simple_segment(surface, color, start, end, w_start, w_end, outline_color=None):
    """
    Рисует простой заливной сегмент (используется для голени и бедер).
    """
    poly = generate_segment_geometry(start, end, w_start, w_end)
    if not poly: return
    points = [(p.x, p.y) for p in poly]
    pygame.draw.polygon(surface, color, points)
    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, points)

def generate_strand_geometry(p0, p1, p2, p3, max_width, taper_start=1.0, taper_end=0.6, segments=20):
    left_side = []
    right_side = []

    for i in range(segments + 1):
        t = i / segments
        center_pos = get_cubic_point(t, p0, p1, p2, p3)
        tangent = get_cubic_derivative(t, p0, p1, p2, p3)
        normal = normalize_vec(pygame.math.Vector2(-tangent.y, tangent.x))
        width_multiplier = taper_start * (1-t) + taper_end * t
        current_width = max_width * width_multiplier
        left_side.append(center_pos + normal * current_width * 0.5)
        right_side.append(center_pos - normal * current_width * 0.5)

    return left_side + right_side[::-1]

def draw_organic_segment(surface, color, p0, p1, p2, p3, max_width, taper_start=1.0, taper_end=0.6, outline_color=None):
    poly = generate_strand_geometry(p0, p1, p2, p3, max_width, taper_start, taper_end)
    poly_points = [(p.x, p.y) for p in poly]
    pygame.draw.polygon(surface, color, poly_points)
    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, poly_points)
    return poly_points

# ==========================================
# --- ПАЛИТРА (Для функций монстра) ---
# ==========================================
C_SKIN_BASE = (60, 170, 160)
C_SKIN_SHADOW = (40, 120, 110)
C_EYE_GLOW = (255, 190, 50)
C_OUTLINE = (15, 20, 35)
C_JOINT = (40, 120, 110)

# ==========================================
# --- КОМПОНЕНТЫ МОНСТРА (ОБНОВЛЕНЫ ДЛЯ АРХАНГЕЛА) ---
# ==========================================

# В файле monster_flo.py

# В файле monster_flo.py


# В файле monster_flo.py


# ==========================================
# --- НОВАЯ ФУНКЦИЯ КАПЮШОНА (Вставьте в конец monster_flo.py) ---
# ==========================================

# В файле monster_flo.py (замените старую draw_archangel_hood)

def draw_archangel_hood(surface, head_center, shoulder_l_pos, shoulder_r_pos, color_base, color_shadow, outline_color):
    """
    Рисует капюшон с пятиугольным верхом, плотно сидящий по голове.
    Низ капюшона стыкуется с началом наплечных платков.
    """
    cx, head_y = head_center
    
    # --- НАСТРОЙКИ ГЕОМЕТРИИ ---
    
    # 1. ВЕРХ (Низкая посадка)
    # Волосы заканчиваются примерно на head_y - 12. Капюшон чуть выше.
    peak_y = head_y - 18 
    
    # 2. УГЛЫ "ПЯТИУГОЛЬНИКА" (Макушка)
    # Точки, где капюшон начинает расширяться в стороны (виски/верх ушей)
    corner_top_y = head_y - 8
    corner_top_w = 20  # Ширина "крыши" капюшона
    
    # 3. СЕРЕДИНА (Самая широкая часть)
    # Уровень щек/ушей
    mid_y = head_y + 4
    mid_w = 29  # Достаточно широко, чтобы обрамить лицо
    
    # 4. НИЗ (Стык с платками)
    # Шея/начало плеч. Здесь капюшон должен уйти под платок.
    bot_y = head_y + 26 
    bot_w = 10  # Узкое горло
    
    # Цвета (можно взять из аргументов или глобальные)
    C_BASE = color_base
    C_BACK = color_shadow  # Темная изнанка
    C_LINE = outline_color

    # ==================================================
    # 1. ЗАДНЯЯ ЧАСТЬ (ТЕМНАЯ ПОДЛОЖКА)
    # ==================================================
    # Рисуем тень внутри капюшона, обрамляющую лицо
    
    face_frame_w = 18 # Насколько узко тень подходит к лицу
    
    shadow_poly = [
        (cx, peak_y + 5), # Верхняя точка тени
        (cx - face_frame_w, mid_y),
        (cx - bot_w + 2, bot_y),
        (cx + bot_w - 2, bot_y),
        (cx + face_frame_w, mid_y)
    ]
    # Сглаживаем низ тени
    pygame.draw.polygon(surface, C_BACK, shadow_poly)


    # ==================================================
    # 2. ОСНОВНАЯ ФОРМА (БЕЛАЯ ТКАНЬ)
    # ==================================================
    
    # Определяем ключевые точки (Vector2 для удобства кривых)
    p_peak = pygame.math.Vector2(cx, peak_y)
    
    p_corner_l = pygame.math.Vector2(cx - corner_top_w, corner_top_y)
    p_corner_r = pygame.math.Vector2(cx + corner_top_w, corner_top_y)
    
    p_side_l = pygame.math.Vector2(cx - mid_w, mid_y)
    p_side_r = pygame.math.Vector2(cx + mid_w, mid_y)
    
    p_bot_l = pygame.math.Vector2(cx - bot_w, bot_y)
    p_bot_r = pygame.math.Vector2(cx + bot_w, bot_y)

    # --- ГЕНЕРАЦИЯ КОНТУРА ---
    
    # А. Верхняя часть (Пятиугольная крыша) - ПРЯМЫЕ ЛИНИИ
    # От левого угла к пику и к правому углу.
    roof_points = [p_corner_l, p_peak, p_corner_r]
    
    # Б. Бока (Изогнутые)
    # От правого угла через бок к низу
    # Контрольная точка для плавного расширения
    ctrl_side_r = (p_corner_r + p_side_r) * 0.5 + pygame.math.Vector2(2, 0)
    curve_side_r_upper = get_bezier_points(p_corner_r, p_side_r, ctrl_side_r, 5)
    
    # Сужение к низу (к шее)
    curve_side_r_lower = get_bezier_points(p_side_r, p_bot_r, p_side_r + pygame.math.Vector2(0, 10), 5)
    
    # В. Низ (Стык)
    # Небольшая дуга внизу
    curve_bottom = get_bezier_points(p_bot_r, p_bot_l, pygame.math.Vector2(cx, bot_y + 3), 4)

    # Г. Левая сторона (Зеркально)
    curve_side_l_lower = get_bezier_points(p_bot_l, p_side_l, p_side_l + pygame.math.Vector2(0, 10), 5)
    
    ctrl_side_l = (p_corner_l + p_side_l) * 0.5 + pygame.math.Vector2(-2, 0)
    curve_side_l_upper = get_bezier_points(p_side_l, p_corner_l, ctrl_side_l, 5)
    
    # Собираем все точки
    hood_poly_vec = (roof_points + 
                     curve_side_r_upper[1:] + 
                     curve_side_r_lower[1:] + 
                     curve_bottom[1:] + 
                     curve_side_l_lower[1:] + 
                     curve_side_l_upper[1:])
                     
    hood_points = [(p.x, p.y) for p in hood_poly_vec]

    # --- ОТРИСОВКА ---
    draw_organic_polygon(surface, C_BASE, hood_points)
    
    # Контур (Outline)
    pygame.draw.aalines(surface, C_LINE, True, hood_points)
    
    # --- ДЕТАЛИ (СКЛАДКИ) ---
    # Небольшая складка от пика вниз (шов капюшона)
    pygame.draw.line(surface, C_BACK, (cx, peak_y), (cx, peak_y + 6), 1)
    
    # Складки по бокам у шеи (где ткань собирается)
    fold_l_start = p_bot_l + pygame.math.Vector2(-2, -5)
    fold_l_end = p_bot_l + pygame.math.Vector2(5, 0)
    pygame.draw.line(surface, C_BACK, fold_l_start.xy, fold_l_end.xy, 1)

    fold_r_start = p_bot_r + pygame.math.Vector2(2, -5)
    fold_r_end = p_bot_r + pygame.math.Vector2(-5, 0)
    pygame.draw.line(surface, C_BACK, fold_r_start.xy, fold_r_end.xy, 1)


def draw_shoulder_shawl(surface, neck_pos, shoulder_pos, elbow_pos, is_left, outline_color):
    """
    Рисует накидку.
    Исправлено:
    - Убран острый угол (треугольник).
    - Теперь это одна плавная дуга, повторяющая форму плеча.
    - Объем (выпирание) смещен так, чтобы платок выглядел как естественная одежда.
    """
    C_SHAWL_BASE = (245, 250, 255)
    C_SHAWL_SHADOW = (200, 210, 230)
    
    # --- 1. ВЕКТОРЫ ---
    vec_arm = pygame.math.Vector2(elbow_pos) - pygame.math.Vector2(shoulder_pos)
    if vec_arm.length_squared() > 0.01:
        vec_arm = vec_arm.normalize()
    else:
        vec_arm = pygame.math.Vector2(0, 1)

    side_mult = -1 if is_left else 1 
    
    # Перпендикуляр (смотрит "наружу")
    perp = pygame.math.Vector2(vec_arm.y * side_mult, -vec_arm.x * side_mult)

    # =================================================================================
    # === НАСТРОЙКИ ФОРМЫ ===
    # =================================================================================
    
    shawl_length_along = 15.0   # Чуть удлинили, чтобы закрывало дельту
    shawl_offset_out = -2.0     # Кончик спрятан за контур руки
    
    # Ширина арки. 
    # Делаем достаточно большой, чтобы она была "чуть больше плеча"
    width_arch_main = 22.0       
    
    # =================================================================================

    # --- 2. ТОЧКИ ---
    p_neck = pygame.math.Vector2(neck_pos)
    
    # Точка на линии руки
    p_on_arm_line = pygame.math.Vector2(shoulder_pos) + vec_arm * shawl_length_along
    # Конечная точка
    p_end = p_on_arm_line + perp * shawl_offset_out

    # --- 3. КРИВЫЕ (ПЛАВНАЯ ФОРМА ПЛЕЧА) ---
    
    # -- ВЕРХНЯЯ ДУГА (Внешняя) --
    # Мы убрали разделение на две части. Теперь это одна гладкая кривая.
    # Чтобы "опустить угол в самый низ" и убрать остроту:
    # Мы ставим контрольную точку ровно посередине (0.5) или чуть ниже.
    # Это создает идеальную дугу без острых пиков.
    
    ctrl_top = p_neck.lerp(p_end, 0.5) + perp * width_arch_main
    
    # segments=12 для плавности
    curve_top = get_bezier_points(p_neck, p_end, ctrl_top, segments=12)


    # -- НИЖНЯЯ ДУГА (Внутренняя) --
    # Делаем её слегка изогнутой, чтобы у платка был объем (толщина)
    inner_curve_factor = 0.3
    ctrl_inner = p_neck.lerp(p_end, 0.5) + perp * (width_arch_main * inner_curve_factor)
    
    curve_inner = get_bezier_points(p_end, p_neck, ctrl_inner, segments=10)

    # --- 4. ОТРИСОВКА ---
    poly_points = [(p.x, p.y) for p in curve_top + curve_inner]
    
    draw_organic_polygon(surface, C_SHAWL_BASE, poly_points, outline_color=None)
    
    # Тень для объема
    if len(curve_inner) > 2:
        pts_shadow = [(p.x, p.y) for p in curve_inner]
        pygame.draw.aalines(surface, C_SHAWL_SHADOW, False, pts_shadow)

    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, poly_points)



def draw_pear_chest(surface, cx, top_y, bottom_y, width_total, color_base, color_shadow, outline_color, breath=0):
    """
    Отрисовка груди.
    ИЗМЕНЕНИЯ:
    1. cloth_chest_width уменьшен (края ближе к телу).
    2. Добавлен main_sag в генерацию волны (центр ниже).
    """
    def get_cubic_curve(p0, p1, p2, p3, segments=20):
        res = []
        p0, p1, p2, p3 = pygame.math.Vector2(p0), pygame.math.Vector2(p1), pygame.math.Vector2(p2), pygame.math.Vector2(p3)
        for i in range(segments+1):
            t = i / segments
            x = (1-t)**3*p0.x + 3*(1-t)**2*t*p1.x + 3*(1-t)*t**2*p2.x + t**3*p3.x
            y = (1-t)**3*p0.y + 3*(1-t)**2*t*p1.y + 3*(1-t)*t**2*p2.y + t**3*p3.y
            res.append(pygame.math.Vector2(x, y))
        return res
        
    h = bottom_y - top_y
    bounce = breath * 1.5 
    neck_narrowness = 0.6 
    bulb_width = 1.9  
    
    # --- ЛЕВАЯ СТОРОНА (Кожа) ---
    l_start = pygame.math.Vector2(cx - width_total * neck_narrowness+1, top_y-1)
    l_end = pygame.math.Vector2(cx - width_total * 0.4, bottom_y + bounce + 3)
    l_cp1 = pygame.math.Vector2(cx - width_total * 0.15, top_y + h * 0.19)
    l_cp2 = pygame.math.Vector2(cx - width_total * bulb_width+3, bottom_y - h * 0.05 + bounce)
    
    l_outer = get_cubic_curve(l_start, l_cp1, l_cp2, l_end, 20)
    l_inner_start = pygame.math.Vector2(cx - 5, bottom_y - h * 0.05 + bounce - 3)
    l_inner_end = pygame.math.Vector2(cx, top_y + h * 0.2)
    l_inner = get_bezier_points(l_end, l_inner_end, l_inner_start, 10)
    l_poly = [(p.x, p.y) for p in l_outer + l_inner]
    
    # --- ПРАВАЯ СТОРОНА (Кожа) ---
    r_start = pygame.math.Vector2(cx + width_total * neck_narrowness+1, top_y-1)
    r_end = pygame.math.Vector2(cx + width_total * 0.4, bottom_y + bounce + 3)
    r_cp1 = pygame.math.Vector2(cx + width_total * 0.15, top_y + h * 0.19)
    r_cp2 = pygame.math.Vector2(cx + width_total * bulb_width+3, bottom_y - h * 0.05 + bounce)
    
    r_outer = get_cubic_curve(r_start, r_cp1, r_cp2, r_end, 20)
    r_inner_start = pygame.math.Vector2(cx +5, bottom_y - h * 0.05 + bounce - 3)
    r_inner_end = pygame.math.Vector2(cx, top_y + h * 0.2)
    r_inner = get_bezier_points(r_end, r_inner_end, r_inner_start, 10)
    r_poly = [(p.x, p.y) for p in r_outer + r_inner]
    
    # ==================================================
    # === СЛОЙ 1: КОЖА ===
    # ==================================================
    pygame.draw.polygon(surface, color_base, l_poly)
    pygame.draw.polygon(surface, color_base, r_poly)
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in l_outer])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in r_outer])
    pygame.draw.line(surface, color_shadow, (cx, bottom_y - h * 0.5 + bounce), (cx, bottom_y + bounce - 2), 1)

    # ==================================================
    # === СЛОЙ 2: ОДЕЖДА (ПЛАТОК) ===
    # ==================================================
    
    C_CLOTH_WHITE = (245, 250, 255)
    C_CLOTH_SHADOW_TEAL = (200, 210, 230)
    
    cloth_top_y = top_y - 8
    cloth_bottom_y = bottom_y + bounce + 4
    cloth_neck_width = width_total * 0.5
    
    # ИЗМЕНЕНИЕ 1: Ширина уменьшена с 1.4 до 1.25 (края ближе к телу)
    cloth_chest_width = width_total * 1.25 

    p_tl = pygame.math.Vector2(cx - cloth_neck_width, cloth_top_y)
    p_tr = pygame.math.Vector2(cx + cloth_neck_width, cloth_top_y)
    
    # Слегка приподнимаем углы (-4), чтобы центральное провисание выглядело глубже
    p_bl = pygame.math.Vector2(cx - cloth_chest_width, cloth_bottom_y - 4)
    p_br = pygame.math.Vector2(cx + cloth_chest_width, cloth_bottom_y - 4)

    concave_force = 22.0
    ctrl_l = p_tl.lerp(p_bl, 0.5) + pygame.math.Vector2(concave_force, 0)
    ctrl_r = p_tr.lerp(p_br, 0.5) + pygame.math.Vector2(-concave_force, 0)
    
    cloth_side_l = get_bezier_points(p_tl, p_bl, ctrl_l, 12)
    cloth_side_r = get_bezier_points(p_br, p_tr, ctrl_r, 12)

    # --- ВОЛНИСТЫЙ НИЗ (С центральной выемкой) ---
    wave_points = []
    num_wave_points = 15
    start_wave = cloth_side_l[-1]
    end_wave = cloth_side_r[0]
    
    for i in range(num_wave_points + 1):
        t = i / num_wave_points
        base_x = start_wave.x + (end_wave.x - start_wave.x) * t
        base_y = start_wave.y + (end_wave.y - start_wave.y) * t
        
        # 1. Мелкая рябь (немного уменьшили амплитуду, чтобы не мешать основному прогибу)
        ripples = math.sin(t * math.pi * 3) * 2.0 
        
        # ИЗМЕНЕНИЕ 2: Центральное провисание (Main Sag)
        # Синус от 0 до Пи дает дугу. Умножаем на 5.0, чтобы опустить центр вниз.
        main_sag = math.sin(t * math.pi) * 5.0 
        
        final_y = base_y + ripples + main_sag
        
        wave_points.append(pygame.math.Vector2(base_x, final_y))

    cloth_poly_points = cloth_side_l + wave_points[1:-1] + cloth_side_r

    draw_organic_polygon(surface, C_CLOTH_WHITE, [(p.x, p.y) for p in cloth_poly_points])

    pygame.draw.aalines(surface, C_CLOTH_SHADOW_TEAL, False, [(p.x, p.y) for p in cloth_side_l])
    pygame.draw.aalines(surface, C_CLOTH_SHADOW_TEAL, False, [(p.x, p.y) for p in cloth_side_r])
    pygame.draw.aalines(surface, C_CLOTH_SHADOW_TEAL, False, [(p.x, p.y) for p in wave_points])

    # ==================================================
    # === СЛОЙ 3: КОНТУР ГРУДИ ===
    # ==================================================
    pygame.draw.lines(surface, outline_color, False, [(p.x, p.y) for p in l_outer], 1)
    pygame.draw.lines(surface, outline_color, False, [(p.x, p.y) for p in r_outer], 1)


def draw_joint(surface, center, radius, color, outline_color):
    """Отрисовка сустава с кастомными цветами и контуром."""
    pygame.draw.circle(surface, color, (int(center[0]), int(center[1])), int(radius))
    pygame.draw.circle(surface, outline_color, (int(center[0]), int(center[1])), int(radius), 1)
    draw_alpha_circle(surface, (255, 255, 255, 40), (center[0]-2, center[1]-2), 2)

def draw_anatomical_shoulder(surface, center, width, is_left_visual, color, outline_color):
    """
    Рисует маленькое округлое плечо с частичным контуром.
    Контур рисуется только снаружи, чтобы плечо плавно переходило в тело.
    """
    side_mult = 1 if is_left_visual else -1
    cx, cy = center
    
    # Уменьшаем визуальный размер относительно переданной ширины
    # Плечо будет компактным "шариком"
    radius_w = width * 0.5
    radius_h = width * 0.5
    
    # Точки привязки
    # p_top - верх, уходит под трапецию
    p_top = pygame.math.Vector2(cx - (width * 0.1 * side_mult), cy - radius_h * 0.8)
    # p_out - самый внешний край
    p_out = pygame.math.Vector2(cx + (width * 0.4 * side_mult), cy)
    # p_bot - низ, уходит в руку
    p_bot = pygame.math.Vector2(cx, cy + radius_h * 0.9)
    # p_in - внутренняя часть (в подмышке), глубоко внутри
    p_in = pygame.math.Vector2(cx - (width * 0.5 * side_mult), cy + radius_h * 0.2)
    
    # --- ГЕОМЕТРИЯ ---
    # 1. Верхняя внешняя дуга
    ctrl_top = pygame.math.Vector2(p_out.x - (2 * side_mult), p_top.y)
    seg_outer_top = get_bezier_points(p_top, p_out, ctrl_top, 6)
    
    # 2. Нижняя внешняя дуга
    ctrl_bot = pygame.math.Vector2(p_out.x - (2 * side_mult), p_bot.y)
    seg_outer_bot = get_bezier_points(p_out, p_bot, ctrl_bot, 6)
    
    # 3. Замыкание внутри (скрыто заливкой)
    seg_inner = get_bezier_points(p_bot, p_in, pygame.math.Vector2(p_in.x, p_bot.y), 4)
    seg_close = get_bezier_points(p_in, p_top, pygame.math.Vector2(p_in.x, p_top.y), 4)
    
    full_poly = seg_outer_top + seg_outer_bot + seg_inner + seg_close
    poly_points = [(p.x, p.y) for p in full_poly]
    
    # 1. ЗАЛИВКА (Полная форма)
    pygame.draw.polygon(surface, color, poly_points)
    
    # Легкая тень внутри для объема
    shadow_pos = (cx - 1 * side_mult, cy + 1)
    draw_alpha_circle(surface, (0, 0, 0, 15), shadow_pos, width * 0.3)

    # 2. КОНТУР (ТОЛЬКО ВНЕШНИЙ)
    # Мы не рисуем линию по seg_inner и seg_close, чтобы не было "шва" на теле.
    if outline_color:
        # Рисуем только внешнюю дугу
        outer_curve = seg_outer_top + seg_outer_bot
        pygame.draw.lines(surface, outline_color, False, [(p.x, p.y) for p in outer_curve], 1)


# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ГЕОМЕТРИИ ПРЕДПЛЕЧЬЯ ---
def draw_forearm_shape(surface, start, end, color, outline_color, w_upper=10, is_left_visual=True):
    """
    Рисует предплечье.
    Исправлено: Внутренняя и внешняя стороны поменяны местами.
    """
    vec = pygame.math.Vector2(end) - pygame.math.Vector2(start)
    length = vec.length()
    if length < 1: return
    
    # Нормаль всегда смотрит "Влево" относительно вектора руки
    normal = normalize_vec(pygame.math.Vector2(-vec.y, vec.x))
    
    points_side_pos = [] 
    points_side_neg = [] 
    segments = 20
    
    # Настройки (оставляем уменьшенными, как ты просил)
    max_muscle_bulge = 1.5  
    max_flat_bulge = 0.15    
    
    base_thick = 3.0
    start_thick = w_upper / 2

    for i in range(segments + 1):
        t = i / segments
        pos = pygame.math.Vector2(start) + vec * t
        
        start_taper = (1-t) * start_thick + t * base_thick
        end_taper = (1-t) * base_thick + t * 3.5 
        current_base_thick = start_taper * (1-t) + end_taper * t

        # 1. Большая дуга (Мышца)
        if t < 0.8: 
            t_m = t / 0.8
            angle = t_m * math.pi
            val_muscle = math.sin(angle) * max_muscle_bulge * (1.2 - 1.0 * t_m)
        else:
            val_muscle = 0
            
        # 2. Малая дуга (Плоская часть)
        if t < 0.6:
            t_f = t / 0.6
            angle = t_f * math.pi
            val_flat = math.sin(angle) * max_flat_bulge
        else:
            val_flat = 0

        # --- ЗЕРКАЛИРОВАНИЕ (ПОМЕНЯЛИ МЕСТАМИ) ---
        if is_left_visual:
            # БЫЛО: bulge_pos = val_muscle, bulge_neg = val_flat
            # СТАЛО: Наоборот
            bulge_pos = val_flat       # Теперь плоское снаружи (слева)
            bulge_neg = val_muscle     # Теперь мышца внутри (справа)
        else:
            # БЫЛО: bulge_pos = val_flat, bulge_neg = val_muscle
            # СТАЛО: Наоборот
            bulge_pos = val_muscle     # Теперь мышца снаружи (слева для правой руки)
            bulge_neg = val_flat       # Теперь плоское внутри (справа для правой руки)

        offset_pos = normal * (current_base_thick + bulge_pos)
        offset_neg = normal * -(current_base_thick + bulge_neg)
        
        points_side_pos.append(pos + offset_pos)
        points_side_neg.append(pos + offset_neg)
        
    poly = points_side_pos + points_side_neg[::-1]
    
    pygame.draw.polygon(surface, color, [(p.x, p.y) for p in poly])
    
    if outline_color:
        pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in points_side_pos])
        pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in points_side_neg])



def draw_arm_lower_humanoid(surface, elbow, wrist, is_left_visual, forearm_strength_factor, color_base, outline_color):
    """
    Просто вызывает отрисовку формы, передавая флаг зеркалирования.
    """
    wrist_r = 3.5
    vec_lower = pygame.math.Vector2(wrist) - pygame.math.Vector2(elbow)
    
    # Начинаем от локтя
    lower_start = pygame.math.Vector2(elbow) 
    lower_end = pygame.math.Vector2(wrist) - vec_lower.normalize() * (wrist_r - 1)

    # Передаем is_left_visual для переключения выпуклостей
    draw_forearm_shape(surface, lower_start, lower_end, color_base, outline_color, w_upper=10, is_left_visual=is_left_visual)
    
    # Запястье (шарик)
    pygame.draw.circle(surface, color_base, (int(wrist[0]), int(wrist[1])), int(wrist_r))
    if outline_color:
         pygame.draw.circle(surface, outline_color, (int(wrist[0]), int(wrist[1])), int(wrist_r), 1)


# --- ОБНОВЛЕННАЯ ФУНКЦИЯ ВЕРХНЕЙ ЧАСТИ РУКИ (БИЦЕПС) ---
def draw_arm_upper_humanoid(surface, shoulder, elbow, is_left_visual, color_base, outline_color):
    """
    Отрисовка бицепса. Стыки теперь бесшовные (заливаются кругом на суставе).
    """
    w_upper_start = 9
    w_upper_end = 7
    joint_r = 5.0 # Радиус "заплатки" на локте
    
    vec_upper = pygame.math.Vector2(elbow) - pygame.math.Vector2(shoulder)
    length = vec_upper.length()
    if length < 1: return
    
    normal = normalize_vec(pygame.math.Vector2(-vec_upper.y, vec_upper.x))
    
    p1 = pygame.math.Vector2(shoulder) + normal * (w_upper_start / 2)
    p2 = pygame.math.Vector2(shoulder) - normal * (w_upper_start / 2)
    p3 = pygame.math.Vector2(elbow) - normal * (w_upper_end / 2)
    p4 = pygame.math.Vector2(elbow) + normal * (w_upper_end / 2)
    
    # Рисуем саму руку и кружок на локте одним цветом
    pygame.draw.polygon(surface, color_base, [p1, p2, p3, p4])
    pygame.draw.circle(surface, color_base, (int(elbow[0]), int(elbow[1])), int(joint_r))
    
    if outline_color:
        # Рисуем только боковые линии, не замыкаем контур на локте!
        pygame.draw.line(surface, outline_color, p1, p4)
        pygame.draw.line(surface, outline_color, p2, p3)



def draw_divine_eye(surface, center, width, is_left, target_pos, openness, color_iris=(0, 200, 255), outline_color=(15, 20, 35)):
    """
    Рисует глаз. Форма сужена на 20%, но размер зрачков сохранен.
    """
    cx, cy = center
    
    # 1. --- РАЗМЕРЫ ---
    # Высота формы глаза (СУЖЕНА на 20%: 0.75 * 0.8 = 0.6)
    eye_height_shape = width * 0.6 
    
    # Высота для расчета размера зрачка (Оставляем оригинальную пропорцию 0.75, 
    # чтобы зрачки не уменьшались вместе с глазом)
    eye_height_pupil_ref = width * 0.75
    
    # --- 2. ЕСЛИ ГЛАЗ ЗАКРЫТ ---
    if openness <= 0.05:
        # Используем суженную высоту для закрытого века
        lash_curve_y = cy + eye_height_shape * 0.15 
        curve_pts = [
            (cx - width/2, lash_curve_y),
            (cx, lash_curve_y + 2),
            (cx + width/2, lash_curve_y)
        ]
        pygame.draw.lines(surface, outline_color, False, curve_pts, 2)
        return

    # --- 3. РАСЧЕТ ДВИЖЕНИЯ ЗРАЧКА (Эллипс) ---
    pupil_offset_x = 0
    pupil_offset_y = 0
    
    # Радиусы движения зрачка адаптируем под новую форму
    range_x = width * 0.32
    range_y = eye_height_shape * 0.35 # Используем новую, узкую высоту
    
    if target_pos is not None:
        if hasattr(target_pos, 'x'):
            tx, ty = target_pos.x, target_pos.y
        else:
            tx, ty = target_pos

        dx = tx - cx
        dy = ty - cy
        angle = math.atan2(dy, dx)
        
        pupil_offset_x = math.cos(angle) * range_x
        pupil_offset_y = math.sin(angle) * range_y

    # --- 4. ОТРИСОВКА ГЕОМЕТРИИ ---
    # Текущая высота открытия (на основе суженной формы)
    current_h = eye_height_shape * openness
    
    eye_poly = [
        (cx - width/2, cy),
        (cx - width/4, cy - current_h/2),
        (cx + width/4, cy - current_h/2),
        (cx + width/2, cy),
        (cx + width/4, cy + current_h/2),
        (cx - width/4, cy + current_h/2)
    ]
    
    # Белок
    pygame.draw.polygon(surface, (245, 245, 250), eye_poly)
    
    # --- 5. ОТРИСОВКА ЗРАЧКА ---
    if openness > 0.2:
        iris_x = cx + pupil_offset_x
        iris_y = cy + pupil_offset_y
        
        # ВАЖНО: Размер радужки считаем от "старой" высокой референсной высоты,
        # чтобы она осталась большой, несмотря на сужение глаза.
        iris_size = (eye_height_pupil_ref * openness) * 0.55
        pupil_size = iris_size * 0.45 
        
        # Радужка
        pygame.draw.circle(surface, color_iris, (int(iris_x), int(iris_y)), int(iris_size))
        # Зрачок
        pygame.draw.circle(surface, (10, 10, 20), (int(iris_x), int(iris_y)), int(pupil_size))
        
        # Блик
        glint_off = -3 if is_left else 3
        draw_alpha_circle(surface, (255, 255, 255, 220), (iris_x + glint_off, iris_y - iris_size*0.3), 2)

    # --- 6. ВЕКИ ---
    top_lid = [
        (cx - width/2 - 1, cy + 1), 
        (cx - width/4, cy - current_h/2 - 1),
        (cx + width/4, cy - current_h/2 - 1),
        (cx + width/2 + 1, cy + 1)
    ]
    pygame.draw.lines(surface, outline_color, False, top_lid, 2)
    
    bot_lid = [
        (cx - width/2, cy),
        (cx, cy + current_h/2),
        (cx + width/2, cy)
    ]
    pygame.draw.lines(surface, (outline_color[0], outline_color[1], outline_color[2], 100), False, bot_lid, 1)


def draw_humanoid_head_minimal(surface, cx, head_y, color_base, outline_color, color_shadow, time_ticks=0, target_pos=None):
    """
    Отрисовка головы с увеличенным временем удержания взгляда.
    """
    # ... (Геометрия головы без изменений) ...
    face_w = 14.0          
    chin_drop = 22         
    ear_y = head_y + 2     
    chin_pt = pygame.math.Vector2(cx, head_y + chin_drop)
    jaw_y = head_y + 12
    temple_w = face_w + 1
    jaw_w = face_w * 0.75
    
    pts_l = get_bezier_points(pygame.math.Vector2(cx - temple_w, head_y - 5), pygame.math.Vector2(cx - jaw_w, jaw_y), pygame.math.Vector2(cx - temple_w, jaw_y - 5), segments=6)
    pts_l2 = get_bezier_points(pygame.math.Vector2(cx - jaw_w, jaw_y), chin_pt, pygame.math.Vector2(cx - jaw_w * 0.6, chin_pt.y - 2), segments=6)
    pts_r2 = get_bezier_points(chin_pt, pygame.math.Vector2(cx + jaw_w, jaw_y), pygame.math.Vector2(cx + jaw_w * 0.6, chin_pt.y - 2), segments=6)
    pts_r = get_bezier_points(pygame.math.Vector2(cx + jaw_w, jaw_y), pygame.math.Vector2(cx + temple_w, head_y - 5), pygame.math.Vector2(cx + temple_w, jaw_y - 5), segments=6)
    
    forehead = [pts_l[0], pts_r[-1]]
    face_poly = [(p.x, p.y) for p in (pts_l + pts_l2 + pts_r2 + pts_r + forehead)]
    
    ear_w, ear_h = 5, 10
    ear_l = [(cx - temple_w + 2, ear_y - ear_h/2), (cx - temple_w - ear_w, ear_y - 2), (cx - temple_w + 3, ear_y + ear_h/2)]
    pygame.draw.polygon(surface, color_base, ear_l)
    pygame.draw.aalines(surface, outline_color, False, ear_l)
    ear_r = [(cx + temple_w - 2, ear_y - ear_h/2), (cx + temple_w + ear_w, ear_y - 2), (cx + temple_w - 3, ear_y + ear_h/2)]
    pygame.draw.polygon(surface, color_base, ear_r)
    pygame.draw.aalines(surface, outline_color, False, ear_r)

    draw_organic_polygon(surface, color_base, face_poly, outline_color=None)
    neck_shadow_poly = [(cx - 4, chin_pt.y + 4), (cx + 4, chin_pt.y + 4), (chin_pt.x, chin_pt.y)]
    draw_alpha_polygon(surface, color_shadow, neck_shadow_poly)
    pygame.draw.aalines(surface, outline_color, True, face_poly)

    # --- ЛОГИКА ГЛАЗ (ВРЕМЯ УВЕЛИЧЕНО ЕЩЕ В 2 РАЗА) ---
    cycle_duration = 900 # Полный цикл ~15 секунд
    cycle_time = time_ticks % cycle_duration
    
    # Окно открытия увеличено до 400 тиков (примерно 6-7 секунд при 60 FPS)
    open_window = 400 
    start_open = cycle_duration - open_window
    
    openness = 0.0
    if cycle_time > start_open:
        local_t = (cycle_time - start_open) / open_window
        # Быстро открывает (10%), долго держит (80%), быстро закрывает (10%)
        if local_t < 0.1: 
            openness = math.sin(local_t * 10 * (math.pi/2)) 
        elif local_t > 0.9: 
            openness = math.sin((1-local_t) * 10 * (math.pi/2))
        else:
            openness = 1.0 # Полностью открыты большую часть времени
            
        openness *= 0.9 # Ограничиваем макс. открытие (натуральный вид)

    # -- Глаза --
    eye_y = head_y + 6
    eye_spacing_x = 7.5
    eye_width = 8
    eye_color = (100, 230, 255) 
    
    draw_divine_eye(surface, (cx - eye_spacing_x, eye_y), eye_width, True, target_pos, openness, eye_color, outline_color)
    draw_divine_eye(surface, (cx + eye_spacing_x, eye_y), eye_width, False, target_pos, openness, eye_color, outline_color)
    
    # -- Нос --
    nose_y = head_y + 13
    nose_poly = [(cx - 1, nose_y - 3), (cx + 1, nose_y), (cx - 2, nose_y + 1)]
    draw_alpha_polygon(surface, color_shadow, nose_poly)
    
    # -- Рот --
    mouth_y = head_y + 17
    mouth_w = 5
    mouth_curve = [(cx - mouth_w/2, mouth_y), (cx, mouth_y + 1), (cx + mouth_w/2, mouth_y)]
    pygame.draw.lines(surface, (180, 100, 100), False, mouth_curve, 1) 
    draw_alpha_circle(surface, (255, 255, 255, 100), (cx, mouth_y + 1.5), 1)

    # -- Брови (поднимаются при открытии глаз) --
    brow_lift = openness * 1.5
    brow_y = eye_y - 4 - brow_lift
    brow_w = 7
    pygame.draw.line(surface, color_shadow, (cx - 4, brow_y), (cx - 4 - brow_w, brow_y + 1), 1)
    pygame.draw.line(surface, color_shadow, (cx + 4, brow_y), (cx + 4 + brow_w, brow_y + 1), 1)
    
    # Румянец
    blush_color = (255, 150, 150, 40)
    draw_alpha_circle(surface, blush_color, (cx - 9, nose_y), 5)
    draw_alpha_circle(surface, blush_color, (cx + 9, nose_y), 5)

    return (cx, head_y)

# --- НОВАЯ ФУНКЦИЯ ДЛЯ ОТРИСОВКИ ТЕНЕЙ МЫШЦ/V-ЛИНИЙ ---
def draw_muscle_shadows(surface, cx, hip_line_y, crotch_y, color_shadow):
    """
    ЗАГЛУШКА: Удаляем старую логику, чтобы сосредоточиться на форме ноги.
    Вам, вероятно, понадобится реализовать здесь V-линии живота/паха позже.
    """
    pass

# ==========================================
# --- НОВЫЕ ФУНКЦИИ НОГ (Вставьте в monster_flo.py) ---
# ==========================================


# ==========================================
# --- ИТОГОВЫЕ ФУНКЦИИ НОГ (ЧИСТЫЕ) ---
# ==========================================

def draw_shin_shape(surface, knee_pos, ankle_pos, width_knee, width_ankle, is_left_leg, color, outline_color):
    """
    Рисует анатомичную голень.
    ОБНОВЛЕНИЕ: Сухожилие ('палочка') теперь имеет коническую форму:
    толстое у основания икры и узкое у стопы.
    """
    vec = ankle_pos - knee_pos
    length = vec.length()
    if length < 1: return
    
    normal = pygame.math.Vector2(-vec.y, vec.x).normalize()
    
    # ЛОГИКА СТОРОН
    if is_left_leg:
        dir_outer = normal
        dir_inner = -normal
    else:
        dir_outer = -normal
        dir_inner = normal

    # --- НАСТРОЙКИ АНАТОМИИ ---
    ratio_outer = 0.65   # Внешняя икра опускается низко
    ratio_inner = 0.55   # Внутренняя икра чуть выше
    
    # === ИЗМЕНЕНИЕ ЗДЕСЬ: КОНУСНОСТЬ СУХОЖИЛИЯ ===
    # Делаем верх сухожилия (где оно выходит из мышцы) заметно шире лодыжки.
    # width_ankle ~ 2.8, значит верх будет ~ 6.5 пикселей
    width_tendon_top = width_ankle * 2.3  
    width_ankle_base = width_ankle        

    outer_bulge = 8.0     
    inner_bulge = 3.5     

    # --- 1. ОПРЕДЕЛЕНИЕ ТОЧЕК ---
    
    # Верх (Колено)
    p_knee_out = knee_pos + dir_outer * (width_knee * 0.5)
    p_knee_in  = knee_pos + dir_inner * (width_knee * 0.5)
    
    # Середина (Конец мышцы / Начало сухожилия)
    pos_mid_outer = knee_pos.lerp(ankle_pos, ratio_outer)
    pos_mid_inner = knee_pos.lerp(ankle_pos, ratio_inner)
    
    # Точки стыка (ШИРОКИЕ)
    p_muscle_end_out = pos_mid_outer + dir_outer * (width_tendon_top * 0.5)
    p_muscle_end_in  = pos_mid_inner + dir_inner * (width_tendon_top * 0.5)
    
    # Низ (Лодыжка) (УЗКИЕ)
    p_ankle_out = ankle_pos + dir_outer * (width_ankle_base * 0.5)
    p_ankle_in  = ankle_pos + dir_inner * (width_ankle_base * 0.5)

    # --- 2. ПОСТРОЕНИЕ КОНТУРОВ ---
    
    # ВНЕШНЯЯ СТОРОНА (Мышца)
    # Сдвигаем контрольную точку чуть выше, чтобы компенсировать ширину низа
    ctrl_outer_pos = p_knee_out.lerp(p_muscle_end_out, 0.4) 
    ctrl_outer = ctrl_outer_pos + dir_outer * outer_bulge
    curve_outer = get_bezier_points(p_knee_out, p_muscle_end_out, ctrl_outer, segments=10)
    
    # ВНУТРЕННЯЯ СТОРОНА (Мышца)
    ctrl_inner_pos = p_knee_in.lerp(p_muscle_end_in, 0.4)
    ctrl_inner = ctrl_inner_pos + dir_inner * inner_bulge
    curve_inner = get_bezier_points(p_muscle_end_in, p_knee_in, ctrl_inner, segments=10)
    
    # --- 3. СБОРКА ПОЛИГОНА ---
    poly_points = []
    
    # Вниз по внешней мышце
    poly_points.extend([(p.x, p.y) for p in curve_outer])
    
    # Вниз к лодыжке (Теперь это наклонная линия, сужающаяся к низу)
    poly_points.append((p_ankle_out.x, p_ankle_out.y))
    
    # Переход через низ лодыжки
    poly_points.append((p_ankle_in.x, p_ankle_in.y))
    
    # Вверх к началу внутренней мышцы (Тоже наклонная линия, расширяющаяся к верху)
    poly_points.append((p_muscle_end_in.x, p_muscle_end_in.y))
    
    # Вверх по внутренней мышце
    poly_points.extend([(p.x, p.y) for p in curve_inner[1:]])
    
    # Отрисовка
    pygame.draw.polygon(surface, color, poly_points)
    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, poly_points)

def draw_divine_foot(surface, ankle_pos, toe_tip_pos, is_left_leg, color, outline_color):
    """
    Улучшенная отрисовка ступни: анатомичная форма с пяткой, сводом и подъемом.
    Поза: вытянутый носок (полет).
    """
    # 1. Базовая математика векторов
    vec = toe_tip_pos - ankle_pos
    length = vec.length()
    if length < 1: return
    
    tangent = vec.normalize()
    # Нормаль: для левой ноги смотрит "внутрь/вправо", для правой "внутрь/влево"
    # Но для удобства построения определим направление "Верх стопы" и "Низ стопы"
    normal = pygame.math.Vector2(-tangent.y, tangent.x)
    
    # Логика сторон:
    # is_left_leg = True -> левая нога персонажа.
    # Если персонаж смотрит на нас, внутренняя сторона левой ноги - это справа от вектора.
    if is_left_leg:
        dir_inner = -normal  # Внутренняя сторона (свод стопы, большой палец)
        dir_outer = normal   # Внешняя сторона (пятка, мизинец)
    else:
        dir_inner = normal
        dir_outer = -normal

    # 2. Опорные точки геометрии
    
    # Пятка: Сдвинута назад от лодыжки и немного наружу
    heel_offset = length * 0.25
    heel_width_shift = length * 0.15
    heel_pos = ankle_pos - tangent * heel_offset + dir_outer * heel_width_shift
    
    # Подъем стопы (Instep): Верхняя дуга, должна быть красивой и высокой
    instep_height = length * 0.35
    instep_ctrl = ankle_pos + tangent * (length * 0.4) + dir_inner * instep_height
    
    # Подушечка стопы (Ball): Нижняя точка перед пальцами
    ball_pos = ankle_pos + tangent * (length * 0.75) + dir_inner * (length * 0.05)
    
    # Свод стопы (Sole Arch): Вогнутость снизу
    sole_arch_ctrl = ankle_pos + tangent * (length * 0.3) + dir_outer * (length * 0.1)

    # 3. Построение кривых (Контур)
    
    # А) Верхняя часть (от лодыжки к кончику пальцев)
    # Используем ankle_pos как старт, но чуть смещаем для толщины
    ankle_top = ankle_pos + dir_inner * 2
    curve_top = get_bezier_points(ankle_top, toe_tip_pos, instep_ctrl, segments=8)
    
    # Б) Подошва (от кончика пальцев к пятке через подушечку)
    # Разбиваем на две части для красивого изгиба, если нужно, или одна сложная.
    # Сделаем одну кривую от носка до пятки, контрольная точка - подушечка/свод.
    # Но лучше: Носок -> Подушечка -> Пятка.
    curve_sole = get_bezier_points(toe_tip_pos, heel_pos, ball_pos + dir_outer * (length*0.1), segments=8)
    
    # В) Задник пятки (от пятки к лодыжке)
    heel_back_ctrl = heel_pos - tangent * 2 + dir_outer * 2
    ankle_back = ankle_pos + dir_outer * 2
    curve_heel = get_bezier_points(heel_pos, ankle_back, heel_back_ctrl, segments=4)

    # Собираем полигон
    poly_points = [(p.x, p.y) for p in curve_top + curve_sole + curve_heel]
    
    # 4. Отрисовка
    
    # Основная форма
    draw_organic_polygon(surface, color, poly_points, outline_color=None)
    
    # 5. Детализация
    
    # Тень на подошве (придает объем снизу)
    shadow_color = (max(0, color[0]-40), max(0, color[1]-40), max(0, color[2]-40))
    sole_pts = [(p.x, p.y) for p in curve_sole]
    if len(sole_pts) > 2:
        pygame.draw.aalines(surface, shadow_color, False, sole_pts)

    # Лодыжка (Malleolus) - косточка
    ankle_bone_pos = ankle_pos + dir_outer * 1.5 - tangent * 1.0
    draw_alpha_circle(surface, shadow_color + (50,), (ankle_bone_pos.x, ankle_bone_pos.y), 3)
    
    # Контур (Outline)
    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, poly_points)
        
    # Блик на подъеме (High instep highlight) - делает ногу "божественной" и гладкой
    highlight_start = ankle_pos + tangent * (length * 0.2) + dir_inner * (instep_height * 0.4)
    highlight_end = ankle_pos + tangent * (length * 0.6) + dir_inner * (instep_height * 0.3)
    highlight_color = (255, 255, 255, 60) # Полупрозрачный белый
    pygame.draw.line(surface, highlight_color, highlight_start.xy, highlight_end.xy, 2)

def draw_archangel_legs(surface, body_center, time_ticks, color_base, color_shadow, outline_color, hip_width_max, knee_width, hip_y_pos, crotch_y_pos):
    """
    Главная функция отрисовки ног.
    """
    cx = body_center.x
    
    # --- ПРОПОРЦИИ ---
    THIGH_LENGTH = 42         
    SHIN_LENGTH = 60          
    FOOT_LENGTH = 16          
    
    HIP_W = hip_width_max      
    THIGH_W_KNEE = 6.0        
    ANKLE_WIDTH = 2.8         
    
    # Анимация
    sway_y = math.sin(time_ticks * 0.05) * 4 
    sway_x = math.cos(time_ticks * 0.04) * 2
    thigh_bulge_anim = 8 + math.cos(time_ticks * 0.05) * 1.0 

    HIP_LINE_Y = hip_y_pos
    KNEE_Y = crotch_y_pos + THIGH_LENGTH  
    ANKLE_Y = KNEE_Y + SHIN_LENGTH    
    OVERLAP_OFFSET = 6.0 

    # Переменная для "заправки" верха ноги внутрь тела
    # Смещаем точку крепления внутрь на 4 пикселя, чтобы угол не торчал
    TUCK_IN_OFFSET = 4.0 

    # === ЛЕВАЯ НОГА ===
    L_KNEE_POS = pygame.math.Vector2(cx - 7 + sway_x * 0.3, KNEE_Y + sway_y * 0.5)
    L_ANKLE_POS = pygame.math.Vector2(cx - 10 + sway_x * 0.5, ANKLE_Y + sway_y)
    L_TOE_POS = L_ANKLE_POS + pygame.math.Vector2(-2, FOOT_LENGTH)
    
    # 1. Бедро
    p1_hip_in = pygame.math.Vector2(cx - 1, HIP_LINE_Y + 5 - OVERLAP_OFFSET) 
    
    # --- ИСПРАВЛЕНИЕ: сужаем верхнюю точку (вычитаем TUCK_IN_OFFSET из ширины) ---
    p2_hip_out = pygame.math.Vector2(cx - (HIP_W - TUCK_IN_OFFSET), HIP_LINE_Y - OVERLAP_OFFSET) 
    
    # Контрольная точка остается широкой (HIP_W), чтобы сохранить объем бедер
    p3_ctrl_out = pygame.math.Vector2(cx - HIP_W - thigh_bulge_anim, HIP_LINE_Y + 20) 
    
    p4_knee_out = L_KNEE_POS + pygame.math.Vector2(-THIGH_W_KNEE/2, 0)
    p5_knee_in = L_KNEE_POS + pygame.math.Vector2(THIGH_W_KNEE/2, 0) 
    
    outer_thigh_l = get_bezier_points(p2_hip_out.xy, p4_knee_out.xy, p3_ctrl_out.xy, segments=10)
    inner_thigh_l = [p5_knee_in] + [p1_hip_in] 
    
    thigh_poly_l = [(p.x, p.y) for p in outer_thigh_l] + [(p.x, p.y) for p in inner_thigh_l]
    pygame.draw.polygon(surface, color_base, thigh_poly_l)
    pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in outer_thigh_l])
    
    short_crotch_pt = p5_knee_in.lerp(p1_hip_in, 0.75)
    pygame.draw.line(surface, outline_color, p5_knee_in.xy, short_crotch_pt.xy, 1)

    # 2. Колено
    draw_joint(surface, L_KNEE_POS, THIGH_W_KNEE * 0.6, color_base, outline_color)

    # 3. Ступня
    draw_divine_foot(surface, L_ANKLE_POS, L_TOE_POS, True, color_base, outline_color)

    # 4. ГОЛЕНЬ
    draw_shin_shape(surface, L_KNEE_POS, L_ANKLE_POS, THIGH_W_KNEE, ANKLE_WIDTH, True, color_base, outline_color)


    # === ПРАВАЯ НОГА ===
    R_KNEE_POS = pygame.math.Vector2(cx + 7 + sway_x * 0.3, KNEE_Y + sway_y * 0.5)
    R_ANKLE_POS = pygame.math.Vector2(cx + 10 + sway_x * 0.5, ANKLE_Y + sway_y)
    R_TOE_POS = R_ANKLE_POS + pygame.math.Vector2(2, FOOT_LENGTH)
    
    # 1. Бедро
    p1_hip_in_r = pygame.math.Vector2(cx + 1, HIP_LINE_Y + 5 - OVERLAP_OFFSET) 
    
    # --- ИСПРАВЛЕНИЕ: сужаем верхнюю точку (добавляем TUCK_IN_OFFSET к координате) ---
    p2_hip_out_r = pygame.math.Vector2(cx + (HIP_W - TUCK_IN_OFFSET), HIP_LINE_Y - OVERLAP_OFFSET)
    
    # Контрольная точка остается широкой
    p3_ctrl_out_r = pygame.math.Vector2(cx + HIP_W + thigh_bulge_anim, HIP_LINE_Y + 20) 
    
    p4_knee_out_r = R_KNEE_POS + pygame.math.Vector2(THIGH_W_KNEE/2, 0)
    p5_knee_in_r = R_KNEE_POS + pygame.math.Vector2(-THIGH_W_KNEE/2, 0) 
    
    outer_thigh_r = get_bezier_points(p2_hip_out_r.xy, p4_knee_out_r.xy, p3_ctrl_out_r.xy, segments=10)
    inner_thigh_r = [p5_knee_in_r] + [p1_hip_in_r] 
    
    thigh_poly_r = [(p.x, p.y) for p in outer_thigh_r] + [(p.x, p.y) for p in inner_thigh_r]
    pygame.draw.polygon(surface, color_base, thigh_poly_r)
    pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in outer_thigh_r])
    
    short_crotch_pt_r = p5_knee_in_r.lerp(p1_hip_in_r, 0.75)
    pygame.draw.line(surface, outline_color, p5_knee_in_r.xy, short_crotch_pt_r.xy, 1)

    # 2. Колено
    draw_joint(surface, R_KNEE_POS, THIGH_W_KNEE * 0.6, color_base, outline_color)

    # 3. Ступня
    draw_divine_foot(surface, R_ANKLE_POS, R_TOE_POS, False, color_base, outline_color)

    # 4. ГОЛЕНЬ
    draw_shin_shape(surface, R_KNEE_POS, R_ANKLE_POS, THIGH_W_KNEE, ANKLE_WIDTH, False, color_base, outline_color)




# ==========================================
# --- НОВАЯ ЛОГИКА КИСТЕЙ (ИЗ MONSTER_СТАРЫЙ) ---
# ==========================================

# ==========================================
# --- НОВАЯ ЛОГИКА КИСТЕЙ (РАЗБИТАЯ НА СЛОИ) ---
# ==========================================

# ==========================================
# --- НОВАЯ ЛОГИКА КИСТЕЙ (С ПОДДЕРЖКОЙ FLIP_VERTICAL) ---
# ==========================================

def draw_segment_poly_v2(surface, start_pos, angle_rad, length, w_start, w_end, color, outline_color):
    if hasattr(start_pos, 'x'):
        start_pos = (start_pos.x, start_pos.y)

    w_start = max(1.0, w_start)
    w_end = max(1.0, w_end)

    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    end_pos = (start_pos[0] + dx * length, start_pos[1] + dy * length)
    
    perp_x = -dy
    perp_y = dx
    
    p1 = (start_pos[0] + perp_x * (w_start / 2), start_pos[1] + perp_y * (w_start / 2))
    p2 = (start_pos[0] - perp_x * (w_start / 2), start_pos[1] - perp_y * (w_start / 2))
    p3 = (end_pos[0] - perp_x * (w_end / 2), end_pos[1] - perp_y * (w_end / 2))
    p4 = (end_pos[0] + perp_x * (w_end / 2), end_pos[1] + perp_y * (w_end / 2))
    
    points = [p1, p2, p3, p4]
    
    pygame.draw.polygon(surface, color, points)
    if outline_color:
        pygame.draw.aalines(surface, outline_color, True, points)
    
    return end_pos

def draw_detailed_hand_palm(surface, wrist_pos, arm_angle, is_left, color, outline_color, grip_factor=0.3, scale=1.0, flip_vertical=False):
    """
    Рисует ладонь. flip_vertical=True переворачивает кисть "вверх ногами".
    """
    cx = wrist_pos.x if hasattr(wrist_pos, 'x') else wrist_pos[0]
    cy = wrist_pos.y if hasattr(wrist_pos, 'y') else wrist_pos[1]
    
    # Множитель для вертикального отражения
    v_mult = -1 if flip_vertical else 1

    # === ЛАДОНЬ ===
    palm_seg1_len = 12 * scale
    palm_seg1_w_start = 14 * scale
    palm_seg1_w_end = 18 * scale
    
    # Сгиб ладони
    palm_curl = grip_factor * 0.15
    # Если рука левая, curl положителен. v_mult инвертирует это при перевороте.
    curl_dir = palm_curl if is_left else -palm_curl
    angle_seg1 = arm_angle + (curl_dir * v_mult)
    
    mid_palm_pos = draw_segment_poly_v2(surface, (cx, cy), angle_seg1, palm_seg1_len, 
                                     palm_seg1_w_start, palm_seg1_w_end, color, outline_color)
    
    # Сегмент 2 (Пясть)
    palm_seg2_len = 14 * scale
    palm_seg2_w_start = 18 * scale
    palm_seg2_w_end = 32 * scale 
    
    angle_seg2 = angle_seg1 + (curl_dir * 0.5 * v_mult)
    
    knuckles_pos = draw_segment_poly_v2(surface, mid_palm_pos, angle_seg2, palm_seg2_len,
                                     palm_seg2_w_start, palm_seg2_w_end, color, outline_color)

    # Сустав запястья
    pygame.draw.circle(surface, color, (int(cx), int(cy)), int(6*scale))
    if outline_color:
        pygame.draw.circle(surface, outline_color, (int(cx), int(cy)), int(6*scale), 1)

    return mid_palm_pos, knuckles_pos, angle_seg2

def draw_detailed_hand_fingers(surface, palm_data, is_left, color, outline_color, grip_factor=0.3, scale=1.0, flip_vertical=False):
    """
    Рисует пальцы. Акцент на последней фаланге для хвата.
    """
    mid_palm_pos, knuckles_pos, angle_seg2 = palm_data
    v_mult = -1 if flip_vertical else 1

    finger_configs = {
        'index':  {'lens': [14, 10, 8],  'widths': [7, 6, 4],   'base_offset': -10},
        'middle': {'lens': [15, 11, 9],  'widths': [7.5, 6.5, 4], 'base_offset': -2},
        'ring':   {'lens': [13, 10, 8],  'widths': [7, 6, 4],   'base_offset': 6},
        'pinky':  {'lens': [10, 8, 6],   'widths': [6, 5, 3],   'base_offset': 13}, 
        'thumb':  {'lens': [12, 10],     'widths': [8, 6],      'base_offset': -14}
    }

    # === ПАЛЬЦЫ ===
    fingers_order = ['pinky', 'ring', 'middle', 'index']
    if not is_left: fingers_order = fingers_order[::-1]

    def draw_single_finger(name, origin, base_angle_rad):
        cfg = finger_configs[name]
        offset = cfg['base_offset'] * scale
        
        d_cos = math.cos(base_angle_rad)
        d_sin = math.sin(base_angle_rad)
        p_cos = -d_sin
        p_sin = d_cos
        
        effective_offset = offset 
        if not is_left: effective_offset *= -1
        effective_offset *= v_mult 

        start_pos = (origin[0] + p_cos * effective_offset, origin[1] + p_sin * effective_offset)
        
        fan_angle = offset * 0.005 
        if not is_left: fan_angle *= -1
        fan_angle *= v_mult 
        
        current_pos = start_pos
        current_angle = base_angle_rad + fan_angle
        
        # Общий потенциал сгиба
        total_curl_potential = 160 * grip_factor
        bend_dir = 1 if is_left else -1 

        num_segments = len(cfg['lens'])
        
        for i in range(num_segments):
            length = cfg['lens'][i] * scale
            w_s = cfg['widths'][i] * scale
            w_e = w_s * 0.75
            
            # --- ЛОГИКА ИЗГИБА ФАЛАНГ ---
            # Базовый изгиб для всех
            segment_curl = total_curl_potential / 3.5 
            
            # Если это не первая фаланга, добавляем изгиб
            if i > 0: 
                segment_curl += (total_curl_potential / 3.5) * grip_factor
            
            # === ИЗМЕНЕНИЕ: АКЦЕНТ НА КОНЧИКЕ ===
            # Если это последняя фаланга (кончик)
            is_tip = (i == num_segments - 1)
            if is_tip:
                # Добавляем "крючок" (extra curl), чтобы палец впивался
                # Значение 40 градусов при полном хвате
                tip_extra_curl = 40.0 * grip_factor 
                segment_curl += tip_extra_curl

            current_angle += math.radians(segment_curl) * bend_dir
            current_pos = draw_segment_poly_v2(surface, current_pos, current_angle, length, w_s, w_e, color, outline_color)

    for f_name in fingers_order:
        draw_single_finger(f_name, knuckles_pos, angle_seg2)

    # === БОЛЬШОЙ ПАЛЕЦ ===
    def draw_thumb_finger(origin, base_angle_rad):
        cfg = finger_configs['thumb']
        
        d_cos = math.cos(base_angle_rad)
        d_sin = math.sin(base_angle_rad)
        p_cos = -d_sin
        p_sin = d_cos
        
        side_off = -12 * scale 
        if not is_left: side_off *= -1 
        side_off *= v_mult 

        back_off = -4 * scale
        start_pos = (origin[0] + p_cos * side_off + d_cos * back_off,
                     origin[1] + p_sin * side_off + d_sin * back_off)
        
        thumb_base_offset = math.radians(50)
        
        base_calc = thumb_base_offset if is_left else -thumb_base_offset
        if flip_vertical: base_calc *= -1
            
        thumb_base = base_angle_rad - base_calc
        
        thumb_sweep_dir = 1 if is_left else -1
        if flip_vertical: thumb_sweep_dir *= -1
            
        thumb_sweep = math.radians(70 * grip_factor) * thumb_sweep_dir
        
        current_pos = start_pos
        current_angle = thumb_base + thumb_sweep
        
        bend_dir_thumb = 1 if is_left else -1
        if flip_vertical: bend_dir_thumb *= -1

        num_segments = len(cfg['lens'])

        for i in range(num_segments):
            length = cfg['lens'][i] * scale
            w_s = cfg['widths'][i] * scale
            w_e = w_s * 0.8
            
            # Логика изгиба большого пальца
            segment_curl = 60 * grip_factor
            
            # Кончик большого пальца тоже загибаем сильнее для прижатия
            if i == num_segments - 1:
                 segment_curl += 30 * grip_factor
            
            current_angle += math.radians(segment_curl) * bend_dir_thumb
            current_pos = draw_segment_poly_v2(surface, current_pos, current_angle, length, w_s, w_e, color, outline_color)

    draw_thumb_finger(mid_palm_pos, angle_seg2)

def draw_detailed_hand(surface, wrist_pos, arm_angle, is_left, color, outline_color, grip_factor=0.3, scale=1.0, flip_vertical=False):
    palm_data = draw_detailed_hand_palm(surface, wrist_pos, arm_angle, is_left, color, outline_color, grip_factor, scale, flip_vertical)
    draw_detailed_hand_fingers(surface, palm_data, is_left, color, outline_color, grip_factor, scale, flip_vertical)

def draw_archangel_torso(surface, body_center, shoulder_l_base, shoulder_r_base, time_ticks, death_pose_factor, color_base, color_shadow, outline_color, target_pos=None, elbow_l=None, elbow_r=None):
    """
    Отрисовка торса. Добавлены аргументы elbow_l и elbow_r для платка.
    """
    cx, cy = body_center.xy
    
    # ... (ПРОПОРЦИИ И ПЕРЕМЕННЫЕ ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ) ...
    # Просто скопируйте блок настроек пропорций из прошлого ответа, если нужно, 
    # но главное изменение ниже в секции "ПЛАТОК".
    # Для краткости я приведу ключевые части.
    
    RIBCAGE_LENGTH_OFFSET = -20 
    WAIST_Y_OFFSET = 16       
    HIP_Y_OFFSET = 13          
    CROTCH_Y_OFFSET = 18      
    waist_w = 6.5               
    ribcage_w = 10.5     
    HIP_WIDTH_TOP = 16.0      
    KNEE_WIDTH = 8.0         
    SHOULDER_WIDTH_BODY = 7.0 
    BREAST_BOTTOM_OFFSET = -20
    BREAST_VOLUME = 8.0
    
    ribcage_bottom_y = cy + RIBCAGE_LENGTH_OFFSET
    waist_y = ribcage_bottom_y + WAIST_Y_OFFSET
    hip_line_y = waist_y + HIP_Y_OFFSET
    crotch_y = hip_line_y + CROTCH_Y_OFFSET
    chest_bottom_y = cy + BREAST_BOTTOM_OFFSET
    
    breath = math.sin(time_ticks * 0.05) * 2.0
    base_shoulder_y = cy - 31
    death_factor_ease = death_pose_factor * death_pose_factor
    shoulder_lift = math.sin(time_ticks * 0.05) * 1.5 
    shoulder_lift = shoulder_lift * (1.0 - death_factor_ease) + (5.0) * death_factor_ease 
    shoulder_roll_x = 0 * (1.0 - death_factor_ease) + (10.0) * death_factor_ease
    shoulder_y = base_shoulder_y + shoulder_lift - 10
    armpit_y = shoulder_y + 12  
    neck_y = shoulder_y - 8
    head_y = neck_y - 25

    shoulder_width_total = SHOULDER_WIDTH_BODY
    neck_w = 5
    hip_w = HIP_WIDTH_TOP 
    
    joint_offset = SHOULDER_WIDTH_BODY + 9.0
    anim_shoulder_l = pygame.math.Vector2(cx - joint_offset - shoulder_roll_x, shoulder_y)
    anim_shoulder_r = pygame.math.Vector2(cx + joint_offset + shoulder_roll_x, shoulder_y)
    
    # 1.0. НОГИ (Вызов без изменений)
    draw_archangel_legs(surface, body_center, time_ticks, color_base, color_shadow, outline_color, HIP_WIDTH_TOP, KNEE_WIDTH, hip_line_y, crotch_y)

    # ... (ВСЯ ГЕОМЕТРИЯ ТОРСА БЕЗ ИЗМЕНЕНИЙ ДО СЕКЦИИ ПЛАТКОВ) ...
    # (trap_l, shoulder_cap_l, side_l... и т.д. копируем из предыдущего кода)
    
    # ДЛЯ ЭКОНОМИИ МЕСТА Я ПРОПУСКАЮ БЛОК ГЕОМЕТРИИ ТЕЛА, ОН НЕ МЕНЯЛСЯ.
    # ВСТАВЬТЕ СЮДА ВЕСЬ КОД ОТРИСОВКИ ТЕЛА (ПОЛИГОНЫ, КОНТУРЫ, ТЕНИ, ГРУДЬ)
    
    # ГЕНЕРАЦИЯ ГЕОМЕТРИИ ДЛЯ ПРИМЕРА (чтобы код работал):
    trap_l = get_bezier_points(pygame.math.Vector2(cx - neck_w, neck_y), anim_shoulder_l, pygame.math.Vector2(cx - neck_w - 5, shoulder_y - 5), 6)
    shoulder_cap_l = get_bezier_points(anim_shoulder_l, pygame.math.Vector2(cx - shoulder_width_total + 2, armpit_y), pygame.math.Vector2(anim_shoulder_l.x + 22, shoulder_y + 10), 6)
    p_armpit_l = pygame.math.Vector2(cx - shoulder_width_total + 2, armpit_y)
    p_rib_bottom_l = pygame.math.Vector2(cx - ribcage_w, ribcage_bottom_y)
    ctrl_side_l = p_armpit_l.lerp(p_rib_bottom_l, 0.5) + pygame.math.Vector2(2, 0)
    side_l = get_bezier_points(p_armpit_l, p_rib_bottom_l, ctrl_side_l, 6)
    stomach_l = get_bezier_points(pygame.math.Vector2(cx - ribcage_w, ribcage_bottom_y), pygame.math.Vector2(cx - waist_w, waist_y), pygame.math.Vector2(cx - ribcage_w, (ribcage_bottom_y + waist_y)/2), 6)
    hip_curve_l = get_bezier_points(pygame.math.Vector2(cx - waist_w, waist_y), pygame.math.Vector2(cx - hip_w, hip_line_y), pygame.math.Vector2(cx - waist_w - 5, (waist_y + hip_line_y)/2), 6)
    crotch_pt = pygame.math.Vector2(cx, crotch_y) 
    crotch_l = get_bezier_points(pygame.math.Vector2(cx - hip_w, hip_line_y), crotch_pt, pygame.math.Vector2(cx - hip_w * 0.4, crotch_y - 1), 3)
    crotch_r = get_bezier_points(crotch_pt, pygame.math.Vector2(cx + hip_w, hip_line_y), pygame.math.Vector2(cx + hip_w * 0.4, crotch_y - 1), 3)
    hip_curve_r = get_bezier_points(pygame.math.Vector2(cx + hip_w, hip_line_y), pygame.math.Vector2(cx + waist_w, waist_y), pygame.math.Vector2(cx + waist_w + 5, (waist_y + hip_line_y)/2), 6)
    stomach_r = get_bezier_points(pygame.math.Vector2(cx + waist_w, waist_y), pygame.math.Vector2(cx + ribcage_w, ribcage_bottom_y), pygame.math.Vector2(cx + ribcage_w, (ribcage_bottom_y + waist_y)/2), 6)
    p_armpit_r = pygame.math.Vector2(cx + shoulder_width_total - 2, armpit_y)
    p_rib_bottom_r = pygame.math.Vector2(cx + ribcage_w, ribcage_bottom_y)
    ctrl_side_r = p_armpit_r.lerp(p_rib_bottom_r, 0.5) + pygame.math.Vector2(-2, 0)
    side_r = get_bezier_points(p_rib_bottom_r, p_armpit_r, ctrl_side_r, 6)
    shoulder_cap_r = get_bezier_points(p_armpit_r, anim_shoulder_r, pygame.math.Vector2(anim_shoulder_r.x - 22, shoulder_y + 10), 6)
    trap_r = get_bezier_points(anim_shoulder_r, pygame.math.Vector2(cx + neck_w, neck_y), pygame.math.Vector2(cx + neck_w + 5, shoulder_y - 5), 6)
    neck_connect = [pygame.math.Vector2(cx - neck_w, neck_y)] 
    full_torso_poly_vec = (trap_l + shoulder_cap_l + side_l + stomach_l + hip_curve_l + crotch_l + crotch_r + hip_curve_r + stomach_r + side_r + shoulder_cap_r + trap_r + neck_connect)
    unique_poly_vec = []
    seen = set()
    for p in full_torso_poly_vec:
        p_key = (int(p.x*10), int(p.y*10))
        if p_key not in seen:
            unique_poly_vec.append(p)
            seen.add(p_key)
    full_torso_poly = [(p.x, p.y) for p in unique_poly_vec]
    draw_organic_polygon(surface, color_base, full_torso_poly, outline_color=None)
    left_outline_vec = trap_l + shoulder_cap_l + side_l + stomach_l + hip_curve_l
    pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in left_outline_vec])
    right_outline_vec = hip_curve_r + stomach_r + side_r + shoulder_cap_r + trap_r
    pygame.draw.aalines(surface, outline_color, False, [(p.x, p.y) for p in right_outline_vec])
    crotch_l_pts = [(p.x, p.y) for p in crotch_l]
    if len(crotch_l_pts) >= 2:
        split_idx = int(len(crotch_l_pts) * 0.85)
        pts_to_draw = crotch_l_pts[split_idx:]
        if len(pts_to_draw) >= 2:
            pygame.draw.aalines(surface, outline_color, False, pts_to_draw)
    crotch_r_pts = [(p.x, p.y) for p in crotch_r]
    if len(crotch_r_pts) >= 2:
        split_idx = int(len(crotch_r_pts) * 0.15) 
        pts_to_draw = crotch_r_pts[:split_idx]
        if len(pts_to_draw) >= 2:
            pygame.draw.aalines(surface, outline_color, False, pts_to_draw)
    pygame.draw.line(surface, outline_color, (cx - neck_w, neck_y), (cx + neck_w, neck_y))
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in stomach_l])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in crotch_l[2:]]) 
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in crotch_r[:-2]])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in hip_curve_l])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in hip_curve_r])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in side_r])
    pygame.draw.line(surface, color_shadow, (cx, waist_y - 2), (cx, waist_y + 5), 1)
    draw_muscle_shadows(surface, cx, hip_line_y, crotch_y, color_shadow)
    draw_anatomical_shoulder(surface, anim_shoulder_l.xy, 10, True, color_base, outline_color)
    draw_anatomical_shoulder(surface, anim_shoulder_r.xy, 10, False, color_base, outline_color)
    top_y_chest = armpit_y - 16
    base_width = ribcage_w + BREAST_VOLUME
    draw_pear_chest(surface, cx, top_y_chest, chest_bottom_y, base_width, color_base, color_shadow, outline_color, breath)
    pygame.draw.line(surface, color_shadow, (cx, cy-5), (cx, cy+5), 2)
    
    # --- ШЕЯ ---
    n_top_y = head_y + 12      
    n_base_y = neck_y + 4      
    n_w_top = 4.5              
    n_w_base = 6.5
    neck_pos_l = pygame.math.Vector2(cx - n_w_base, n_base_y)
    neck_pos_r = pygame.math.Vector2(cx + n_w_base, n_base_y)
    neck_l = get_bezier_points(pygame.math.Vector2(cx - n_w_top, n_top_y), neck_pos_l, pygame.math.Vector2(cx - n_w_top + 1.5, (n_top_y + n_base_y)/2), 6)
    neck_r = get_bezier_points(neck_pos_r, pygame.math.Vector2(cx + n_w_top, n_top_y), pygame.math.Vector2(cx + n_w_top - 1.5, (n_top_y + n_base_y)/2), 6)
    neck_poly = [(p.x, p.y) for p in (neck_l + neck_r)]
    draw_organic_polygon(surface, color_base, neck_poly, outline_color=outline_color)
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in neck_l])
    pygame.draw.aalines(surface, color_shadow, False, [(p.x, p.y) for p in neck_r])
    shadow_poly = [(cx - n_w_top, n_top_y), (cx + n_w_top, n_top_y), (cx, n_top_y + 8)]
    draw_organic_polygon(surface, color_shadow, shadow_poly, outline_color=outline_color)

    # ==================================================
    # !!! НОВОЕ: ПЛАТКИ-ПОЛУМЕСЯЦЫ С ПРИВЯЗКОЙ К РУКАМ !!!
    # ==================================================
    # Если локти переданы, используем их для поворота.
    # Если нет (для совместимости), берем дефолтное направление вниз.
    
    default_elbow_drop = pygame.math.Vector2(0, 30)
    
    use_elbow_l = elbow_l if elbow_l else (anim_shoulder_l + default_elbow_drop)
    use_elbow_r = elbow_r if elbow_r else (anim_shoulder_r + default_elbow_drop)
    
    draw_shoulder_shawl(surface, neck_pos_l, anim_shoulder_l, use_elbow_l, True, outline_color)
    draw_shoulder_shawl(surface, neck_pos_r, anim_shoulder_r, use_elbow_r, False, outline_color)

    # --- ГОЛОВА ---
    head_center_pos = draw_humanoid_head_minimal(surface, cx, head_y, color_base, outline_color, color_shadow, time_ticks, target_pos)

    return anim_shoulder_l, anim_shoulder_r, pygame.math.Vector2(head_center_pos)

