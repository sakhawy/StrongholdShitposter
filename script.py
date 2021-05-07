# NOTES From Reversing:
# [x] All the entities in Stronghold Crusader including the main ones are stored in an array of structures.
# That array has a base pointer of 0x1387B50 (assuming the base address is 0x00400000)
# [x] The first entity's address is 0xd64 bytes away from the base pointer
# [x] The entity's structure is 0x490 bytes
# [x] The entity's type is 0x25e bytes away from its address
# [x] The entity's alliance is 0x266 bytes away from its address
# [x] A main character's type is 55

# NOTE: I have a clean code allergy 

# pywin32: windows-api python access
import win32gui, win32api, win32process

# pymem: memory manipulation
import pymem

import random
import time

def read(addr, l):
    # For less writing
    
    return int.from_bytes(mem.read_bytes(addr, l), byteorder="little")

def is_main_character(e):
    # A main character's type is 55
    
    return e["type"][1] == 55

def get_players_count(all_entities):
    # We don't want the main character's alliance to change
    
    return len(list(filter(is_main_character, all_entities)))

def change_alliance(entities, players_count): 
    # Change the alliance randomly 
    
    changed = 0
    for e in entities:
        if random.choice([0, 1]) and not is_main_character(e):
            aln = random.randint(2, players_count)

            mem.write_int(e["alliance"][0], aln)
            e["alliance"][1] = aln
            changed += 1
    return changed

def scan_entities():
    # Scan memory for entities

    # Base pointer
    entities_pointer = 0x1387B50
    entities_count = read(entities_pointer, 4)
    
    all_entities = []

    # First entity's address
    e_addr = entities_pointer + 0xd64
    
    # Get entities info
    for e in range(entities_count):
        e_type_ptr = e_addr + 0x25e
        e_alliance_ptr = e_addr + 0x266

        # A structure for easy access
        e_type = read(e_type_ptr, 2)
        e_alliance = read(e_alliance_ptr, 2)
        all_entities.append({
            "addr": e_addr,
            "type": [e_type_ptr, e_type],
            "alliance": [e_alliance_ptr, e_alliance]
        })
        
        # Next entity
        e_addr += 0x490

    return all_entities 

def main():
    # Main
    
    global mem

    # Hook the process' memory 
    pid = win32process.GetWindowThreadProcessId(win32gui.FindWindow(None, "Crusader"))[1]
    mem = pymem.Pymem()
    mem.open_process_from_id(pid)
    
    # Keystroke loop

    print('Listening for `F6` (Press `F8` to quit)...')
    while True:
        
        # F6 key
        if win32api.GetAsyncKeyState(0x75):
            # Get/update entities
            all_entities = scan_entities()
            players_count = get_players_count(all_entities)
            human_player_entities = list(filter(lambda e: e["alliance"][1] == 1, all_entities))

            # Change entities
            changed = change_alliance(human_player_entities, players_count)
            
            print(f"Changed {changed}/{len(human_player_entities)} entities")
            print('\nListening for `F6` (Press `F8` to quit)...')

            # Multiple keypresses lazy mitigation
            time.sleep(1)

        if win32api.GetAsyncKeyState(0x77):
            print("Exiting...")
            exit()

if __name__ == "__main__":
    main()
