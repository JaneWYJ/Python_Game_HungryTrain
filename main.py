try:
    import pygame_sdl2
    pygame_sdl2.import_as_pygame()
except ImportError:
    pass


import pygame
import sys,os
from pygame.locals import *
from random import randint


class Player(pygame.sprite.Sprite):
    '''The class that holds the main player, and controls how they jump. nb. The player doens't move left or right, the world moves around them'''
    def __init__(self, info, width, height):   # 50,100,20,30
        pygame.sprite.Sprite.__init__(self)
        self.info = info
        #self.jump_sound = self.info.jump_sound
        self.player_image = self.info.trainR_image
        self.trainL_image = self.info.trainL_image
        self.imageL = pygame.transform.scale(pygame.image.load(self.trainL_image),(width,height))
        self.imageR = pygame.transform.scale(pygame.image.load(self.player_image),(width,height))
        self.image = self.imageR
        self.rect = self.image.get_rect()
        self.rect.x = self.info.player_start_x
        self.rect.y = self.info.player_start_y
        self.speed_y = 0
        self.base = pygame.Rect(self.rect.x,self.rect.y + height, width, 2)
        #self.sound = pygame.mixer.Sound(self.jump_sound)
        self.gravity = self.info.gravity

    def move_y(self):
        '''this calculates the y-axis movement for the player in the 
        current speed'''

        collided_y = manager.scene.world.collided_get_y(self.base) #return -1 means no collide, /if collide, return value of y currently on
        if self.speed_y <= 0 or collided_y < 0:  # if still jumping and no colide, jumping is -ve y speed
            self.rect.y = self.rect.y+self.speed_y
            self.speed_y = self.speed_y + self.gravity  #+1 is gravity, make it down
        if collided_y > 0 and self.speed_y > 0:
            self.rect.y = collided_y
        self.base.y = self.rect.y + self.rect.height  #update base y position

        
    def jump(self, speed):  
        '''This sets the player to jump, but it only can if its feet are on the floor'''
        if manager.scene.world.collided_get_y(self.base)>0:
            self.speed_y = speed

    def chgdir(self,direction):
        if direction == self.info.left:
            self.image = self.imageL
        elif direction == self.info.right:
            self.image = self.imageR

class World():
    '''This will hold the platforms and the goal. 
     the world moves left and right rather than the player'''
    def __init__(self, info): # block size = 30
        self.info = info
        self.platforms = []
        self.goals = []
        self.bananas=[]
        self.posn_y = 0
        self.colour = self.info.platform_colour
        self.score = self.info.score
        self.block_size = self.info.block_size
        self.level = self.info.level

        for line in self.level:
            self.posn_x = 0
            for block in line:
                if block == "-":
                    self.platforms.append(pygame.Rect(self.posn_x,self.posn_y,self.block_size,self.info.platform_height))
                if block == "G":
                    self.goals.append(Goal(self.posn_x,self.posn_y))
                if block == "B":
                    self.bananas.append(Banana(self.posn_x,self.posn_y))
                self.posn_x = self.posn_x + self.block_size
            self.posn_y = self.posn_y + self.block_size
        self.goals_plain = pygame.sprite.RenderPlain(self.goals)
        self.bananas_plain = pygame.sprite.RenderPlain(self.bananas)
                    
    def move(self, dist):
        '''move the world dist pixels right (a negative dist means left)'''
        for block in self.platforms:
            block.move_ip(dist,0)
        for goal in self.goals:
            goal.rect.move_ip(dist,0)
        for banana in self.bananas:
            banana.rect.move_ip(dist,0)

    def collided_get_y(self, player_rect):
        '''get the y value of the platform the player is currently on'''
        return_y = -1
        for block in self.platforms: 
            if block.colliderect(player_rect):
               return_y = block.y - self.block_size + 1 #
        return return_y

    def at_obj(self,player_rect):
        return_y = 0
        for banana in self.bananas:
            if banana.rect.colliderect(player_rect):
                banana.reset(banana.rect.x,banana.rect.y)
                self.score = self.score + 1
                return 1
        return return_y

        
    def at_goal(self, player_rect):
        '''return True if the player is currently in contact with the goal. False otherwise'''
        for goal in self.goals:
            if goal.rect.colliderect(player_rect):
                return True
        return False

    def update(self, screen):
        '''draw all the rectangles onto the screen'''
        for block in self.platforms:
            pygame.draw.rect(screen, self.colour, block, 0)
        self.goals_plain.draw(screen)
        self.bananas_plain.draw(screen)
        
class Banana(pygame.sprite.Sprite):
    def __init__(self,banana_x, banana_y):
        pygame.sprite.Sprite.__init__(self)
        self.banana_image= os.path.join(os.path.sep,path_dir,'image','hpbanana.png')
        self.image = pygame.transform.scale(pygame.image.load(self.banana_image),(30,30))
        self.rect = self.image.get_rect()
        self.rect.x = banana_x
        self.rect.y = banana_y

    def reset(self,banana_x,banana_y):
        #reset
        platformsize = len(manager.scene.world.platforms)
        rand_check = False
        while not rand_check:
            rand = randint(0,platformsize-1)
            if manager.scene.world.goals[0].rect.topleft != (manager.scene.world.platforms[rand].x,manager.scene.world.platforms[rand].y-30):
                rand_check = True
        self.rect.topleft = manager.scene.world.platforms[rand].x,manager.scene.world.platforms[rand].y-30
        
        

class Goal(pygame.sprite.Sprite):
    def __init__(self,goal_x,goal_y):
        pygame.sprite.Sprite.__init__(self)
        self.goal_image = os.path.join(os.path.sep, path_dir,'image','house.png')
        self.image = pygame.transform.scale(pygame.image.load(self.goal_image),(30,30))
        self.rect = self.image.get_rect()
        self.rect.x = goal_x
        self.rect.y = goal_y
        
class Doom():
    '''this class holds all the things that can kill the player'''
    def __init__(self, info):

        self.info = info        
        self.firepit = FirePit(info.pit_depth)
        self.firepit_plain = pygame.sprite.RenderPlain(self.firepit)
        self.fallingmushroom_size = self.info.fallingmushroom_size
        
        self.fallingmushrooms = []
        for i in range(0,self.info.fallingmushroom_number):
            self.fallingmushrooms.append(FallingMushroom(self.fallingmushroom_size,self.info.fallingmushroom_low_speed,self.info.fallingmushroom_high_speed))
        self.fallingmushroom_plain = pygame.sprite.RenderPlain(self.fallingmushrooms)

    def move(self, dist):
        '''move everything right dist pixels (negative dist means left)'''
        for fallingmushroom in self.fallingmushrooms:
            fallingmushroom.move_x(dist)

    def update(self, screen):
        '''move fallingmushrooms down, and draw everything on the screen'''
        for fallingmushroom in self.fallingmushrooms:
            fallingmushroom.move_y()
        self.fallingmushroom_plain.draw(screen)
        self.firepit_plain.draw(screen)

    def collided(self, player_rect):
        '''check if the player is currently in contact with any of the doom.
        nb. shrink the rectangle for the fallingmushrooms to make it fairer'''
        for fallingmushroom in self.fallingmushrooms:
            if fallingmushroom.rect.colliderect(player_rect):
                hit_box = fallingmushroom.rect.inflate(-int(self.fallingmushroom_size/2),-int(self.fallingmushroom_size/2))
                if hit_box.colliderect(player_rect):
                    return True
        return self.firepit.rect.colliderect(player_rect)

class FirePit(pygame.sprite.Sprite):
    def __init__(self,pit_depth):
        pygame.sprite.Sprite.__init__(self)
        self.pit_image= os.path.join(os.path.sep,path_dir,'image','Fire.png')
        self.image = pygame.transform.scale(pygame.image.load(self.pit_image),(screen_x,pit_depth))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 350

        
class FallingMushroom(pygame.sprite.Sprite):
    '''this class holds the mushroom that fall from the sky'''
    def __init__(self,size,lspeed,hspeed):
        pygame.sprite.Sprite.__init__(self)
        self.fallingmushroom_image = os.path.join(os.path.sep,path_dir,"image","mushroom.png")
        self.image = pygame.transform.scale(pygame.image.load(self.fallingmushroom_image),(size,size))
        self.rect = self.image.get_rect()
        self.fallingmushroom_low_speed = lspeed
        self.fallingmushroom_high_speed = hspeed
        self.reset()
        
    def reset(self):
        '''re-generate the fallingmushroom a random distance along the screen and give them a random speed'''
        self.y = 0
        self.speed_y = randint(self.fallingmushroom_low_speed,self.fallingmushroom_high_speed)
        self.x = randint(0,screen_x)
        self.rect.topleft = self.x, self.y

    def move_x(self, dist):
        '''move the fallingmushrooms dist pixels to the right 
        (negative dist means left)'''
        self.rect.move_ip(dist,0)
        if self.rect.x < -50 or self.rect.x > screen_x:
            self.reset()

    def move_y(self):
        '''move the fallingmushroom the appropriate distance down the screen
        nb. fallingmushrooms don't accellerate with gravity, but have a random speed. if the fallingmushroom has reached the bottom of the screen, 
        regenerate it'''
        self.rect.move_ip(0,self.speed_y)
        if self.rect.y > screen_y:
            self.reset()

class Scene(object):
    def __init__(self):
        pass

    def render(self,screen):
        raise NotimplementedError

    def update(self):
        raise NotimplementedError

    def handle_events(self, events):
        raise NotimplementedError

class GameInfo():
    def __init__(self,level):
        self.player_start_x = 50
        self.player_start_y = 200
        self.platform_colour = (100, 100, 100)
        self.gravity = 1
        self.jump_speed = -10
        self.doom_colour = (255,0,0)
        self.fallingmushroom_size = 30
        self.fallingmushroom_number = 0
        self.fallingmushroom_low_speed = 3
        self.fallingmushroom_high_speed = 7
        self.right = 10
        self.left = 20
        self.score = 0
        self.block_size = 30
        self.platform_height = 15
        self.background_image = os.path.join(os.path.sep,path_dir,'image','bg%s.png' %level)
		#"/home/pi/python_files/image/bg%s.png" %level
        self.level = []
        self.time = 260 # time in seconds, after 20 second, game over
        self.pit_depth = 50
        #self.jump_sound = "qubodup-cfork-ccby3-jump.ogg"
        self.trainR_image = os.path.join(os.path.sep,path_dir,"image","train1_R.png")
        self.trainL_image = os.path.join(os.path.sep,path_dir,"image","train1_L.png")
        self.currentlevel = 1
        self.finallevel = 5

       
        
        
class GameScene(Scene):
    def __init__(self,level):

        self.gameinfo = GameInfo(level)
        self.gameinfo.currentlevel = level
        self.gameinfo.fallingmushroom_number = self.gameinfo.fallingmushroom_number + level
        
        pygame.time.set_timer(USEREVENT+1,1000) #(event id, milliseconds), set milliseconds to 0 to disable the timer for an event

        with open(os.path.join(os.path.sep,path_dir,"Level","%s" %self.gameinfo.currentlevel))as f:
            self.gameinfo.level= f.readlines()

        self.world = World(self.gameinfo)
        self.player = Player(self.gameinfo,30, 30)
        self.player_plain = pygame.sprite.RenderPlain(self.player)
        self.doom = Doom(self.gameinfo)

        #setup the background
        self.background = pygame.transform.scale(pygame.image.load(self.gameinfo.background_image),(screen_x,screen_y)).convert()
        self.bg_1_x = -100
        self.bg_2_x = screen_x -100

    def render(self,screen):  
        screen.blit(self.background,(self.bg_1_x,0))
        screen.blit(self.background,(self.bg_2_x,0))
        self.player_plain.draw(screen)
    
        self.world.update(screen)
        self.doom.update(screen)

    def update(self):
        #check which keys are held
        key_state = pygame.key.get_pressed()
        if key_state[K_LEFT]:
            self.player.chgdir(self.gameinfo.left)
            if key_state[K_f]:
                self.world.move(4)
                self.doom.move(4)
                self.bg_1_x = self.bg_1_x + 3
                self.bg_2_x = self.bg_2_x + 3
            else:
                self.world.move(2)
                self.doom.move(2)
                self.bg_1_x = self.bg_1_x + 1
                self.bg_2_x = self.bg_2_x + 1
            if self.bg_1_x > screen_x:
                self.bg_1_x = -screen_x
            if self.bg_2_x > screen_x:
                self.bg_2_x = -screen_x

        elif key_state[K_RIGHT]:
            self.player.chgdir(self.gameinfo.right)
            if key_state[K_f]:
                self.world.move(-4)
                self.doom.move(-4)
                self.bg_1_x = self.bg_1_x - 3
                self.bg_2_x = self.bg_2_x - 3
            else:
                self.world.move(-2)
                self.doom.move(-2)
                self.bg_1_x = self.bg_1_x - 1
                self.bg_2_x = self.bg_2_x - 1
            if self.bg_1_x < -screen_x:
                self.bg_1_x = screen_x
            if self.bg_2_x < -screen_x:
                self.bg_2_x = screen_x



        if key_state[K_SPACE]:
            self.player.jump(self.gameinfo.jump_speed)

        #move the player with gravity
        self.player.move_y()

        #check if the player is at obj
        self.world.at_obj(self.player.rect)


    def handle_event(self,events):
        
        #check if the player is dead
        if self.doom.collided(self.player.rect):
            print ("You Lose!")
            print ("Your Score = ",self.world.score)
            manager.go_to(LoseScene())
            
        #check if the player has completed the level
        if self.world.at_goal(self.player.rect):
            if self.gameinfo.currentlevel != self.gameinfo.finallevel:
                print("Level %s Done!" %self.gameinfo.currentlevel)
                print ("Your Score = ",self.world.score)

                self.gameinfo.currentlevel = self.gameinfo.currentlevel + 1
                manager.total_score = manager.total_score  + self.world.score
                manager.go_to(TitleScene(self.gameinfo.currentlevel))
            else:
                print("Winner !")
                print ("Your Score = ",self.world.score)
                manager.go_to(FinalScene())
        
        #check events
        for event in events:
            if event.type  == USEREVENT+1:
                self.gameinfo.time -=1
            if event.type == QUIT:
                return True
        if self.gameinfo.time == 0:
            print ("Game Over, Time out")
            return True

class LoseScene(object):
    def __init__(self):
        super(LoseScene,self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.score = score
        #setup the background image
        self.cover_bg_image = os.path.join(os.path.sep,path_dir,"image","bgcover.png") 
        self.background = pygame.transform.scale(pygame.image.load(self.cover_bg_image),(screen_x,screen_y)).convert()
    
    def render(self,screen):
        #screen.fill((0,200,0))
        screen.blit(self.background,(0,0))
        text1 = self.font.render("Hungry Train", True, (180,100,180))
        text2 = self.font.render('Try Again!', True, (180,100,180))
        text3 = self.sfont.render("Your Score = %s" %manager.total_score, True, (180,100,180))
        screen.blit(text1, (150, 50))
        screen.blit(text2, (200,150))
        screen.blit(text3, (150, 250))

    def update(self):
        pass

    def handle_event(self,events):
        for e in events:
            if e.type==QUIT:
                return True

class FinalScene(object):
    def __init__(self):
        super(FinalScene,self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.score = score
        #setup the background image
        self.cover_bg_image = os.path.join(os.path.sep,path_dir,"image","bgcover.png") 
        self.background = pygame.transform.scale(pygame.image.load(self.cover_bg_image),(screen_x,screen_y)).convert()
    

    def render(self,screen):
        #screen.fill((0,200,0))
        screen.blit(self.background,(0,0))
        text1 = self.font.render("Hungry Train", True, (180,100,180))
        text2 = self.font.render('Win!', True, (180,100,180))
        text3 = self.sfont.render("Your Score = %s" %manager.total_score, True, (180,100,180))
        screen.blit(text1, (150, 50))
        screen.blit(text2, (200,150))
        screen.blit(text3, (150, 250))

    def update(self):
        pass

    def handle_event(self,events):
        for e in events:
            if e.type==QUIT:
                return True

class TitleScene(object):
    def __init__(self, level):
		super(TitleScene,self).__init__()
		self.font = pygame.font.SysFont('Arial', 56)
		self.sfont = pygame.font.SysFont('Arial', 32)
		self.current_level = level
		#setup the background image
		self.cover_bg_image = os.path.join(os.path.sep,path_dir,'image','bgcover.png')
		self.background = pygame.transform.scale(pygame.image.load(self.cover_bg_image),(screen_x,screen_y)).convert()

    def render(self,screen):
        screen.blit(self.background,(0,0))
        text1 = self.font.render("Hungry Train", True, (180,100,180))
        text2 = self.sfont.render('> press space to start <', True, (180,100,180))
        text3 = self.font.render("Level %s" %self.current_level, True, (180,100,180))
        screen.blit(text1, (150, 50))
        screen.blit(text3, (200,150))
        screen.blit(text2, (150, 350))

    def update(self):
        pass

    def handle_event(self,events):
        for e in events:
            if e.type==KEYDOWN and e.key == K_SPACE:
                self.manager.go_to(GameScene(self.current_level))

class SceneManager(object):
    def __init__(self):
        self.total_score = 0
        self.go_to(TitleScene(1))

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self

path_dir=sys.path[0]
print(path_dir)
screen_x = 480
screen_y = 320
game_name = "Hungry Train"
score = 0
pygame.font.init()
#initialise pygame
window = pygame.display.set_mode((screen_x,screen_y))
pygame.display.set_caption(game_name)
screen = pygame.display.get_surface()
#initialise pygame.mixer
pygame.mixer.pre_init(44100,-16,8,2048)
pygame.mixer.init()

manager = SceneManager()

	
	
def main():
	pygame.init()


	#initialise variables
	clock = pygame.time.Clock()


	#scene = GameScene()
	finished = False
	while not finished:

		#blank screen
		screen.fill((0,0,0))
		
		#check which keys are held
		manager.scene.update()

		#render the frame
		manager.scene.render(screen)

		#update the display
		pygame.display.update()
		
		#Check event
		finished = manager.scene.handle_event(pygame.event.get())

		#set the speed of the game
		clock.tick(20) #20 times a second

if __name__ == "__main__":
    main()