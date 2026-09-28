import pygame
import serial
import time
import serialInterface


def calcScore(score_dict):
    score_base = 0
    if score_dict["p1"] == 1:
        score_base += 15
    elif score_dict["p1"] == 2:
        score_base += 25

    if score_dict["p2"] == 1:
        score_base += 15
    elif score_dict["p2"] == 2:
        score_base += 25
    
    return (score_dict["goal"] * 3 + score_dict["exc"] + score_base)

pygame.init
pygame.font.init()

screen_width = 1920
screen_height = 1080
logo_size = 900

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.SCALED)
clock = pygame.time.Clock()
running = True

redScoreDict = {
    "goal": 0,
    "exc": 0,
    "p1": 0,
    "p2": 0
}
blueScoreDict = {
    "goal": 0,
    "exc": 0,
    "p1": 0,
    "p2": 0
}

center_logo = pygame.transform.scale(pygame.image.load("resources/liftoff_logo.png").convert_alpha(), (logo_size, logo_size))

arduinoConnected = True
try:
    arduino = ArduinoInterface()
except Exception as e:
    print("Field controller not connected, entering debug mode")
    arduinoConnected = False

timer_state = 0
timer_start = time.time()

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if (event.key == pygame.K_v) and (not arduinoConnected):
                redScoreDict["goal"] +=1
            if (event.key == pygame.K_b) and (not arduinoConnected):
                blueScoreDict["goal"] +=1
            if event.key == pygame.K_t:
                redScoreDict["exc"] +=1
            if (event.key == pygame.K_g) and (redScoreDict["exc"] >0):
                redScoreDict["exc"] -=1
            if (event.key == pygame.K_y) and (redScoreDict["p1"] <2):
                redScoreDict["p1"] +=1
            if (event.key == pygame.K_h) and (redScoreDict["p1"] >0):
                redScoreDict["p1"] -=1
            if (event.key == pygame.K_u) and (redScoreDict["p2"] <2):
                redScoreDict["p2"] +=1
            if (event.key == pygame.K_j) and (redScoreDict["p2"] >0):
                redScoreDict["p2"] -=1
            if event.key == pygame.K_i:
                blueScoreDict["exc"] +=1
            if (event.key == pygame.K_k) and (blueScoreDict["exc"] >0):
                blueScoreDict["exc"] -=1
            if (event.key == pygame.K_o) and (blueScoreDict["p1"] <2):
                blueScoreDict["p1"] +=1
            if (event.key == pygame.K_l) and (blueScoreDict["p1"] >0):
                blueScoreDict["p1"] -=1
            if (event.key == pygame.K_p) and (blueScoreDict["p2"] <2):
                blueScoreDict["p2"] +=1
            if (event.key == pygame.K_SEMICOLON) and (blueScoreDict["p2"] >0):
                blueScoreDict["p2"] -=1
            if event.key == pygame.K_r:
                timer_state = 0
                redScoreDict = dict.fromkeys(redScoreDict, 0)
                blueScoreDict = dict.fromkeys(blueScoreDict, 0)
            if (event.key == pygame.K_q) or (event.key == pygame.K_ESCAPE):
                running = False
            if event.key == pygame.K_SPACE:
                timer_state = 1
                timer_start = time.time()

            
    if arduinoConnected:
        redScoreDict["goal"], blueScoreDict["goal"] = updateGoals(arduino, redScoreDict["goal"], blueScoreDict["goal"])

    # fill the screen with a color to wipe away anything from last frame
    screen.fill((166, 25, 25))
    pygame.draw.rect(screen, "black", (screen_width*.075, screen_height*.07, screen_width * .5, screen_height*.34), border_radius=30)
    pygame.draw.rect(screen, (255, 190, 0), (screen_width*.075, screen_height*.07, screen_width * .5, screen_height*.34), 15, border_radius=30)
    screen.blit(center_logo, (screen_width*.75 - logo_size/2, screen_height*.5 - logo_size/2))

    timer_text = "1:00"
    if timer_state == 1:
        timer_left = int(60-(time.time() - timer_start))
        mins, secs = divmod(timer_left, 60)
        timer_text = f'{mins:01d}:{secs:02d}'
        if timer_left <= 0:
            timer_state = 2
    elif timer_state == 2:
        timer_text = "0:00"

    timer_font = pygame.font.Font('freesansbold.ttf', int(screen_height/3))

    timer_text = timer_font.render(timer_text, True, (255, 255, 255))
    timer_rect = timer_text.get_rect()
    timer_rect.center = (screen_width*.325, screen_height*.26)
    screen.blit(timer_text, timer_rect)  

    score_font = pygame.font.Font('freesansbold.ttf', int(screen_height/4))

    score_box_height = 0.25
    if (timer_state == 2):
        score_box_height = .45

    pygame.draw.rect(screen, "black", (screen_width*.075, screen_height*.5, screen_width * .25, screen_height*score_box_height), border_radius=30)
    pygame.draw.rect(screen, (255, 190, 0), (screen_width*.075, screen_height*.5, screen_width * .25, screen_height * score_box_height), 15, border_radius=30)
    red_score = score_font.render(str(calcScore(redScoreDict)), True, (255, 255, 255))
    red_score_rect = red_score.get_rect()
    red_score_rect.center = (screen_width*.2, screen_height*.65)
    screen.blit(red_score, red_score_rect)

    if timer_state == 2:
        subscore_font = pygame.font.Font('freesansbold.ttf', int(screen_height/16))
        sub_red = subscore_font.render("GOAL: " + str(redScoreDict["goal"]), True, (255,255,255))
        sub_red_rect = sub_red.get_rect()
        sub_red_rect.center = (screen_width*.2, screen_height*.8)
        screen.blit(sub_red, sub_red_rect)

        sub_red = subscore_font.render("EXCL: " + str(redScoreDict["exc"]), True, (255,255,255))
        sub_red_rect = sub_red.get_rect()
        sub_red_rect.center = (screen_width*.2, screen_height*.85)
        screen.blit(sub_red, sub_red_rect)

        sub_red = subscore_font.render("PARK: " + str(redScoreDict["p1"]), True, (255,255,255))
        sub_red_rect = sub_red.get_rect()
        sub_red_rect.center = (screen_width*.2, screen_height*.9)
        screen.blit(sub_red, sub_red_rect)

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()