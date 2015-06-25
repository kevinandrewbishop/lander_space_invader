import pygame
from pygame.locals import *
from sys import exit
from random import randint

WIDTH = 1140
HEIGHT = 880
pygame.init()
SCREEN_SIZE = (WIDTH,HEIGHT)
clock = pygame.time.Clock()
screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)

import game_functions2 as f

class Ground():
    def __init__(self, difficulty = 5, number_of_changes = 20, screen_size = SCREEN_SIZE):
        self.x_points = [0] + [randint(0,screen_size[0]) for i in range(number_of_changes)] + [screen_size[1]]
        self.x_points.sort()
        self.y_points = [screen_size[1]]
        for i in range(number_of_changes):
            y = self.y_points[i] + randint(-difficulty*10,difficulty*10)
            if y > screen_size[1]: y = screen_size[1]-1
            if y < screen_size[1]/2: y = int(screen_size[1]/2)
            self.y_points.append(y)
        self.y_points.append(screen_size[1])
        self.points = []
        for i in range(len(self.x_points)):
            self.points.append((self.x_points[i],self.y_points[i]))
        
    def render(self, screen):
        pygame.draw.polygon(screen,(0,0,0),self.points)

class MissileSilo():
    def __init__(self, ground, target):
        location = randint(1,len(ground.points)-3)
        self.coord = ground.points[location]
        self.missiles = []
        self.target = target
        self.destroyed = False
        self.time_since_last_launch = 0

    def render(self, screen):
        rect = [self.coord, (self.coord[0]+8, self.coord[1]), (self.coord[0]+8, self.coord[1]-8),(self.coord[0], self.coord[1]-8)]
        pygame.draw.polygon(screen,(0,0,200),rect)
        if self.destroyed:
            for i in range(3):
                color = (randint(250,255),randint(0,255),0)
                pygame.draw.circle(screen,color,(self.coord[0] + randint(-15,15),self.coord[1] + randint(-15,15)), 4)
        

    def launch_missile(self, target):
        if not self.destroyed:
            self.missiles.append(Missile(self, target))
            self.time_since_last_launch = 0

    def update_missiles(self):
        self.time_since_last_launch += 1
        if (len(self.missiles) == 0 or self.time_since_last_launch > 60) and (len(self.missiles) < 5):
            self.launch_missile(self.target)
        for missile in self.missiles:
            missile.launch()
            missile.check_explosion()
            missile.render(screen)

class Missile():
    def __init__(self, silo, target):
        self.coord = f.Vector2(silo.coord[0], silo.coord[1])
        self.coord_int = self.coord.int_()
        self.silo = silo
        self.target = target
        self.accel = self.coord.get_heading(target.coord)
        self.accel.normalize()
        self.accel = self.accel*.05
        self.vel = f.Vector2(0,0)

    def launch(self):
        self.vel += self.accel
        self.coord += self.vel
        self.coord_int = self.coord.int_()
        if self.coord.get_heading(self.silo.coord).get_magnitude() > 3000:
            self.silo.missiles.remove(self)

    def check_explosion(self):
        if self.coord.get_heading(self.target.coord).get_magnitude() < 5:
            self.accel = f.Vector2(0,0)
            self.vel = f.Vector2(0,0)
            self.target.crash()

    def render(self, screen):
        self.points = [(self.coord_int.x, self.coord_int.y), (int(self.coord_int.x + self.accel.x*100), int(self.coord_int.y + self.accel.y*100))]
        pygame.draw.polygon(screen, (255,0,0), self.points,3)
        
class Bomb():
    def __init__(self, lander):
        self.lander = lander
        self.coord = lander.coord
        self.coord_int = self.coord.int_()
        self.vel = f.Vector2(0,0)
        self.accel = f.Vector2(0,.01)
        self.exploded = False
        self.frames_exploded = 0

    def check_explosion(self, ground, target_list):
        if self.exploded:
            self.frames_exploded += 1
            if self.frames_exploded > 15:
                self.lander.bombs.remove(self)
                return None
        for i in range(1,len(ground.x_points)):
            if self.coord.x <= ground.x_points[i]:
                index = i
                ground_elevation = min(ground.y_points[index], ground.y_points[index-1])
                break
        if self.coord.y + 5 < ground_elevation:
            return None
        else:
            rise = ground.y_points[index] - ground.y_points[index-1]
            run = ground.x_points[index] - ground.x_points[index-1]
            slope = rise/run
            x_position = self.coord.x - ground.x_points[index-1]
            if self.coord.y + 1 >= ground.y_points[index-1] + slope*x_position:
                self.exploded = True
                self.accel = f.Vector2(0,0)
                self.vel = f.Vector2(0,0)
                for target in target_list:
                    if self.coord.get_heading(target.coord).get_magnitude() < 50:
                        target.destroyed = True

    def move(self):
        self.vel += self.accel
        self.coord += self.vel
        self.coord_int = self.coord.int_()

    def render(self, screen):
        pygame.draw.circle(screen,(255,150,0),(self.coord_int.x, self.coord_int.y), 2)
        if self.exploded:
            self.frames_exploded += 1
            for i in range(3):
                color = (randint(250,255),randint(0,255),0)
                pygame.draw.circle(screen,color,(self.coord_int.x + randint(-15,15),self.coord_int.y + randint(-15,15)), 4)
        

    
        
class Lander():
    def __init__(self,coord=f.Vector2(WIDTH/10,HEIGHT/10)):
        self.coord = coord
        self.coord_int = coord.int_()
        self.vel = f.Vector2(0,0);
        self.accel_due_to_gravity = f.Vector2(0,.01)
        self.accel_due_to_thrust = f.Vector2(0,0)
        self.accel = self.accel_due_to_gravity + self.accel_due_to_thrust
        self.crashed = False
        self.landed = False
        self.safe_to_land = False
        self.fuel = 100
        self.bombs = []
        self.time_since_last_bomb = 0
    
    def check_thrusters(self, thrust_power = .05):
        pressed_keys = pygame.key.get_pressed()
        if self.fuel <=0:
            self.accel_due_to_thrust = f.Vector2(0,0)
            return None
        no_key_pressed = True
        if pressed_keys[K_UP]:
            self.accel_due_to_thrust.y = -thrust_power
            no_key_pressed = False
        if pressed_keys[K_DOWN]:
            self.accel_due_to_thrust.y = thrust_power
            no_key_pressed = False
        if pressed_keys[K_LEFT]:
            self.accel_due_to_thrust.x = -thrust_power
            no_key_pressed = False
        if pressed_keys[K_RIGHT]:
            self.accel_due_to_thrust.x = thrust_power
            no_key_pressed = False
        if no_key_pressed:
            self.accel_due_to_thrust.y = 0
            self.accel_due_to_thrust.x = 0
        if not no_key_pressed:
            self.landed = False
            self.fuel -= .1

    def drop_bomb(self):
        self.time_since_last_bomb += 1
        if self.time_since_last_bomb < 60:
            return None
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_SPACE]:
            self.bombs.append(Bomb(self))
            self.time_since_last_bomb = 0
        
    def handle_bombs(self, ground, target_list, screen):
        for bomb in self.bombs:
            bomb.check_explosion(ground, target_list)
            bomb.move()
            bomb.render(screen)

    def move(self):
        if self.landed:
            self.accel_due_to_gravity = f.Vector2(0.0,0.0)
        else:
            self.accel_due_to_gravity = f.Vector2(0.0,.01)
        if not self.crashed:
            self.check_thrusters()
            self.accel = self.accel_due_to_gravity + self.accel_due_to_thrust
            self.vel += self.accel
            self.coord += self.vel
        self.coord_int = self.coord.int_()

    def check_landing(self, ground):
        ground_elevation = HEIGHT
        for i in range(1,len(ground.x_points)):
            if self.coord.x <= ground.x_points[i]:
                index = i
                ground_elevation = min(ground.y_points[index], ground.y_points[index-1])
                break
        if self.coord.y + 5 < ground_elevation:
            return None
        else:
            rise = ground.y_points[index] - ground.y_points[index-1]
            run = ground.x_points[index] - ground.x_points[index-1]
            slope = rise/run
            if abs(slope) <= .1: self.safe_to_land = True
            x_position = self.coord.x - ground.x_points[index-1]
            if self.coord.y + 5 >= ground.y_points[index-1] + slope*x_position:
                if abs(slope) > .1:
                    self.crash()
                if self.vel.get_magnitude() > .5:
                    self.crash()
                self.vel = f.Vector2(0,0)
                self.accel = f.Vector2(0,0)
                self.landed = True

    def crash(self):
        self.crashed = True
        self.vel = f.Vector2(0,0)
        self.accel = f.Vector2(0,0)
            
    

    def render(self, screen = screen):
        pygame.draw.circle(screen,(200,200,200),(self.coord_int.x,self.coord_int.y), 5)
        if self.crashed:
            for i in range(1):
                color = (randint(250,255),randint(0,255),0)
                pygame.draw.circle(screen,color,(self.coord_int.x + randint(-5,5),self.coord_int.y + randint(-5,5)), 4)
        if self.accel_due_to_thrust.y < 0:
            pygame.draw.circle(screen,(255,100,0),(self.coord_int.x,self.coord_int.y+5), 2)
        if self.accel_due_to_thrust.y > 0:
            pygame.draw.circle(screen,(255,100,0),(self.coord_int.x,self.coord_int.y-5), 2)
        if self.accel_due_to_thrust.x > 0:
            pygame.draw.circle(screen,(255,100,0),(self.coord_int.x-5,self.coord_int.y), 2)
        if self.accel_due_to_thrust.x < 0:
            pygame.draw.circle(screen,(255,100,0),(self.coord_int.x+5,self.coord_int.y), 2)
        


        
capsule = Lander()
moon = Ground(10, 40)
silos = [MissileSilo(moon, capsule) for i in range(10)]
font = pygame.font.SysFont("arial", 15)
font2 = pygame.font.SysFont("arial", 75)

pixels_per_second = 10

silos[0].launch_missile(capsule)
silos[1].launch_missile(capsule)

paused = False
while True:    
    for event in pygame.event.get():
        if event.type == QUIT:
            exit()
    
    pause_message = 'PAUSED'
    text_surface4 = font2.render(pause_message, True, (255, 255, 255))
    screen.blit(text_surface4, (WIDTH/3, HEIGHT/3))

    
    
    #MAIN GAME LOOP GOES HERE
    screen.fill((50,50,50))
    time_passed = clock.tick(70)
    time_passed_seconds = time_passed/1000

    
    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[K_p]:
        paused = not paused

    if paused:
        continue
    
        

    pygame.draw.circle(screen,(255,255,255),(550,150),35)
    capsule.move()
    capsule.check_landing(moon)
    capsule.drop_bomb()
    capsule.handle_bombs(moon, silos, screen)
    capsule.render(screen)
    moon.render(screen)
    for silo in silos:
        silo.render(screen)
        silo.update_missiles()

    if capsule.landed and not capsule.crashed:
        score = sum([silo.destroyed for silo in silos])*5
        score += capsule.fuel
        victory_message = 'VICTORY! Score = %.1f' %score
        text_surface3 = font2.render(victory_message, True, (255, 255, 255))
        screen.blit(text_surface3, (WIDTH/4, HEIGHT/3))
        paused = True

    if capsule.crashed:
        loss_message = 'YOU LOSE!'
        text_surface3 = font2.render(loss_message, True, (255, 255, 255))
        screen.blit(text_surface3, (WIDTH/3, HEIGHT/3))
        paused = True

    
        
        

    speed = 'Speed: %.1f' %capsule.vel.get_magnitude()
    fuel = 'Fuel: %.1f' %capsule.fuel
    text_surface = font.render(speed, True, (255, 255, 255))
    text_surface2 = font.render(fuel, True, (255, 255, 255))
    screen.blit(text_surface, (5, 5))
    screen.blit(text_surface2, (5, 20))

    
    
    
    pygame.display.update()
