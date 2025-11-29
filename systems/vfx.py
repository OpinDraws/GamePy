import pygame
import random
import math
from core.asset_manager import AssetManager
from core.config import (
    all_sprites, particles, 
    COLOR_PARTICLE, COLOR_VAMPIRE_SKIN, 
    COLOR_VAMPIRE_CLOAK, COLOR_VAMPIRE_ACCENT, 
    COLOR_MONSTER_BODY, COLOR_MONSTER_OUTLINE, 
    COLOR_MONSTER_EYE, COLOR_MONSTER_GLOW,
    COLOR_BLOOD_CORE, 
    TILE_SIZE 
)
# ВАЖНО: Проверьте этот импорт. Если boss_weapons еще не перенесен, путь может отличаться.
# Если вы уже на этапе 13, путь должен быть entities.weapons.boss_weapons.
# Если возникнет ошибка импорта ChaosMagicProjectile, мы поправим её позже.
# Пока используем локальный импорт внутри метода spawn_projectile, чтобы избежать циклов.

# --- Цвета ---
C_CYAN_DEEP = (0, 100, 150, 255)         
C_CYAN_BRIGHT = (50, 200, 255, 255)      
C_CYAN_GLOW = (100, 255, 255, 150)       
C_GOLD_BRIGHT = (255, 215, 50, 255) 

C_RED_DEEP = (150, 0, 0, 255)
C_RED_BRIGHT = (255, 50, 50, 255)
C_RED_GLOW = (255, 100, 100, 150)

C_VOID_PURPLE = (100, 0, 150, 200) 
C_VOID_BLACK = (20, 0, 30, 255)


# --- Хелперы ---

def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))

def draw_alpha_polygon(surface, color, points):
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
    radius = int(radius)
    if radius <= 0: return
    if isinstance(center, pygame.math.Vector2):
        center = (int(center.x), int(center.y))
        
    target_rect = pygame.Rect(center[0]-radius, center[1]-radius, radius*2, radius*2)
    if target_rect.width <= 0 or target_rect.height <= 0: return
    
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)

# --- ЭФФЕКТЫ ---

class ChaosRiftVFX(pygame.sprite.Sprite):
    """Разлом, который открывается и стреляет магией."""
    def __init__(self, pos, duration_frames, player):
        super().__init__()
        particles.add(self)
        all_sprites.add(self)
        
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration_frames
        self.player = player
        self.time_alive = 0
        
        self.shoot_interval = 6 
        self.shoot_timer = 0
        
        self.max_radius = 45
        self.radius = 0
        self.rotation_offset = random.uniform(0, 360)
        
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.time_alive += 1
        
        progress = self.time_alive / self.duration
        if progress < 0.1:
            scale = progress / 0.1
        elif progress > 0.9:
            scale = (1.0 - progress) / 0.1
        else:
            scale = 1.0
            
        self.radius = self.max_radius * scale
        self.rotation_offset += 2 
        
        if scale > 0.8:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                self.shoot_timer = 0
                self.spawn_projectile()
        
        if self.time_alive >= self.duration:
            self.kill()

    def spawn_projectile(self):
        # Локальный импорт во избежание циклических зависимостей
        # Путь зависит от того, выполнили вы Этап 13 или нет.
        # Если папка entities/weapons создана:
        from entities.weapons.boss_weapons import ChaosMagicProjectile
        
        target = self.player.pos + pygame.math.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
        ChaosMagicProjectile(self.pos, target, all_sprites)

    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        if self.radius < 1: return
        
        num_arcs = 3
        for i in range(num_arcs):
            angle = self.rotation_offset + (i * 360 / num_arcs)
            rad_angle = math.radians(angle)
            
            arc_offset = pygame.math.Vector2(math.cos(rad_angle), math.sin(rad_angle)) * (self.radius * 0.8)
            p1 = draw_pos + arc_offset
            p2 = draw_pos - arc_offset
            
            pygame.draw.line(surface, C_CYAN_BRIGHT, p1, p2, 2)
            draw_alpha_circle(surface, C_CYAN_GLOW, p1, int(self.radius * 0.3))

        draw_alpha_circle(surface, (20, 10, 40, 200), draw_pos, int(self.radius))
        
        pulse = (math.sin(pygame.time.get_ticks() * 0.02) * 0.2 + 0.8)
        core_radius = int(self.radius * 0.3 * pulse)
        
        if core_radius > 0:
            draw_alpha_circle(surface, C_RED_GLOW, draw_pos, int(core_radius * 1.5))
            pygame.draw.circle(surface, C_RED_BRIGHT, (int(draw_pos.x), int(draw_pos.y)), core_radius)
            pygame.draw.circle(surface, (255, 255, 200), (int(draw_pos.x), int(draw_pos.y)), int(core_radius * 0.5))


class ShieldWaveVFX(pygame.sprite.Sprite):
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
        self.damage_applied = False 
        self.color = C_GOLD_BRIGHT
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.time_alive += 1
        progress = self.time_alive / self.duration
        current_radius = self.max_radius * progress
        
        if not self.damage_applied:
            for sprite in all_sprites:
                if type(sprite).__name__ == 'Player':
                    dist = (self.pos - sprite.pos).length()
                    if dist < current_radius + 20: 
                        sprite.take_damage(self.damage)
                        if dist > 0:
                            push_dir = (sprite.pos - self.pos).normalize()
                        else:
                            push_dir = pygame.math.Vector2(1, 0)
                        sprite.pos += push_dir * self.push_force
                        self.damage_applied = True 
        
        if self.time_alive >= self.duration:
            self.kill()

    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        progress = self.time_alive / self.duration
        current_radius = self.max_radius * progress
        width = int(20 * (1 - progress)) 
        alpha = int(255 * (1 - progress))
        
        if width > 1:
            pygame.draw.circle(surface, self.color[:3] + (alpha,), (int(draw_pos.x), int(draw_pos.y)), int(current_radius), width)
            draw_alpha_circle(surface, self.color[:3] + (alpha // 3,), draw_pos, int(current_radius * 0.9))


class CelestialSmiteVFX(pygame.sprite.Sprite):
    """Эффект AoE-атаки Celestial Smite."""
    AOE_RADIUS_BASE = 80        
    BLAST_MAX_RADIUS_BASE = 120 
    SMITE_SHAKE_INTENSITY = 15 

    def __init__(self, pos, blast_delay_frames, blast_duration_frames, damage, player, shake_func, prep_delay_frames=0, size_mult=1.0, color_mode='cyan'):
        super().__init__()
        particles.add(self) 
        all_sprites.add(self)
        
        self.initial_pos_or_getter = pos 
        self.pos = pygame.math.Vector2(0, 0) 

        self.player = player
        self.damage = damage
        self.shake_func = shake_func
        
        self.aoe_radius = self.AOE_RADIUS_BASE * size_mult
        self.blast_max_radius = self.BLAST_MAX_RADIUS_BASE * size_mult
        
        self.color_mode = color_mode
        if self.color_mode == 'red':
            self.color_bright = C_RED_BRIGHT
            self.color_glow = C_RED_GLOW
        else:
            self.color_bright = C_CYAN_BRIGHT
            self.color_glow = C_CYAN_GLOW
        
        self.prep_delay = prep_delay_frames 
        self.blast_delay = blast_delay_frames
        self.blast_duration = blast_duration_frames
        self.time_alive = 0
        
        self.IS_PREPARING = False 
        self.BLAST_PHASE = False
        self.damage_applied = False
        
        self.image = pygame.Surface((1,1)) 
        
        if isinstance(self.initial_pos_or_getter, pygame.math.Vector2):
            self.pos = self.initial_pos_or_getter
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.time_alive += 1
        
        if not self.IS_PREPARING:
            if self.time_alive >= self.prep_delay:
                if callable(self.initial_pos_or_getter):
                    self.pos = self.initial_pos_or_getter() 
                else:
                    self.pos = self.initial_pos_or_getter
                
                self.rect.center = self.pos 
                self.IS_PREPARING = True
                self.time_alive = 0 
            return 
        
        if not self.BLAST_PHASE and self.time_alive >= self.blast_delay:
            self.BLAST_PHASE = True
            
        if self.BLAST_PHASE:
            if not self.damage_applied:
                self.check_damage()
                self.shake_func(self.SMITE_SHAKE_INTENSITY)
                self.damage_applied = True
            if self.time_alive >= self.blast_delay + self.blast_duration:
                self.kill()

    def check_damage(self):
        smite_rect = pygame.Rect(
            self.pos.x - self.aoe_radius,
            self.pos.y - self.aoe_radius,
            self.aoe_radius * 2,
            self.aoe_radius * 2
        )
        player_hitbox = self.player.get_hitbox_rect()
        if player_hitbox.colliderect(smite_rect):
            self.player.take_damage(self.damage)

    def draw_custom(self, surface, offset):
        if not self.IS_PREPARING: return

        draw_pos = self.pos + offset
        current_bright = self.color_bright
        current_glow = self.color_glow
        
        if not self.BLAST_PHASE:
            progress = self.time_alive / self.blast_delay
            if self.color_mode == 'cyan_to_red':
                t = max(0.0, (progress - 0.6) / 0.4) 
                current_bright = lerp_color(C_CYAN_BRIGHT, C_RED_BRIGHT, t)
                current_glow = lerp_color(C_CYAN_GLOW, C_RED_GLOW, t)
            
            pulse = math.sin(self.time_alive * 0.4) * 0.15 + 0.85
            alpha_mult = progress * pulse 
            alpha = int(255 * alpha_mult * 0.7) 
            
            glow_radius = self.aoe_radius * 1.2
            draw_alpha_circle(surface, current_glow[:3] + (int(alpha * 0.7),), draw_pos, glow_radius)
            border_width = 1 + int(progress * 2) 
            pygame.draw.circle(surface, current_bright[:3] + (alpha,), (int(draw_pos.x), int(draw_pos.y)), int(self.aoe_radius), border_width)
            
            inner_radius = 5 + int(progress * 5)
            draw_alpha_circle(surface, (255, 255, 255, 255), draw_pos, inner_radius)
            
        else:
            progress = (self.time_alive - self.blast_delay) / self.blast_duration
            current_radius = self.aoe_radius + (self.blast_max_radius - self.aoe_radius) * progress
            alpha = int(255 * (1.0 - progress) * 0.8) 
            
            if self.color_mode == 'red' or self.color_mode == 'cyan_to_red':
                blast_color = (255, 200, 150, alpha)
                ring_color = C_RED_BRIGHT
            else:
                blast_color = (255, 255, 255, alpha)
                ring_color = C_CYAN_BRIGHT

            draw_alpha_circle(surface, blast_color, draw_pos, int(current_radius))
            draw_alpha_circle(surface, ring_color[:3] + (alpha // 2,), draw_pos, int(current_radius * 0.7))

class GraphicsGenerator:
    @staticmethod
    def create_vampire_sprite(radius):
        size = radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        rect_cloak = pygame.Rect(0, 0, radius * 2.2, radius * 1.8)
        rect_cloak.center = center
        pygame.draw.ellipse(surf, COLOR_VAMPIRE_CLOAK, rect_cloak)
        pygame.draw.circle(surf, COLOR_VAMPIRE_ACCENT, (center[0] - 2, center[1]), radius, 2)
        head_pos = (center[0] + 3, center[1])
        pygame.draw.circle(surf, COLOR_VAMPIRE_SKIN, head_pos, radius * 0.6)
        pygame.draw.circle(surf, (255, 0, 0), (head_pos[0] + 4, head_pos[1] - 3), 2)
        pygame.draw.circle(surf, (255, 0, 0), (head_pos[0] + 4, head_pos[1] + 3), 2)
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
        self.scale_speed = scale_speed 
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
            pygame.draw.circle(self.image, curr_color, (int(self.size), int(self.size)), int(self.size))
            self.rect = self.image.get_rect(center=self.pos)

class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.decay = 0.9 # Значение затухания
        
    def shake(self, intensity):
        self.intensity = max(self.intensity, intensity)
        
    # --- ДОБАВЛЕН МЕТОД UPDATE ---
    def update(self, dt):
        if self.intensity > 0.1:
            # Используем простое затухание пока что (0.9 каждый кадр)
            # dt передается для будущего улучшения (frame-rate independence)
            self.intensity *= self.decay
            if self.intensity < 0.1:
                self.intensity = 0
    
    def get_offset(self):
        if self.intensity > 0.5:
            offset_x = random.uniform(-self.intensity, self.intensity)
            offset_y = random.uniform(-self.intensity, self.intensity)
            # Логика затухания перемещена в update()!
            return pygame.math.Vector2(offset_x, offset_y)
        return pygame.math.Vector2(0, 0)

class GhostMistVFX(pygame.sprite.Sprite):
    def __init__(self, pos, duration=40, size_start=10, size_end=80):
        super().__init__()
        particles.add(self) 
        all_sprites.add(self)
        
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration
        self.time_alive = 0
        self.size_start = size_start
        self.size_end = size_end
        
        self.color_base = C_CYAN_BRIGHT
        self.color_glow = C_CYAN_GLOW
        self.image = pygame.Surface((1,1))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.time_alive += 1
        if self.time_alive >= self.duration:
            self.kill()

    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        progress = self.time_alive / self.duration
        if progress < 0.2: alpha_mult = progress / 0.2
        elif progress > 0.8: alpha_mult = 1.0 - (progress - 0.8) / 0.2
        else: alpha_mult = 1.0
        alpha_mult = max(0.0, min(1.0, alpha_mult))

        current_size = self.size_start + (self.size_end - self.size_start) * progress
        for i in range(3):
            layer_jitter_offset = pygame.math.Vector2(random.uniform(-current_size*0.05, current_size*0.05),
                                                      random.uniform(-current_size*0.05, current_size*0.05))
            layer_size = current_size * (1 - i * 0.15)
            layer_alpha_base = int(self.color_base[3] * alpha_mult * (0.8 - i * 0.2))
            layer_alpha_glow = int(self.color_glow[3] * alpha_mult * (0.5 - i * 0.1))

            draw_alpha_circle(surface, self.color_base[:3] + (layer_alpha_base,), draw_pos + layer_jitter_offset, layer_size)
            draw_alpha_circle(surface, self.color_glow[:3] + (layer_alpha_glow,), draw_pos + layer_jitter_offset * 0.5, layer_size * 0.7)

# Добавьте этот класс в конец файла systems/vfx.py

class CloudSummonVFX(pygame.sprite.Sprite):
    def __init__(self, pos, duration_ms):
        super().__init__()
        particles.add(self)
        all_sprites.add(self)
        self.pos = pygame.math.Vector2(pos)
        self.duration = duration_ms
        self.spawn_time = pygame.time.get_ticks()
        self.image = pygame.Surface((1, 1)) # Невидимый, рисуем в draw_custom
        self.rect = self.image.get_rect(center=pos)
        
    def update(self, dt):
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()
            
    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        elapsed = pygame.time.get_ticks() - self.spawn_time
        
        # ИСПРАВЛЕНИЕ 1: Прогресс не может быть больше 1.0
        progress = min(1.0, elapsed / self.duration)
        
        # Круг сжимается перед выстрелом
        radius = 40 * (1.0 - progress * 0.5) 
        
        # ИСПРАВЛЕНИЕ 2: Альфа не может быть меньше 0
        alpha = max(0, int(150 * (1.0 - progress)))
        
        # Вращающиеся частицы (имитация)
        for i in range(5):
            angle = (pygame.time.get_ticks() * 0.01) + (i * 72)
            ox = math.cos(angle) * 20
            oy = math.sin(angle) * 20
            p = draw_pos + pygame.math.Vector2(ox, oy)
            
            # ИСПРАВЛЕНИЕ 3: Рисуем, только если цвет валидный (альфа > 0)
            if alpha > 0:
                draw_alpha_circle(surface, (200, 255, 255, alpha), p, radius * 0.5)
            
        # Для центрального круга тоже нужна проверка, но draw_alpha_circle внутри имеет проверки
        # Однако лучше передавать валидный цвет
        draw_alpha_circle(surface, (100, 200, 255, 100), draw_pos, radius)


class TelekineticSpike(pygame.sprite.Sprite):
    def __init__(self, pos, damage, player):
        super().__init__()
        all_sprites.add(self)
        particles.add(self) 
        
        self.pos = pygame.math.Vector2(pos)
        self.player = player
        self.damage = damage
        
        self.DELAY_FRAMES = 60       
        self.ACTIVE_DURATION = 20    
        self.timer = 0
        
        self.has_hit = False
        self.radius = 35             
        
        self.image = pygame.Surface((1, 1))
        self.rect = self.image.get_rect(center=self.pos)

        # --- НОВОЕ: ВЫЧИСЛЕНИЕ НАКЛОНА ---
        # Вектор от шипа к игроку (только по X, чтобы шип наклонялся вбок)
        # Если хотите наклон точно на игрока (включая Y), уберите .x и используйте полный вектор
        dx = self.player.pos.x - self.pos.x
        dy = self.player.pos.y - self.pos.y
        # Нормализуем, но сохраняем направление
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            self.slant_dir = pygame.math.Vector2(dx/dist, dy/dist)
        else:
            self.slant_dir = pygame.math.Vector2(0, 0)

    def update(self, dt):
        self.timer += 1
        
        if self.timer == self.DELAY_FRAMES:
            self.strike()
            
        if self.timer >= self.DELAY_FRAMES + self.ACTIVE_DURATION:
            self.kill()

    def strike(self):
        self.has_hit = True
        AssetManager().play_sound('brain_spike')
        if hasattr(self.player, 'shake_func'):
            self.player.shake_func(5)
            
        dist = self.pos.distance_to(self.player.pos)
        hit_dist = self.radius + getattr(self.player, 'radius', 15)
        
        if dist < hit_dist:
            self.player.take_damage(self.damage)

    def draw_custom(self, surface, offset):
        draw_pos = self.pos + offset
        
        C_WARN = (100, 0, 100)
        C_WARN_INNER = (200, 50, 200)
        C_SPIKE = (80, 20, 90)
        C_SPIKE_LIGHT = (200, 100, 255)
        
        # ФАЗА 1: ПРЕДУПРЕЖДЕНИЕ
        if self.timer < self.DELAY_FRAMES:
            progress = self.timer / self.DELAY_FRAMES
            r_outer = self.radius * (1.5 - 0.5 * progress)
            alpha_outer = int(100 * progress)
            draw_alpha_circle(surface, (*C_WARN, alpha_outer), draw_pos, r_outer)
            r_inner = self.radius * progress
            draw_alpha_circle(surface, (*C_WARN_INNER, 100), draw_pos, r_inner)
            pygame.draw.circle(surface, (255, 100, 255), (int(draw_pos.x), int(draw_pos.y)), self.radius, 1)

        # ФАЗА 2: УДАР (ДИАГОНАЛЬНЫЙ ШИП)
        else:
            anim_progress = (self.timer - self.DELAY_FRAMES) / self.ACTIVE_DURATION
            alpha = int(255 * (1 - anim_progress))
            
            if alpha > 0:
                spike_height = 140
                spike_half_w = 15
                slant_strength = 60 # Насколько сильно наклоняется верхушка
                
                # Основание (на земле)
                p_base_center = draw_pos
                p_left = (draw_pos.x - spike_half_w, draw_pos.y)
                p_right = (draw_pos.x + spike_half_w, draw_pos.y)
                
                # Вершина (смещена по вектору наклона)
                # Шип растет вверх (-Y) и смещается в сторону игрока (slant_dir)
                tip_offset = self.slant_dir * slant_strength
                p_top = (draw_pos.x + tip_offset.x, draw_pos.y - spike_height + tip_offset.y)
                
                # Рисуем
                draw_alpha_polygon(surface, (*C_SPIKE, alpha), [p_top, p_left, p_right])
                draw_alpha_polygon(surface, (*C_SPIKE_LIGHT, alpha), [p_top, p_base_center, p_right])