import shutil
import os
import glob
import time
import configparser
import pync


def main():
    PATH_TO_INI_FILE = "/Users/clementsicard/Dev/GitHub/Automove/config.ini"

    config = configparser.ConfigParser()
    config.read(PATH_TO_INI_FILE)

    onedrive_path = config["PATHS"]["onedrive_path"]
    icloud_path = config["PATHS"]["icloud_path"]

    nothing = False

    pync.notify("Automove started!", title="AutoMove 🔁",
                activate="com.apple.finder")

    while True:
        icloud_folders = [folder for folder in os.listdir(
            icloud_path) if folder[0] != "."]

        files = []
        for folder in icloud_folders:
            relative_paths_files = [path[len(onedrive_path) - 1:] for path in
                                    glob.glob(onedrive_path + folder + "/*.*", recursive=True)]
            if relative_paths_files != []:
                files.extend(relative_paths_files)

        if files != []:
            nothing = False
            for f in files:
                shutil.move(onedrive_path[:-1] + f, icloud_path +
                            f, copy_function=shutil.copy)
            pync.notify(str(len(files)) +
                        " fichier(s) déplacé(s) depuis OneDrive vers iCloud bg", title="AutoMove 🔁", activate="com.apple.finder")

        elif nothing == False:
            nothing = True
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
