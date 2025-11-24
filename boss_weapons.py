import pygame
import math
from config import all_sprites, enemies 
from rendering.archangel_render import draw_spear_projectile

class AngelSpearProjectile(pygame.sprite.Sprite):
    
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
             
        # P_final - это фактическая конечная точка, за пределами экрана, 
        # но направление движения берется через P_target.
        self.P_final = P_target + V_unit * extension_distance
        
        self.pos = self.P_start.copy() 
        self.damage = 35 
        
        # --- ФАЗЫ ЖИЗНИ ---
        self.travel_time = custom_travel_time_ms
        self.duration = custom_travel_time_ms + 100 # Общее время жизни после активации
        self.mist_duration = mist_duration        # Время появления (фаза Vfx)
        
        self.time_alive = 0                       # Время жизни снаряда
        self.is_active_projectile = False         # Флаг, указывающий на начало полета
        self.time_since_activation = 0            # Время, прошедшее с начала полета
        
        # Угол для отрисовки
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.angle = math.degrees(math.atan2(direction.y, direction.x)) 
        
        # Начальная заглушка (размер должен быть достаточно большим)
        self.size = 100 # Большой размер для захвата всего копья
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.radius = 10 # Радиус копья для упрощенной коллизии
        
        # Создаем Rect для коллизии копья
        self.collision_rect = pygame.Rect(0, 0, 20, 20) # Упрощенный хитбокс снаряда
        
        # Копье начинается в фазе Vfx
        self.mist_timer = 0 
        self.SPEAR_APPEAR_THRESHOLD = 0.5 

    def activate_flight(self):
        """Переводит снаряд из фазы появления в фазу полета."""
        self.is_active_projectile = True
        self.time_since_activation = 0

    def update(self, dt):
        
        dt_ms = dt * 1000
        
        if not self.is_active_projectile:
            # --- ФАЗА ПОЯВЛЕНИЯ (VFX) ---
            self.mist_timer += dt_ms
            
            # Если время появления истекло, активируем полет (как запасной вариант)
            if self.mist_timer >= self.mist_duration:
                self.activate_flight()

            # Позиция остается P_start
            self.pos = self.P_start.copy()
            self.rect.center = self.pos
            self.collision_rect.center = self.pos # Неактивный снаряд не имеет коллизии
            
            # Визуальный прогресс появления
            mist_progress = min(1.0, self.mist_timer / self.mist_duration)
            
            # --- Генерация image для отрисовки в фазе Vfx ---
            self.image.fill((0, 0, 0, 0)) 
            
            # Копье появляется после SPEAR_APPEAR_THRESHOLD
            if mist_progress >= self.SPEAR_APPEAR_THRESHOLD:
                # Прогресс появления копья после начала дымки
                spear_appear_phase_progress = (mist_progress - self.SPEAR_APPEAR_THRESHOLD) / (1.0 - self.SPEAR_APPEAR_THRESHOLD)
                spear_appear_phase_progress = max(0.0, min(1.0, spear_appear_phase_progress))

                alpha = int(255 * spear_appear_phase_progress) 
                
                local_center = pygame.math.Vector2(self.size // 2, self.size // 2)
                draw_spear_projectile(self.image, local_center, self.angle, alpha=alpha)

            return
            
        else:
            # --- ФАЗА ПОЛЕТА (ACTIVE) ---
            self.time_since_activation += dt_ms
            
            # Прогресс полета от 0.0 до 1.0
            if self.travel_time > 0:
                progress = min(1.0, self.time_since_activation / self.travel_time)
            else:
                progress = 1.0
                
            # Движение по интерполяции
            self.pos = self.P_start.lerp(self.P_final, progress)
            
            # Обновление Rect и коллизионного прямоугольника
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            self.collision_rect.center = self.pos
            
            # --- Генерация image для отрисовки в фазе полета ---
            self.image.fill((0, 0, 0, 0)) 
            
            alpha_mult = 1.0
            
            # Fade-out (последние 100 мс)
            if self.time_since_activation > self.travel_time - 100:
                alpha_mult = (self.duration - self.time_since_activation) / 100
                
            alpha = int(255 * max(0.0, min(1.0, alpha_mult)))

            local_center = pygame.math.Vector2(self.size // 2, self.size // 2)
            draw_spear_projectile(self.image, local_center, self.angle, alpha=alpha)


            # --- ЛОГИКА САМОУНИЧТОЖЕНИЯ И КОЛЛИЗИИ ---
            if self.time_since_activation > self.duration:
                self.kill()
                return

            self.check_player_collision()
        
    def check_player_collision(self):
        
        # Коллизия только в активной фазе
        if not self.is_active_projectile:
            return

        for sprite in all_sprites:
            # Проверяем, что это объект Player
            if type(sprite).__name__ == 'Player':
                
                player_hitbox = sprite.get_hitbox_rect()
                
                if player_hitbox.colliderect(self.collision_rect):
                    
                    # Наносим урон и убиваем снаряд
                    sprite.take_damage(self.damage) # <--- ВЫЗОВ МЕТОДА УРОНА
                    self.kill()
                    return
