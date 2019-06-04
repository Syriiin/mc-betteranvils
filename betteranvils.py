import os
import sys
from tqdm import tqdm
from nbt import nbt, region

world_path = sys.argv[1] or "./world/"

if not os.path.exists(world_path):
    print("World folder not found. Specify path or place in directory with world folder.")
    exit()

playerdata_path = os.path.join(world_path, "playerdata/")
region_path = os.path.join(world_path, "region/")

player_files = [os.path.join(playerdata_path, filename) for filename in os.listdir(playerdata_path) if filename.endswith(".dat")]
region_files = [os.path.join(region_path, filename) for filename in os.listdir(region_path) if filename.endswith(".mca")]

def reset_repair_cost(item_tag):
    try:
        if item_tag["tag"]["RepairCost"].value > 0:
            item_tag["tag"]["RepairCost"].value = 0
            return True
        else:
            return False
    except KeyError:
        return False

print("Searching players")
for path in tqdm(player_files):
    reset_count = 0
    nbtfile = nbt.NBTFile(path)

    # search ender chest items and inventory
    for item_tag in nbtfile["EnderItems"].tags + nbtfile["Inventory"].tags:
        if reset_repair_cost(item_tag):
            reset_count += 1

    if reset_count > 0:
        nbtfile.write_file(path)
        tqdm.write(f"{reset_count} items reset")
        reset_count = 0


print("Searching map")
for path in tqdm(region_files):
    regionfile = region.RegionFile(path)

    for chunk in tqdm(regionfile.iter_chunks(), total=regionfile.chunk_count()):
        reset_count = 0
        # search dropped items and chest minecarts
        for entity in chunk["Level"]["Entities"]:
            try:
                items = entity["Items"]
                for item in items:
                    if reset_repair_cost(item):
                        reset_count += 1
            except KeyError:
                try:
                    if reset_repair_cost(entity):
                        reset_count += 1
                except KeyError:
                    pass

        # search blocks with storage
        for entity in chunk["Level"]["TileEntities"]:
            try:
                items = entity["Items"]
                for item in items:
                    if reset_repair_cost(item):
                        reset_count += 1
            except KeyError:
                pass
        
        if reset_count > 0:
            regionfile.write_chunk(chunk.loc.x, chunk.loc.z, chunk)
            tqdm.write(f"{reset_count} items reset")
            reset_count = 0

print("\r\nWorld successfully rid of anvil repair cost yay")
