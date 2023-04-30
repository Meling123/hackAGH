import pygame
import time
import os
import math
from plik import scale_image, blit_rotate_center
from typing import Tuple, List

TRACK = scale_image(pygame.image.load("imgs/dywan.png"), 1)

TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.1)

RED_CAR = scale_image(pygame.image.load("imgs/red-car.png"), 1)
YELLOW_CAR = scale_image(pygame.image.load("imgs/yellow-car.png"), 1)

PURPLE_CAR = scale_image(pygame.image.load("imgs/purple-car.png"), 1)
GREEN_CAR = scale_image(pygame.image.load("imgs/green-car.png"), 1)

WIDTH, HEIGHT =  1000,600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("symulacja")

FPS = 30

PATH = [ (492, 330),(800, 350),(492, 330),(300, 400) ] 
PATH = PATH * 100


class AbstractCar:
    def __init__(self, max_vel, rotation_vel,id,key, status: bool= True, doors_lock: bool=False, engine: bool=True, lights: bool=False):
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel*10
        self.angle = 270
        self.x, self.y = self.START_POS
        self.acceleration = 0.1
        self.status = status
        self.doors_lock = doors_lock
        self.engine = engine
        self.lights = lights
        self.id = id
        self.key = key

    def rotate(self, left=False, right=False):
        if left and self.vel>0.5:
            self.angle += self.rotation_vel
        elif right and self.vel>0.5:
            self.angle -= self.rotation_vel

    def draw(self, win):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()



    def move(self):
        radians = math.radians(self.angle)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel

        self.y -= vertical
        self.x -= horizontal

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 0.5,0)
        self.move()

    def reduce_brak(self):
        self.vel = abs(max(self.vel - self.acceleration*1.5 , 0))
        self.move()

    def change_color_purple(self):
        self.img = PURPLE_CAR

    def change_color_red(self):
        self.img = RED_CAR
        self.lights = False
    
    def change_color_yellow(self):
        self.img = YELLOW_CAR
        self.lights = True

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel/2)
        self.move()




class ComputerCar(AbstractCar):
    IMG = RED_CAR
    START_POS = (260, 410)  

    def __init__(self, max_vel, rotation_vel,id,key, path=[]):
        super().__init__(max_vel, rotation_vel,id=id,key=key)
        self.path = path
        self.current_point = 0
        self.vel = max_vel

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 5)

    def draw(self, win):
        super().draw(win)
        # self.draw_points(win)

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radian_angle = math.pi / 2
        else:
            desired_radian_angle = math.atan(x_diff / y_diff)

        if target_y > self.y:
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)
        if difference_in_angle >= 180:
            difference_in_angle -= 360

        if difference_in_angle > 0:
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else:
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        target = self.path[self.current_point]
        rect = pygame.Rect(
            self.x, self.y, self.img.get_width(), self.img.get_height())
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        if self.current_point >= len(self.path):
            return

        self.calculate_angle()
        self.update_path_point()
        super().move()


    def change_engine(self):
        self.engine = not(self.engine)

    def change_lock(self):
        self.doors_lock = not(self.doors_lock)  

    def get_position(self):
        return self.x, self.y
    
    def change_vel(self, max_vel):
        self.reduce_speed()
    
    def change_lights(self):
        self.lights = True

    def clear(self):
            os.system('cls')
    
    def get_vel(self):
        return self.vel
    
    def print_parametry(self):
        self.clear()
        if self.status==True:
            print('*'*100)
            print(' '*35+'Aktualna prędkość: {}        {} {} {}'.format(self.vel*30,0,'['+'#'*int(20*(self.vel/self.max_vel))+' '*int(20*(1-self.vel/self.max_vel))+']',self.max_vel*30))
            print(' '*35+'Wspołrzędne X:{} Y:{}'.format(self.x,self.y))
            print(' '*35+'Zamknięte drzwi: {}'.format(self.doors_lock))
            print(' '*35+'Włączone światła: {}'.format(self.lights))
            print('*'*100)
        else:
            print('*'*100)
            print(' '*35+'Brak kontaktu z serverem')
            print('*'*100)


class Server:
    def __init__(self, car: AbstractCar):
        self.car = car
        self.status = False
        self.alarm = 0

    
    def statuse(self,car_id, key):
        if self.__autorization(car_id, key):
            self.status = self.car.status
            return self.status

    
    def __autorization(self, car_id, key):
        if car_id == self.car.id and key == self.car.key:
            return True
        if car_id != self.car.id and key != self.car.key:
            return False
        if car_id == self.car.id and key != self.car.key:
            self.alarm += 1
            return False
        

    #funkcjonalności pojazdu
    def set_max_vel(self,car_id, key,vel):
        if self.__autorization(car_id, key) and self.car.engine==True:
            self.car.change_vel(vel)


    def doors_lock(self,car_id, key):
        if self.__autorization(car_id, key):
            self.car.change_lock()


    def engine_start_stop(self,car_id, key):
        if self.__autorization(car_id, key):
            if self.car.velocity==0 and self.car.engine==True:
                self.car.change_engine(False)
            if self.car.velocity==0 and self.car.engine==False:
                self.car.change_engine(True)
            if self.car.velocity != 0:
                print('Can not turn off engine while driving')


    def position(self,car_id, key):
        if self.__autorization(car_id, key):
            return self.car.get_position()
         
        
    def change_lights_alarm(self, car_id, key):
        if self.__autorization(car_id, key):
            self.car.change_color_purple()
       
    
    def change_lights_off(self, car_id, key):
        if self.__autorization(car_id, key):
            self.car.change_color_red()
        
    def change_lights_on(self, car_id, key):
        if self.__autorization(car_id, key):
            self.car.change_color_yellow()

    def disp(self, car_id, key):
        if self.__autorization(car_id, key):
            return self.car.print_parametry()
        
    def get_alarm(self):
        return self.alarm
        

class Typ:
    def __init__(self):
        c = ComputerCar()

class Kierowca:
    def __init__(self,key,car_id, Ser):
        self.key=key
        self.car_id=car_id
        self.Ser = Ser

    def velosity(self,vel):
        self.Ser.set_max_vel(self.car_id,self.key,vel)

    def door(self):
        self.Ser.doors_lock(self.car_id,self.key)

    def engine(self):
        self.Ser.engine_start_stop(self.car_id,self.key)

    def pos(self):
        return self.Ser.position(self.car_id,self.key)

    def lights_on(self):
        self.Ser.change_lights_on(self.car_id,self.key)
    
    def lights_off(self):
        self.Ser.change_lights_off(self.car_id,self.key)

    def stat(self):
        return self.Ser.statuse(self.car_id, self.key)
    
    def disp(self):
        return self.Ser.disp(self.car_id, self.key)


def draw(win, images, computer_car):
    for img, pos in images:
        win.blit(img, pos)


    computer_car.draw(win)
    pygame.display.update()



run = True
clock = pygame.time.Clock()
images = [(TRACK, (0, 0))]
computer_car = ComputerCar(2, 2,'111','222', path=PATH)

s = Server(computer_car)


change = False
alarm = False
d = False
disp = False

while run:
    clock.tick(FPS)
    k = Kierowca('222', '111',s)

    draw(WIN, images, computer_car)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            break

    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_m]:
        alarm = True
        d = True

    if alarm and d:
        computer_car.change_color_purple()
        alarm = False
    else:
        computer_car.change_color_red()
        alarm = True

    if keys[pygame.K_a]:
        computer_car.rotate(left=True,)
    if keys[pygame.K_d]:
        computer_car.rotate(right=True)
    if keys[pygame.K_w]:
        moved = True
        computer_car.move_forward()
    if keys[pygame.K_s]:
        moved = True
        computer_car.reduce_brak()
    if keys[pygame.K_g]:
        computer_car.change_color_purple()
    if keys[pygame.K_r]:
        computer_car.change_color_red()
    if keys[pygame.K_x]:
        break
    if keys[pygame.K_b]:
        moved = True
        computer_car.move_backward()
    if keys[pygame.K_0]:
        #wyświetlacz
        k.disp()
    if keys[pygame.K_1]:
        #pozycja
        print(k.pos())
    if keys[pygame.K_2]:
        #światłą
        k.lights_on()
    if keys[pygame.K_3]:
        k.lights_off()
    if keys[pygame.K_4]:
        #silnik
        k.engine()
    if keys[pygame.K_5]:
        #drzwii
        k.door()
    if keys[pygame.K_6]:
        #zmniejsz prędkość
        change = True
    if keys[pygame.K_7]:
        disp = True

    if change:
        k.velosity(1)

    if computer_car.get_vel() <= 1:
        print(computer_car.get_position())
        change = False

    computer_car.move()
    
    if disp:
        k.disp()

pygame.quit()