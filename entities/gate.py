import pygame
from core.config import TILE_SIZE

class Gate(pygame.sprite.Sprite):
    def __init__(self, pos, groups, is_horizontal=True):
        super().__init__(groups)
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        # Визуал закрытой двери (например, золотой цвет)
        self.image.fill((200, 150, 50)) 
        # Небольшая обводка
        pygame.draw.rect(self.image, (100, 80, 20), (0,0, TILE_SIZE, TILE_SIZE), 4)
        
        self.rect = self.image.get_rect(topleft=pos)
        self.is_open = False

    def open(self):
        if not self.is_open:
            self.is_open = True
            # Визуально дверь "открывается" (становится темной/прозрачной или исчезает)
            self.image.fill((20, 15, 20)) # Цвет пола
            # Убираем коллизию, смещая рект куда-то далеко или используя kill() в зависимости от логики
            # Но лучше просто пометить флагом, а в GameScene проверять коллизию.
            # Для простоты здесь мы просто уберем спрайт из группы препятствий, если она передана отдельно,
            # но так как мы используем общую физику, проще сделать kill()
            self.kill()