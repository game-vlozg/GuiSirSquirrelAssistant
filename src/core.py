from src import common
import logging
import os
import json

logger = logging.getLogger(__name__)

def refill_enkephalin():
    """Converts Energy to Modules"""
    logger.info("Converting Enkephalin to Modules")
    common.click_matching("pictures/general/module.png")
    if common.match_image("pictures/general/insufficient_enke.png"):
        common.click_matching("pictures/general/cancel.png")
    else:
        common.click_matching("pictures/general/right_arrow.png")
        common.click_matching("pictures/general/confirm_w.png")
        common.click_matching("pictures/general/cancel.png")

def navigate_to_md():
    """Navigates to Mirror Dungeon from Main Menu"""
    logger.info("Navigating to Mirror Dungeon")
    while(not common.match_image("pictures/general/MD.png")): #This is due to a bug with PM's menu where sometimes the click doesnt register if its too fast
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
        common.sleep(1)
    common.click_matching("pictures/general/MD.png")

def md_setup():
    refill_enkephalin()
    navigate_to_md()

def squad_order(status):
    """Returns a list of the image locations depending on the sinner order specified in the json file"""
    characters_positions = {
    "yisang": (580, 500),
    "faust": (847, 500),
    "donquixote": (1113, 500),
    "ryoshu": (1380, 500),
    "meursault": (1647, 500),
    "honglu": (1913, 500),
    "heathcliff": (580, 900),
    "ishmael": (847, 900),
    "rodion": (1113, 900),
    "sinclair": (1380, 900),
    "outis": (1647, 900),
    "gregor": (1913, 900)
    }

    with open("config/squad_order.json", "r") as f:
        squads = json.load(f)
    squad = squads[status]
    squad = dict(sorted(squad.items(), key=lambda item: item[1])) #sorts the dictionary by value so i can do direct retrieval
    sinner_order = []
    for name in squad:
        x,y = characters_positions[name]
        sinner_order.append(common.uniform_scale_coordinates(x,y))
    return sinner_order

def check_loading():
    """Checks for Loading Screens"""
    common.sleep(2) #Handles fade to black
    logger.info("Loading")
    while(common.match_image("pictures/general/loading.png")): #checks for loading screen bar
        common.sleep(0.5) #handles the remaining loading

def transition_loading():
    """Theres a load that occurs while transitioning to the next floor"""
    logger.info("Moving to Next Floor")
    common.sleep(5)

def post_run_load():
    """There is some oddity in the loading time for this that makes it annoying to measure so this is a blanket wait for main menu stall"""
    while(not common.match_image("pictures/general/module.png")):
        common.sleep(1)
    logger.info("Loaded back to Main Menu")

def reconnect():
    while(common.match_image("pictures/general/server_error.png")):
        common.sleep(6)
        common.click_matching("pictures/general/retry.png")
        common.mouse_move(200,200)
    if common.match_image("pictures/general/no_op.png"):
        common.click_matching("pictures/general/close.png")
        logger.info("COULD NOT RECONNECT TO THE SERVER. SHUTTING DOWN!")
        os._exit(0)

def battle():
    """Handles battles by mashing winrate, also handles skill checks and end of battle loading"""
    logger.info("Starting Battle")
    battle_finished = 0
    while(battle_finished != 1):
        while(common.match_image("pictures/battle/in_progress.png")):
            common.sleep(1)
        if common.match_image("pictures/general/loading.png"): #Checks for loading screen to end the while loop
            common.mouse_up()
            check_loading()
            battle_finished = 1
        elif common.match_image("pictures/events/skip.png"): #Checks for special battle skill checks prompt then calls skill check functions
            common.mouse_up()
            while(True):
                common.click_skip(1)
                if common.match_image("pictures/mirror/general/event.png"):
                    battle_check()
                    break
                if common.match_image("pictures/events/skill_check.png"):
                    skill_check()
                    break
        elif common.match_image("pictures/battle/winrate.png"):
            common.mouse_up()
            x,y = common.uniform_scale_coordinates(2165,1343)
            common.mouse_move_click(x,y)
            common.key_press("p") #win rate keyboard key
            ego_check()
            common.key_press("enter") #Battle Start key
            common.mouse_down()


def ego_check():
    """Checks for hopeless/struggling clashes and uses E.G.O if possible"""
    bad_clashes = []
    if match := common.match_image("pictures/battle/ego/hopeless.png",0.79):
        logger.debug("HOPELESS FOUND")
        bad_clashes += match
        
    if match := common.match_image("pictures/battle/ego/struggling.png",0.79):
        logger.debug("STRUGGLING FOUND")
        bad_clashes += match
    
    bad_clashes = [i for i in bad_clashes if i]
    if len(bad_clashes):
        bad_clashes = [x for x in bad_clashes if x[1] > common.scale_y(1023)] # this is to remove any false positives
        logger.debug("BAD CLASHES FOUND")
        for x,y in bad_clashes:
            usable_ego = []
            common.mouse_move(x-common.scale_x(55),y+common.scale_y(100))
            common.mouse_hold()
            egos = common.match_image("pictures/battle/ego/sanity.png")
            for x,y in egos:
                logger.debug(common.luminence(x,y))
                if common.luminence(x,y) > 100:#Sanity icon
                    usable_ego.append((x,y))
            if len(usable_ego):
                logger.debug("EGO USABLE")
                ego = common.random_choice(usable_ego)
                x,y = ego
                if common.match_image("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(x + common.scale_x(30), y+common.scale_y(30))
                    common.sleep(0.5)
                    common.mouse_click()
                    common.sleep(1)
            else:
                logger.debug("EGO UNUSABLE")
                if common.match_image("pictures/battle/ego/sanity.png"):
                    common.mouse_move_click(200,200)
                    common.sleep(1)
        common.key_press("p") #Change to Damage
        common.key_press("p") #Deselects
        common.key_press("p") #Back to winrate
    return
    
def battle_check(): #pink shoes, woppily, doomsday clock
    logger.info("Battle Event Check")
    common.sleep(1)
    if match := common.match_image("pictures/battle/investigate.png"): #Woppily
        logger.debug("WOPPILY")
        common.click_matching_coords(match)
        common.wait_skip("pictures/events/continue.png")
        return 0
        
    elif match := common.match_image("pictures/battle/NO.png"): #Woppily
        logger.info("WOPPILY PT2")
        for i in range(3):
            common.click_matching_coords(match)
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(not common.match_image("pictures/events/proceed.png")):
                if found := common.match_image("pictures/events/continue.png"):
                    common.click_matching_coords(found)
                    return 0
                common.mouse_click()
            common.click_matching("pictures/events/proceed.png")
            common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
            while(not common.match_image("pictures/battle/NO.png")):
                common.mouse_click()

    elif match := common.match_image("pictures/battle/refuse.png"): # Pink Shoes
        logger.info("PINK SHOES")
        common.click_matching_coords(match)
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0
    
    elif common.match_image("pictures/battle/shield_passive.png"): #Hohenheim
        logger.info("Hohenheim")
        options = ["pictures/battle/shield_passive.png","pictures/battle/poise_passive.png", "pictures/battle/sp_passive.png"]
        for option in options:
            if option == "pictures/battle/sp_passive.png":
                common.click_matching("pictures/battle/small_scroll.png")
                for i in range(5):
                    common.mouse_scroll(-1000)
            common.click_matching(option)
            common.sleep(0.5)
            if not common.match_image("pictures/events/result.png",0.9):
                continue
            else:
                break
        common.wait_skip("pictures/events/continue.png")
        return 0
    
    elif common.match_image("pictures/battle/offer_sinner.png"): #Doomsday Clock
        logger.info("DOOMSDAY CLOCK")
        found = common.match_image("pictures/battle/offer_clay.png")
        if found:
            x,y = common.random_choice(found)
            logger.info("Found Clay Option")
            logger.debug(common.luminence(x,y-common.uniform_scale_single(72)))
            if common.luminence(x,y-common.uniform_scale_single(72)) < 195:
                logger.info("Offer Clay")
                common.click_matching("pictures/battle/offer_clay.png")
                common.wait_skip("pictures/events/continue.png")
                return 0

        logger.info("Using Sinner")
        common.click_matching("pictures/battle/offer_sinner.png")
        common.wait_skip("pictures/events/proceed.png")
        skill_check()
        return 0

    elif match := common.match_image("pictures/battle/hug_bear.png"):
        logger.info("TEDDY BEAR")
        common.click_matching_coords(match)
        while(not common.match_image("pictures/events/proceed.png")):
            common.sleep(0.5)
        common.click_matching("pictures/events/proceed.png")
        skill_check()
        return 0

    return 1

def skill_check():
    """Handles Skill checks in the game"""
    logger.info("Skill Check")
    check_images = [
        "pictures/events/very_high.png",
        "pictures/events/high.png",
        "pictures/events/normal.png",
        "pictures/events/low.png",
        "pictures/events/very_low.png"
        ] #Images for the skill check difficulties
    
    common.wait_skip("pictures/events/skill_check.png")
    common.sleep(1) #for the full list to render
    for i in check_images: #Choose the highest to pass check
        if common.match_image(i,0.9):
            common.click_matching(i)
            logger.info("Selected Sinner for skill check")
            break

    common.click_matching("pictures/events/commence.png")
    common.sleep(3) #Waits for coin tosses
    logger.info("Coin tosses finished")
    common.mouse_move_click(common.scale_x(1193),common.scale_y(623))
    while(True):
        common.mouse_click()
        if match := common.match_image("pictures/events/proceed.png"):
            common.click_matching_coords(match)
            break
        if match := common.match_image("pictures/events/continue.png"):
            common.click_matching_coords(match)
            break
    logger.info("Finished Skill check")

    if common.match_image("pictures/events/skip.png"):
        if common.match_image("pictures/events/skill_check.png"):#for retry scenarios
            logger.info("Failed Skill Check, Retrying")
            skill_check()
        if common.match_image("pictures/battle/violet_hp.png"):
            logger.info("NOON OF VIOLET")
            common.wait_skip("pictures/battle/violet_hp.png")
            common.wait_skip("pictures/events/continue.png")

    else:
        common.sleep(1) #in the event of ego gifts
        if common.match_image("pictures/mirror/general/ego_gift_get.png"):
            common.click_matching("pictures/general/confirm_b.png")
            logger.info("DEBUG: EGO Gift prompt")