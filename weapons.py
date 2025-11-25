import pygame
import random
import math
from config import *
from vfx import Particle

class SlashProjectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, particle_groups):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.speed = 22 
        self.vel = direction.normalize() * self.speed
        self.particle_groups = particle_groups
        
        # --- ПАРАМЕТРЫ АТАКИ ---
        self.max_distance = 500
        self.distance_traveled = 0
        self.damage = 12 
        
        self.is_fading = False
        self.fade_duration = 150 
        self.fade_timer = 0
        self.original_alpha = 255

        # --- ВИЗУАЛ (Багровый разрез) ---
        # Сохраняем угол для расчета хитбоксов
        self.angle = math.degrees(math.atan2(-direction.y, direction.x))
        
        self.original_image = self._create_slash_image()
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        
        self.spawn_time = pygame.time.get_ticks()
        
        # Хитбоксы (инициализация)
        self.hitboxes = []

    def _create_slash_image(self):
        """Рисует процедурный серп/разрез."""
        w, h = 60, 60
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Цвета (БАГРОВЫЕ)
        color_core = (255, 200, 200) 
        color_glow = (180, 0, 40)    
        
        rect = pygame.Rect(10, 10, w-20, h-20)
        pygame.draw.arc(surf, color_glow + (200,), rect, -math.pi/4, math.pi/4, 8)
        pygame.draw.arc(surf, color_core, rect, -math.pi/4, math.pi/4, 3)
        
        return surf

    def update(self, dt):
        dt_ms = dt * 1000
        
        if self.is_fading:
            self.fade_timer += dt_ms
            if self.fade_timer >= self.fade_duration:
                self.kill()
            else:
                progress = self.fade_timer / self.fade_duration
                new_alpha = int(255 * (1 - progress))
                self.image.set_alpha(new_alpha)
                self.pos += self.vel * 0.3 * dt * 60
                self.rect.center = self.pos
            return

        move_step = self.vel * dt * 60
        self.pos += move_step
        self.distance_traveled += move_step.length()
        self.rect.center = self.pos
        
        # --- ОБНОВЛЕНИЕ ДУГООБРАЗНОГО ХИТБОКСА ---
        # Создаем 3 маленьких круга, смещенных относительно центра в форме дуги
        # Смещение рассчитывается в локальных координатах (считаем, что снаряд летит вправо/angle=0)
        # А потом поворачивается на реальный угол полета self.angle
        
        offsets = [
            pygame.math.Vector2(15, -20), # Верхняя часть дуги
            pygame.math.Vector2(25, 0),   # Середина (чуть дальше)
            pygame.math.Vector2(15, 20)   # Нижняя часть дуги
        ]
        
        self.hitboxes = []
        for off in offsets:
            # Поворачиваем смещение на угол полета
            # Внимание: rotate принимает градусы. 
            # У Pygame ось Y вниз, а углы CCW. Vector2.rotate вращает по часовой? Нет, Vector2.rotate вращает CLOCKWISE.
            # А math.atan2 выдает стандартный угол.
            # Обычно в Pygame для Vector2 нужно инвертировать угол или использовать отрицание.
            # Но так как self.angle мы считали через atan2(-y, x), это уже "экранные градусы" для rotate image.
            # Методом тыка Vector2.rotate(-self.angle) часто совпадает с визуалом.
            # Попробуем просто .rotate(-self.angle), так как y инвертирован.
            
            rotated_off = off.rotate(-self.angle) 
            
            self.hitboxes.append({
                'type': 'circle',
                'center': (self.pos.x + rotated_off.x, self.pos.y + rotated_off.y),
                'radius': 8 # Очень маленький радиус (точный хитбокс)
            })

        if self.distance_traveled >= self.max_distance:
            self.is_fading = True

        if random.random() < 0.4:
            Particle(self.pos, self.particle_groups, color=(150, 10, 10), speed=1, decay=25)

    def create_impact_vfx(self):
        """Эффект при попадании"""
        for _ in range(5):
            Particle(self.pos, self.particle_groups, color=(255, 50, 50), speed=6, decay=15)