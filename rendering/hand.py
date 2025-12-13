import pygame
import math

# ==========================================
# --- НАСТРОЙКИ ---
# ==========================================
C_SKIN_BASE = (60, 170, 160)
C_OUTLINE = (15, 20, 35)
C_JOINT = (40, 120, 110)

def draw_segment_poly(surface, start_pos, angle_rad, length, w_start, w_end, color, outline_color):
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
    
    pygame.draw.circle(surface, outline_color, (int(start_pos[0]), int(start_pos[1])), 2)
    return end_pos

class RoboticHand:
    def __init__(self, x, y, is_left=True):
        self.pos = (x, y)
        self.is_left = is_left
        self.global_angle = 0
        
        # Длины фаланг те же, короткие
        self.finger_configs = {
            'index':  {'lens': [14, 10, 8],  'widths': [7, 6, 4],   'base_offset': -10},
            'middle': {'lens': [15, 11, 9],  'widths': [7.5, 6.5, 4], 'base_offset': -2},
            'ring':   {'lens': [13, 10, 8],  'widths': [7, 6, 4],   'base_offset': 6},
            'pinky':  {'lens': [10, 8, 6],   'widths': [6, 5, 3],   'base_offset': 13}, 
            'thumb':  {'lens': [12, 10],     'widths': [8, 6],      'base_offset': -14}
        }

    def draw(self, surface, grip_factor=0.5):
        cx, cy = self.pos
        wrist_rad = math.radians(self.global_angle)
        
        # === 1. КОРОТКАЯ ЛАДОНЬ ===
        
        # Сегмент 1 (Основание) - стал короче (12 пикселей)
        palm_seg1_len = 12 
        palm_seg1_w_start = 14
        palm_seg1_w_end = 18
        
        # При сжатии ладонь чуть "чашечкой" сгибается (совсем немного)
        palm_curl = grip_factor * 0.15
        angle_seg1 = wrist_rad + (palm_curl if self.is_left else -palm_curl)
        
        mid_palm_pos = draw_segment_poly(surface, (cx, cy), angle_seg1, palm_seg1_len, 
                                         palm_seg1_w_start, palm_seg1_w_end, C_SKIN_BASE, C_OUTLINE)
        
        # Сегмент 2 (Пясть) - стал короче (14 пикселей)
        palm_seg2_len = 14 
        palm_seg2_w_start = 18
        # Ширина осталась большой (32), чтобы держать мизинец
        palm_seg2_w_end = 32 
        
        angle_seg2 = angle_seg1 + (palm_curl * 0.5 if self.is_left else -palm_curl * 0.5)
        
        knuckles_pos = draw_segment_poly(surface, mid_palm_pos, angle_seg2, palm_seg2_len,
                                         palm_seg2_w_start, palm_seg2_w_end, C_SKIN_BASE, C_OUTLINE)

        # Сустав запястья
        pygame.draw.circle(surface, C_SKIN_BASE, (int(cx), int(cy)), 6)
        pygame.draw.circle(surface, C_OUTLINE, (int(cx), int(cy)), 6, 1)

        # === 2. ПАЛЬЦЫ (ПОРЯДОК ОТРИСОВКИ) ===
        # Рисуем от дальнего к ближнему
        fingers_order = ['pinky', 'ring', 'middle', 'index']
        if not self.is_left: fingers_order = fingers_order[::-1]

        for f_name in fingers_order:
            self._draw_finger(surface, f_name, knuckles_pos, angle_seg2, grip_factor)

        # Большой палец рисуем последним, чтобы он перекрывал кулак при сжатии
        self._draw_thumb(surface, mid_palm_pos, angle_seg2, grip_factor)

    def _draw_finger(self, surface, name, origin, base_angle_rad, grip):
        cfg = self.finger_configs[name]
        offset = cfg['base_offset']
        
        # Расчет позиции
        d_cos = math.cos(base_angle_rad)
        d_sin = math.sin(base_angle_rad)
        p_cos = -d_sin
        p_sin = d_cos
        
        start_pos = (origin[0] + p_cos * offset, origin[1] + p_sin * offset)
        
        # === ЛОГИКА "ВПЕРЕД" (FORWARD CURL) ===
        # Мы убрали 'convergence' (сдвиг в бок).
        # Пальцы остаются параллельными в основании.
        
        # Небольшой веер (fan_angle) нужен, чтобы пальцы не выглядели как забор, 
        # но он статичен и не меняется от grip.
        fan_angle = offset * 0.005 # Очень маленький веер
        
        current_pos = start_pos
        current_angle = base_angle_rad + fan_angle
        
        # Сила скручивания (Curl)
        # 160 градусов - это почти полный оборот (спираль)
        total_curl_potential = 160 * grip 
        
        # Направление сгиба (всегда "вниз" относительно ладони)
        # Если is_left=True и угол 0 (вправо), низ это +Y (угол увеличивается)
        # Подбираем направление экспериментально, чтобы гнулись "в ладонь"
        bend_dir = 1
        
        for i in range(len(cfg['lens'])):
            length = cfg['lens'][i]
            w_s = cfg['widths'][i]
            w_e = cfg['widths'][i] * 0.75
            
            # --- КАСКАДНОЕ СЖАТИЕ ---
            # Суставы сгибаются неравномерно. 
            # Кончик (i=2) начинает сгибаться раньше, чем основание (i=0).
            # Это создает эффект "сворачивания".
            
            # Базовый сгиб для всех
            segment_curl = total_curl_potential / 2.5
            
            # Добавка для кончиков (чтобы они сильнее закручивались)
            if i > 0: 
                segment_curl += (total_curl_potential / 3.0) * grip
            
            current_angle += math.radians(segment_curl) * bend_dir
            
            current_pos = draw_segment_poly(surface, current_pos, current_angle, length, w_s, w_e, C_SKIN_BASE, C_OUTLINE)

    def _draw_thumb(self, surface, palm_mid_pos, palm_angle, grip):
        cfg = self.finger_configs['thumb']
        
        d_cos = math.cos(palm_angle)
        d_sin = math.sin(palm_angle)
        p_cos = -d_sin
        p_sin = d_cos
        
        # Крепление большого пальца
        side_off = -12 
        back_off = -4
        
        start_pos = (palm_mid_pos[0] + p_cos * side_off + d_cos * back_off,
                     palm_mid_pos[1] + p_sin * side_off + d_sin * back_off)
        
        # Большой палец торчит в бок (противопоставлен)
        thumb_base = palm_angle - math.radians(50) 
        
        # === ЛОГИКА БОЛЬШОГО ПАЛЬЦА ===
        # При сжатии он идет ПОПЕРЕК ладони (закрывает кулак)
        # Это значит, он вращается сильнее к центру
        thumb_sweep = math.radians(70 * grip)
        
        current_pos = start_pos
        current_angle = thumb_base + thumb_sweep
        
        for i in range(len(cfg['lens'])):
            length = cfg['lens'][i]
            w_s = cfg['widths'][i]
            w_e = cfg['widths'][i] * 0.8
            
            # Фаланги большого пальца тоже сгибаются
            current_angle += math.radians(60 * grip)
            
            current_pos = draw_segment_poly(surface, current_pos, current_angle, length, w_s, w_e, C_SKIN_BASE, C_OUTLINE)

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Short Hand & Forward Grip")
    clock = pygame.time.Clock()
    
    hand = RoboticHand(300, 300, is_left=True)
    hand.global_angle = -90
    grip = 0.5 
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: hand.global_angle -= 3
        if keys[pygame.K_RIGHT]: hand.global_angle += 3
        if keys[pygame.K_UP]: grip = min(1.0, grip + 0.02)
        if keys[pygame.K_DOWN]: grip = max(0.0, grip - 0.02)
            
        screen.fill((20, 20, 30))
        
        # Инфо
        font = pygame.font.SysFont("Arial", 16)
        txt = font.render(f"Grip: {grip:.2f} (Forward curl)", True, (200, 200, 200))
        screen.blit(txt, (10, 10))
        
        hand.draw(screen, grip_factor=grip)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()