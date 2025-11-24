import pygame
import random
import math
from config import (
    all_sprites, particles, 
    COLOR_PARTICLE, COLOR_VAMPIRE_SKIN, 
    COLOR_VAMPIRE_CLOAK, COLOR_VAMPIRE_ACCENT, 
    COLOR_MONSTER_BODY, COLOR_MONSTER_OUTLINE, 
    COLOR_MONSTER_EYE, COLOR_MONSTER_GLOW,
    COLOR_BLOOD_CORE, 
    TILE_SIZE # Импортируем, если он нужен в config
)

# --- Добавление цветов, необходимых для Архангела (если их нет в config.py) ---
# Для работы GhostMistVFX требуется палитра Архангела. Предполагаем, что они выглядят так:
C_CYAN_DEEP = (0, 100, 150, 255)         
C_CYAN_BRIGHT = (50, 200, 255, 255)      
C_CYAN_GLOW = (100, 255, 255, 150)       
C_GOLD_BRIGHT = (255, 215, 50, 255) # Для волны щита


# --- Хелперы для Альфа-Рендеринга (Для GhostMistVFX) ---

def draw_alpha_polygon(surface, color, points):
    """Рисует полигон с поддержкой альфа-канала (прозрачности)."""
    if len(points) < 3: return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    w, h = int(max_x - min_x), int(max_y - min_y)
    if w <= 0 or h <= 0: return
    
    shape_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    local_points = [(p[0] - min_x, p[1] - min_y) for p in points]
    pygame.draw.polygon(shape_surf, color, local_points)
    surface.blit(shape_surf, (min_x, min_y))

def draw_alpha_circle(surface, color, center, radius):
    """Рисует круг с поддержкой альфа-канала."""
    radius = int(radius)
    if radius <= 0: return
    # Если передана Vector2, преобразуем в кортеж
    if isinstance(center, pygame.math.Vector2):
        center = (int(center.x), int(center.y))
        
    target_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    
    # Проверка на выход за пределы экрана
    if target_rect.width <= 0 or target_rect.height <= 0: return
    
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)

# --- НОВЫЙ ЭФФЕКТ: ВОЛНА ЩИТА ---
class ShieldWaveVFX(pygame.sprite.Sprite):
    """Золотая волна, расходящаяся от босса, отталкивающая игрока."""
    def __init__(self, center_pos, max_radius=150, damage=15, push_force=20, duration=20):
        super().__init__()
        particles.add(self)
        all_sprites.add(self)
        
        self.pos = pygame.math.Vector2(center_pos)
        self.max_radius = max_radius
        self.damage = damage
        self.push_force = push_force
        self.duration = duration
        self.time_alive = 0
        
        self.damage_applied = False # Урон наносится один раз
        
        # Визуал
        self.color = C_GOLD_BRIGHT
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.time_alive += 1
        progress = self.time_alive / self.duration
        
        # Текущий радиус волны
        current_radius = self.max_radius * progress
        
        # Проверка коллизии с игроком (Кольцо урона)
        if not self.damage_applied:
            # Ищем игрока в группе
            # (В идеале передавать player в __init__, но можно найти через all_sprites для универсальности)
            for sprite in all_sprites:
                if type(sprite).__name__ == 'Player':
                    dist = (self.pos - sprite.pos).length()
                    
                    # Если игрок внутри радиуса волны
                    if dist < current_radius + 20: # +20 для ширины волны
                        # Наносим урон
                        sprite.take_damage(self.damage)
                        
                        # Отталкивание
                        if dist > 0:
                            push_dir = (sprite.pos - self.pos).normalize()
                        else:
                            push_dir = pygame.math.Vector2(1, 0)
                            
                        sprite.pos += push_dir * self.push_force
                        self.damage_applied = True # Урон нанесен
        
        if self.time_alive >= self.duration:
            self.kill()

    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        progress = self.time_alive / self.duration
        
        current_radius = self.max_radius * progress
        width = int(20 * (1 - progress)) # Волна истончается
        alpha = int(255 * (1 - progress))
        
        if width > 1:
            pygame.draw.circle(surface, self.color[:3] + (alpha,), (int(draw_pos.x), int(draw_pos.y)), int(current_radius), width)
            # Внутреннее свечение
            draw_alpha_circle(surface, self.color[:3] + (alpha // 3,), draw_pos, int(current_radius * 0.9))


class CelestialSmiteVFX(pygame.sprite.Sprite):
# ... (Код CelestialSmiteVFX остается без изменений, как в предыдущей версии)
    """Эффект AoE-атаки Celestial Smite: индикатор, взрыв и урон."""
    
    # --- Константы Атаки ---
    AOE_RADIUS = 80             # Радиус AoE круга для индикатора и урона
    BLAST_MAX_RADIUS = 120      # Максимальный радиус взрыва
    SMITE_SHAKE_INTENSITY = 15  # Интенсивность тряски экрана

    # *** ИЗМЕНЕНИЕ: pos теперь может быть Vector2 или вызываемой функцией (pos_getter) ***
    def __init__(self, pos, blast_delay_frames, blast_duration_frames, damage, player, shake_func, prep_delay_frames=0):
        super().__init__()
        particles.add(self) 
        all_sprites.add(self)
        
        # *** ИЗМЕНЕНИЕ: pos может быть Vector2 или функцией, которая возвращает Vector2 ***
        self.initial_pos_or_getter = pos 
        
        # Фактическая позиция взрыва, будет установлена при начале подготовки
        self.pos = pygame.math.Vector2(0, 0) 

        self.player = player
        self.damage = damage
        self.shake_func = shake_func
        
        # Тайминги
        self.prep_delay = prep_delay_frames 
        self.blast_delay = blast_delay_frames
        self.blast_duration = blast_duration_frames
        self.time_alive = 0
        
        # Состояния
        self.IS_PREPARING = False # Начинаем с фазы ожидания (если prep_delay > 0)
        self.BLAST_PHASE = False
        self.damage_applied = False
        
        # Визуал
        self.color_bright = C_CYAN_BRIGHT
        self.color_glow = C_CYAN_GLOW
        self.image = pygame.Surface((1,1)) 
        
        # Предварительная установка rect (будет скорректирована в update)
        if isinstance(self.initial_pos_or_getter, pygame.math.Vector2):
            self.pos = self.initial_pos_or_getter
        self.rect = self.image.get_rect(center=self.pos)


    def update(self, dt):
        self.time_alive += 1
        
        # --- ФАЗА ОЖИДАНИЯ (Prep Delay) ---
        if not self.IS_PREPARING:
            if self.time_alive >= self.prep_delay:
                
                # *** ИЗМЕНЕНИЕ: Фиксация позиции в момент начала подготовки ***
                if callable(self.initial_pos_or_getter):
                    # Если переданная 'pos' была функцией, вызываем её сейчас
                    self.pos = self.initial_pos_or_getter() 
                else:
                    # Если была передана Vector2, используем её
                    self.pos = self.initial_pos_or_getter
                
                self.rect.center = self.pos # Обновляем Rect
                self.IS_PREPARING = True
                self.time_alive = 0 # Сбрасываем счетчик для фазы подготовки
            return 
        
        # --- ФАЗА ПОДГОТОВКИ (Prepare) ---
        
        if not self.BLAST_PHASE and self.time_alive >= self.blast_delay:
            # --- Фаза ВЗРЫВА ---
            self.BLAST_PHASE = True
            
        if self.BLAST_PHASE:
            # Нанесение урона в первый кадр взрыва
            if not self.damage_applied:
                self.check_damage()
                self.shake_func(self.SMITE_SHAKE_INTENSITY)
                self.damage_applied = True
                
            # Завершение
            if self.time_alive >= self.blast_delay + self.blast_duration:
                self.kill()

    # check_damage и draw_custom остаются без изменений, так как они используют self.pos

    def check_damage(self):
        """Проверяет коллизию игрока с AoE и наносит урон."""
        
        # Создаем временный Rect для области урона
        smite_rect = pygame.Rect(
            self.pos.x - self.AOE_RADIUS,
            self.pos.y - self.AOE_RADIUS,
            self.AOE_RADIUS * 2,
            self.AOE_RADIUS * 2
        )
        
        player_hitbox = self.player.get_hitbox_rect()
        
        if player_hitbox.colliderect(smite_rect):
            self.player.take_damage(self.damage)


    def draw_custom(self, surface, offset):
        """Отрисовка индикатора (AoE) или взрыва (BLAST)."""
        
        # Если мы в фазе ожидания (prep_delay), не рисуем ничего
        if not self.IS_PREPARING:
            return

        draw_pos = self.pos + offset
        
        if not self.BLAST_PHASE:
            # --- Фаза PREPARE (Индикатор AoE) ---
            progress = self.time_alive / self.blast_delay
            
            # Пульсирующий альфа-канал
            # time_alive здесь - это счетчик в фазе подготовки, поэтому пульсация будет уникальной для каждого AoE
            pulse = math.sin(self.time_alive * 0.4) * 0.15 + 0.85
            # Прогрессирующее увеличение альфа-канала
            alpha_mult = progress * pulse 
            alpha = int(255 * alpha_mult * 0.7) # Макс альфа 70%
            
            # 1. Свечение (большой, полупрозрачный круг)
            glow_radius = self.AOE_RADIUS * 1.2
            draw_alpha_circle(surface, self.color_glow[:3] + (int(alpha * 0.7),), 
                              draw_pos, glow_radius)
                              
            # 2. Индикатор (четкий круг)
            border_width = 1 + int(progress * 2) 
            pygame.draw.circle(surface, self.color_bright[:3] + (alpha,), 
                               (int(draw_pos.x), int(draw_pos.y)), self.AOE_RADIUS, border_width)
            
            # Индикатор готовности в центре
            inner_radius = 5 + int(progress * 5)
            draw_alpha_circle(surface, (255, 255, 255, 255), draw_pos, inner_radius)
            
        else:
            # --- Фаза BLAST (Взрыв) ---
            progress = (self.time_alive - self.blast_delay) / self.blast_duration
            
            # Быстрое расширение и исчезновение
            current_radius = self.AOE_RADIUS + (self.BLAST_MAX_RADIUS - self.AOE_RADIUS) * progress
            alpha = int(255 * (1.0 - progress) * 0.8) # Быстрый fade-out до 0
            
            # Белый/яркий взрыв
            blast_color = (255, 255, 255, alpha)
            draw_alpha_circle(surface, blast_color, draw_pos, current_radius)
            draw_alpha_circle(surface, self.color_bright[:3] + (alpha // 2,), draw_pos, current_radius * 0.7)

# --- СУЩЕСТВУЮЩИЕ КЛАССЫ (GraphicsGenerator, Particle, ScreenShake, GhostMistVFX) ---
# ... (Остальной код vfx.py)
class GraphicsGenerator:
# [Immersive content redacted for brevity. Original file content is preserved below.]
    @staticmethod
    def create_vampire_sprite(radius):
        """
        Рисует вампира вид сверху: плащ и голова.
        Возвращает Surface, смотрящий 'вправо' (для последующей ротации).
        """
        size = radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        
        # 1. Плащ (тело) - вытянутый овал
        rect_cloak = pygame.Rect(0, 0, radius * 2.2, radius * 1.8)
        rect_cloak.center = center
        pygame.draw.ellipse(surf, COLOR_VAMPIRE_CLOAK, rect_cloak)
        
        # Акцент плаща (воротник)
        pygame.draw.circle(surf, COLOR_VAMPIRE_ACCENT, (center[0] - 2, center[1]), radius, 2)

        # 2. Голова - бледный круг
        head_pos = (center[0] + 3, center[1])
        pygame.draw.circle(surf, COLOR_VAMPIRE_SKIN, head_pos, radius * 0.6)
        
        # 3. Глаза (смотрят вправо)
        eye_offset_x = 4
        eye_offset_y = 3
        pygame.draw.circle(surf, (255, 0, 0), (head_pos[0] + eye_offset_x, head_pos[1] - eye_offset_y), 2)
        pygame.draw.circle(surf, (255, 0, 0), (head_pos[0] + eye_offset_x, head_pos[1] + eye_offset_y), 2)
        
        return surf

    @staticmethod
    def create_monster_sprite(radius, seed_val=None):
        """
        Создает уникального монстра с помощью шума.
        Генерирует полигон с 'шипами' и неравномерностью.
        """
        if seed_val:
            random.seed(seed_val)
            
        size = radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        
        # Генерация вершин полигона (органическая форма)
        points = []
        num_points = 12 # Количество вершин
        for i in range(num_points):
            angle = math.radians(i * (360 / num_points))
            # Шум: радиус варьируется от 0.7 до 1.3 от базового
            variation = random.uniform(0.7, 1.4)
            r = radius * variation
            x = center[0] + math.cos(angle) * r
            y = center[1] + math.sin(angle) * r
            points.append((x, y))
            
        # Рисуем тело
        pygame.draw.polygon(surf, COLOR_MONSTER_BODY, points)
        pygame.draw.polygon(surf, COLOR_MONSTER_OUTLINE, points, 2)
        
        # Рисуем глаза (случайное количество и положение внутри тела)
        num_eyes = random.randint(1, 4)
        for _ in range(num_eyes):
            # Случайное смещение от центра, но не слишком далеко
            offset_angle = random.uniform(0, 6.28)
            offset_dist = random.uniform(0, radius * 0.5)
            ex = center[0] + math.cos(offset_angle) * offset_dist
            ey = center[1] + math.sin(offset_angle) * offset_dist
            
            eye_radius = random.randint(2, 5)
            # Желтый глаз
            pygame.draw.circle(surf, COLOR_MONSTER_EYE, (ex, ey), eye_radius)
            # Вертикальный зрачок
            pygame.draw.line(surf, (0,0,0), (ex, ey - eye_radius + 1), (ex, ey + eye_radius - 1), 1)

        # Сброс сида, чтобы не повлиять на другие рандомы в игре
        if seed_val:
            random.seed()
            
        return surf

    @staticmethod
    def create_blood_bolt():
        """Снаряд магии крови"""
        surf = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Внешнее свечение
        pygame.draw.circle(surf, (100, 0, 0, 100), (10, 10), 8)
        # Ядро
        pygame.draw.circle(surf, COLOR_BLOOD_CORE, (10, 10), 4)
        return surf

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color=COLOR_PARTICLE, speed=3, decay=10, scale_speed=0):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        angle = random.uniform(0, 6.28)
        self.vel = pygame.math.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(speed*0.5, speed)
        
        self.lifetime = 255
        self.decay = decay
        self.color = color
        self.base_size = random.randint(3, 6)
        self.size = self.base_size
        self.scale_speed = scale_speed # Если нужно, чтобы частица уменьшалась/росла
        
        self.image = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.pos)
        
    def update(self, dt):
        self.pos += self.vel * dt * 60
        self.lifetime -= self.decay * dt * 60
        self.size -= self.scale_speed * dt * 60
        
        if self.lifetime <= 0 or self.size <= 0:
            self.kill()
        else:
            self.image.fill((0,0,0,0))
            alpha = max(0, int(self.lifetime))
            curr_color = (*self.color[:3], alpha)
            
            # Рисуем квадрат для разнообразия или круг
            pygame.draw.circle(self.image, curr_color, (int(self.size), int(self.size)), int(self.size))
            self.rect = self.image.get_rect(center=self.pos)

class ScreenShake:
    """Менеджер тряски экрана"""
    def __init__(self):
        self.intensity = 0
        self.decay = 0.9
        
    def shake(self, intensity):
        self.intensity = max(self.intensity, intensity)
        
    def get_offset(self):
        if self.intensity > 0.5:
            offset_x = random.uniform(-self.intensity, self.intensity)
            offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= self.decay
            return pygame.math.Vector2(offset_x, offset_y)
        return pygame.math.Vector2(0, 0)


# --- НОВЫЙ КЛАСС ДЛЯ ДЫМКИ (Phantom Spear Mist) ---

class GhostMistVFX(pygame.sprite.Sprite):
    """Эффект появления призрачного копья из дымки."""
    def __init__(self, pos, duration=40, size_start=10, size_end=80):
        super().__init__()
        # Предполагаем, что PARTICLE_LAYER = 3 или определен в config.py
        # Добавляем его в группу частиц, чтобы он рисовался в правильном порядке
        particles.add(self) 
        all_sprites.add(self)
        
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration  # Длительность анимации в кадрах
        self.time_alive = 0
        self.size_start = size_start
        self.size_end = size_end
        
        self.color_base = C_CYAN_BRIGHT
        self.color_glow = C_CYAN_GLOW
        self.image = pygame.Surface((1,1)) # Заглушка
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.time_alive += 1
        if self.time_alive >= self.duration:
            self.kill()

    def draw_custom(self, surface, offset):
        """Отрисовка эффекта дымки."""
        draw_pos = self.pos + offset
        
        progress = self.time_alive / self.duration
        
        # Фазы: появление (0-0.2), пик (0.2-0.8), исчезновение (0.8-1.0)
        if progress < 0.2: 
            alpha_mult = progress / 0.2
        elif progress > 0.8: 
            alpha_mult = 1.0 - (progress - 0.8) / 0.2
        else: 
            alpha_mult = 1.0
            
        alpha_mult = max(0.0, min(1.0, alpha_mult))

        # Размер дымки: от size_start до size_end
        current_size = self.size_start + (self.size_end - self.size_start) * progress
        
        # Отрисовка нескольких слоев для эффекта дымки
        for i in range(3):
            # Добавляем случайное смещение для эффекта "клубящегося" дыма
            layer_jitter_offset = pygame.math.Vector2(random.uniform(-current_size*0.05, current_size*0.05),
                                                      random.uniform(-current_size*0.05, current_size*0.05))
            
            layer_size = current_size * (1 - i * 0.15)
            layer_alpha_base = int(self.color_base[3] * alpha_mult * (0.8 - i * 0.2))
            layer_alpha_glow = int(self.color_glow[3] * alpha_mult * (0.5 - i * 0.1))

            # Основная форма дымки (полупрозрачный круг/овал)
            draw_alpha_circle(surface, self.color_base[:3] + (layer_alpha_base,), 
                              draw_pos + layer_jitter_offset, layer_size)
            
            # Свечение по краям
            draw_alpha_circle(surface, self.color_glow[:3] + (layer_alpha_glow,), 
                              draw_pos + layer_jitter_offset * 0.5, layer_size * 0.7)