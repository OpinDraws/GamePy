import pygame
import math
import random
from core.config import *
from entities.base_enemy import BaseEnemy
from rendering.monsters import draw_procedural_monster_v2

class TentacleEnemy(BaseEnemy):
    # --- СОСТОЯНИЯ ---
    STATE_CHASE = 0
    STATE_PREPARE_LUNGE = 1
    STATE_LUNGE = 2
    STATE_RECOVER = 3

    def __init__(self, pos, player, groups, particle_groups, shake_func):
        super().__init__(pos, player, groups, particle_groups, shake_func, health=150)
        
        # --- ПАРАМЕТРЫ АТАКИ ---
        self.DAMAGE_LUNGE = 30
        self.MIN_LUNGE_DIST = 150
        self.MAX_LUNGE_DIST = 500
        self.LUNGE_PREP_TIME = 36     # 0.6 сек
        self.LUNGE_SPEED = 25
        
        # Кулдаун атаки (3 секунды)
        self.LUNGE_COOLDOWN_FRAMES = 180 
        self.cooldown_timer = 0
        
        self.state = self.STATE_CHASE
        self.state_timer = 0
        self.lunge_target_pos = pygame.math.Vector2(0, 0)
        self.lunge_velocity = pygame.math.Vector2(0, 0)
        self.damage_dealt = False
        
        # Флаг движения для анимации
        self.is_moving = False

        # --- АНИМАЦИЯ ---
        self.scale = 0.5
        self.base_body_radius = 85 * self.scale
        self.visual_radius = self.base_body_radius
        
        # Контроль формы щупалец
        self.tentacle_spread = 1.0   
        self.tentacle_extension = 0.0 
        self.front_tentacle_spread = 1.0 
        
        self.radius = 35 
        self.hitboxes = []

        self.time = random.uniform(0, 100)
        self.front_tentacle_pos = 1.0 
        self.num_vertices = 9
        self.vertex_offsets = [random.uniform(-5, 5) * self.scale for _ in range(self.num_vertices)]
        self.angle_left = 0.0
        self.angle_right = 0.0 
        
        self.surface_size = int(500 * self.scale) + 100
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)
        
        # Скорость передвижения (пикселей за кадр при 60 FPS)
        self.base_speed = 3.0

    def update_logic(self, dt):
        dist_to_player = (self.player.pos - self.pos).length()
        
        # Сбрасываем флаг движения
        self.is_moving = False
        
        # 1. CHASE (Преследование)
        if self.state == self.STATE_CHASE:
            if self.cooldown_timer > 0:
                self.cooldown_timer -= 1
            
            # --- Логика движения и дистанции ---
            # Если атака готова: держимся на 160 (идеально для прыжка)
            # Если кулдаун: держимся подальше (250)
            desired_dist = 250 if self.cooldown_timer > 0 else 160
            
            # Вектор к игроку
            direction = (self.player.pos - self.pos)
            if direction.length_squared() > 0:
                direction = direction.normalize()
            else:
                direction = pygame.math.Vector2(1, 0)

            # Если мы слишком далеко - подходим
            if dist_to_player > desired_dist:
                self.pos += direction * self.base_speed * dt * 60
                self.is_moving = True
            
            # Если мы слишком близко (игрок подошел вплотную) - отходим назад
            elif dist_to_player < 100: 
                self.pos -= direction * (self.base_speed * 0.8) * dt * 60
                self.is_moving = True

            # --- Попытка атаки ---
            # Атакуем, только если КД прошел И мы в правильном диапазоне (150-500)
            if self.cooldown_timer <= 0:
                if self.MIN_LUNGE_DIST <= dist_to_player <= self.MAX_LUNGE_DIST:
                    self.state = self.STATE_PREPARE_LUNGE
                    self.state_timer = self.LUNGE_PREP_TIME
                    self.lunge_target_pos = self.player.pos.copy()

        # 2. PREPARE (Подготовка/Сжатие)
        elif self.state == self.STATE_PREPARE_LUNGE:
            self.state_timer -= 1
            # Эффект сжатия (Squash)
            progress = 1.0 - (self.state_timer / self.LUNGE_PREP_TIME)
            self.visual_radius = self.base_body_radius * (1.0 - 0.2 * progress)
            
            if self.state_timer <= 0:
                self.state = self.STATE_LUNGE
                self.damage_dealt = False
                
                # Расчет вектора прыжка
                jump_vec = self.lunge_target_pos - self.pos
                if jump_vec.length() > 0:
                    self.lunge_velocity = jump_vec.normalize() * self.LUNGE_SPEED
                else:
                    self.lunge_velocity = pygame.math.Vector2(0, 0)
                
                self.shake_func(5)

        # 3. LUNGE (Полет)
        elif self.state == self.STATE_LUNGE:
            # Движение в полете (быстрое) - тут dt тоже важен для стабильности
            self.pos += self.lunge_velocity * dt * 60
            
            self.visual_radius = self.base_body_radius * 1.1 # Растяжение (Stretch)
            
            # Нанесение урона
            if not self.damage_dealt:
                if self.pos.distance_to(self.player.pos) < (self.radius + self.player.radius):
                    self.player.take_damage(self.DAMAGE_LUNGE)
                    self.damage_dealt = True
                    self.shake_func(10)
            
            # Проверка приземления
            dist_to_target = self.pos.distance_to(self.lunge_target_pos)
            # Условие остановки: близко к цели ИЛИ перелетели слишком далеко
            if dist_to_target < self.LUNGE_SPEED * 1.5 or dist_to_target > 1000:
                self.pos = self.lunge_target_pos
                self.state = self.STATE_RECOVER
                self.state_timer = 40 

        # 4. RECOVER (Отдых)
        elif self.state == self.STATE_RECOVER:
            self.state_timer -= 1
            # Плавный возврат формы
            self.visual_radius += (self.base_body_radius - self.visual_radius) * 0.1
            
            if self.state_timer <= 0:
                self.state = self.STATE_CHASE
                self.cooldown_timer = self.LUNGE_COOLDOWN_FRAMES

        # Мягкие коллизии (расталкивание)
        if self.state != self.STATE_LUNGE:
            self.soft_collision()

    def update_animation(self):
        # Базовая скорость
        anim_speed = 0.05
        
        # Ускорение анимации при ходьбе (перебирают лапками быстрее)
        if self.is_moving:
            anim_speed *= 2.5
            
        self.time += anim_speed
        
        target_spread = 1.0
        target_extension = 0.0
        target_angle = 0.0
        target_front_spread = 1.0 
        
        speed = 0.1

        if self.state == self.STATE_PREPARE_LUNGE:
            # СЖАТИЕ (Твои настройки)
            target_spread = 0.65
            target_extension = -30.0 
            target_angle = -1.5 
            target_front_spread = 0.0 
            speed = 0.15
            
        elif self.state == self.STATE_LUNGE:
            # РЫВОК (Твои настройки)
            target_spread = 0.75
            target_extension = 100.0
            target_angle = 0.8
            target_front_spread = 0.2 
            speed = 0.2
            
        else: # CHASE / RECOVER
            target_spread = 1.0 + math.sin(self.time) * 0.05
            target_extension = math.cos(self.time) * 10.0
            target_angle = math.sin(self.time) * 0.5
            target_front_spread = 1.0
            speed = 0.05

        # Интерполяция параметров
        self.tentacle_spread += (target_spread - self.tentacle_spread) * speed
        self.tentacle_extension += (target_extension - self.tentacle_extension) * speed
        self.angle_left += (target_angle - self.angle_left) * speed
        self.angle_right += (-target_angle - self.angle_right) * speed
        self.front_tentacle_spread += (target_front_spread - self.front_tentacle_spread) * speed

        cycle_state = (self.time // 22.5) % 2
        target_front = 1 if cycle_state == 0 else -1
        self.front_tentacle_pos += (target_front - self.front_tentacle_pos) * 0.02

    def update_hitbox(self):
        self.hitboxes = [{'type': 'circle', 'center': (self.pos.x, self.pos.y), 'radius': self.radius}]

    def update(self, dt):
        # Передаем dt в логику
        self.update_logic(dt)
        self.update_animation()
        
        self.image.fill((0, 0, 0, 0))
        
        draw_procedural_monster_v2(
            self.image,
            self.visual_center,
            self.time,
            self.visual_radius,
            self.vertex_offsets,
            self.angle_left,
            self.angle_right,
            self.front_tentacle_pos,
            scale=self.scale,
            tentacle_spread=self.tentacle_spread,
            tentacle_extension=self.tentacle_extension,
            front_tentacle_spread=self.front_tentacle_spread 
        )
        
        self.rect = self.image.get_rect(center=self.pos)
        self.update_hitbox()