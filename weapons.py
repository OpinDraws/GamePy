import pygame
import random
import math
from config import *
from vfx import GraphicsGenerator, Particle

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups, particle_groups):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.vel = direction.normalize() * 16 # Быстрая магия
        self.particle_groups = particle_groups
        
        # Используем новый спрайт магии
        self.original_image = GraphicsGenerator.create_blood_bolt()
        # Поворачиваем пулю по направлению полета
        angle = math.degrees(math.atan2(-direction.y, direction.x))
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.pos)
        
        self.damage = 15
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1500

    def update(self, dt):
        self.pos += self.vel * dt * 60
        self.rect.center = self.pos
        
        # Эффект следа (Trail) - Кровавые капли
        if random.random() < 0.5:
            # Смещение, чтобы след был немного размытым
            offset = pygame.math.Vector2(random.uniform(-2,2), random.uniform(-2,2))
            Particle(self.pos + offset, self.particle_groups, color=COLOR_BLOOD_TRAIL, speed=0.5, decay=20, scale_speed=3)

        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
            
    def create_impact_vfx(self):
        """Взрыв магии при попадании"""
        for _ in range(8):
            Particle(self.pos, self.particle_groups, color=COLOR_BLOOD_CORE, speed=5, decay=10)
        for _ in range(4):
            Particle(self.pos, self.particle_groups, color=(255, 255, 255), speed=3, decay=15)