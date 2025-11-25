import pygame
from core.config import TILE_SIZE, COLOR_GRID

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        # Цвет стен (темно-серый камень)
        self.image.fill((50, 50, 60)) 
        # Рисуем рамку для наглядности
        pygame.draw.rect(self.image, (30, 30, 40), (0, 0, TILE_SIZE, TILE_SIZE), 2)
        self.rect = self.image.get_rect(topleft=pos)

class Map:
    def __init__(self, map_data):
        self.map_data = map_data
        self.obstacles = pygame.sprite.Group()      # Группа для коллизий
        self.all_map_sprites = pygame.sprite.Group() # Группа для отрисовки
        
        # Вычисляем реальные размеры мира в пикселях
        self.width = len(map_data[0]) * TILE_SIZE
        self.height = len(map_data) * TILE_SIZE
        
        self._generate_map()

    def _generate_map(self):
        """Парсит список строк и создает тайлы."""
        for row, tiles in enumerate(self.map_data):
            for col, tile in enumerate(tiles):
                if tile == '#':
                    pos = (col * TILE_SIZE, row * TILE_SIZE)
                    Tile(pos, [self.obstacles, self.all_map_sprites])