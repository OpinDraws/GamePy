import pygame
import math
import random
from config import *
from vfx import GraphicsGenerator, Particle
from rendering import draw_eldritch_horror, get_bezier_points

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, player, groups, particle_groups, shake_func):
        super().__init__(groups)
        
        self.radius = 20 
        self.base_radius = random.randint(24, 28)
        
        # --- ПАРАМЕТРЫ ПОВОРОТА ---
        # ИЗМЕНЕНИЕ: Уникальная скорость поворота для каждого монстра.
        # Это разобьет синхронность толпы.
        self.turn_speed = random.uniform(0.04, 0.12)
        
        # --- НОГИ ---
        self.num_legs = random.randint(6, 8) 
        self.max_leg_dist = 90
        self.step_dist = 60
        self.legs = []
        
        for i in range(self.num_legs):
            angle = (i / self.num_legs) * 2 * math.pi
            target_pos = pygame.math.Vector2(pos) + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * 50
            
            self.legs.append({
                'ik_target': target_pos,
                'is_stepping': False,
                'step_progress': 0.0,
                'step_start': target_pos.copy(),
                'step_end': target_pos.copy(),
                'angle_offset': angle,
                'parent_body_idx': 0 
            })

        # --- ТЕЛО ---
        self.num_segments = random.randint(4, 6)
        self.body_parts = []
        
        # 1. Голова
        head_r = self.base_radius
        self.body_parts.append({
            'radius': head_r,
            'offset': pygame.math.Vector2(0, 0),
            'pulse_phase': 0,
            'eyes': [], 
            'seed': random.randint(0, 1000)
        })
        
        # 2. Сегменты
        for i in range(1, self.num_segments):
            parent_idx = int(random.triangular(0, i, 0))
            parent = self.body_parts[parent_idx]
            
            curr_r = parent['radius'] * random.uniform(0.6, 0.8)
            if curr_r < 6: curr_r = 6
            
            attach_angle = math.radians(random.uniform(0, 360))
            dist = parent['radius'] + curr_r - min(parent['radius'], curr_r) * 0.3
            
            relative_offset = pygame.math.Vector2(math.cos(attach_angle), math.sin(attach_angle)) * dist
            total_offset = parent['offset'] + relative_offset
            
            eyes = []
            if curr_r > 14: 
                if random.random() < 0.3: 
                    eye_size = random.randint(4, int(curr_r * 0.5))
                    eyes.append({
                        'angle': random.uniform(-0.5, 0.5), 
                        'size': eye_size,
                        'dist': random.uniform(0.3, 0.6) * curr_r
                    })

            self.body_parts.append({
                'radius': curr_r,
                'offset': total_offset,
                'pulse_phase': random.uniform(0, 6.28),
                'eyes': eyes,
                'seed': random.randint(0, 1000),
                'parent_idx': parent_idx 
            })

        for leg in self.legs:
            valid_parents = [idx for idx, p in enumerate(self.body_parts) if p['radius'] > 10]
            leg['parent_body_idx'] = random.choice(valid_parents) if valid_parents else 0

        self.surface_size = 450 
        self.image = pygame.Surface((self.surface_size, self.surface_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.visual_center = pygame.math.Vector2(self.surface_size // 2, self.surface_size // 2)
        
        self.pos = pygame.math.Vector2(pos)
        self.player = player
        
        self.base_speed = random.uniform(2.5, 4.0)
        self.current_speed = 0
        self.lunge_timer = random.randint(0, 60) 
        self.state = 'PREPARE'
        
        # Векторы взгляда
        start_angle = random.uniform(0, 6.28)
        self.head_look_dir = pygame.math.Vector2(math.cos(start_angle), math.sin(start_angle))
        self.pupil_look_dir = self.head_look_dir.copy()
        self.move_dir = self.head_look_dir.copy()
        
        self.attention_timer = random.randint(0, 100)
        self.attention_state = 'WANDER'
        self.wander_target = self.head_look_dir.copy()
        
        self.particle_groups = particle_groups
        self.shake_func = shake_func
        self.health = 80 
        self.anim_offset = random.uniform(0, 6.28)

    def soft_collision(self):
        for other in enemies:
            if other != self:
                dist_vec = self.pos - other.pos
                dist = dist_vec.length()
                if 0 < dist < 70: 
                    push = dist_vec.normalize() * (2.0 / dist * 60)
                    self.pos += push

    def update_physics_movement(self):
        target_move_dir = self.head_look_dir
        
        # ИЗМЕНЕНИЕ: Используем индивидуальную скорость поворота (self.turn_speed)
        # вместо константного 0.15. Теперь враги поворачиваются не синхронно.
        if self.move_dir.length() > 0 and target_move_dir.length() > 0:
             self.move_dir = self.move_dir.lerp(target_move_dir, self.turn_speed).normalize()
        
        self.lunge_timer += 1
        
        if self.state == 'PREPARE':
            self.current_speed = self.base_speed * 0.2
            if self.lunge_timer > 45:
                self.state = 'LUNGE'
                self.lunge_timer = 0
        elif self.state == 'LUNGE':
            progress = self.lunge_timer / 30
            speed_mult = 4.5 * (1 - progress)
            self.current_speed = self.base_speed * speed_mult
            if self.lunge_timer > 30:
                self.state = 'PREPARE'
                self.lunge_timer = 0
        
        self.pos += self.move_dir * self.current_speed

    def update_legs(self):
        move_dir_vec = self.move_dir
        tentacle_strips = []
        stepping_count = sum(1 for l in self.legs if l['is_stepping'])
        
        for i, leg in enumerate(self.legs):
            parent_segment = self.body_parts[leg['parent_body_idx']]
            segment_world_pos = self.pos + parent_segment['offset']
            
            angle_rad = leg['angle_offset']
            ideal_dir = pygame.math.Vector2(math.cos(angle_rad), math.sin(angle_rad))
            ideal_world_pos = self.pos + ideal_dir * 80 + move_dir_vec * 60
            
            dist_to_ideal = (leg['ik_target'] - ideal_world_pos).length()
            dist_stretch = (leg['ik_target'] - self.pos).length()
            
            if not leg['is_stepping']:
                if dist_stretch > self.max_leg_dist or dist_to_ideal > self.step_dist:
                    if stepping_count < 3: 
                        if random.random() < 0.2:
                            leg['is_stepping'] = True
                            leg['step_start'] = leg['ik_target'].copy()
                            leg['step_end'] = ideal_world_pos.copy()
                            leg['step_progress'] = 0.0
                            stepping_count += 1
            
            if leg['is_stepping']:
                leg['step_progress'] += 0.1
                if leg['step_progress'] >= 1.0:
                    leg['step_progress'] = 0.0
                    leg['is_stepping'] = False
                    leg['ik_target'] = leg['step_end'].copy() 
                else:
                    t = leg['step_progress']
                    base_pos = leg['step_start'].lerp(leg['step_end'], t)
                    leg['ik_target'] = base_pos
            
            body_attach_local = self.visual_center + parent_segment['offset']
            to_leg_world = (leg['ik_target'] - segment_world_pos)
            if to_leg_world.length() > 0:
                body_attach_local += to_leg_world.normalize() * (parent_segment['radius'] * 0.8)
            
            foot_local = leg['ik_target'] - self.pos + self.visual_center
            mid = (body_attach_local + foot_local) / 2
            control = mid + pygame.math.Vector2(0, -50) 
            if leg['is_stepping']: 
                control.y -= 40 
            
            points = get_bezier_points(body_attach_local, foot_local, control, segments=8)
            tentacle_strips.append(points)

        return tentacle_strips

    def update_look_direction(self):
        self.attention_timer += 1
        
        if self.attention_timer > 100:
            self.attention_timer = 0
            if random.random() < 0.95:
                self.attention_state = 'FOCUS'
            else:
                self.attention_state = 'WANDER'
                rand_angle = random.uniform(0, 6.28)
                self.wander_target = pygame.math.Vector2(math.cos(rand_angle), math.sin(rand_angle))

        if self.attention_state == 'FOCUS':
            target_look = self.player.pos - self.pos
            if target_look.length() > 0: target_look = target_look.normalize()
        else:
            target_look = self.wander_target

        self.head_look_dir = self.head_look_dir.lerp(target_look, 0.03)
        if self.head_look_dir.length() > 0: self.head_look_dir = self.head_look_dir.normalize()
        
        self.pupil_look_dir = self.pupil_look_dir.lerp(target_look, 0.15)
        if self.pupil_look_dir.length() > 0: self.pupil_look_dir = self.pupil_look_dir.normalize()

    def animate_procedural(self):
        self.image.fill((0,0,0,0))
        self.update_look_direction()
        tentacles = self.update_legs()
        
        draw_eldritch_horror(
            self.image, 
            self.visual_center, 
            self.body_parts, 
            tentacles, 
            self.anim_offset,
            self.head_look_dir,
            self.pupil_look_dir
        )

    def take_damage(self, amount):
        self.health -= amount
        self.attention_state = 'FOCUS'
        self.attention_timer = 50 
        for _ in range(5):
            Particle(self.pos, self.particle_groups, color=(100, 0, 100), speed=4, decay=10)
        if self.health <= 0:
            self.die()

    def die(self):
        self.shake_func(12)
        for _ in range(40):
            Particle(self.pos, self.particle_groups, color=COLOR_MONSTER_BODY, speed=6, decay=3)
        self.kill()

    def update(self, dt):
        self.update_physics_movement()
        self.soft_collision()
        self.animate_procedural()
        self.rect = self.image.get_rect(center=self.pos)