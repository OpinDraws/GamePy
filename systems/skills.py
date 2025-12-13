import pygame
import math
from rendering.skill_vfx import draw_slash_flurry
# Импортируем классы снарядов и эффектов
from entities.weapons.player_weapons import PhantomDagger
from systems.vfx import CloudSummonVFX
# Импортируем глобальные группы спрайтов
from core.config import all_sprites, bullets, particles

class SkillManager:
    def __init__(self, player):
        self.player = player
        self.skills = {
            'flurry': SlashFlurry(player),
            'cloud': DaggerCloudSkill(player) # Наш новый скилл
        }
    
    def handle_input(self, keys, mouse_world_pos=None):
        if keys[pygame.K_e]:
            self.skills['flurry'].activate()
        
        # Активация скилла на Q
        if keys[pygame.K_q] and mouse_world_pos:
            self.skills['cloud'].activate(mouse_world_pos)
            
    def update(self, dt, enemies):
        for skill in self.skills.values():
            skill.update(dt, enemies)
            
    def draw(self, surface, camera_offset):
        for skill in self.skills.values():
            skill.draw(surface, camera_offset)

# --- Старый скилл Flurry (без изменений) ---
class SlashFlurry:
    def __init__(self, owner):
        self.owner = owner
        self.cooldown = 9000     
        self.duration = 400      
        self.damage = 280        
        self.radius = 140         
        self.hitbox_radius = 220
        self.timer = -10000       
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
            # Используем центр для более точного попадания по боссу
            if hasattr(enemy, 'rect'):
                enemy_pos = pygame.math.Vector2(enemy.rect.center)
            else:
                enemy_pos = enemy.pos

            dist = (enemy_pos - attack_center).length()
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

# --- НОВЫЙ СКИЛЛ ---
class DaggerCloudSkill:
    def __init__(self, owner):
        self.owner = owner
        self.cooldown = 7000      # 7 секунд отката
        self.cast_delay = 400     # Задержка перед выстрелом
        self.damage = 45          # Урон
        
        self.timer = -7000
        self.cast_start_time = 0
        self.is_casting = False
        self.target_pos = pygame.math.Vector2(0, 0)

    def activate(self, target_pos):
        current_time = pygame.time.get_ticks()
        if current_time - self.timer > self.cooldown:
            self.is_casting = True
            self.timer = current_time
            self.cast_start_time = current_time
            self.target_pos = pygame.math.Vector2(target_pos)
            
            # Эффект облака на месте курсора
            CloudSummonVFX(self.target_pos, self.cast_delay)

    def update(self, dt, enemies):
        if not self.is_casting: return
        
        current_time = pygame.time.get_ticks()
        if current_time - self.cast_start_time >= self.cast_delay:
            self.fire_daggers(enemies)
            self.is_casting = False

    def fire_daggers(self, enemies):
        nearest_enemy = None
        min_dist = 1200 # Радиус поиска цели
        
        # 1. Поиск ближайшей цели (включая Босса)
        for enemy in enemies:
            # ВАЖНО: Используем rect.center, чтобы корректно находить Босса.
            # У босса self.pos может быть далеко от его реального центра.
            if hasattr(enemy, 'rect'):
                enemy_center = pygame.math.Vector2(enemy.rect.center)
            else:
                enemy_center = enemy.pos

            dist = self.target_pos.distance_to(enemy_center)
            
            # Приоритет боссу: если дистанция примерно одинаковая, бьем босса
            # (Здесь просто ищем ближайшего, но использование центра решает проблему "невидимости" босса для кода)
            if dist < min_dist:
                min_dist = dist
                nearest_enemy = enemy
        
        # 2. Определение направления
        base_direction = pygame.math.Vector2(1, 0)
        
        if nearest_enemy:
            # ... (расчет направления на врага) ...
            if hasattr(nearest_enemy, 'rect'):
                target_center = pygame.math.Vector2(nearest_enemy.rect.center)
            else:
                target_center = nearest_enemy.pos
            diff = target_center - self.target_pos
            if diff.length_squared() > 0:
                base_direction = diff.normalize()
        
        # 3. Веерный залп
        # ИЗМЕНЕНО: Теперь 4 угла вместо 3
        # Распределяем их симметрично относительно центра: -24, -8, +8, +24 градуса
        angles = [-24, -8, 8, 24]
        
        projectile_groups = [all_sprites, bullets]
        
        for angle_deg in angles:
            rotated_dir = base_direction.rotate(angle_deg)
            PhantomDagger(self.target_pos, rotated_dir, projectile_groups, particles)

    def draw(self, surface, camera_offset):
        pass