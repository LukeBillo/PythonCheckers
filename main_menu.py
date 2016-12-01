import pygame, checkers_game
from sys import exit

class Menu:
    def __init__(self):
        pygame.init()

        self.size = (600, 600) 
        self.surface = pygame.display.set_mode(self.size) #created the surface of the screen
        self.caption = pygame.display.set_caption("Checkers Online: Main Menu")

    def run(self):
        buttonImg = pygame.image.load('images\\button_image.png') #button base images
        rolloverImg = pygame.image.load('images\\button_selected.png')

        self.menuContainer = pygame.rect.Rect((200, 0), (200, 600)) #container for the buttons / menu

        self.hostBtn = pyButton(self.surface, "Host Game", (self.menuContainer.x, self.menuContainer.y+150), (buttonImg, rolloverImg), "host") #buttons
        self.joinBtn = pyButton(self.surface, "Join Game", (self.menuContainer.x, self.menuContainer.y+300), (buttonImg, rolloverImg), "join")
        self.singleBtn = pyButton(self.surface, "Single Player", (self.menuContainer.x, self.menuContainer.y+450), (buttonImg, rolloverImg), "1-player")

        self.buttons = pygame.sprite.Group() #button group
        self.buttons.add(self.hostBtn, self.joinBtn, self.singleBtn)

        self.background = pygame.Surface(self.surface.get_size())
        self.background.fill(0xffecb8)
        self.surface.blit(self.background, (0,0)) #background blitted

        self.buttons.draw(self.surface) #draws buttons to surf

        font = pygame.font.SysFont("arial rounded mt bold", 36)
        displayText = font.render("Checkers Online", 1, (0, 0, 0)) #title
        textPos = displayText.get_rect()
        textPos.x = (self.size[0] / 2) - (textPos.width / 2) #centered
        textPos.y = 50

        self.surface.blit(displayText, textPos) #blitted

        while True:
            for event in pygame.event.get():
                mousePos = pygame.mouse.get_pos()
               
                if event.type == pygame.QUIT:
                    exit()

                elif event.type == pygame.MOUSEBUTTONUP: #triggers click event on rollover
                    rollover(self.buttons, self.surface, mousePos, True)

                else: #controls rollover on buttons
                    rollover(self.buttons, self.surface, mousePos, False)

                pygame.display.update()

class pyButton(pygame.sprite.Sprite):
    def __init__(self, surface, btnText, location, images, function): 
        pygame.sprite.Sprite.__init__(self)

        self.image = images[0] #normal img
        self.rollover = images[1] #rollover img

        self.loca = location #location relative to container
        self.rect = images[0].get_rect()
        self.rect.x = self.loca[0]
        self.rect.y = self.loca[1]

        self.func = function #function of the button

        font = pygame.font.SysFont("arial rounded mt bold", 36)
        self.surfaceText = font.render(btnText, 1, (255, 255, 255))
        self.textPos = self.surfaceText.get_rect()

        self.textPos.x = self.rect.centerx - (self.textPos.width / 2)
        self.textPos.y = self.rect.centery - (self.textPos.height / 2)

        self.draw(surface) #draws btn to surf

    def draw(self, surface, mouseOver=False):

        if mouseOver == True: #if mouse is on
            surface.blit(self.rollover, self.rect) #shows 'highlighted' button

        else: #else shows normal img
            surface.blit(self.image, self.rect)

        surface.blit(self.surfaceText, self.textPos)

    def click(self, checkersNet):
        global checkersGame
        if self.func == 'forfeit':
            checkersNet.sendData("F")
            checkersNet.getData = False
            checkersNet.sock.close()
            exit()

        elif self.func == 'menu_forfeit':
            checkersNet.sendData("F")
            checkersNet.getData = False
            checkersNet.sock.close()
            mainMenu = Menu()
            mainMenu.run()

        elif self.func == 'menu':
            mainMenu = Menu()
            mainMenu.run()

        elif self.func == 'host':
           checkersGame = checkers_game.game()
           checkersGame.gameLoop(True, True)

        elif self.func == 'join':
            checkersGame = checkers_game.game()
            checkersGame.gameLoop(True)

        elif self.func == '1-player':
            checkersGame = checkers_game.game()
            checkersGame.gameLoop()

        else:
            exit()

def rollover(buttons, surface, pos, click, network=None):
    for button in buttons:
        if (button.rect.collidepoint(pos)) and (click == True):
            button.click(network) #calls click function of the button

        elif button.rect.collidepoint(pos):
            button.draw(surface, True) #draws rollover image
            
        else:
            button.draw(surface, False) #draws standard image


if __name__ == '__main__':
    mainMenu = Menu()
    mainMenu.run()

