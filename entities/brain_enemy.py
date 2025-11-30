import pygame
import random
import os
from core.config import *
from entities.base_enemy import BaseEnemy
from rendering.brain_monsters import draw_brain_monster
from systems.vfx import Particle, TelekineticSpike 
import math
from core.asset_manager import AssetManager

class BrainEnemy(BaseEnemy):
    def __init__(self, pos, player, groups, particle_groups, shake_func):
        super().__init__(pos, player, groups, particle_groups, shake_func, health=400)
        
        self.radius = 25 
        self.time_ticks = random.randint(0, 1000)
        
        # --- ПАРАМЕТРЫ БАФФЕРА ---
        self.buff_range = 800       
        self.buff_cooldown = 600    
        self.buff_timer = 0
        self.buff_duration = 300    
        self.buff_speed_mult = 2.0
        self.buff_damage_mult = 1.5
        self.buff_cooldown_mult = 2.0 

        # --- ПАРАМЕТРЫ АТАКИ ШИПАМИ ---
        self.spike_cooldown_max = 420  
        self.spike_timer = random.randint(100, 300) 
        self.spike_damage = 50
        self.spike_range = 700 
        
        self.brain_img = None
        try:
            img_path = os.path.join(ASSETS_DIR, 'brain.png') 
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                target_size = (int(100 * 0.5), int(60 * 0.5))
                self.brain_img = pygame.transform.smoothscale(img, target_size)
        except Exception as e:
            print(f"Warning: Brain image not found ({e})")

        self.surface_size = 250 
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)
        
        # Инициализируем хитбоксы сразу
        self.update_hitbox()

    def update(self, dt):
        self.time_ticks += 1
        
        # ОБЯЗАТЕЛЬНО: Обновляем позицию хитбокса каждый кадр
        self.update_hitbox()
        
        if self.ai_active:
            self.update_buffs()
            self.soft_collision() 
            
            if self.buff_timer > 0:
                self.buff_timer -= 1
            else:
                if self.try_apply_buff():
                    self.buff_timer = self.buff_cooldown

            if self.spike_timer > 0:
                self.spike_timer -= 1 * self.cooldown_mult 
            else:
                dist_to_player = self.pos.distance_to(self.player.pos)
                if dist_to_player < self.spike_range:
                    self.attack_spikes()
                    self.spike_timer = self.spike_cooldown_max

        self.image.fill((0,0,0,0))
        
        if self.buff_timer <= 0 and self.ai_active:
             pulse = (math.sin(self.time_ticks * 0.1) + 1) * 10
             pygame.draw.circle(self.image, (255, 100, 100, 50), self.visual_center, 60 + pulse, 2)

        draw_pos_on_surface = (self.visual_center.x, self.visual_center.y + 80) 
        
        draw_brain_monster(
            self.image, 
            draw_pos_on_surface, 
            self.time_ticks, 
            self.player.pos - self.pos + draw_pos_on_surface, 
            self.brain_img
        )
        
        self.rect = self.image.get_rect(center=self.pos)

    # ИЗМЕНЕНИЕ: Добавлен метод создания явного хитбокса
    def update_hitbox(self):
        self.hitboxes = [{'type': 'circle', 'center': (self.pos.x, self.pos.y), 'radius': self.radius}]

    def attack_spikes(self):
        player_pos = self.player.pos
        side_offset = 90
        
        pos_left = player_pos + pygame.math.Vector2(-side_offset, random.randint(-10, 10))
        TelekineticSpike(pos_left, self.spike_damage, self.player)
        
        pos_right = player_pos + pygame.math.Vector2(side_offset, random.randint(-10, 10))
        TelekineticSpike(pos_right, self.spike_damage, self.player)
        
        for _ in range(10):
            Particle(self.pos, self.particle_groups, color=(150, 0, 200), speed=3, decay=5)

    def try_apply_buff(self):
        best_target = None
        min_dist_to_player = float('inf')
        for enemy in enemies:
            if enemy is not self and enemy.health > 0 and not getattr(enemy, 'is_buffed', False):
                if self.pos.distance_to(enemy.pos) < self.buff_range:
                    dist_to_p = enemy.pos.distance_to(self.player.pos)
                    if dist_to_p < min_dist_to_player:
                        min_dist_to_player = dist_to_p
                        best_target = enemy
        if best_target:
            best_target.apply_rage_buff(self.buff_duration, self.buff_speed_mult, self.buff_damage_mult, self.buff_cooldown_mult)
            self.spawn_cast_vfx(best_target.pos)
            return True
        return False

    def spawn_cast_vfx(self, target_pos):
        diff = target_pos - self.pos
        dist = diff.length()
        if dist > 0:
            steps = int(dist / 20)
            direction = diff.normalize()
            for i in range(steps):
                p = self.pos + direction * (i * 20)
                Particle(p, self.particle_groups, color=(255, 50, 50), speed=1, decay=15, scale_speed=0.5)