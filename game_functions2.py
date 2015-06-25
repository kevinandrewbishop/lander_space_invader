import pygame
from pygame.locals import *
from sys import exit
from random import randint

WIDTH = 1900
HEIGHT = 1000
pygame.init()
SCREEN_SIZE = (WIDTH,HEIGHT)

class Vector2():
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return "(%s, %s)"%(self.x, self.y)

    def get_heading_to_point(self, point):
        return Vector2( point[0] - self[0], point[1] - self[1] )

    def get_heading(self, point):
        return Vector2( point[0] - self[0], point[1] - self[1] )

    def get_distance_from_point(self, point):
        heading = self.get_heading(point)
        distance = heading.get_magnitude()
        return distance

    def get_magnitude(self):
        return ( self.x**2 + self.y**2 )**.5

    def normalize(self):
        magnitude = self.get_magnitude()
        if magnitude == 0:
            self.x = 0
            self.y = 0
            return None
        self.x /= magnitude
        self.y /= magnitude

        # rhs stands for Right Hand Side
    def __add__(self, rhs):
        return Vector2(self.x + rhs.x, self.y + rhs.y)

    def __sub__(self, rhs):
        return Vector2(self.x - rhs.x, self.y - rhs.y)

    def __neg__(self):
        return Vector2(-self.x, -self.y)

    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)

    def __div__(self, scalar):
        return Vector2(self.x / scalar, self.y / scalar)

    def __getitem__(self, index):
        if index == 0:
            return self.x
        if index == 1:
            return self.y

    def int_(self):
        return Vector2(int(self.x), int(self.y))


class World():
    def __init__(self):
        self.entities = {}
        self.entity_id = 0
        self.background = pygame.surface.Surface(SCREEN_SIZE).convert()
        self.background.fill((0, 255, 0))
        self.entity_add_list = set()
        self.entity_remove_list = set()

    def add_entity(self, entity):
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def remove_entity(self, entity):
        self.entities[entity.id] = None
        del self.entities[entity.id]

    def get(self, entity_id):
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def process(self, time_passed_seconds):
        for entity in self.entities.values():
            entity.process(time_passed_seconds)

        for entity in self.entity_add_list:
            self.add_entity(entity)

        for entity in self.entity_remove_list:
            self.remove_entity(entity)

        self.entity_add_list.clear()
        self.entity_remove_list.clear()

    def render(self, surface):
        surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)

    def get_close_entity(self, name, coord, Range=100.):
        location = Vector2(coord.x, coord.y)
        for entity in self.entities.values():
            if entity.name == name:
                distance = location.get_heading(entity.coord).get_magnitude()
                if distance < Range:
                    return entity
        return None

#TESTING CODE
if __name__ == '__main__':
    vec = Vector2(5,6)
    print(vec[0])
    point = (10,12)
    heading = vec.get_heading_to_point(point)
    print(heading)
    point = Vector2(10,12)
    heading = vec.get_heading_to_point(point)
    print(heading)
