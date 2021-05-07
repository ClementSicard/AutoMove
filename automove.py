import shutil
import os
import glob
import time
import configparser
import pync
import re


SERIES_REGEXP = r"\w+ - S\d*.\w+$"
HW_REGEXP = r"\w+ - HW\d*.\w+$"
EXAM_REGEXP = r"\w+ - E\d*.\w+$"
REVISION_REGEXP = r"\w+ - R\d*.\w+$"
LECTURE_REGEXP = r"\w+ - (\d*|Lecture notes|SLIDES|Slides).\w+$"
CS_REGEXP = r"\w+ - (Summary|Tricks|Useful to know|Cheatsheet|Formulaire)*.\w+$"


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
    elif re.search(EXAM_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "EXAMS" + file_name[idx:]
    elif re.search(REVISION_REGEXP, file_name):
        idx = file_name[1:].find("/") + 1
        return file_name[: idx + 1] + "REVISIONS" + file_name[idx:]
    else:
        return file_name


def terminal_command(path: str) -> str:
    return "terminal-notifier -title 'Title' -message 'Message' -actions 'Close' -execute 'open ~/'"


def main():
    PATH_TO_INI_FILE = "/Users/clementsicard/Developer/GitHub/Automove/config.ini"

    config = configparser.ConfigParser()
    config.read(PATH_TO_INI_FILE)

    onedrive_path = config["PATHS"]["onedrive_path"]
    icloud_path = config["PATHS"]["icloud_path"]

    nothing = False
    pync.notify("📣 AutoMove a démarré !", title="AutoMove 🔁", actions="Close",
                execute="open \"{}\"".format(icloud_path[:-1]))

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
            new_bool = False
            for f in files:
                new_path = modified_path_with_regex(f)
                file_name = f[f.rfind("/") + 1:]
                try:
                    new_bool = os.path.exists(icloud_path + new_path)
                    shutil.move(onedrive_path[:-1] + f, icloud_path +
                                new_path, copy_function=shutil.copy)
                    if len(files) == 1 and new_path != f:
                        if not new_bool:
                            pync.notify("✅  " + file_name +
                                        " a été déplacé depuis OneDrive vers iCloud.", title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(icloud_path + new_path))
                        else:
                            pync.notify("✅  " + file_name +
                                        " a été mis à jour sur iCloud.", title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(icloud_path + new_path))

                    elif new_path == f:
                        pync.notify("❓ Oups! Path inconnu\n" + file_name + " a été déplacé à la racine du dossier.",
                                    title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(icloud_path + new_path))
                except:
                    try:
                        shutil.move(onedrive_path[:-1] + f, icloud_path +
                                    f, copy_function=shutil.copy)
                        pync.notify("❓ Oups! Path iconnu\n" + file_name + " a été déplacé à la racine du dossier.",
                                    title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(icloud_path + f))
                    except:
                        pync.notify("❌ Oups, impossible de déplacer " + file_name + ".",
                                    title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(onedrive_path[:-1] + f))

            if len(files) > 1:
                pync.notify("✅  Bonne nouvelle ! \n" + str(len(files)) +
                            " fichier(s) déplacé(s) vers iCloud.", title="AutoMove 🔁", actions="Close", execute="open \"{}\"".format(icloud_path))

        elif nothing == False:
            nothing = True
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
