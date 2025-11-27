# entities/tentacle_enemy.py
import pygame
import math
import random
from core.config import *
from entities.base_enemy import BaseEnemy
from rendering.monsters import draw_procedural_monster_v2

class TentacleEnemy(BaseEnemy):
    def __init__(self, pos, player, groups, particle_groups, shake_func):
        super().__init__(pos, player, groups, particle_groups, shake_func, health=150)
        
        # --- МАСШТАБ ---
        self.scale = 0.5
        
        # --- ХИТБОКС (ИЗМЕНЕНИЯ ЗДЕСЬ) ---
        # 1. Радиус для мягких столкновений (между врагами и игроком)
        # body_radius будет 42.5, берем чуть меньше для удобства
        self.radius = 35 
        
        # 2. Хитбоксы для снарядов (будут обновляться в update)
        self.hitboxes = []

        # Параметры анимации
        self.time = 0
        self.body_radius = 85 * self.scale
        self.front_tentacle_pos = 1.0 
        
        self.num_vertices = 9
        self.vertex_offsets = [random.uniform(-5, 5) * self.scale for _ in range(self.num_vertices)]

        self.angle_left = 0.0
        self.angle_right = 2.0 
        self.speed_left = math.pi / (1.8 * 60)
        self.speed_right = self.speed_left * 1.07 

        # Графика
        self.surface_size = int(500 * self.scale) + 50 
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)
        
        # Физика
        self.base_speed = 2.0
        self.chase_range = 600
        
        # Состояние
        self.attention_state = 'WANDER'
        self.attention_timer = 0

    def update_animation(self):
        self.time += 0.05
        cycle_state = (self.time // 22.5) % 2
        target = 1 if cycle_state == 0 else -1
        self.front_tentacle_pos += (target - self.front_tentacle_pos) * 0.02
        self.angle_left += self.speed_left
        self.angle_right += self.speed_right

    def update_physics(self):
        if self.base_speed > 0:
            dist_vec = self.player.pos - self.pos
            dist = dist_vec.length()
            if dist < self.chase_range and dist > 50:
                self.pos += dist_vec.normalize() * self.base_speed
        self.soft_collision()

    def update_hitbox(self):
        """Обновляем позицию хитбокса вслед за монстром."""
        # Создаем круглый хитбокс вокруг центра (тела)
        # Радиус берем чуть меньше визуального радиуса тела (body_radius ~ 42px -> hitbox 35px)
        self.hitboxes = [
            {
                'type': 'circle',
                'center': (self.pos.x, self.pos.y),
                'radius': 35 
            }
        ]

    def update(self, dt):
        self.update_physics()
        self.update_animation()
        
        # Отрисовка
        self.image.fill((0, 0, 0, 0))
        draw_procedural_monster_v2(
            self.image,
            self.visual_center,
            self.time,
            self.body_radius,
            self.vertex_offsets,
            self.angle_left,
            self.angle_right,
            self.front_tentacle_pos,
            scale=self.scale
        )
        
        self.rect = self.image.get_rect(center=self.pos)
        
        # ВАЖНО: Обновляем хитбокс каждый кадр
        self.update_hitbox()