import pygame
from abc import ABC, abstractmethod

class Scene(ABC):
    """
    Абстрактный базовый класс для всех игровых сцен (Меню, Игра, Game Over и т.д.).
    """
    def __init__(self, manager):
        self.manager = manager

    @abstractmethod
    def handle_input(self, events):
        """Обработка событий (нажатия клавиш, мышь)."""
        pass

    @abstractmethod
    def update(self, dt):
        """Обновление логики (физика, таймеры)."""
        pass

    @abstractmethod
    def draw(self, surface):
        """Отрисовка кадра."""
        pass

    def enter(self):
        """Вызывается при входе в сцену (инициализация, запуск музыки)."""
        pass

    def exit(self):
        """Вызывается при выходе из сцены (очистка, остановка звуков)."""
        pass

class SceneManager:
    """
    Управляет текущей активной сценой и передает ей управление.
    """
    def __init__(self):
        self.current_scene = None

    def switch_to(self, new_scene):
        """
        Переключает текущую сцену на новую.
        Вызывает exit() у старой и enter() у новой.
        """
        if self.current_scene is not None:
            self.current_scene.exit()
        
        self.current_scene = new_scene
        
        if self.current_scene is not None:
            self.current_scene.enter()

    def handle_input(self, events):
        if self.current_scene:
            self.current_scene.handle_input(events)

    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface):
        if self.current_scene:
            self.current_scene.draw(surface)