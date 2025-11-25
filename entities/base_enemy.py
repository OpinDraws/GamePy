import pygame
from core.config import enemies, COLOR_MONSTER_BODY
from vfx import Particle

class BaseEnemy(pygame.sprite.Sprite):
    """
    Базовый класс врага. 
    Отвечает за:
    - Регистрацию в группах спрайтов
    - Базовое здоровье
    - Получение урона и смерть (спавн частиц)
    - Мягкие коллизии (чтобы враги не слипались)
    """
    def __init__(self, pos, player, groups, particle_groups, shake_func, health):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.player = player
        self.particle_groups = particle_groups
        self.shake_func = shake_func
        
        self.health = health
        self.max_health = health # На будущее для отрисовки полоски HP
        
        # Заглушка для спрайта (переопределяется в наследниках)
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=pos)

    def soft_collision(self):
        """Расталкивает врагов друг от друга."""
        for other in enemies:
            if other != self:
                dist_vec = self.pos - other.pos
                dist = dist_vec.length()
                # Если слишком близко — отталкиваемся
                if 0 < dist < 70: 
                    push = dist_vec.normalize() * (2.0 / dist * 60)
                    self.pos += push

    def take_damage(self, amount):
        """Базовая логика получения урона."""
        self.health -= amount
        
        # Спавн крови при попадании (общий для всех)
        for _ in range(5):
            Particle(self.pos, self.particle_groups, color=(100, 0, 100), speed=4, decay=10)
            
        if self.health <= 0:
            self.die()

    def die(self):
        """Базовая смерть."""
        self.shake_func(12)
        # Взрыв частиц
        for _ in range(40):
            Particle(self.pos, self.particle_groups, color=COLOR_MONSTER_BODY, speed=6, decay=3)
        self.kill()