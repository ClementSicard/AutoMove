import shutil
import os
import glob
import time
import configparser

PATH_TO_INI_FILE = "ABSOLUTE PATH TO YOUR CONFIG.INI FILE"

config = configparser.ConfigParser()
config.read(PATH_TO_INI_FILE)


onedrive_path = config["PATHS"]["onedrive_path"]
icloud_path = config["PATHS"]["icloud_path"]

nothing = False

while True:
    icloud_folders = [folder for folder in os.listdir(
        icloud_path) if folder[0] != "."]

    files = []
    for folder in icloud_folders:
        relative_paths_files = [path[58:] for path in
                                glob.glob(onedrive_path + folder + "/*.*", recursive=True)]
        if relative_paths_files != []:
            files.extend(relative_paths_files)

    if files != []:
        nothing = False
        print("[AutoMove] Moving", len(files),
              "file(s) from OneDrive to iCloud...")
        for f in files:
            shutil.move(onedrive_path[:-1] + f, icloud_path +
                        f, copy_function=shutil.copy)

        print("[AutoMove] Success!")
    elif nothing == False:
        nothing = True
        print("[AutoMove] Nothing to do for now.\n")
    time.sleep(2)
