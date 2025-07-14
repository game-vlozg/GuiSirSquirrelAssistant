import os
import sys

# Determine if running as executable or script
def get_base_path():
    """Get the base directory path"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        folder_path = os.path.dirname(os.path.abspath(__file__))
        # Check if we're in the src folder or main folder
        if os.path.basename(folder_path) == 'src':
            return os.path.dirname(folder_path)
        return folder_path

# Get base path for resource access
BASE_PATH = get_base_path()

def gift_choice(status):
    """Get gift image path for status"""
    match status:
        case "sinking":
            return "pictures/mirror/gifts/sinking.png"
        case "bleed":
            return "pictures/mirror/gifts/bleed.png"
        case "burn":
            return "pictures/mirror/gifts/burn.png"
        case "charge":
            return "pictures/mirror/gifts/charge.png"        
        case "poise":
            return "pictures/mirror/gifts/poise.png"
        case "rupture":
            return "pictures/mirror/gifts/rupture.png"
        case "tremor":
            return "pictures/mirror/gifts/tremor.png"
        case "slash":
            return "pictures/mirror/gifts/slash.png"
        case "pierce":
            return "pictures/mirror/gifts/pierce.png"
        case "blunt":
            return "pictures/mirror/gifts/blunt.png"
    
def squad_choice(status):
    """Get squad image path for status"""
    match status:
        case "sinking":
            return "pictures/CustomAdded1080p/general/squads/sinking.png"
        case "bleed":
            return "pictures/CustomAdded1080p/general/squads/bleed.png"
        case "burn":
            return "pictures/CustomAdded1080p/general/squads/burn.png"
        case "charge":
            return "pictures/CustomAdded1080p/general/squads/charge.png"        
        case "poise":
            return "pictures/CustomAdded1080p/general/squads/poise.png"
        case "rupture":
            return "pictures/CustomAdded1080p/general/squads/rupture.png"
        case "tremor":
            return "pictures/CustomAdded1080p/general/squads/tremor.png"
        case "slash":
            return "pictures/CustomAdded1080p/general/squads/slash.png"
        case "pierce":
            return "pictures/CustomAdded1080p/general/squads/pierce.png"
        case "blunt":
            return "pictures/CustomAdded1080p/general/squads/blunt.png"     

def pack_choice(status):
    """Get pack image path for status"""   
    match status:
        case "sinking":
            return "pictures/mirror/packs/status/sinking_pack.png"
        case "bleed":
            return "pictures/mirror/packs/status/bleed_pack.png"
        case "burn":
            return "pictures/mirror/packs/status/burn_pack.png"
        case "charge":
            return "pictures/mirror/packs/status/charge_pack.png"        
        case "poise":
            return "pictures/mirror/packs/status/poise_pack.png"
        case "rupture":
            return "pictures/mirror/packs/status/rupture_pack.png"
        case "tremor":
            return "pictures/mirror/packs/status/tremor_pack.png"
        case "slash":
            return "pictures/mirror/packs/status/slash_pack.png"
        case "pierce":
            return "pictures/mirror/packs/status/pierce_pack.png"
        case "blunt":
            return "pictures/mirror/packs/status/blunt_pack.png"
        
def get_status_gift_template(status):
    """
    Returns the template path for status gift images.
    Used in multiple contexts: fusion detection, enhancement, market purchasing.
    
    Args:
        status: The status type (e.g., "bleed", "poise", etc.)
    
    Returns:
        str: Path to the status gift template image
    """
    match status:
        case "sinking":
            return "pictures/mirror/restshop/enhance/sinking_enhance.png"
        case "bleed":
            return "pictures/mirror/restshop/enhance/bleed_enhance.png"
        case "burn":
            return "pictures/mirror/restshop/enhance/burn_enhance.png"
        case "charge":
            return "pictures/mirror/restshop/enhance/charge_enhance.png"        
        case "poise":
            return "pictures/mirror/restshop/enhance/poise_enhance.png"
        case "rupture":
            return "pictures/mirror/restshop/enhance/rupture_enhance.png"
        case "tremor":
            return "pictures/mirror/restshop/enhance/tremor_enhance.png"
        case "slash":
            return "pictures/mirror/restshop/enhance/slash_enhance.png"
        case "pierce":
            return "pictures/mirror/restshop/enhance/pierce_enhance.png"
        case "blunt":
            return "pictures/mirror/restshop/enhance/blunt_enhance.png"

# Backward compatibility alias
enhance_gift_choice = get_status_gift_template
        
def reward_choice(status):
    """Get reward image path for status"""
    match status:
        case "sinking":
            return "pictures/mirror/rewards/sinking_reward.png"
        case "bleed":
            return "pictures/mirror/rewards/bleed_reward.png"
        case "burn":
            return "pictures/mirror/rewards/burn_reward.png"
        case "charge":
            return "pictures/mirror/rewards/charge_reward.png"        
        case "poise":
            return "pictures/mirror/rewards/poise_reward.png"
        case "rupture":
            return "pictures/mirror/rewards/rupture_reward.png"
        case "tremor":
            return "pictures/mirror/rewards/tremor_reward.png"
        case "slash":
            return "pictures/mirror/rewards/slash_reward.png"
        case "pierce":
            return "pictures/mirror/rewards/pierce_reward.png"
        case "blunt":
            return "pictures/mirror/rewards/blunt_reward.png"
    
def market_choice(status):
    """Get market image path for status"""
    match status:
        case "sinking":
            return "pictures/mirror/restshop/market/sinking_market.png"
        case "bleed":
            return "pictures/mirror/restshop/market/bleed_market.png"
        case "burn":
            return "pictures/mirror/restshop/market/burn_market.png"
        case "charge":
            return "pictures/mirror/restshop/market/charge_market.png"        
        case "poise":
            return "pictures/mirror/restshop/market/poise_market.png"
        case "rupture":
            return "pictures/mirror/restshop/market/rupture_market.png"
        case "tremor":
            return "pictures/mirror/restshop/market/tremor_market.png"
        case "slash":
            return "pictures/mirror/restshop/market/slash_market.png"
        case "pierce":
            return "pictures/mirror/restshop/market/pierce_market.png"
        case "blunt":
            return "pictures/mirror/restshop/market/blunt_market.png"
        
def get_fusion_target_button(status):
    """
    Returns the template path for fusion target selection buttons.
    Used for selecting the target status type when fusing gifts.
    
    Args:
        status: The target status type for fusion (e.g., "bleed", "poise", etc.)
    
    Returns:
        str: Path to the fusion target button template image
    """
    match status:
        case "sinking":
            return "pictures/mirror/restshop/fusion/sinking_fusion.png"
        case "bleed":
            return "pictures/mirror/restshop/fusion/bleed_fusion.png"
        case "burn":
            return "pictures/mirror/restshop/fusion/burn_fusion.png"
        case "charge":
            return "pictures/mirror/restshop/fusion/charge_fusion.png"
        case "poise":
            return "pictures/mirror/restshop/fusion/poise_fusion.png"
        case "rupture":
            return "pictures/mirror/restshop/fusion/rupture_fusion.png"
        case "tremor":
            return "pictures/mirror/restshop/fusion/tremor_fusion.png"
        case "slash":
            return "pictures/mirror/restshop/fusion/slash_fusion.png"
        case "pierce":
            return "pictures/mirror/restshop/fusion/pierce_fusion.png"
        case "blunt":
            return "pictures/mirror/restshop/fusion/blunt_fusion.png"

# Backward compatibility alias
fusion_choice = get_fusion_target_button
        
def enhance_shift(status):
    """Get coordinate shift values for enhancement checking"""
    match status:
        case "sinking":
            return (11,-35)
        case "bleed":
            return (12,-36)
        case "burn":
            return (13,-49)
        case "charge":
            return (16,-44)
        case "poise":
            return (12,-41)
        case "rupture":
            return (12,-41)
        case "tremor":
            return (18,-45)
        case "slash":
            return (16,-48)
        case "pierce":
            return (16,-46)
        case "blunt":
            return (10,-48)
        case "wordless":
            return (11,-54)