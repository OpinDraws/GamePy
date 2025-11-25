import pygame
from core.config import WIDTH, HEIGHT

class Camera:
    def __init__(self, width, height):
        # width, height — это размеры всей карты (в пикселях)
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.offset = pygame.math.Vector2(0, 0)

    def update(self, target_rect):
        # Вычисляем смещение, чтобы цель была в центре экрана
        x = -target_rect.centerx + int(WIDTH / 2)
        y = -target_rect.centery + int(HEIGHT / 2)

        # Ограничиваем камеру, чтобы не выходила за пределы карты
        # Левая и верхняя границы: смещение не может быть больше 0
        x = min(0, x)
        y = min(0, y)
        
        # Правая и нижняя границы: смещение не может быть меньше, чем (размер_экрана - размер_карты)
        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)

        self.offset = pygame.math.Vector2(x, y)