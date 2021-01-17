import shutil
import os
import glob
import time
import configparser
import pync
import re


SERIES_REGEXP = r"\w+ - S\d*.\w+$"
HW_REGEXP = r"\w+ - HW\d*.\w+$"
LECTURE_REGEXP = r"(\w+ - \d*.\w+$|Lecture notes.\w+$)"
CS_REGEXP = r"\w+ - (Summary|Tricks|Useful to know)*.\w+$"


def modified_path_with_regex(file_name) -> str:
    if re.search(SERIES_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[:idx + 1] + "EXERCIZES" + file_name[idx:]
    elif re.search(HW_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[:idx + 1] + "HOMEWORKS" + file_name[idx:]
    elif re.search(LECTURE_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "LECTURES" + file_name[idx:]
    elif re.search(CS_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "CHEATSHEETS" + file_name[idx:]
    else:
        return file_name


def main():
    PATH_TO_INI_FILE = "/Users/clementsicard/Dev/GitHub/Automove/config.ini"

    config = configparser.ConfigParser()
    config.read(PATH_TO_INI_FILE)

    onedrive_path = config["PATHS"]["onedrive_path"]
    icloud_path = config["PATHS"]["icloud_path"]

    nothing = False

    pync.notify("📣 AutoMove a démarré !", title="AutoMove 🔁",
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
                new_path = modified_path_with_regex(f)
                file_name = f[f.rfind("/") + 1:]
                try:
                    shutil.move(onedrive_path[:-1] + f, icloud_path +
                                new_path, copy_function=shutil.copy)
                    if len(files) == 1 and new_path != f:
                        pync.notify("✅  " + file_name +
                                    " a été déplacé depuis OneDrive vers iCloud", title="AutoMove 🔁", activate="com.apple.finder")
                    elif new_path == f:
                        pync.notify("❓ Oups! Path inconnu\n" + file_name + " a été déplacé à la racine du dossier",
                                    title="AutoMove 🔁", activate="com.apple.finder")
                except:
                    try:
                        shutil.move(onedrive_path[:-1] + f, icloud_path +
                                    f, copy_function=shutil.copy)
                        pync.notify("❓ Oups! Path iconnu\n" + file_name + " a été déplacé à la racine du dossier",
                                    title="AutoMove 🔁", activate="com.apple.finder")
                    except:
                        pync.notify("❌ Oups, impossible de déplacer " + file_name,
                                    title="AutoMove 🔁", activate="com.apple.finder")

            if len(files) > 1:
                pync.notify("✅  Bonne nouvelle beau gosse ! \n\n" + str(len(files)) +
                            " fichier(s) déplacé(s) vers iCloud", title="AutoMove 🔁", activate="com.apple.finder")

        elif nothing == False:
            nothing = True
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
