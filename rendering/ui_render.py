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

def draw_boss_hud_new(screen, boss_instance, boss_portrait_img, font_name, font_title):
    """
    Модульная отрисовка интерфейса босса с цифровым HP.
    """
    if not boss_instance.alive() or boss_instance.state == -1:
        return

    # Настройки
    width, height = screen.get_size()
    margin_right = 20
    margin_top = 20
    p_size = 80
    bar_width = 300 # Базовая ширина, от которой отталкивается позиция
    bar_height = 16 
    
    p_x = width - margin_right - p_size
    p_y = margin_top
    
    C_GOLD = (218, 165, 32)
    C_GOLD_DARK = (184, 134, 11)
    C_DARK_BG = (20, 15, 25)
    C_HP_BG = (40, 10, 10)
    C_HP_FILL = (180, 30, 30)
    C_HP_GLOW = (220, 80, 80)
    
    # 1. Фон и Портрет
    pygame.draw.rect(screen, C_DARK_BG, (p_x, p_y, p_size, p_size))
    if boss_portrait_img:
        screen.blit(boss_portrait_img, (p_x, p_y))
    
    pygame.draw.rect(screen, C_GOLD, (p_x-2, p_y-2, p_size+4, p_size+4), 2)
    pygame.draw.rect(screen, C_GOLD_DARK, (p_x-5, p_y-5, p_size+10, p_size+10), 1)
    
    corners = [(p_x-2, p_y-2), (p_x+p_size+2, p_y-2), (p_x-2, p_y+p_size+2), (p_x+p_size+2, p_y+p_size+2)]
    for cx, cy in corners:
        pygame.draw.circle(screen, C_GOLD, (cx, cy), 4)

    # 2. Текст
    name_text = "Ресалаида"
    title_text = "Хранительница честивости"
    
    surf_name = font_name.render(name_text, True, (255, 240, 200))
    surf_title = font_title.render(title_text, True, (200, 200, 200))
    
    name_rect = surf_name.get_rect(topright=(p_x - 15, p_y + 5))
    screen.blit(font_name.render(name_text, True, (0, 0, 0)), (name_rect.x + 2, name_rect.y + 2))
    screen.blit(surf_name, name_rect)
    
    title_rect = surf_title.get_rect(topright=(p_x - 15, p_y + 38))
    screen.blit(surf_title, title_rect)

    # 3. Полоска здоровья
    bar_x = p_x - 15 - bar_width
    bar_y = p_y + 60
    
    # Фон полоски (Координаты жестко заданы для стыковки с портретом)
    # Правый верхний угол фона: p_x - 5
    # Левый верхний угол фона: bar_x
    # ИТОГОВАЯ ШИРИНА ФОНА = (p_x - 5) - bar_x = 310 пикселей (а не 300)
    bg_poly = [
        (bar_x - 10, bar_y + bar_height), 
        (bar_x, bar_y), 
        (p_x - 5, bar_y), 
        (p_x - 15, bar_y + bar_height)
    ]
    pygame.draw.polygon(screen, C_HP_BG, bg_poly)
    
    # Расчет заполнения
    hp_pct = max(0, boss_instance.hp / boss_instance.max_hp)
    
    # ИСПРАВЛЕНИЕ: Используем реальную ширину фона (310px), чтобы не было скачков
    real_full_width = (p_x - 5) - bar_x # Это равно 310
    current_bar_w = int(real_full_width * hp_pct)
    
    if current_bar_w > 0:
        # Рисуем параллелограмм заполнения
        fill_poly = [
            (bar_x - 10, bar_y + bar_height), 
            (bar_x, bar_y), 
            (bar_x + current_bar_w, bar_y), 
            (bar_x + current_bar_w - 10, bar_y + bar_height)
        ]
        
        color_fill = C_HP_FILL
        if hasattr(boss_instance, 'invulnerable') and boss_instance.invulnerable:
             color_fill = (100, 100, 120)

        pygame.draw.polygon(screen, color_fill, fill_poly)
        pygame.draw.line(screen, C_HP_GLOW, fill_poly[1], fill_poly[2], 2)

    # Окантовка
    pygame.draw.polygon(screen, C_GOLD, bg_poly, 2)

    # 4. Цифровое значение HP
    hp_str = f"{int(max(0, boss_instance.hp))} / {int(boss_instance.max_hp)}"
    
    hp_surf_shadow = font_title.render(hp_str, True, (0, 0, 0))
    hp_rect_shadow = hp_surf_shadow.get_rect(center=(bar_x + bar_width / 2 + 1, bar_y + bar_height / 2 + 1))
    screen.blit(hp_surf_shadow, hp_rect_shadow)
    
    hp_surf = font_title.render(hp_str, True, (255, 255, 255))
    hp_rect = hp_surf.get_rect(center=(bar_x + bar_width / 2, bar_y + bar_height / 2))
    screen.blit(hp_surf, hp_rect)

def draw_player_hud(screen, player, font_name, font_title):
    """
    Отрисовка интерфейса игрока (Слева, Симметрично боссу, Вампирский стиль).
    """
    if not player.alive(): return

    # Настройки
    margin_left = 20
    margin_top = 20
    p_size = 80
    bar_width = 300
    bar_height = 16
    
    # Координаты портрета (Левый верхний угол)
    p_x = margin_left
    p_y = margin_top
    
    # ВАМПИРСКАЯ ПАЛИТРА
    C_SILVER = (180, 180, 190)       # Вместо золота босса
    C_SILVER_DARK = (100, 100, 110)
    C_DARK_BG = (20, 10, 15)
    C_HP_BG = (30, 5, 5)
    C_HP_FILL = (160, 0, 30)         # Кроваво-красный
    C_HP_GLOW = (255, 50, 50)
    
    # 1. Фон и Портрет (заглушка или можно передать иконку)
    pygame.draw.rect(screen, C_DARK_BG, (p_x, p_y, p_size, p_size))
    
    # Рисуем простой символ "V" или лицо вампира, если нет картинки
    # (В будущем можно передать player.portrait, если добавите)
    center = (p_x + p_size//2, p_y + p_size//2)
    pygame.draw.circle(screen, (200, 200, 220), center, 25) # Бледное лицо
    pygame.draw.circle(screen, (150, 0, 0), (center[0]-8, center[1]-2), 3) # Глаз
    pygame.draw.circle(screen, (150, 0, 0), (center[0]+8, center[1]-2), 3) # Глаз
    
    # Рамка
    pygame.draw.rect(screen, C_SILVER, (p_x-2, p_y-2, p_size+4, p_size+4), 2)
    pygame.draw.rect(screen, C_SILVER_DARK, (p_x-5, p_y-5, p_size+10, p_size+10), 1)
    
    # Декоративные уголки
    corners = [
        (p_x-2, p_y-2), (p_x+p_size+2, p_y-2),
        (p_x-2, p_y+p_size+2), (p_x+p_size+2, p_y+p_size+2)
    ]
    for cx, cy in corners:
        pygame.draw.circle(screen, C_SILVER, (cx, cy), 4)

    # 2. Текст (Имя)
    name_text = "Алукард" # Или любое имя героя
    surf_name = font_name.render(name_text, True, (220, 220, 230))
    
    # Позиционирование (Справа от портрета)
    name_rect = surf_name.get_rect(topleft=(p_x + p_size + 15, p_y + 5))
    
    # Тень
    screen.blit(font_name.render(name_text, True, (0, 0, 0)), (name_rect.x + 2, name_rect.y + 2))
    screen.blit(surf_name, name_rect)

    # 3. Полоска здоровья
    # Начинается справа от портрета и идет вправо
    bar_x = p_x + p_size + 15
    bar_y = p_y + 45 # Чуть ниже имени
    
    hp_pct = max(0, player.hp / player.max_hp)
    current_bar_w = int(bar_width * hp_pct)
    
    # Фон полоски (Симметричный скос)
    # У босса скос слева, у игрока сделаем скос справа для симметрии
    bg_poly = [
        (bar_x, bar_y),                      # Верх-Лево
        (bar_x + bar_width, bar_y),          # Верх-Право
        (bar_x + bar_width + 10, bar_y + bar_height), # Низ-Право (Скос)
        (bar_x - 5, bar_y + bar_height)      # Низ-Лево (небольшой скос назад к портрету)
    ]
    pygame.draw.polygon(screen, C_HP_BG, bg_poly)
    
    # Заливка
    if current_bar_w > 0:
        fill_poly = [
            (bar_x, bar_y),
            (bar_x + current_bar_w, bar_y),
            (bar_x + current_bar_w + 10, bar_y + bar_height),
            (bar_x - 5, bar_y + bar_height)
        ]
        # Если полоска полная, корректируем правый край под фон
        if hp_pct > 0.99:
             fill_poly[2] = (bar_x + bar_width + 10, bar_y + bar_height)
             
        pygame.draw.polygon(screen, C_HP_FILL, fill_poly)
        # Блик сверху
        pygame.draw.line(screen, C_HP_GLOW, fill_poly[0], fill_poly[1], 2)

    # Окантовка
    pygame.draw.polygon(screen, C_SILVER, bg_poly, 2)
    
    # Цифры HP
    hp_str = f"{int(max(0, player.hp))} / {int(player.max_hp)}"
    hp_surf = font_title.render(hp_str, True, (255, 255, 255))
    hp_rect = hp_surf.get_rect(center=(bar_x + bar_width/2, bar_y + bar_height/2))
    # Тень цифр
    hp_shadow = font_title.render(hp_str, True, (0,0,0))
    screen.blit(hp_shadow, (hp_rect.x+1, hp_rect.y+1))
    screen.blit(hp_surf, hp_rect)

def draw_skill_icon(screen, skill_obj, pos, font):
    """
    Отрисовка иконки навыка (Квадрат с эффектом Flurry).
    pos: (x, y) левого верхнего угла.
    """
    x, y = pos
    size = 50
    
    # Цвета (Вампирские/Кровавые)
    C_BG = (30, 5, 10)            # Очень темный бордовый фон
    C_BORDER_READY = (200, 50, 50)# Яркая красная рамка (готов)
    C_BORDER_CD = (100, 50, 50)   # Тусклая рамка (кд)
    
    C_SLASH_CORE = (255, 220, 220) # Белое лезвие
    C_SLASH_GLOW = (200, 0, 50)    # Кровавый след
    C_CD_OVERLAY = (0, 0, 0, 180)  # Затемнение кд
    
    # 1. Фон квадрата
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, C_BG, rect)
    
    # 2. Иконка: Статичные "разрезы" (Имитация скилла)
    # Рисуем несколько перекрещивающихся линий разной толщины
    
    # Разрез 1 (Диагональ)
    pygame.draw.line(screen, C_SLASH_GLOW, (x+8, y+8), (x+42, y+42), 4)
    pygame.draw.line(screen, C_SLASH_CORE, (x+8, y+8), (x+42, y+42), 2)

    # Разрез 2 (Обратная диагональ)
    pygame.draw.line(screen, C_SLASH_GLOW, (x+42, y+8), (x+8, y+42), 4)
    pygame.draw.line(screen, C_SLASH_CORE, (x+42, y+8), (x+8, y+42), 2)

    # Разрез 3 (Горизонтальный быстрый)
    pygame.draw.line(screen, C_SLASH_GLOW, (x+5, y+25), (x+45, y+20), 3)
    pygame.draw.line(screen, C_SLASH_CORE, (x+5, y+25), (x+45, y+20), 1)

    # Разрез 4 (Вертикальный)
    pygame.draw.line(screen, C_SLASH_GLOW, (x+25, y+5), (x+20, y+45), 3)
    
    # 3. Буква "E" (Рисуем ВСЕГДА, в левом верхнем углу)
    key_surf = font.render("E", True, (255, 255, 255))
    # Рисуем небольшую тень для буквы, чтобы она читалась на фоне разрезов
    key_shadow = font.render("E", True, (0, 0, 0))
    screen.blit(key_shadow, (x + 5, y + 3))
    screen.blit(key_surf, (x + 4, y + 2))

    # 4. Кулдаун (Затемнение + Таймер)
    current_time = pygame.time.get_ticks()
    time_left = max(0, skill_obj.cooldown - (current_time - skill_obj.timer))
    
    if time_left > 0:
        cd_pct = time_left / skill_obj.cooldown
        h_cd = int(size * cd_pct)
        
        # Рисуем полупрозрачный черный прямоугольник снизу вверх
        s = pygame.Surface((size, h_cd), pygame.SRCALPHA)
        s.fill(C_CD_OVERLAY)
        screen.blit(s, (x, y + size - h_cd))
        
        # Текст таймера по центру
        seconds = time_left / 1000.0
        # Если меньше 1 сек, показываем десятые, иначе целые
        txt = f"{seconds:.1f}" if seconds < 1.0 else f"{int(seconds + 0.9)}"
        
        txt_surf = font.render(txt, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=(x + size/2, y + size/2))
        
        # Тень для таймера
        txt_shadow = font.render(txt, True, (0, 0, 0))
        screen.blit(txt_shadow, (txt_rect.x + 1, txt_rect.y + 1))
        screen.blit(txt_surf, txt_rect)
        
        border_color = C_BORDER_CD
    else:
        # Если готово - яркая рамка
        border_color = C_BORDER_READY

    # 5. Рамка (Поверх всего)
    pygame.draw.rect(screen, border_color, rect, 2)
def draw_dash_icon(screen, player_obj, pos, font):
    """
    Отрисовка иконки рывка (Сапог в движении).
    pos: (x, y) левого верхнего угла.
    Почти полная копия draw_skill_icon по структуре, но с другой графикой и логикой КД.
    """
    x, y = pos
    size = 50
    
    # Цвета (Вампирские/Призрачные)
    C_BG = (30, 5, 10)            # Темный фон (как у скилла)
    C_BORDER_READY = (100, 200, 255)# Яркая голубая/белая рамка (готов - контраст к красному скиллу)
    C_BORDER_CD = (50, 80, 100)   # Тусклая рамка (кд)
    
    C_BOOT_FILL = (80, 40, 40)    # Темно-красный/коричневый сапог
    C_BOOT_OUTLINE = (200, 100, 100)
    C_MOTION_GLOW = (150, 220, 255)# Призрачный голубой след
    C_CD_OVERLAY = (0, 0, 0, 180) # Затемнение кд
    
    # 1. Фон квадрата
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, C_BG, rect)
    
    # 2. Иконка: Сапог в прыжке с шлейфом
    # Рисуем стилизованный сапог, летящий вправо-вверх
    
    # Шлейф движения (рисуем ПЕРЕД сапогом, чтобы был на фоне)
    # Три изогнутые линии позади
    pygame.draw.line(screen, C_MOTION_GLOW, (x+5, y+45), (x+25, y+35), 3) # Нижний след
    pygame.draw.line(screen, C_MOTION_GLOW, (x+2, y+35), (x+20, y+25), 2) # Средний след
    pygame.draw.line(screen, C_MOTION_GLOW, (x+10, y+20), (x+25, y+15), 2) # Верхний след

    # Сапог (Полигон)
    # Координаты примерные, образуют форму сапога в профиль
    boot_poly = [
        (x + 20, y + 40), # Пятка низ
        (x + 15, y + 30), # Пятка зад
        (x + 25, y + 10), # Голенище верх-зад
        (x + 38, y + 15), # Голенище верх-перед
        (x + 30, y + 32), # Подъем стопы
        (x + 45, y + 35), # Носок верх
        (x + 42, y + 45), # Носок низ
        (x + 28, y + 42), # Подошва центр
    ]
    pygame.draw.polygon(screen, C_BOOT_FILL, boot_poly)
    pygame.draw.lines(screen, C_BOOT_OUTLINE, True, boot_poly, 2)
    
    # 3. Клавиша "SPACE" (Рисуем ВСЕГДА, в левом верхнем углу, шрифт поменьше если не влезает)
    key_text = "SPC" # Используем сокращение, чтобы влезло
    key_surf = font.render(key_text, True, (255, 255, 255))
    key_shadow = font.render(key_text, True, (0, 0, 0))
    screen.blit(key_shadow, (x + 4, y + 3))
    screen.blit(key_surf, (x + 3, y + 2))

    # 4. Кулдаун (Затемнение + Таймер)
    current_time = pygame.time.get_ticks()
    # Вычисляем оставшееся время на основе таймера игрока
    time_left = max(0, player_obj.dash_cooldown - (current_time - player_obj.dash_timer))
    
    # Если игрок только что дэшнулся и еще в процессе дэша, считаем что КД полный
    if not player_obj.can_dash and time_left <= 0:
         time_left = player_obj.dash_cooldown

    if time_left > 0 and not player_obj.can_dash:
        cd_pct = time_left / player_obj.dash_cooldown
        h_cd = int(size * cd_pct)
        
        # Рисуем полупрозрачный черный прямоугольник снизу вверх
        s = pygame.Surface((size, h_cd), pygame.SRCALPHA)
        s.fill(C_CD_OVERLAY)
        screen.blit(s, (x, y + size - h_cd))
        
        # Текст таймера по центру
        seconds = time_left / 1000.0
        txt = f"{seconds:.1f}" if seconds < 1.0 else f"{int(seconds + 0.9)}"
        
        txt_surf = font.render(txt, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect(center=(x + size/2, y + size/2))
        
        txt_shadow = font.render(txt, True, (0, 0, 0))
        screen.blit(txt_shadow, (txt_rect.x + 1, txt_rect.y + 1))
        screen.blit(txt_surf, txt_rect)
        
        border_color = C_BORDER_CD
    else:
        # Если готово - яркая рамка
        border_color = C_BORDER_READY

    # 5. Рамка (Поверх всего)
    pygame.draw.rect(screen, border_color, rect, 2)