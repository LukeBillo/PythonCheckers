#Checkers Online Project
#Imports pygame for pygame functionality, sockets for networking, main_menu to import pybuttons class
#Imports Thread for dynamic game-network setup, sys.exit() to exit, random.randint for turn start and tkMessageBox for classic windows message boxes

import pygame, socket, main_menu, threading
from sys import exit
from random import randint
from tkinter import *
from pickle import dumps, loads


class game:
    def __init__(self): #initialize - creates display
       
        pygame.init()
        self.size = (1000, 800)
        self.surface = pygame.display.set_mode(self.size)
        self.caption = pygame.display.set_caption("Checkers Online: Game")
        self.clock = pygame.time.Clock()

        self.running = True
        self.clickedCheck = False
        self.assisted = False
        self.highlighted = None
        self.validList = []
        self.destrInTurn = False
        self.globalFont = pygame.font.SysFont("arial rounded mt bold", 50)

        self.movedInTurn = []

    def gameLoop(self, online=False, isHost=False):

        self.createBoard() #create board function

        self.background = pygame.Surface(self.surface.get_size()) #create background surface
        self.background.fill(0xffecb8) #fill background with cream colour

        self.surface.blit(self.background, (0,0)) #blit background to surface

        TIME_TRIGGER = pygame.USEREVENT #custom user event definitions
        JOINED_CON = pygame.USEREVENT+1
        RECV_DATA = pygame.USEREVENT+2

        if online:
            displayText = self.globalFont.render("Waiting for connection...", 1, (0, 0, 0))
            textPos = displayText.get_rect()
            textPos.x = (self.size[0] / 2) - (textPos.width / 2)
            textPos.y = (self.size[1] / 2) - textPos.height
            self.surface.blit(displayText, textPos) #blits waiting text
            self.waiting = True

            if isHost:
                self.network = Host()

                self.hostIP = self.network.IP

                displayText = self.globalFont.render("Your IP is:" + self.hostIP, 1, (0, 0, 0))
                textPos = displayText.get_rect()
                textPos.x = (self.size[0] / 2)- (textPos.width / 2)
                textPos.y = (self.size[1] / 2) - (textPos.height * 2)
                self.surface.blit(displayText, textPos) #blits IP to screen

                self.team = ("w", self.whiteTeam) #host is always white
                self.turn = self.turnStart(randint(1,2)) #host decides who begins

            else:
                self.network = Client() #if not host, client
                self.team = ("r", self.redTeam) #client is always red

            while self.waiting: #whilst waiting for connection
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.network.sock.close()
                        exit()

                    elif event.type == JOINED_CON: #custom join event, triggered from Network()
                        self.waiting = False

                pygame.display.update()

            inSync = False

            if isHost:
                self.network.sendData(self.turn) #host decided who starts (turn)
                while not(inSync):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.network.sock.close()
                            exit()

                        elif event.type == RECV_DATA:
                            for data in self.network.netData:
                                if data == "1":
                                    inSync = True

                        pygame.display.update()

            else:
                while not(inSync):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.network.sock.close()
                            exit()

                        elif event.type == RECV_DATA:
                            for data in self.network.netData:
                                self.turn = data[0] #retrieves the self.turn data sent by host
                                self.network.sendData("1") #replies with '1' to say it's received data
                                inSync = True

                        pygame.display.update()

            if self.team[0] == self.turn: #controls if it's their turn / can move checkers
                self.isTurn = True
            else:
                self.isTurn = False

        else: #else not networked
            self.turn = self.turnStart(randint(1,2)) #decides who's turn it is
            self.network = None

        self.surface.blit(self.background, (0,0))
        self.surface.blit(self.boardImg, (0,0)) #blit tile image on
        self.surface.blit(pygame.image.load('images\\woodborder_right.png'), (600, 0))
        self.surface.blit(pygame.image.load('images\\woodborder_bottom.png'), (0, 600))

        self.whiteTeam.draw(self.surface)
        self.redTeam.draw(self.surface)

        self.createGUI() #create GUI

        self.timer = 90 #timer for TIME_TRIGGER - counts down -= 1 on trig

        pygame.time.set_timer(TIME_TRIGGER, 1000) #user event triggered every second
            

        while self.running:

            if online:
                if self.isTurn: #if its their turn
                    self.playersTurn()
                else:
                    print("Waiting for opponent.")
                    self.waitForResp()

            else:
                self.isTurn = True
                if self.turn == "r":
                    self.team = (self.turn, self.redTeam)
                else:
                    self.team = (self.turn, self.whiteTeam)
                self.playersTurn()

            if len(self.whiteTeam.sprites()) == 0: #if white team has 0 checkers remaining
                if online:
                    self.network.getData = False
                self.updateGUI("r")
                self.running = False

            elif len(self.redTeam.sprites()) == 0: #if red team has 0 checkers remaining
                if online:
                    self.network.getData = False
                self.updateGUI("w")
                self.running = False

        while True:
            for event in pygame.event.get():
                mousePos = pygame.mouse.get_pos()

                main_menu.rollover(self.buttons, self.surface, mousePos, False)

                if event.type == pygame.QUIT:
                    self.network.getData = False
                    self.network.socket.close()
                    exit()

                elif event.type == pygame.MOUSEBUTTONUP:
                    main_menu.rollover(self.buttons, self.surface, mousePos, True, self.network)

                pygame.display.update()


    def playersTurn(self):

        TIME_TRIGGER = pygame.USEREVENT
        RECVD_DATA = pygame.USEREVENT+2

        while self.isTurn: #while it's the player's turn
            for event in pygame.event.get():
                mousePos = pygame.mouse.get_pos()
                self.updateGUI()

                if event.type == pygame.QUIT: #handles exit event
                    if self.network != None:
                        self.network.sendData("F")
                        self.network.getData = False
                        self.network.sock.close()
                    exit()

                elif (event.type == pygame.MOUSEBUTTONUP) and (self.clickedCheck == False): #handles mouse click when no checker selected
                    
                    if self.turn == self.team[0]:
                        self.highlight(mousePos, self.team[1], True)

                    main_menu.rollover(self.buttons, self.surface, mousePos, True, self.network)


                elif self.clickedCheck == False: #handles when a checker is not clicked

                    if self.turn == self.team[0]:
                        self.highlight(mousePos, self.team[1], False)

                    main_menu.rollover(self.buttons, self.surface, mousePos, False)

                elif self.clickedCheck and (self.assisted == False): #checker clicked, but assist hasn't been blitted yet

                    self.validList = self.highlighted.createValidLi(self.boardLocs)
                    self.assisted = self.highlighted.moveAssist(self.surface, self.transCheck, self.validList)

                elif (event.type == pygame.MOUSEBUTTONUP) and (self.clickedCheck == True):
                    extraJump = False
                    isValid = False
                    for row in range(8): #for row in list
                        for tile in range(4): #each tile
                            if (self.tileClicks[row][tile].collidepoint(mousePos)): #if mouse is colliding with tile's clickable rect/region
                                for move in self.validList: #iterates through valid moves in list
                                    if (move[0], move[1]) == (row, tile): #if the player's move is valid
                                        if move[2]:
                                            self.movedInTurn = [(move[0], move[1]), self.highlighted.listLoc, move[2].listLoc]
                                        else:
                                            self.movedInTurn = [(move[0], move[1]), self.highlighted.listLoc, None]
                                        self.boardLocs[row][tile] = self.highlighted
                                        self.boardLocs[self.highlighted.listLoc[0]][self.highlighted.listLoc[1]] = False
                                        self.highlighted.updateLoc((row, tile)) #updates position in boardLocs
                                        self.highlighted.moveAssist(self.surface, self.tileImg, self.validList) #remove assists from the screen
                                        self.assisted = False #removed assists
                                        
                                        if isinstance(move[2], checker):
                                            self.boardLocs = move[2].destroyCheck(self.surface, self.tileImg, self.boardLocs)
                                            if move[2].team == "w":
                                                self.whiteTeam.remove(move[2]) #remove from groups
                                            else:
                                                self.redTeam.remove(move[2])

                                            self.destrInTurn = True

                                        self.highlighted.moveCheck(self.tileClicks[row][tile], self.surface, self.tileImg) #moves checker to new pos - calibrate w/ RECT
                                        self.validList = []
                                        self.validList = self.highlighted.createValidLi(self.boardLocs)
                                        
                                        if self.destrInTurn == True: #destroyed a checker during their turn
                                            for validMove in self.validList:
                                                    if validMove[2] != None:
                                                        extraJump = True #checks for extra jump

                                        if extraJump == False: #if they dont have an extra jump
                                            self.clickedCheck = False
                                            self.highlighted = None
                                            self.destrInTurn = False
                                            self.changeTurn() #changes turn

                                        self.movedInTurn += self.turn

                                        self.timerControl(True)

                                        if self.network != None:
                                            self.network.sendData(self.movedInTurn)

                                        self.movedInTurn = []
                                        break
                                break


                    if not(self.highlighted == None) and (extraJump == False):
                        self.highlighted.moveAssist(self.surface, self.tileImg, self.validList)
                        self.assisted = False
                    self.clickedCheck = False
                    self.highlighted = None #mouse click and checker highlighted - movement of checkers
                    

                if event.type == TIME_TRIGGER: #timer
                    self.timer -= 1
                    self.timerControl(False)

                if event.type == RECVD_DATA:
                    if self.network.netData == "F":
                        print("Opponent forfeit.")
                        self.network.getData = False
                        self.network.sock.close()
                        self.updateGUI(self.team[0])

                        self.isTurn = False
                        self.running = False

                pygame.display.update() #update screen
                self.clock.tick(60) #60 fps, but does 'waste' time in processor

    def waitForResp(self):

        TIME_TRIGGER = pygame.USEREVENT
        RECVD_DATA = pygame.USEREVENT+2

        while not(self.isTurn):
            for event in pygame.event.get():
                mousePos = pygame.mouse.get_pos()
                self.updateGUI()

                main_menu.rollover(self.buttons, self.surface, mousePos, False)

                if (event.type == pygame.QUIT): #handles forfeit
                    self.network.sendData("F")
                    self.network.getData = False
                    self.network.sock.close() #closes socket so it doesnt hang
                    exit()

                if event.type == TIME_TRIGGER:
                    self.timer -= 1
                    self.timerControl(False)

                if event.type == pygame.MOUSEBUTTONUP:
                    main_menu.rollover(self.buttons, self.surface, mousePos, True, self.network)

                if event.type == RECVD_DATA:    #pos      [0][0]    [0][1]          [1][0]              [1][1]            [2][0]      [2][1]           [3]
                    data = self.network.netData #data: [(new xPos, new yPos), (checker moved's x, checker moved's y), (destroyed x, destroyed y), team's turn]
                    #HANDLING RECEIVED DATA, TRIGGERING EVENTS

                    if data == "F":
                        print("Opponent forfeit.")
                        self.updateGUI(self.team[0]) #if enemy has forfeit ("F" stands for forfeit)
                        self.isTurn = True
                        self.running = False

                    else:

                        checkerObj = self.boardLocs[data[1][0]][data[1][1]]

                        self.boardLocs[data[0][0]][data[0][1]] = checkerObj #self.boardLocs[row][tile] = new checker; moving opponent checker in boardLoc
                        self.boardLocs[checkerObj.listLoc[0]][checkerObj.listLoc[1]] = False  #self.boardLocs[prev. row][prev. tile] = False; replacing old location with 'False' i.e. no checker
                        checkerObj.updateLoc((data[0][0], data[0][1])) #updates position in boardLocs

                        if data[2] != None:
                            destroyedCheck = self.boardLocs[data[2][0]][data[2][1]]
                            self.boardLocs = destroyedCheck.destroyCheck(self.surface, self.tileImg, self.boardLocs)
                            if destroyedCheck.team == "w":
                                self.whiteTeam.remove(destroyedCheck) #remove from groups
                            else:
                                self.redTeam.remove(destroyedCheck)

                        checkerObj.moveCheck(self.tileClicks[data[0][0]][data[0][1]], self.surface, self.tileImg)

                        if data[3] == self.team[0]:
                            self.changeTurn()

                        self.timerControl(True)

                    self.network.clearData()
        
                pygame.display.update()

    def createBoard(self):
        self.boardImg = pygame.image.load('images\\tile_board.png') #tile board image
        redCheck = pygame.image.load('images\\red_checker.png') #red and...
        whiteCheck = pygame.image.load('images\\white_checker.png') #white Checkers
        redKing = pygame.image.load('images\\red_king.png')
        whiteKing = pygame.image.load('images\\white_king.png')
        self.tileImg = pygame.image.load('images\\tile.png') #tile image
        self.transCheck = pygame.image.load('images\\trans_check.png') #translucent checker for move assist

        self.whiteTeam = pygame.sprite.Group()
        self.redTeam = pygame.sprite.Group()

        self.boardLocs = [[False for x in range(4)] for y in range(8)]
        self.tileClicks = [[False for x in range(4)] for y in range(8)]
        


        for y in range(3): #create white checkers and top 3 rows of tile rects
            for x in range(4):
                if y % 2 == 0: #if even number
                    yCord = (y*75) 
                    xCord = 2*(x*75) #places counters counter-space-counter-space
                    checkerObj = checker((xCord, yCord), "w", whiteCheck, whiteKing, (y, x))
                    self.boardLocs[y][x] = checkerObj #places into the array
                    self.tileClicks[y][x] = pygame.Rect(xCord, yCord, 75, 75)

                else: #else odd number
                    yCord = (y*75)
                    xCord = 2*(x*75)+75 #places space-counter-space-counter
                    checkerObj = checker((xCord, yCord), "w", whiteCheck, whiteKing, (y, x))
                    self.boardLocs[y][x] = checkerObj #places into the array
                    self.tileClicks[y][x] = pygame.Rect(xCord, yCord, 75, 75) #rect of the tile area


                self.whiteTeam.add(checkerObj) #add each checker object to white team group


        for y in range(2): #blank tile rects inbetween two teams
            for x in range(4):
                dy = y+3
                if y % 2 == 0:
                    yCord = (dy*75)
                    xCord = 2*(x*75)+75
                    self.tileClicks[dy][x] = pygame.Rect(xCord, yCord, 75, 75)
                else:
                    yCord = (dy*75)
                    xCord = 2*(x*75)
                    self.tileClicks[dy][x] = pygame.Rect(xCord, yCord, 75, 75)


        for y in range(3): #create red checkers and top 3 rows of tile rects
            for x in range(4):
                dy = y+5
                if y % 2 == 0:
                    yCord = (dy*75)
                    xCord = 2*(x*75)+75
                    checkerObj = checker((xCord, yCord),  "r", redCheck, redKing, (dy, x))
                    self.boardLocs[dy][x] = checkerObj
                    self.tileClicks[dy][x] = pygame.Rect(xCord, yCord, 75, 75)
                else:
                    yCord = (dy*75)
                    xCord = 2*(x*75)
                    checkerObj = checker((xCord, yCord),  "r", redCheck, redKing, (dy, x))
                    self.boardLocs[dy][x] = checkerObj
                    self.tileClicks[dy][x] = pygame.Rect(xCord, yCord, 75, 75)
                        
                self.redTeam.add(checkerObj) #add each checker object to the red team group

    def createGUI(self):
        self.btnImages = (pygame.image.load('images\\button_image.png'), pygame.image.load('images\\button_selected.png'))

        self.sideGUI_container = pygame.rect.Rect((600, 0), (400, 600)) #container for right-side GUI
        self.bottomGUI_container = pygame.rect.Rect((0, 600), (1000, 400)) #container for the bottom of the screen GUI

        font = pygame.font.SysFont("arial rounded mt bold", 36)

        textList = [("Current team's turn:", 10), ("Turn time remaining:", 154), ("Red checkers remaining:", 298), ("White checkers remaining:", 442)] #list of sentences to render
        for text in textList:
            displayText = font.render(text[0], 1, (0, 0, 0)) #render text surface, blit later
            textPos = displayText.get_rect()
            textPos.x = self.sideGUI_container.centerx - (textPos.width / 2) #calibrate x
            textPos.y = text[1] #calibrate y

            self.surface.blit(displayText, textPos) #blit to screen

        btnHeightLoc = self.bottomGUI_container.centery - 140 #button always centered height-wise

        self.buttons = pygame.sprite.Group()

        menuButton = main_menu.pyButton(self.surface, "Main Menu", ((self.bottomGUI_container.width - 200) / 5, btnHeightLoc), self.btnImages, 'menu_forfeit') #buttons created using button class
        self.buttons.add(menuButton)
        forfeitButton = main_menu.pyButton(self.surface, "Exit", (4*((self.bottomGUI_container.width - 200) / 5), btnHeightLoc), self.btnImages, 'forfeit')
        self.buttons.add(forfeitButton)

    def updateGUI(self, winner=''):

        textList = [(str(self.timer), 226), (str(len(self.redTeam.sprites())), 370), (str(len(self.whiteTeam.sprites())), 514)]

        if self.turn == "r":
            textList.append(("Red", 82))
        else:
            textList.append(("White", 82))

        for text in textList:
            displayText = self.globalFont.render(text[0], 1, (0, 0, 0))
            textPos = displayText.get_rect()
            textPos.x = self.sideGUI_container.centerx - (textPos.width / 2)
            textPos.y = text[1]

            self.surface.fill(0xffecb8, (textPos.x-20, textPos.y, textPos.width+40, textPos.height))
            self.surface.blit(displayText, textPos)

        if winner:
            self.surface.fill(0xffecb8)

            if winner == "r":
                winner = "Red"
            else:
                winner = "White"

            winText = winner + " Team Wins!"
            winText = self.globalFont.render(winText, 1, (0, 0, 0))
            winFont = pygame.font.SysFont("arial rounded mt bold", 148)
            textPos =  winText.get_rect()
            textPos.x = (self.surface.get_rect()).centerx - (textPos.width / 2)
            textPos.y = (self.surface.get_rect()).centery - (textPos.height / 2)

            self.surface.blit(winText, textPos)

            btnHeightLoc = self.bottomGUI_container.centery - 140
            self.buttons.empty()
            menuButton = main_menu.pyButton(self.surface, "Main Menu", ((self.bottomGUI_container.width - 200) / 5, btnHeightLoc), self.btnImages, 'menu') #buttons created using button class
            self.buttons.add(menuButton)
            forfeitButton = main_menu.pyButton(self.surface, "Exit", (4*((self.bottomGUI_container.width - 200) / 5), btnHeightLoc), self.btnImages, 'exit')
            self.buttons.add(forfeitButton)

    def turnStart(self, random):
        if random == 1:
            return "r"
        else:
            return "w"

    def highlight(self, pos, team, click):
        found = False
        for sprite in team: #only checks their own checkers - cant move enemy checkers
            if (sprite.rect.collidepoint(pos)) and (self.timer != 1):
                pygame.draw.circle(self.surface, 0xffffff, sprite.rect.center, 37, 3) #highlight with white circle
                self.highlighted = sprite
                found = True

            else:
                pygame.draw.circle(self.surface, 0x000000, sprite.rect.center, 37, 3) #remove highlight with black circle
                
            if (click == True) and (found == True):
                self.clickedCheck = True

    def timerControl(self, resetTimer):
        if self.timer == 0: #if user runs out of time
            self.changeTurn() #swaps turn
            self.timer = 90 #resets timer to 90

        elif resetTimer == True:
            self.timer = 90

    def changeTurn(self):
        if self.turn == "r":
            self.turn = "w"
        else:
            self.turn = "r"

        if self.isTurn:
            self.isTurn = False
            
        else:
            self.isTurn = True

class checker(pygame.sprite.Sprite):

    def __init__(self, loca, team, img, kingImg, boardListLoc):
        pygame.sprite.Sprite.__init__(self)

        self.image = img #image used/loaded
        
        self.kingImg = kingImg

        self.rect = img.get_rect() #get rect of pixel coordinates
        self.rect.x = loca[0]
        self.rect.y = loca[1]

        self.team = team #object's team
        self.king = False
        self.listLoc = boardListLoc #location in the gameLoop.boardLoc

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def destroyCheck(self, surface, tileImage, checkLocs):
        self.moveCheck(pygame.Rect((-75, -75), (75, 75)), surface, tileImage)
        checkLocs[self.listLoc[0]][self.listLoc[1]] = False #remove itself from the boardLocs in gameLoop

        return checkLocs

    def moveAssist(self, surface, useImage, validMoves):

        self.assistRect = self.image.get_rect() #rect for assists
        
        for i in validMoves:
            self.assistRect.y = i[0]*75
            if i[0] % 2 == 0:
                self.assistRect.x = 2*(i[1]*75)
                
            else:
                self.assistRect.x = 2*(i[1]*75)+75
            surface.blit(useImage, self.assistRect)
            
    def createValidLi(self, checkLocs):

        validMoves_x = [] #initialise list of valid moves for x index
        validMoves_y = [] #initialise list of valid moves for y index
        validMoves = [] #list of total valid moves - merge x and y lists
        canTake = [] #list of checkers able to take

        if self.listLoc[0] % 2 == 0: #if row is even (y index 0, 2, 4, 6)
            if self.listLoc[1] == 0:
                validMoves_x.append(self.listLoc[1])

            else:
                validMoves_x.extend((self.listLoc[1], self.listLoc[1]-1))

        else: #else row is odd (y index 1, 3, 5, 7)
            if self.listLoc[1] == 3:
                validMoves_x.append(self.listLoc[1])

            else:
                validMoves_x.extend((self.listLoc[1], self.listLoc[1]+1))

        if (self.team == "r") or (self.king == True): #red or is king
            if self.listLoc[0] != 0:
                validMoves_y.append(self.listLoc[0]-1)

        if (self.team == "w") or (self.king == True): #white or is king
            if self.listLoc[0] != 7:
                validMoves_y.append(self.listLoc[0]+1)

        for yPos in validMoves_y:
            for xPos in validMoves_x: #for each [y][x]

                validMoves += self.checkJumpMove(checkLocs, yPos, xPos) #checks for valid jump moves

        return validMoves #returns list of valid moves - checkers that can be taken during the move are in validMoves[moveLocation][2]

    def checkJumpMove(self, checkLocs, yPos, xPos):

        validJumpMoves = []
        validJumpMoves_x = []
        validJumpMoves_y = []

        if isinstance(checkLocs[yPos][xPos], checker): #case: checker is on the valid move tile
            if checkLocs[yPos][xPos].team != self.team: #case: checker in tile is on the enemy team, therefore it can be 'taken'

                newPos_y = yPos #new variables created so that the list is NOT MODIFIED (editing yPos would edit only existing value of y)
                newPos_x = xPos

                canTake = checkLocs[yPos][xPos]

                if (yPos % 2 == 0) and (xPos != 0): #new y is even and x is not at index 0 (no tile for checker behind index 0, so cant jump over checker)

                    if xPos - self.listLoc[1] == 0: #moved to the LEFT previously
                        newPos_x -= 1 #therefore move one to the LEFT again

                    #else it must be +1 and has moved right
                    #x does not change, moved right again

                elif (yPos % 2 != 0) and (xPos != 3): #new y is odd and x is not at index 3

                    if xPos - self.listLoc[1] == 0: #x moved to the RIGHT reviously
                        newPos_x += 1 #move to the right again

                    #else must be x-1 and moved LEFT previously
                    #x does not change, moved left again

                #else not a possible move

                if (yPos - self.listLoc[0] == 1) and (yPos != 7): #checker has moved down board
                    newPos_y += 1 #therefore move down board again

                elif (yPos - self.listLoc[0] == -1) and (yPos != 0):#checker has moved up board
                    newPos_y -= 1 #so move up board again

                if not(isinstance(checkLocs[newPos_y][newPos_x], checker)): #if the new position isnt another checker
                    if newPos_x != self.listLoc[1]: #and if it isnt going directly downwards (not allowed)
                        if (newPos_y != yPos) or (newPos_y != yPos):
                            validJumpMoves.append((newPos_y, newPos_x, canTake))       

                #else checker on this position too, so cant jump over two checkers

        else: #else tile is empty
            validJumpMoves.append((yPos, xPos, None))

        return validJumpMoves

    def moveCheck(self, tileRect, surface, tileImage):

        surface.blit(tileImage, (self.rect.x, self.rect.y)) #replace location of check with image of tile

        self.rect = tileRect
        self.rect.x = tileRect.x
        self.rect.y = tileRect.y

        self.draw(surface) #redraw checker to surf

    def updateLoc(self, newLoc):
        self.listLoc = newLoc #update the checker object's location in board
        if (self.team == "r") and (self.listLoc[0] == 0):
            self.makeKing()

        elif (self.team == "w") and (self.listLoc[0] == 7):
            self.makeKing()

    def makeKing(self):
        self.image = self.kingImg
        self.king = True #king status set to True

class Host:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #ipv4 sock

        self.netData = [] #container for received data

        self.IP = socket.gethostbyname(socket.gethostname()) #for blitting ip to screen
        host_thread = threading.Thread(target = self.createHost)
        host_thread.start()    

    def createHost(self):
        try:
            self.sock.bind(('', 55555))
        except socket.error as errorMsg:
            print("Error: Socket bind failed", "Failed to bind socket to port 55555.\nError: " + errorMsg[1] + ". " + errorMsg[0] + ".")

        self.sock.listen(1)
        print("Host established. Listening.")
        print("Waiting for connection.")

        try:
            self.connect, self.address = self.sock.accept() #accept incoming connection, I/O BLOCK
        except OSError:
            exit()
        except socket.error:
            print("Socket error.")
            self.sock.close()
            exit()

        JOIN_EVENT = pygame.event.Event(pygame.USEREVENT+1) #triggers join event for main program
        pygame.event.post(JOIN_EVENT)

        print("Connected to:" + self.address[0] + ":" + str(self.address[1]))

        self.getData = True #getData is true, so .recv method in while constantly active

        recvData_thread = threading.Thread(target = self.recvData) #thread for .recv
        recvData_thread.start()

    def sendData(self, data):
        pkleData = None
        if data != []:
            pkleData = dumps(data) #pickle data so it is binary

            self.connect.sendall(pkleData) #sent along con

    def recvData(self):
        RECV_EVENT = pygame.event.Event(pygame.USEREVENT+2) #custom event

        while self.getData:
            try:
                self.netData = self.connect.recv(8192) #always ready for receiving data, I/O BLOCK
            except OSError:
                self.getData = False
            except socket.error:
                print("Socket error.")
                exit()
            self.netData = loads(self.netData) #unpacks pickle

            if self.netData != []: #if data isn't empty list

                pygame.event.post(RECV_EVENT) #triggers event in main program, main program unpacks data

    def clearData(self):
        self.netData = []

class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #ipv4 sock

        self.netData = [] #container for received data

        client_thread = threading.Thread(target = self.createClient)
        client_thread.start()

    def createClient(self):
        master = Tk() #tkinter window dialogue
        master.wm_title("Connect to IP")
        inputLabel = Label(master, text="Enter the host's IP and click 'Set IP', then 'Confirm' below:")
        inputLabel.pack(side=TOP)
        textBox = Entry(master, text="127.0.0.1")
        textBox.pack(side=TOP)
        IP_button = Button(master, text="Set IP", command=lambda: self.getText(textBox)) #tkinter entry textbox retrieves entered IP
        quit_button = Button(master, text="Confirm", command=master.destroy)

        IP_button.pack(side=LEFT)
        quit_button.pack(side=RIGHT)

        master.mainloop()

        self.sock.connect((self.hostIP, 55555)) #connects to IP entered in tk entry
        JOIN_EVENT = pygame.event.Event(pygame.USEREVENT+1) #triggers join event in main program
        pygame.event.post(JOIN_EVENT)            

        self.getData = True #for .recv method again

        recvData_thread = threading.Thread(target = self.recvData)
        recvData_thread.start()

    def getText(self, textBox):
        self.hostIP = textBox.get() #retrieves text from tkinter textbox
        if len(self.hostIP) == 0: #checks textbox isnt empty
            exit()

    def sendData(self, data):
        pkleData = None
        if data != []:
            pkleData = dumps(data) #pickles data before sending, same as Host

            self.sock.sendall(pkleData)

    def recvData(self):
        RECV_EVENT = pygame.event.Event(pygame.USEREVENT+2)

        while self.getData:
            try:
                self.netData = self.sock.recv(8192)
            except OSError:
                exit()
            except socket.error:
                print("Socket error.")
                exit()

            self.netData = loads(self.netData) #same as host

            if self.netData != []:

                pygame.event.post(RECV_EVENT)

    def clearData(self):
        self.netData = [] 

if __name__ == '__main__':
    print("Please launch main_menu.py first.")