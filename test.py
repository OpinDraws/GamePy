import pygame
import math

def generate_archangel_icon(size=128):
    """
    Генерирует иконку босса Архангела процедурно (кодом).
    Возвращает pygame.Surface с прозрачным фоном.
    size: размер квадратной иконки (по умолчанию 128x128).
    """
    # Создаем поверхность с поддержкой альфа-канала (прозрачности)
    icon_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # --- Палитра (на основе скетча) ---
    # Используем яркие циановые и белые цвета для свечения
    C_WHITE = (255, 255, 255)
    C_CYAN_BRIGHT = (100, 255, 255)
    C_CYAN_MID = (50, 200, 230)
    C_BLUE_DARK = (30, 80, 150) # Для контуров и теней

    cx, cy = size // 2, size // 2 # Центр иконки

    # --- Вспомогательная функция для рисования свечения ---
    def draw_glow(surf, pos, radius, color, intensity_alpha=100):
        """Рисует мягкое свечение используя аддитивное смешивание"""
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Рисуем круг с альфа-каналом
        pygame.draw.circle(glow_surf, (*color, intensity_alpha), (radius, radius), radius)
        # Накладываем в режиме сложения цветов (BLEND_RGBA_ADD) для яркости
        surf.blit(glow_surf, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)

    # ================= РИСОВАНИЕ БОССА =================

    # 1. Фон/Аура (общее синее свечение позади фигуры)
    draw_glow(icon_surf, (cx, cy + size//6), size//2, C_BLUE_DARK, 80)

    # 2. Нимб (Кольцо над головой)
    halo_pos = (cx, size // 4.5)
    halo_radius = size // 5
    # Свечение нимба
    draw_glow(icon_surf, halo_pos, halo_radius + 5, C_CYAN_BRIGHT, 120)
    # Само кольцо (белое, толстое)
    pygame.draw.circle(icon_surf, C_WHITE, halo_pos, halo_radius, width=int(size/30))

    # 3. Тело и Голова
    # Голова (эллипс)
    head_rect = pygame.Rect(0, 0, size//4, size//3.2)
    head_rect.center = (cx, size // 2.3)
    pygame.draw.ellipse(icon_surf, C_CYAN_MID, head_rect)
    # Тонкий контур головы
    pygame.draw.ellipse(icon_surf, C_BLUE_DARK, head_rect, width=2)

    # Торс (полигон в форме трапеции)
    torso_top_y = size // 2
    torso_bottom_y = size // 1.25
    torso_points = [
        (cx - size//6, torso_top_y),       # Левое плечо
        (cx + size//6, torso_top_y),       # Правое плечо
        (cx + size//10, torso_bottom_y),   # Правое бедро
        (cx - size//10, torso_bottom_y),   # Левое бедро
    ]
    pygame.draw.polygon(icon_surf, C_CYAN_MID, torso_points)
    
    # 4. Глаз на груди (Символ из скетча)
    eye_pos = (cx, size // 1.7)
    # Свечение из груди
    draw_glow(icon_surf, eye_pos, size//8, C_CYAN_BRIGHT, 150)
    # Белок глаза (эллипс)
    eye_rect = pygame.Rect(0, 0, size//5, size//8)
    eye_rect.center = eye_pos
    pygame.draw.ellipse(icon_surf, C_WHITE, eye_rect)
    # Зрачок (циан)
    pygame.draw.circle(icon_surf, C_CYAN_MID, eye_pos, size//18)

    # 5. Светящиеся руки (на основе скетча)
    hand_y = size // 1.5
    hand_offset_x = size // 3.5
    # Свечение левой руки
    draw_glow(icon_surf, (cx - hand_offset_x, hand_y), size//9, C_WHITE, 180)
    # Свечение правой руки
    draw_glow(icon_surf, (cx + hand_offset_x, hand_y), size//9, C_WHITE, 180)
    
    # 6. Финальная рамка для иконки (стилизация под интерфейс)
    # Внутренняя светящаяся рамка
    pygame.draw.rect(icon_surf, C_CYAN_BRIGHT, (1, 1, size-2, size-2), width=2)
    # Внешняя темная рамка
    pygame.draw.rect(icon_surf, C_BLUE_DARK, (0, 0, size, size), width=2)

    return icon_surf

# ==========================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ (Можно запустить этот файл отдельно)
# ==========================================
if __name__ == "__main__":
    pygame.init()
    # Создаем окно как на твоем скриншоте (примерно)
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Archangel Boss Icon Test")
    clock = pygame.time.Clock()

    # --- ВАЖНО: Генерируем иконку ОДИН РАЗ перед игровым циклом ---
    # Размер 150x150, чтобы было хорошо видно в углу
    ICON_SIZE = 150
    boss_portrait = generate_archangel_icon(ICON_SIZE)
    
    # Координаты для правого верхнего угла (с отступом 20 пикселей)
    icon_x = WIDTH - ICON_SIZE - 20
    icon_y = 20

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Очистка экрана (темный фон как в игре)
        screen.fill((20, 20, 35))

        # 2. Отрисовка игры.... (тут твой игровой мир)
        # Для примера нарисуем что-то на фоне
        pygame.draw.rect(screen, (40, 30, 60), (100, 100, 200, 300))

        # 3. ОТРИСОВКА ИНТЕРФЕЙСА
        # Просто рисуем готовую картинку босса в нужном месте
        screen.blit(boss_portrait, (icon_x, icon_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()