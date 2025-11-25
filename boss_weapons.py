import pygame
import math
import random
from core.config import all_sprites, enemies
from rendering.archangel_render import draw_spear_projectile

# --- ЦВЕТА ДЛЯ МАГИИ ---
C_MAGIC_CORE = (255, 255, 255)
C_MAGIC_GLOW = (255, 50, 100, 200) # Красноватый для 2 фазы

class AngelSpearProjectile(pygame.sprite.Sprite):
    # ... (Существующий код AngelSpearProjectile остается без изменений) ...
    
    # *** ИЗМЕНЕНИЕ: Принимаем P_target и custom_travel_time_ms ***
    def __init__(self, pos, direction, P_target, custom_travel_time_ms, mist_duration, groups): 
        super().__init__(groups)
        
        self.P_start = pygame.math.Vector2(pos)
        
        # --- НОВЫЙ РАСЧЕТ P_final (точки за экраном) ---
        V_to_target = P_target - self.P_start
        extension_distance = 1000 
        
        if V_to_target.length_squared() == 0:
             V_unit = pygame.math.Vector2(1, 0)
        else:
             V_unit = V_to_target.normalize()
             
        self.P_final = P_target + V_unit * extension_distance
        
        self.pos = self.P_start.copy() 
        self.damage = 35 
        
        self.travel_time = custom_travel_time_ms
        self.duration = custom_travel_time_ms + 100 
        self.mist_duration = mist_duration        
        
        self.time_alive = 0                       
        self.is_active_projectile = False         
        self.time_since_activation = 0            
        
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.angle = math.degrees(math.atan2(direction.y, direction.x)) 
        
        self.size = 100 
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.radius = 10 
        
        self.collision_rect = pygame.Rect(0, 0, 20, 20) 
        
        self.mist_timer = 0 
        self.SPEAR_APPEAR_THRESHOLD = 0.5 

    def activate_flight(self):
        self.is_active_projectile = True
        self.time_since_activation = 0

    def update(self, dt):
        dt_ms = dt * 1000
        
        if not self.is_active_projectile:
            self.mist_timer += dt_ms
            if self.mist_timer >= self.mist_duration:
                self.activate_flight()

            self.pos = self.P_start.copy()
            self.rect.center = self.pos
            self.collision_rect.center = self.pos 
            
            mist_progress = min(1.0, self.mist_timer / self.mist_duration)
            self.image.fill((0, 0, 0, 0)) 
            
            if mist_progress >= self.SPEAR_APPEAR_THRESHOLD:
                spear_appear_phase_progress = (mist_progress - self.SPEAR_APPEAR_THRESHOLD) / (1.0 - self.SPEAR_APPEAR_THRESHOLD)
                spear_appear_phase_progress = max(0.0, min(1.0, spear_appear_phase_progress))
                alpha = int(255 * spear_appear_phase_progress) 
                local_center = pygame.math.Vector2(self.size // 2, self.size // 2)
                draw_spear_projectile(self.image, local_center, self.angle, alpha=alpha)
            return
            
        else:
            self.time_since_activation += dt_ms
            if self.travel_time > 0:
                progress = min(1.0, self.time_since_activation / self.travel_time)
            else:
                progress = 1.0
                
            self.pos = self.P_start.lerp(self.P_final, progress)
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.collision_rect.center = self.pos
            
            self.image.fill((0, 0, 0, 0)) 
            alpha_mult = 1.0
            if self.time_since_activation > self.travel_time - 100:
                alpha_mult = (self.duration - self.time_since_activation) / 100
            alpha = int(255 * max(0.0, min(1.0, alpha_mult)))

            local_center = pygame.math.Vector2(self.size // 2, self.size // 2)
            draw_spear_projectile(self.image, local_center, self.angle, alpha=alpha)

            if self.time_since_activation > self.duration:
                self.kill()
                return

            self.check_player_collision()
        
    def check_player_collision(self):
        if not self.is_active_projectile: return
        for sprite in all_sprites:
            if type(sprite).__name__ == 'Player':
                player_hitbox = sprite.get_hitbox_rect()
                if player_hitbox.colliderect(self.collision_rect):
                    sprite.take_damage(self.damage) 
                    self.kill()
                    return

# --- НОВЫЙ КЛАСС: CHAOS BOLT ---
class ChaosMagicProjectile(pygame.sprite.Sprite):
    """Магический шар, летящий по прямой."""
    def __init__(self, pos, target_pos, groups):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        
        direction = target_pos - self.pos
        if direction.length_squared() > 0:
            self.vel = direction.normalize() * 9 # Скорость полета
        else:
            self.vel = pygame.math.Vector2(1, 0)
            
        self.damage = 15
        self.radius = 8
        
        # Рисуем снаряд один раз
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, C_MAGIC_GLOW, (10, 10), 10)
        pygame.draw.circle(self.image, C_MAGIC_CORE, (10, 10), 5)
        
        self.rect = self.image.get_rect(center=self.pos)
        self.time_alive = 0
        self.max_lifetime = 300 # 5 секунд

    def update(self, dt):
        # dt приходит в секундах, но для движения используем 60 FPS базу
        self.pos += self.vel * (dt * 60)
        self.rect.center = self.pos
        
        # Удаление за пределами экрана (с запасом)
        if not (-100 < self.pos.x < 2000 and -100 < self.pos.y < 1500):
            self.kill()
            
        # Коллизия
        for sprite in all_sprites:
            if type(sprite).__name__ == 'Player':
                # Простая проверка дистанции
                if (self.pos - sprite.pos).length() < self.radius + 15:
                    sprite.take_damage(self.damage)
                    self.kill()