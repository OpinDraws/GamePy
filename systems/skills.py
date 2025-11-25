import pygame
import math
from rendering.skill_vfx import draw_slash_flurry

class SkillManager:
    def __init__(self, player):
        self.player = player
        self.skills = {
            'flurry': SlashFlurry(player)
        }
    
    def handle_input(self, keys):
        if keys[pygame.K_e]:
            self.skills['flurry'].activate()
            
    def update(self, dt, enemies):
        for skill in self.skills.values():
            skill.update(dt, enemies)
            
    def draw(self, surface, camera_offset):
        for skill in self.skills.values():
            skill.draw(surface, camera_offset)

class SlashFlurry:
    def __init__(self, owner):
        self.owner = owner
        self.cooldown = 2000     
        self.duration = 400      
        self.damage = 150         
        self.radius = 140         
        self.hitbox_radius = 220
        self.timer = -2000       
        self.active_timer = 0    
        self.is_active = False
        self.hit_enemies = set()
        self.cast_angle = 0

    def activate(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.timer > self.cooldown:
            self.is_active = True
            self.timer = current_time
            self.active_timer = 0
            self.hit_enemies.clear()
            self.cast_angle = self.owner.angle
            self.owner.shake_func(4)

    def update(self, dt, enemies):
        if not self.is_active: return
        self.active_timer += dt * 1000
        if self.active_timer >= self.duration:
            self.is_active = False
            return

        rad = math.radians(self.cast_angle)
        direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
        base_pos = self.owner.pos
        shoulder_height = pygame.math.Vector2(0, -50)
        forward_offset = direction * 60 
        attack_center = base_pos + shoulder_height + forward_offset
        
        for enemy in enemies:
            if enemy in self.hit_enemies: continue
            dist = (enemy.pos - attack_center).length()
            if dist < self.hitbox_radius:
                enemy.take_damage(self.damage)
                self.hit_enemies.add(enemy)
                push_dir = (enemy.pos - self.owner.pos).normalize()
                enemy.pos += push_dir * 20

    def draw(self, surface, camera_offset):
        if self.is_active:
            progress = self.active_timer / self.duration
            world_pos = self.owner.pos
            shoulder_height = pygame.math.Vector2(0, -50)
            rad = math.radians(self.cast_angle)
            direction = pygame.math.Vector2(math.cos(rad), math.sin(rad))
            forward_offset = direction * 60 
            final_draw_pos = world_pos + shoulder_height + forward_offset + camera_offset
            draw_slash_flurry(surface, final_draw_pos, self.cast_angle, progress, self.radius)