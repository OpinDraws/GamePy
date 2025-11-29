import pygame
import math
import random
from core.config import *
from entities.base_enemy import BaseEnemy
from rendering.monsters import draw_procedural_monster_v2

class TentacleEnemy(BaseEnemy):
    # ... (Константы состояний STATE_... те же) ...
    STATE_CHASE = 0
    STATE_PREPARE_LUNGE = 1
    STATE_LUNGE = 2
    STATE_RECOVER = 3
    STATE_STRIKE_LIFT = 4    
    STATE_STRIKE_AIM = 5     
    STATE_STRIKE_HIT = 6     
    STATE_STRIKE_RETRACT = 7 

    def __init__(self, pos, player, groups, particle_groups, shake_func):
        super().__init__(pos, player, groups, particle_groups, shake_func, health=150)
        
        # ... (Инициализация архетипов и параметров без изменений) ...
        self.archetype = random.choice(['bruiser', 'jumper', 'combo'])
        self.base_speed = 3.0 * random.uniform(0.9, 1.1)
        self.radius = 35 
        
        self.DAMAGE_LUNGE = 30
        self.MIN_LUNGE_DIST = 150
        self.MAX_LUNGE_DIST = 700 + random.randint(-80, 80)
        self.LUNGE_PREP_TIME = 36
        self.LUNGE_SPEED = 25
        
        self.DAMAGE_STRIKE = 40
        self.base_strike_range = 250 + random.randint(-25, 25)
        self.STRIKE_RANGE = self.base_strike_range
        
        self.BASE_TIME_LIFT = int(0.25 * 60)
        self.BASE_TIME_AIM = int(random.uniform(0.0, 0.09) * 60)
        self.BASE_TIME_HIT = 8
        self.TIME_RETRACT = 30
        
        self.lunge_cd_max = 180 
        self.strike_cd_max = 90 
        self.combo_primed = False 
        
        if self.archetype == 'bruiser':
            self.base_speed *= 1.10 
            self.lunge_cd_max = 300 
            self.strike_cd_max = 90
            self.STRIKE_RANGE = int(self.STRIKE_RANGE * 1.20)
            self.BASE_TIME_LIFT = int(self.BASE_TIME_LIFT * 0.85)
            self.BASE_TIME_AIM = int(self.BASE_TIME_AIM * 0.85)
            self.BASE_TIME_HIT = int(self.BASE_TIME_HIT * 0.85)
        elif self.archetype == 'jumper':
            self.lunge_cd_max = 120 
            self.strike_cd_max = 120 
        elif self.archetype == 'combo':
            self.lunge_cd_max = 300 
            self.strike_cd_max = 300 
            self.MAX_LUNGE_DIST = int(self.MAX_LUNGE_DIST * 1.3)

        self.current_lift_time = self.BASE_TIME_LIFT
        self.current_aim_time = self.BASE_TIME_AIM
        self.current_hit_time = self.BASE_TIME_HIT

        self.lunge_timer_cd = 0
        self.strike_timer_cd = 0
        
        self.state = self.STATE_CHASE
        self.state_timer = 0
        
        self.lunge_target_pos = pygame.math.Vector2(0, 0)
        self.lunge_velocity = pygame.math.Vector2(0, 0)
        self.strike_target_pos = pygame.math.Vector2(0, 0)
        self.strike_p2 = pygame.math.Vector2(0, 0)
        self.strike_p3 = pygame.math.Vector2(0, 0)
        
        self.damage_dealt = False
        self.is_moving = False

        self.path = []
        self.path_index = 0
        self.path_timer = 0
        self.PATH_UPDATE_RATE = 45
        self.separation_check_timer = 0
        self.cached_separation_force = pygame.math.Vector2(0, 0)
        self.SEPARATION_DIST = 200 

        # Анимационные переменные
        self.scale = 0.5
        self.base_body_radius = 85 * self.scale
        self.visual_radius = self.base_body_radius
        self.tentacle_spread = 1.0   
        self.tentacle_extension = 0.0 
        self.front_tentacle_spread = 1.0 
        self.hitboxes = []
        self.time = random.uniform(0, 100)
        self.front_tentacle_pos = 1.0 
        self.num_vertices = 9
        self.vertex_offsets = [random.uniform(-5, 5) * self.scale for _ in range(self.num_vertices)]
        self.angle_left = 0.0
        self.angle_right = 0.0 
        self.surface_size = int(500 * self.scale) + 300 
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)

    # ... (Методы _generate_chaotic_path и _update_separation_cache без изменений) ...
    def _generate_chaotic_path(self, target_pos):
        # Код без изменений, можно оставить старый
        start = self.pos
        end = target_pos
        diff = end - start
        dist = diff.length()
        if dist < 60:
            self.path = [end]
            self.path_index = 0
            return
        num_points = 35 
        if self.archetype == 'bruiser':
            tactic = random.choices(['direct', 'arc'], weights=[80, 20])[0]
        else:
            tactic = random.choices(['direct', 'arc'], weights=[30, 70])[0]
        if dist > 0: perp = pygame.math.Vector2(-diff.y, diff.x).normalize()
        else: perp = pygame.math.Vector2(0, 0)
        mid_point = start + diff * 0.5
        control_offset = 0
        if tactic == 'direct': control_offset = random.uniform(-40, 40)
        else:
            side = random.choice([-1, 1])
            factor = random.uniform(0.1, 1.2) 
            control_offset = side * (dist * factor)
        control_point = mid_point + perp * control_offset
        self.path = []
        for i in range(1, num_points + 1):
            t = i / num_points 
            p = (1 - t)**2 * start + 2 * (1 - t) * t * control_point + t**2 * end
            self.path.append(p)
        self.path_index = 0

    def _update_separation_cache(self):
        # Код без изменений
        separation = pygame.math.Vector2(0, 0)
        count = 0
        for other in enemies:
            if other is not self and isinstance(other, TentacleEnemy):
                dist_vec = self.pos - other.pos
                dist = dist_vec.length()
                if 0 < dist < self.SEPARATION_DIST:
                    separation += dist_vec.normalize() / dist
                    count += 1
        if count > 0:
            separation /= count
            if separation.length() > 0: self.cached_separation_force = separation.normalize() * 1.5
            else: self.cached_separation_force = pygame.math.Vector2(0,0)
        else: self.cached_separation_force = pygame.math.Vector2(0,0)

    # --- ИЗМЕНЕНИЯ В ДВИЖЕНИИ ---
    def _perform_movement(self, dt, dist_to_player):
        # ... (код separation таймера без изменений) ...
        self.separation_check_timer -= 1
        if self.separation_check_timer <= 0:
            self._update_separation_cache()
            self.separation_check_timer = 60

        desired_dist = 160
        if self.archetype == 'combo': desired_dist = 500
        elif self.archetype == 'bruiser': desired_dist = 50
        too_close_dist = 100
        if self.archetype == 'combo': too_close_dist = 450
            
        # УЧЕТ СКОРОСТИ БАФФА (self.speed_mult)
        current_speed_val = self.base_speed * self.speed_mult

        if dist_to_player < too_close_dist: 
            direction = (self.player.pos - self.pos).normalize()
            retreat_speed_mult = 0.9
            if self.archetype == 'combo': retreat_speed_mult *= 1.3 
            
            self.pos -= direction * (current_speed_val * retreat_speed_mult) * dt * 60
            self.is_moving = True
            self.path = [] 
            return

        if dist_to_player > desired_dist:
            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path or self.path_index >= len(self.path):
                self._generate_chaotic_path(self.player.pos)
                self.path_timer = self.PATH_UPDATE_RATE + random.randint(-15, 15)
            
            if self.path:
                target_point = self.path[self.path_index]
                move_vec = target_point - self.pos
                dist_to_point = move_vec.length()
                if dist_to_point < 15: 
                    self.path_index += 1
                    if self.path_index < len(self.path):
                        target_point = self.path[self.path_index]
                        move_vec = target_point - self.pos
                
                if move_vec.length_squared() > 0:
                    path_dir = move_vec.normalize()
                    final_dir = (path_dir + self.cached_separation_force).normalize()
                    # Применяем множитель скорости
                    self.pos += final_dir * current_speed_val * dt * 60
                    self.is_moving = True

    # --- ИЗМЕНЕНИЯ В ЛОГИКЕ ---
    def update_logic(self, dt):
        self.update_buffs()
        dist_to_player = (self.player.pos - self.pos).length()
        self.is_moving = False
        
        # Ускоряем откат способностей множителем кулдауна
        # Если cooldown_mult = 2.0, то за 1 кадр проходит 2 единицы времени
        if self.lunge_timer_cd > 0: 
            self.lunge_timer_cd -= 1 * self.cooldown_mult
        if self.strike_timer_cd > 0: 
            self.strike_timer_cd -= 1 * self.cooldown_mult

        if self.state == self.STATE_CHASE or self.state in [self.STATE_STRIKE_LIFT, self.STATE_STRIKE_AIM, self.STATE_STRIKE_HIT, self.STATE_STRIKE_RETRACT]:
            self._perform_movement(dt, dist_to_player)

        if self.state == self.STATE_CHASE:
            # (Логика выбора атаки без изменений)
            if self.archetype == 'bruiser':
                if dist_to_player <= self.STRIKE_RANGE and self.strike_timer_cd <= 0:
                    self._start_strike_attack()
                    return
                if dist_to_player > self.STRIKE_RANGE and self.MIN_LUNGE_DIST <= dist_to_player <= self.MAX_LUNGE_DIST and self.lunge_timer_cd <= 0:
                    self._start_lunge_attack()
                    return
            elif self.archetype == 'jumper':
                if self.MIN_LUNGE_DIST <= dist_to_player <= self.MAX_LUNGE_DIST and self.lunge_timer_cd <= 0:
                    self._start_lunge_attack()
                    return
                if dist_to_player <= self.STRIKE_RANGE and self.strike_timer_cd <= 0:
                    self._start_strike_attack()
                    return
            elif self.archetype == 'combo':
                if self.combo_primed:
                    boosted_range = self.STRIKE_RANGE * 1.6
                    if dist_to_player <= boosted_range and self.strike_timer_cd <= 0:
                        self._start_strike_attack(is_boosted=True)
                        return
                if not self.combo_primed and self.MIN_LUNGE_DIST <= dist_to_player <= self.MAX_LUNGE_DIST and self.lunge_timer_cd <= 0:
                    self._start_lunge_attack()
                    return

        # УСКОРЯЕМ ТАЙМЕРЫ СОСТОЯНИЙ (self.state_timer)
        
        elif self.state == self.STATE_PREPARE_LUNGE:
            self.state_timer -= 1 * self.anim_mult # Ускорение
            if self.archetype == 'jumper' and self.state_timer > self.LUNGE_PREP_TIME // 2:
                self.lunge_target_pos = self.player.pos.copy()
            
            # Визуальный прогресс считаем от базового времени, чтобы не дергалось
            # Но так как таймер уменьшается быстрее, анимация ускорится
            progress = 1.0 - (self.state_timer / self.LUNGE_PREP_TIME)
            self.visual_radius = self.base_body_radius * (1.0 - 0.2 * progress)
            
            if self.state_timer <= 0:
                self.state = self.STATE_LUNGE
                self.damage_dealt = False
                jump_vec = self.lunge_target_pos - self.pos
                if jump_vec.length() > 0: 
                    # Скорость рывка тоже увеличиваем
                    self.lunge_velocity = jump_vec.normalize() * self.LUNGE_SPEED * self.speed_mult
                else: 
                    self.lunge_velocity = pygame.math.Vector2(0, 0)
                self.shake_func(5)

        elif self.state == self.STATE_LUNGE:
            self.pos += self.lunge_velocity * dt * 60
            self.visual_radius = self.base_body_radius * 1.1
            if not self.damage_dealt:
                if self.pos.distance_to(self.player.pos) < (self.radius + self.player.radius):
                    # ПРИМЕНЕНИЕ УРОНА С БАФФОМ
                    self.player.take_damage(self.DAMAGE_LUNGE * self.damage_mult)
                    self.damage_dealt = True
                    self.shake_func(10)
            
            dist_to_target = self.pos.distance_to(self.lunge_target_pos)
            # Условие выхода с поправкой на скорость
            if dist_to_target < (self.LUNGE_SPEED * self.speed_mult) * 1.5 or dist_to_target > 1000:
                self.pos = self.lunge_target_pos
                self.state = self.STATE_RECOVER
                self.state_timer = 40 

        elif self.state == self.STATE_RECOVER:
            self.state_timer -= 1 * self.anim_mult # Ускорение
            self.visual_radius += (self.base_body_radius - self.visual_radius) * 0.1
            if self.state_timer <= 0:
                self.state = self.STATE_CHASE
                self.lunge_timer_cd = self.lunge_cd_max
                if self.archetype == 'combo':
                    self.combo_primed = True

        # АТАКА ЩУПАЛЬЦЕМ (УСКОРЕНИЕ)
        elif self.state == self.STATE_STRIKE_LIFT:
            self.state_timer += 1 * self.anim_mult
            if self.state_timer >= self.current_lift_time:
                self.state = self.STATE_STRIKE_AIM
                self.state_timer = 0
                self.strike_target_pos = self.player.pos.copy()

        elif self.state == self.STATE_STRIKE_AIM:
            self.state_timer += 1 * self.anim_mult
            if self.state_timer >= self.current_aim_time:
                self.state = self.STATE_STRIKE_HIT
                self.state_timer = 0
                self.shake_func(2)

        elif self.state == self.STATE_STRIKE_HIT:
            self.state_timer += 1 * self.anim_mult
            if not self.damage_dealt:
                tip_world_pos = self.pos + (self.strike_p3 - self.visual_center)
                if tip_world_pos.distance_to(self.player.pos) < 40: 
                    # ПРИМЕНЕНИЕ УРОНА С БАФФОМ
                    self.player.take_damage(self.DAMAGE_STRIKE * self.damage_mult)
                    self.damage_dealt = True
                    self.shake_func(15)

            if self.state_timer >= self.current_hit_time:
                self.state = self.STATE_STRIKE_RETRACT
                self.state_timer = 0

        elif self.state == self.STATE_STRIKE_RETRACT:
            self.state_timer += 1 * self.anim_mult
            if self.state_timer >= self.TIME_RETRACT:
                self.state = self.STATE_CHASE
                self.strike_timer_cd = self.strike_cd_max
                if self.archetype == 'combo':
                    self.combo_primed = False
                    self.STRIKE_RANGE = self.base_strike_range
                    self.current_lift_time = self.BASE_TIME_LIFT
                    self.current_aim_time = self.BASE_TIME_AIM
                    self.current_hit_time = self.BASE_TIME_HIT

        if self.state != self.STATE_LUNGE:
            self.soft_collision()

    # (Методы _start_lunge_attack, _start_strike_attack без изменений)
    def _start_lunge_attack(self):
        self.state = self.STATE_PREPARE_LUNGE
        self.state_timer = self.LUNGE_PREP_TIME
        self.lunge_target_pos = self.player.pos.copy()

    def _start_strike_attack(self, is_boosted=False):
        self.state = self.STATE_STRIKE_LIFT
        self.state_timer = 0
        self.damage_dealt = False
        if is_boosted:
            self.current_hit_time = int(self.BASE_TIME_HIT * 0.7) 
            self.current_lift_time = int(self.BASE_TIME_LIFT * 0.8) 
            self.current_aim_time = int(self.BASE_TIME_AIM * 0.8)
        else:
            self.current_hit_time = self.BASE_TIME_HIT
            self.current_lift_time = self.BASE_TIME_LIFT
            self.current_aim_time = self.BASE_TIME_AIM

    def update_animation(self):
        # Ускоряем общую анимацию (покачивание и т.д.)
        anim_speed = 0.05 * self.anim_mult 
        if self.is_moving: anim_speed *= 2.5
        self.time += anim_speed
        
        # ... (весь остальной код анимации такой же, логика интерполяции не меняется) ...
        # Просто скопируйте оставшуюся часть метода из старого файла
        target_spread = 1.0
        target_extension = 0.0
        target_angle = 0.0
        target_front_spread = 1.0 
        
        if self.state == self.STATE_PREPARE_LUNGE:
            target_spread = 0.65
            target_extension = -30.0 
            target_angle = -1.5 
            target_front_spread = 0.0 
        elif self.state == self.STATE_LUNGE:
            target_spread = 0.75
            target_extension = 100.0
            target_angle = 0.8
            target_front_spread = 0.2 
        else: 
            target_spread = 1.0 + math.sin(self.time) * 0.05
            target_extension = math.cos(self.time) * 10.0
            target_angle = math.sin(self.time) * 0.5
            target_front_spread = 1.0

        self.tentacle_spread += (target_spread - self.tentacle_spread) * 0.1
        self.tentacle_extension += (target_extension - self.tentacle_extension) * 0.1
        self.angle_left += (target_angle - self.angle_left) * 0.1
        self.angle_right += (-target_angle - self.angle_right) * 0.1
        self.front_tentacle_spread += (target_front_spread - self.front_tentacle_spread) * 0.1

        cycle_state = (self.time // 22.5) % 2
        target_front = 1 if cycle_state == 0 else -1
        self.front_tentacle_pos += (target_front - self.front_tentacle_pos) * 0.02
        
        target_p2 = self.visual_center.copy()
        target_p3 = self.visual_center.copy()
        lift_vec = pygame.math.Vector2(0, -140)
        
        if self.state == self.STATE_STRIKE_LIFT:
            t = self.state_timer / self.current_lift_time
            t = t * t * (3 - 2 * t)
            target_p2 = self.visual_center + lift_vec * 0.5 * t
            target_p3 = self.visual_center + lift_vec * t
        elif self.state == self.STATE_STRIKE_AIM:
            target_p2 = self.visual_center + lift_vec * 0.5
            target_p3 = self.visual_center + lift_vec
            jitter = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
            target_p3 += jitter
        elif self.state == self.STATE_STRIKE_HIT:
            t = self.state_timer / self.current_hit_time
            start_p3 = self.visual_center + lift_vec
            local_target = self.strike_target_pos - self.pos + self.visual_center
            target_p3 = start_p3.lerp(local_target, t)
            target_p2 = self.visual_center.lerp(target_p3, 0.5) + pygame.math.Vector2(0, -50)
        elif self.state == self.STATE_STRIKE_RETRACT:
            t = self.state_timer / self.TIME_RETRACT
            local_target = self.strike_target_pos - self.pos + self.visual_center
            target_p3 = local_target.lerp(self.visual_center, t)
            target_p2 = target_p3.lerp(self.visual_center, 0.5)

        self.strike_p2 = target_p2
        self.strike_p3 = target_p3

    def update(self, dt):
        self.update_logic(dt)
        self.update_animation()
        
        self.image.fill((0, 0, 0, 0))
        
        strike_data = None
        if self.state in [self.STATE_STRIKE_LIFT, self.STATE_STRIKE_AIM, self.STATE_STRIKE_HIT, self.STATE_STRIKE_RETRACT]:
            strike_data = {
                'p2': (self.strike_p2.x, self.strike_p2.y),
                'p3': (self.strike_p3.x, self.strike_p3.y)
            }
        
        # Если есть бафф, меняем цвет тела на красный
        override_color = None
        override_color_dark = None
        if self.is_buffed:
            override_color = (200, 50, 50) # Красный
            override_color_dark = (100, 20, 20)

        # Вызов отрисовки (добавим поддержку цветов если есть, или оставим стандартные)
        # В вашем текущем монстр-рендере цвета зашиты в константы.
        # Чтобы подсветить баффнутого монстра, можно просто рисовать ауру под ним
        
        if self.is_buffed:
             pygame.draw.circle(self.image, (255, 0, 0, 50), self.visual_center, 120 * self.scale)

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
            front_tentacle_spread=self.front_tentacle_spread,
            strike_tentacle_data=strike_data
        )
        
        self.rect = self.image.get_rect(center=self.pos)
        self.update_hitbox()
        
    def update_hitbox(self):
        self.hitboxes = [{'type': 'circle', 'center': (self.pos.x, self.pos.y), 'radius': self.radius}]