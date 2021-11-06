#description: shooter game for homemade arcade machine, RPi based
#author: Ramiro Vargas, August 2021

#pending agregar funcion de respawn para los enemigos, con parametero x random
#eliminar de init() las partes que respawn ya tien


#!/usr/bin/env python

import pygame
from pygame.compat import geterror
import random
import math
from moviepy.editor import *
import RPi.GPIO as GPIO 
from time import sleep


### 1. Game globals - don't touch ########################


# 0 - demo / insert coin screen
# 1 - score screen
# 2 - game over
# 3 - mansion level screen
# 4 - farm level screen
# 5 - game over screen
GameScreen = 0


TestStatus = 0

Global_SightXPos = -99
Global_SightYPos = -99
Global_SightTriggerPulled = False



### 2. Game constants - modify accordingly ###############

#screen size
screen_ylimit = 600
screen_xlimit = 900

#spawn constants
spawn_upper_xlimit = screen_xlimit-50
spawn_lower_xlimit = 450
spawn_ypos = 429
spawncounter_upperlimit =  500
spawncounter_lowerlimit =  100

#sight limits
sight_upper_ylimit = 50
sight_lower_ylimit = 600
sight_upper_xlimit = 1100
sight_lower_xlimit = 300

# debug flag to print info on console
Debug = False
enemy_debug = False
sight_debug = False
update_debug = False
mainloop_debug = False
deep_debug = False
collision_debug = False

# nmy - images
sldimgfolder = './img/characters/soldier'
nmyimgfolder = './img/characters/nmy'
sgtimgfolder = './img/sights'
objimgfolder = './img/objects'


# sight
sight_xspeed = 5
sight_yspeed = 5
sight_xwidth = 84
sight_ywidth = 84
gun_kickback_ytravel = 10
gun_kickback_xtravel = 0

# ammo indicator in screen
soldierclipcapacity = 10
ammoindicator_xstart = 600
ammoindicator_ystart = 550

# enemy
enemy_max = 3 #how many enmies in screen #FIXME: unneeded

#  time that player has to kill all enemies
timerstart_screen3=1
timerstart_screen4=30
timer_delta = 0.01
timertext_xpos = 30
timertext_ypos = 5

# font
arcadefont_path = './font'
scoretext_xpos = 30
scoretext_ypos = 50
finalscoretext_xpos = screen_xlimit/2 - 100
finalscoretext_ypos = screen_ylimit -100

#sequences
orderqueue_orders0 = ["standup", "standfreeze", "shoot", "shoot",
                      "shoot", "shoot", "standfreeze", "duck", "duckfreeze"]

orderqueue_orders1 = ["duck","duckfreeze", "duckfreeze", "duckfreeze", "standup","shoot",
                      "shoot", "shoot", "shoot", "standfreeze", "standfreeze"]


FPS = 30

# Screen 0 (coin acceptor) - images
screen0_introclip = VideoFileClip('./img/Screen0/intro0_video_short.mp4')


#screen 1 - down count

insertcoin0_image = pygame.image.load('./img/Screen0/scree0_intro1_0.png')
insertcoin1_image = pygame.image.load('./img/Screen0/scree0_intro1_1.png')


countdown0_image = pygame.image.load('./img/Screen0/scree0_intro2_0.png')
countdown1_image = pygame.image.load('./img/Screen0/scree0_intro2_1.png')
countdown2_image = pygame.image.load('./img/Screen0/scree0_intro2_2.png')
countdown3_image = pygame.image.load('./img/Screen0/scree0_intro2_3.png')

# Screen 3 - First Level
House0_MainImage = pygame.image.load('./img/Screen3/house0.jpg')
House0_WallImage = pygame.image.load('./img/Screen3/walla.png')

# Screen 4 - Second Level
House1_MainImage = pygame.image.load('./img/Screen4/house1.jpg')
House1_WallImage = pygame.image.load('./img/Screen4/stonewall1.png')
Wallspawn_xpos = 280
Wallspawn_ypos = 300

# Screen 5 - Score Screen
GameOver_MainImage = pygame.image.load('./img/Screen5/screen5_background.png')


### collision boxes - nmy 0
nmy0_headbox_st_tl = -79 #headbox standing position, top limit
nmy0_headbox_st_bl = -127 #headbox standing position, bottom limit
nmy0_headbox_st_ll = 8 #headbox standing position, left  limit
nmy0_headbox_st_rl = 57 #headbox standing position, right  limit

nmy0_chestbox_st_tl = 41 #chestbox standing position, top limit
nmy0_chestbox_st_bl = -79 #chestbox standing position, bottom limit
nmy0_chestbox_st_ll = -20 #chestbox standing position, left  limit
nmy0_chestbox_st_rl = 61 #chestbox standing position, right  limit

# sounds
sound_path = './sound/' #effects
bkgn_path = './sound/level/'     #background


###Health
nmyhealth_initial = 10
nmyhealth_loss = 5



### Animation constants
animationlength_duck = 15
animationlength_shoot = 10
animationlength_fall = 30
animationlenght_freeze = 30
animationlength_reload = 14

#movies
intro_movie = './img/Screen0/intro0_video.mp4'


### 3. Functions  #########################################

# function to play movie
def play_videoFile(filePath,mirror=False):
    cap = cv2.VideoCapture(filePath)
    cv2.namedWindow('Video Life2Coding',cv2.WINDOW_AUTOSIZE)
    while True:
        ret_val, frame = cap.read()
        if mirror:
            frame = cv2.flip(frame, 1)
        cv2.imshow('Video Life2Coding', frame)
        if cv2.waitKey(1) == 27:
            break  # esc to quit
    cv2.destroyAllWindows()

# functions to load image, copied from Chimp example
def load_image(name, colorkey=None):
    try:
        image = pygame.image.load(name)
    except pygame.error:
        #print("Cannot load image:", name)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()

# functions to load sound, copied from Chimp example
def load_sound(name):
    class NoneSound:
        def play(self):
            pass

    if not pygame.mixer or not pygame.mixer.get_init():
        return NoneSound()
    try:
        sound = pygame.mixer.Sound(name)
    except pygame.error:
        #print("Cannot load sound: %s" % name)
        raise SystemExit(str(geterror()))
    return sound

### 6. Classes ##################

#spawning point class for soldier
class ClassSoldier(pygame.sprite.Sprite):

    def __init__(self,xspawn_pos,yspawn_pos):

        imagename = ''
        self.x = xspawn_pos
        self.y = yspawn_pos
        self.occupied = False

        #defining sounds
        self.reload_sound =  load_sound(sound_path+"/gun/pistol_reload_b.wav")

        #rotating arm images
        self.imager0=load_image(sldimgfolder+'/arm_rotating/'+'r0.png',-1)
        self.imager5=load_image(sldimgfolder+'/arm_rotating/'+'r5.png',-1)
        self.imager10=load_image(sldimgfolder+'/arm_rotating/'+'r10.png',-1)
        self.imager15=load_image(sldimgfolder+'/arm_rotating/'+'r15.png',-1)
        self.imager20=load_image(sldimgfolder+'/arm_rotating/'+'r20.png',-1)
        self.imager25=load_image(sldimgfolder+'/arm_rotating/'+'r25.png',-1)
        self.imager30=load_image(sldimgfolder+'/arm_rotating/'+'r30.png',-1)
        self.imager35=load_image(sldimgfolder+'/arm_rotating/'+'r35.png',-1)
        self.imager40=load_image(sldimgfolder+'/arm_rotating/'+'r40.png',-1)
        self.imager45=load_image(sldimgfolder+'/arm_rotating/'+'r45.png',-1)
        self.imager50=load_image(sldimgfolder+'/arm_rotating/'+'r50.png',-1)
        self.imager55=load_image(sldimgfolder+'/arm_rotating/'+'r55.png',-1)
        self.imager60=load_image(sldimgfolder+'/arm_rotating/'+'r60.png',-1)
        self.imager65=load_image(sldimgfolder+'/arm_rotating/'+'r65.png',-1)
        self.imager70=load_image(sldimgfolder+'/arm_rotating/'+'r70.png',-1)

        #loading gun images
        #loading shooting images
        self.images_realoding = []
        for i in range(0,14):
            imagename=sldimgfolder+'/reloading/'+'r'+str(i)+'.png'
            self.images_realoding.append(load_image(imagename,-1))

        self.imgindex = 0  # to update the sprites
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image, self.rect = self.imager0
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = self.x, self.y

        self.sightxpos=-999
        self.sightypos=-999
        self.sighttriggerpulled = False
        self.order = "ready"

    def sightstatusacquire(self,x,y,triggerpulled):

        self.sightxpos = x
        self.sightypos = y
        self.sighttriggerpulled = triggerpulled

    def reload(self):

        if self.imgindex == 0:
            self.reload_sound.play()

        if self.imgindex < (animationlength_reload - 1):
            self.imgindex += 1
            self.image, self.rect = self.images_realoding[self.imgindex]
            self.rect.center = self.x, self.y
        if self.imgindex == (animationlength_reload - 1):
            self.imgindex = 0
            self.order = "reloaded"

    #calculate angle between sight and  soldier, to update the arm
    def armupdate(self):

        difx = abs(self.rect.centerx-self.sightxpos)
        dify = abs(self.rect.centery-self.sightypos)
        h = math.sqrt(difx*difx+dify*dify)
        angle = math.acos(difx/h)*(180/math.pi)
        angle = int(angle)

        if angle >=0 and angle <=4:
            self.image, self.rect = self.imager0
        elif angle >=5 and angle <=9:
            self.image, self.rect = self.imager5
        elif angle >=10 and angle <=14:
            self.image, self.rect = self.imager10
        elif angle >=15 and angle <=19:
            self.image, self.rect = self.imager15
        elif angle >=20 and angle <=24:
            self.image, self.rect = self.imager20
        elif angle >=25 and angle <=29:
            self.image, self.rect = self.imager25
        elif angle >=30 and angle <=34:
            self.image, self.rect = self.imager30
        elif angle >=35 and angle <=39:
            self.image, self.rect = self.imager35
        elif angle >=40 and angle <=44:
            self.image, self.rect = self.imager40
        elif angle >=45 and angle <=49:
            self.image, self.rect = self.imager45
        elif angle >=50 and angle <=54:
            self.image, self.rect = self.imager50
        elif angle >=55 and angle <=59:
            self.image, self.rect = self.imager55
        elif angle >=60 and angle <=64:
            self.image, self.rect = self.imager60
        elif angle >=65 and angle <=70:
            self.image, self.rect = self.imager65
        else:
            self.image, self.rect = self.imager0

        self.rect.center = self.x, self.y
        #print(str(angle)) #FIXME: delete after final test


    def update(self):

        if self.order == "ready":
            self.armupdate()
        elif self.order == "reload":
            self.reload()
######### ########### ############ ############


#enemy Class
#enemytype 0/1 : enemy type
#spawn_x,spawn_y : xy location to spawn
#mode test/normal: testing or not the class

class ClassEnemy (pygame.sprite.Sprite):


    def __init__(self, spawn_x, spawn_y, enemytype):

        imagename = ''
        #enemytype = '1' #0: nmy0, 1:nmy1

        #movement sequence - n steps
        self.orderqueue_index = 0
        self.orderqueue_orders = []

        #spawning
        self.y = spawn_y
        self.spawn_counter = random.randint(spawncounter_lowerlimit,spawncounter_upperlimit)

        if spawn_x != -999:
            self.x = spawn_x
        else:
            self.x = random.randint(spawn_lower_xlimit,spawn_upper_xlimit)


        #loading ducking images
        self.images_ducking = []
        for i in range(0,15):
            imagename=nmyimgfolder+str(enemytype)+'/800x600/ducking/'+'d'+str(i)+'.png'
            #print(imagename)
            self.images_ducking.append(load_image(imagename,-1))

        #loading shooting images
        self.images_shooting = []
        for i in range(0,9):
            imagename=nmyimgfolder+str(enemytype)+'/800x600/shooting/'+'s'+str(i)+'.png'
            #print(imagename)
            self.images_shooting.append(load_image(imagename,-1))

        #loading falling  images
        self.images_falling = []
        for i in range(0,30):
            imagename=nmyimgfolder+str(enemytype)+'/800x600/falling/'+'f'+str(i)+'.png'
            #print(imagename)
            self.images_falling.append(load_image(imagename,-1))

        #loading sounds
        #print("path="+sound_path+"gun/pistol_shot_a.wav")
        self.shot_sound =  load_sound(sound_path+"gun/pistol_shot_a.wav")
        self.pain_sound = load_sound(sound_path+"char/enemy_pain.wav")

        self.imgindex = 0 # to update the sprites
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image, self.rect = self.images_shooting[0] #setting first time image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = self.x, self.y

        self.accountable_death = False
        self.health = nmyhealth_initial

        # order = none, stand, shoot, duck
        self.order = "none"

        #status = waiting, standing,ducking, shooting
        self.status = "waiting" #what the enemy is currently doing

        #FIXME: remove
        self.i_duck = 0  # counter to check how many times ducking() is executed

        self.sightxpos=-999
        self.sightypos=-999
        self.sighttriggerpulled=False

    def spawn(self):

        if self.spawn_counter > 0:
            self.spawn_counter -= 1
        else:
            self.status = "waiting"
            self.order = "none"
            self.health = nmyhealth_initial
            self.spawn_counter = random.randint(spawncounter_lowerlimit, spawncounter_upperlimit)
            self.x = random.randint(spawn_lower_xlimit, spawn_upper_xlimit)
            self.imgindex = 0

        #print("respawning "+str(self.spawn_counter)) #FIXME: remove this after debugg





    def sightstatusacquire(self,x,y,triggerpulled):

        self.sightxpos = x
        self.sightypos = y
        self.sighttriggerpulled = triggerpulled

        #FIXME: remove this
        #print("status acquiere(), triggerpulled="+str(self.sighttriggerpulled))

    #FIXME: eliminate dt from argument
    def getshootstance(self,dt):

        if self.imgindex == 0:
            self.shot_sound.play()

        if self.imgindex < (animationlength_shoot - 1):
            self.image, self.rect = self.images_shooting[self.imgindex]
            self.rect.center = self.x, self.y
            self.imgindex += 1


        if self.imgindex == (animationlength_shoot - 1):
            self.rect.center = self.x, self.y
            self.imgindex = 0
            self.status = "waiting"


    ############ #################################
    def getduckstance(self,type, dt):

        self.i_duck+=1#FIXME: remove this after debugging

        if enemy_debug == True:
            print('     getduckstance()'+',type='+str(type))

        if (type == "Forward"):

            if self.imgindex < (animationlength_duck-1):
                self.image, self.rect = self.images_ducking[self.imgindex]
                self.rect.center = self.x, self.y
                self.imgindex += 1
            elif self.imgindex == (animationlength_duck-1):
                self.rect.center = self.x, self.y
                self.imgindex = 0
                self.status = "waiting"

        elif (type == "Backward"):

            if self.imgindex > 0:
                self.image, self.rect = self.images_ducking[self.imgindex]
                self.rect.center = self.x, self.y
                self.imgindex -= 1
            elif self.imgindex == 0:
                self.rect.center = self.x, self.y
                self.imgindex = 0
                self.status = "waiting"

    ################## ##########################
    def getcrouchstance(self,dt):
        self.imgindex = 0
        for self.imgindex in range(0,14):

            #print('self.imgindex=' + str(self.imgindex))
            self.current_time += dt
            if self.current_time >= self.animation_time:
                self.current_time = 0
                self.image, self.rect = self.images_crouching[self.imgindex]
                self.rect.center = self.x, self.y

    def getfallstance(self,dt):

        if self.imgindex == 0:
            self.pain_sound.play()
            self.accountable_death = True
        else:
            self.accountable_death = False

        if self.imgindex < (animationlength_fall - 1):
            self.image, self.rect = self.images_falling[self.imgindex]
            self.rect.center = self.x, self.y
            self.imgindex += 1
        if self.imgindex == (animationlength_fall - 1):
            self.rect.center = self.x, self.y
            self.imgindex = 0
            self.status = "dead"


    def getfreezestance(self,dt):

        if self.imgindex < (animationlenght_freeze - 1):
            self.imgindex += 1
        if self.imgindex == (animationlenght_freeze - 1):
            self.imgindex = 0
            self.status = "waiting"

    #used to generate a shoot, hide, stand up sequence
    def generateSequence(self, type):

        queuename = "orderqueue_orders"+str(type)

        #self.orderqueue_orders = orderqueue_orders0
        self.orderqueue_orders = globals()[queuename]

    def checkIfshot(self):

        chest_ll=-999
        chest_rl=-999
        chest_tl=-999
        chest_bl=-999

        #FIXME: add enemytype to this as argument
        #FIXME: add head hitbox
        if self.status == "shooting" or self.status == "standfreezing":
            chest_ll=nmy0_chestbox_st_ll
            chest_rl=nmy0_chestbox_st_rl
            chest_tl=nmy0_chestbox_st_tl
            chest_bl=nmy0_chestbox_st_bl
        else:
            return False

        xdif = self.sightxpos - self.rect.centerx
        ydif = self.sightypos - self.rect.centery

        if self.sighttriggerpulled == True and xdif >= chest_ll and xdif <= chest_rl and ydif>=chest_bl and ydif<=chest_tl:
            if collision_debug == True: print("collision detected")
            return True

        #chest hitbox - old logi
        #if self.sighttriggerpulled==True and self.sightxpos >= chest_ll and self.sightxpos <=chest_rl and self.sightypos >= chest_bl and self.sightypos <=chest_tl:
        #    if collision_debug==True:print("collision detected")
        #    return True




    def update(self, dt):

        if update_debug == True:
            print ("Update():starting - nmy status = " + str(self.status)+", order="+str(self.order)+", heath="+str(self.health))

        #FIXME: delete this after completing
        #print ("Enmy Pos="+str(self.rect.center))

        #manage health
        if self.status == "Receive_Shot":
            if self.health > 0:
                self.health -= 1
            elif self.health ==  0:
                self.getfallstance(dt)


        #check if shot
        if self.checkIfshot() == True:
            self.health -= nmyhealth_loss

        #check current health
        if self.health <=0:
            self.order = "fall"

        # check if enemy is open to new orders
        if self.status == "waiting" and self.order == "none":
            self.order = self.orderqueue_orders[self.orderqueue_index]

            if self.orderqueue_index < (len(self.orderqueue_orders)-1):
                self.orderqueue_index += 1
            else:
                self.orderqueue_index = 0

        elif self.status == "waiting" and self.order == "duck":
            self.order = "none"
            self.status = "ducking"
            self.imgindex = 0

        elif self.status == "waiting" and self.order == "standup":
            self.order = "none"
            self.status = "standingup"
            self.imgindex = animationlength_duck-1

        elif self.status == "waiting" and self.order == "shoot":
            self.order = "none"
            self.status = "shooting"
            self.imgindex = 0

        elif self.status == "waiting" and self.order == "fall":
            self.order = "none"
            self.status = "falling"
            self.imgindex = 0

        elif self.status == "waiting" and self.order == "standfreeze":
            self.order = "none"
            self.status = "standfreezing"
            self.imgindex = 0

        elif self.status == "waiting" and self.order == "duckfreeze":
            self.order = "none"
            self.status = "duckfreezing"
            self.imgindex = 0

        elif self.status == "dead":
            self.order = "none"
            self.status = "spawning"
            self.spawn_counter = spawncounter_upperlimit
            self.imgindex = 0

        #### running nmy orders
        if self.status == "ducking":
            self.getduckstance("Forward",dt)
        elif self.status == "standingup":
            self.getduckstance("Backward", dt)
        elif self.status == "shooting":
            self.getshootstance(dt)
        elif self.status == "falling":
            self.getfallstance(dt)
        elif self.status == "duckfreezing" or  self.status == "standfreezing":
            self.getfreezestance(dt)
        elif self.status == "spawning":
            self.spawn()

####### ##### #########

class ClassSight (pygame.sprite.Sprite):

    def __init__(self):

        global sgtimgfolder
        global sight_xspeed, sight_yspeed

        #loading sounds
        self.shot_sound =  load_sound(sound_path+"/gun/pistol_shot_b.wav")
        self.empty_sound =  load_sound(sound_path+"/gun/pistol_empty_b.wav")

        imagename = sgtimgfolder + '/sight0/800x600/small.png'
        #print("Sight image=" + imagename)

        #to control animation speed
        self.current_time = 0
        self.animation_time = 15

        #FIXME: add a random starting position
        #position
        self.x=screen_xlimit/2
        self.y=screen_ylimit/2

        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image, self.rect = load_image(imagename,-1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = self.x, self.y

        self.sightxpos=0
        self.sightypos=0

        self.numberOfbullets = soldierclipcapacity

        self.gun_kickback_ycounter = 0
        self.gun_kickback_xcounter = 0
        self.delay_counter = 0
        self.status = "stopped"

    def aftershot_delay(self,t):

        # adding little delay after shoot
        if self.delay_counter < t:
            self.delay_counter += 1
        else:
            self.gun_kickback_xcounter = 0
            self.gun_kickback_ycounter = 0
            self.delay_counter = 0
            self.status = "stopped"

        #print ("timer"+str(self.delay_counter))#DEBUG

    def update(self,  dt):

        if sight_debug == True:
            print("sight status=" + self.status +", (x,y)="+str(self.sightxpos)+","+str(self.sightypos))


        if self.status == "Move_UP":
            self.move("Move_UP")
        elif self.status == "Move_RIGHT":
            self.move("Move_RIGHT")
        elif self.status == "Move_LEFT":
            self.move("Move_LEFT")
        elif self.status == "Move_DOWN":
            self.move("Move_DOWN")
        elif self.status == "Move_UR":
            self.move("Move_UR")
        elif self.status == "Move_UL":
            self.move("Move_UL")
        elif self.status == "Move_DR":
            self.move("Move_DR")
        elif self.status == "Move_DL":
            self.move("Move_DL")
        elif self.status == "Kickback":
            self.move("Kickback")
        elif self.status == "JustReloaded":
            self.move("Kickback")

    def move(self,direction):

        #FIXME: limits causing error and freeze
        #while self.rect.x >= 0 and  self.rect.x <= screen_xlimit
        #    and self.rect.y >=0 and self.rect.xy <= screen_ylimit:

        if direction == "Move_UP" and self.rect.y>sight_upper_ylimit:
            self.y -= sight_yspeed

        if direction == "Move_RIGHT" and self.rect.x<sight_upper_xlimit:
            self.x += sight_xspeed

        if direction == "Move_LEFT" and self.rect.x>sight_lower_xlimit:
            self.x -= sight_xspeed

        if direction == "Move_DOWN" and self.rect.y<sight_lower_ylimit:
            self.y += sight_yspeed

        if direction == "Move_UR" and self.rect.y>sight_upper_ylimit and self.rect.x<sight_upper_xlimit:
            self.y -= sight_yspeed
            self.x += sight_xspeed

        if direction == "Move_UL" and self.rect.y>sight_upper_ylimit and  self.rect.x>sight_lower_xlimit:
            self.y -= sight_yspeed
            self.x -= sight_xspeed

        if direction == "Move_DR" and self.rect.y<sight_lower_ylimit and self.rect.x<sight_upper_xlimit:
            self.y += sight_yspeed
            self.x += sight_xspeed

        if direction == "Move_DL" and self.rect.y<sight_lower_ylimit and self.rect.x>sight_lower_xlimit:
            self.y += sight_yspeed
            self.x -= sight_xspeed

        if direction == "Kickback":

            #non empty clip
            if self.numberOfbullets > 0:

                gun_kickback_xtravel = 5#random.randint(1,self.gun_kickback_ytravel/2)

                if self.gun_kickback_ycounter==0:
                    self.shot_sound.play()
                    self.numberOfbullets -= 1
                    #print("number of bullets="+str(self.numberOfbullets))

                if self.gun_kickback_ycounter < gun_kickback_ytravel:
                    if self.rect.y>sight_upper_ylimit:self.y -= 3*sight_yspeed
                    self.gun_kickback_ycounter += 1

                    if self.gun_kickback_xcounter < gun_kickback_xtravel:
                        if self.rect.y<sight_upper_xlimit:self.x += sight_xspeed
                        self.gun_kickback_xcounter += 1

                else:
                    self.aftershot_delay(15)

            ## empty clip
            else:
                self.empty_sound.play()
                self.status = "stopped"

        pos = (self.x, self.y)
        self.rect.center = pos

######### ########### ##########

class ClassAmmoIndicator(pygame.sprite.Sprite):

    def __init__(self):

        imagename = ''

        #load bullet images
        self.images_bullets = []
        for i in range(0,soldierclipcapacity+1):
            imagename = objimgfolder+'/ammo_9mm_'+str(i)+'.png'
            self.images_bullets.append(load_image(imagename,-1))

        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = self.images_bullets[soldierclipcapacity]
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = ammoindicator_xstart, ammoindicator_ystart

    ## update function ###
    def update(self,numberOfbullets):

        self.image, self.rect = self.images_bullets[numberOfbullets]
        self.rect.center = ammoindicator_xstart, ammoindicator_ystart


### 5. Game functions  ###########


### 6. Other  functions  ###########

# function to setup the joystick and keys
def GPIOSetup():

    GPIO.setmode(GPIO.BCM)     # set up BCM GPIO numbering  
    GPIO.setup(23, GPIO.IN)    # Joystick Vx RIGHT
    GPIO.setup(24, GPIO.IN)    # Joystick Vx LEFT
    GPIO.setup(20, GPIO.IN)    # Joystick Vy FORWARD
    GPIO.setup(21, GPIO.IN)    # Joystick Vy BACKWARD

#function to  read joystick
# returns 
def JoystickRead():
    
    if GPIO.input(23):  
        #print (", Vx RIGHT " )
        return "Move_RIGHT"
    elif GPIO.input(24):  
        #print (", Vx LEFT " )
        return "Move_LEFT"
    elif GPIO.input(20):  
        #print (", Vy FOR " )
        return "Move_UP"
    elif GPIO.input(21):  
        #print (", Vy BACK " )  
        return "Move_DOWN"
    elif GPIO.input(23) and GPIO.input(21):
        return "Move_UR"
    else:
        return "stopped"
    
    
### 7. Executing game  ###########
def main():
    
    GPIOSetup()

    global House0_MainImage, House0_WallImage, House1_MainImage, House1_WallImage
    global insertcoin0_image,insertcoin1_image
    global screen_xlimit, screen_ylimit
    global TestStatus
    global GameScreen #FIXME not being used
    global timerstart_screen3, timerstart_screen4
    global sight_xspeed,sight_yspeed
    global Global_SightTriggerPulled,Global_SightYPos, Global_SightXPos
    global soldierclipcapacity
    global bkgn_path

    Global_SightTriggerPulled = False
    BuildingBackground = ""

    """this function is called when the program starts.
       it initializes everything it needs, then runs in
       a loop until the function returns."""
    # Initialize Everything
    pygame.init()
    screen = pygame.display.set_mode((screen_xlimit, screen_ylimit))
    pygame.display.set_caption("Paranoidx")

    # Create The Backgound
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))

    #timers
    timer_screen3 = timerstart_screen3
    timer_screen4 = timerstart_screen4

    #starting screen
    pointer = 3 #


    #score
    kills = 0

    #FIXME: update this
    # Put Text On The Background, Centered
    if pygame.font:
        font = pygame.font.Font(None, 36)
        text = font.render("Pummel The Chimp, And Win $$$", 1, (10, 10, 10))
        textpos = text.get_rect(centerx=background.get_width() / 2)
        background.blit(text, textpos)

    # Display The Background
    screen.blit(background, (0, 0))
    pygame.display.flip()


    #timer
    clock = pygame.time.Clock()
    font = pygame.font.Font('./font/Neolion.otf',24)
    scorefont = pygame.font.Font('./font/Neolion.otf',56)
    timertext = -99

    #enemies, soldiers and landscapes
    enemy0 = ClassEnemy(-999,spawn_ypos,0)
    enemy1 = ClassEnemy(-999,spawn_ypos,1)
    soldier = ClassSoldier(150,480)
    sight = ClassSight()
    ammoindicator = ClassAmmoIndicator()

    #allsprites = pygame.sprite.RenderPlain(enemy,sight) #FIXME: is this required?
    nmy0sprite = pygame.sprite.RenderPlain(enemy0)
    nmy1sprite = pygame.sprite.RenderPlain(enemy1)
    soldiersprite = pygame.sprite.RenderPlain(soldier)
    sgtsprite = pygame.sprite.RenderPlain(sight)
    ammoindicatorsprite = pygame.sprite.RenderPlain(ammoindicator)

    enemy0.generateSequence(0);enemy0.order = "none";enemy0.status = "idle"
    enemy1.generateSequence(1);enemy1.order = "none";enemy1.status = "idle"

    # Main Loop
    going = True
    while going:

        Global_SightTriggerPulled = False #FIXME: needed one?

        if mainloop_debug: print ("main loop(), enemy status="+str(enemy.status)+",order="+str(enemy.order))


        clock.tick(60) #needed to control execution speed



        # FIXME: remove this block
        #dt = clock.tick(FPS) / 1000  # Amount of seconds between each loop.
        dt=1

        # Handle Input Events with keyboard
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                going = False

            #handling key  event
            if event.type == pygame.KEYDOWN and sight.status=="stopped":

                #for sight test
                if event.key == pygame.K_KP8:
                    sight.status = "Move_UP"
                elif event.key == pygame.K_KP2:
                    sight.status = "Move_DOWN"
                elif event.key == pygame.K_KP6:
                    sight.status = "Move_RIGHT"
                elif event.key == pygame.K_KP4:
                    sight.status = "Move_LEFT"
                elif event.key == pygame.K_KP7:
                    sight.status = "Move_UL"
                elif event.key == pygame.K_KP9:
                    sight.status = "Move_UR"
                elif event.key == pygame.K_KP1:
                    sight.status = "Move_DL"
                elif event.key == pygame.K_KP3:
                    sight.status = "Move_DR"
                elif event.key == pygame.K_SPACE:
                    sight.status = "Kickback"
                    if sight.numberOfbullets >0:Global_SightTriggerPulled = True
                    else:Global_SightTriggerPulled = False

                elif event.key == pygame.K_RCTRL:
                    soldier.order = "reload"


            else:
                if sight.status != "Kickback":
                    sight.status = "stopped"

        mov= JoystickRead()
        print(mov)
        sight.status = mov    
        
        #sharing information between objects in game
        #sharing Universal X,Y Pos for sight between classes
        Global_SightXPos = sight.rect.centerx
        Global_SightYPos = sight.rect.centery
        enemy0.sightstatusacquire(Global_SightXPos,Global_SightYPos,Global_SightTriggerPulled)
        enemy1.sightstatusacquire(Global_SightXPos, Global_SightYPos, Global_SightTriggerPulled)
        soldier.sightstatusacquire(Global_SightXPos, Global_SightYPos, Global_SightTriggerPulled)

        if soldier.order == "reloaded":
            sight.numberOfbullets = soldierclipcapacity
            soldier.order = "ready"
            #sight.status = "JustReloaded"

        if enemy0.accountable_death or enemy1.accountable_death:
            kills+=1

        nmy0sprite.update(dt)
        nmy1sprite.update(dt)
        soldiersprite.update()
        sgtsprite.update(dt)
        ammoindicatorsprite.update(sight.numberOfbullets)



        if pointer == 0:
            print("Running Screen0")

            clip = VideoFileClip('./img/Screen0/intro0_video.mp4')
            #clip = VideoFileClip(screen0_introclip) #FIXME: use parameter instead of this
            clip.preview()
            clip.close()
            pointer = 1


        if pointer == 1:
            print("Running Screen1")
            #coin has been detected

            pygame.mixer.music.load(bkgn_path + '/Density & Time - MAZE.mp3')
            pygame.mixer.music.play(0, 0.0)

            #countdown
            #print("countdown")
            screen.blit(countdown0_image, (0, 0))
            pygame.display.update()
            pygame.time.delay(1000)
            screen.blit(countdown1_image, (0, 0))
            pygame.display.update()
            pygame.time.delay(1000)
            screen.blit(countdown2_image, (0, 0))
            pygame.display.update()
            pygame.time.delay(1000)
            screen.blit(countdown3_image, (0, 0))
            pygame.display.update()
            pygame.time.delay(1000)

            pointer = 3

        if pointer == 3:

            enemy0.order = "none";enemy0.status = "waiting"
            enemy1.order = "none";enemy1.status = "waiting"

            BuildingBackground = House0_MainImage
            Wall = House0_WallImage

            #running  timer
            if timer_screen3 > 0:
                timer_screen3 -= timer_delta
                timertext = int(timer_screen3)
            else:
                pointer = 4

            #print (str(timertext))#FIXME: delete after debug

        if pointer == 4:
            BuildingBackground = House1_MainImage
            Wall = House1_WallImage

            #running  timer
            if timer_screen4 > 0:
                timer_screen4 -= timer_delta
                timertext = int(timer_screen4)
            else:
                pointer = 5

        if pointer == 5:

            #stopping enmies
            enemy0.status = "idle"
            enemy1.status = "idle"

            #gameover and score screen
            BuildingBackground = GameOver_MainImage
            screen.blit(BuildingBackground, (0, 0))
            screen.blit(scorefont.render("Score "+str(kills), True, (0, 0, 255)), (finalscoretext_xpos, finalscoretext_ypos))
            pygame.display.update()
            pygame.time.wait(3000)
            pointer = 0

        if pointer == 3 or pointer == 4:
            # Draw Everything
            screen.blit(BuildingBackground, (0,0)) #draw house
            if enemy0.status!="dead" and enemy0.status!="spawning":nmy0sprite.draw(screen)
            if enemy1.status!= "dead" and enemy1.status!="spawning":nmy1sprite.draw(screen)
            screen.blit(Wall, (Wallspawn_xpos,Wallspawn_ypos ))  #draw  wall
            ammoindicatorsprite.draw(screen)
            soldiersprite.draw(screen)
            sgtsprite.draw(screen)
            screen.blit(font.render("time "+str(timertext), True, (255, 255, 255)), (timertext_xpos, timertext_ypos))
            screen.blit(font.render("kills "+str(kills), True, (0, 0, 255)), (scoretext_xpos, scoretext_ypos))
            pygame.display.update()



    pygame.quit()
# Game Over


# this calls the 'main' function when this script is executed
if __name__ == "__main__":
    main()