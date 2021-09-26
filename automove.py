import paramiko
import configparser
import shutil
import os
import glob
import time
import configparser
import pync
import re
import paramiko
from fnmatch import fnmatch
from typing import List

SERIES_REGEXP = r"\w+ - S\d*.*.\w+$"
HW_REGEXP = r"\w+ - HW\d*.*.\w+$"
EXAM_REGEXP = r"\w+ - E\d*.*.\w+$"
REVISION_REGEXP = r"\w+ - R\d*.*.\w+$"
LECTURE_REGEXP = r"\w+ - (\d*|Lecture notes|SLIDES|Slides).*.\w+$"
CS_REGEXP = r"\w+ - (Summary|Tricks|Useful to know|Cheatsheet|Formulaire)*.*.\w+$"

PATH_TO_INI_FILE = "/Users/clementsicard/Developer/GitHub/Automove/config.ini"


class AutoMove:

    sftp: paramiko.SFTPClient
    sftp_backup_path: str
    sftp_path: str
    icloud_path: str
    host: str
    port: int
    account: str
    pw: str

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(PATH_TO_INI_FILE)

        self.icloud_path = config["PATHS"]["icloud_path"]
        self.sftp_path = config["PATHS"]["sftp_path"]
        self.sftp_backup_path = config["PATHS"]["sftp_backup_path"]

        self.host = config["SFTP"]["sftp_host"]
        self.port = int(config["SFTP"]["sftp_port"])
        self.account = config["SFTP"]["sftp_account"]
        self.pw = config["SFTP"]["sftp_pw"]

        self.sftp = self.__connect_to_SFTP()
        self.sftp.chdir(self.sftp_backup_path)

        pync.notify("📣 AutoMove a démarré !", title="AutoMove 🔁", actions="Close",
                    execute=f'open "{self.icloud_path}"')

    def run(self):
        nothing = False

        while True:
            icloud_folders = [folder for folder in next(os.walk(self.icloud_path))[
                1] if folder[0] != "."]

            files_to_upload = []

            for folder in icloud_folders:
                files_to_upload_by_folder = self.__get_files_to_upload(folder)

                if files_to_upload_by_folder:
                    files_to_upload.extend(files_to_upload_by_folder)

            if files_to_upload:
                nothing = False

                self.__copy_files_to_icloud(files_to_upload)
                print("Done copying to iCloud")

                self.__backup_on_NAS(files_to_upload)
                print("Done backing up files to NAS")

            elif not nothing:
                nothing = True

            time.sleep(1)

    def __terminal_command(self, path: str) -> str:
        return "terminal-notifier -title 'Title' -message 'Message' -actions 'Close' -execute 'open ~/'"

    def __connect_to_SFTP(self) -> paramiko.SFTPClient:
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(None, self.account, self.pw)
        return paramiko.SFTPClient.from_transport(transport)

    def __backup_on_NAS(self, paths: List[str]):
        try:
            for f in paths:
                new_path = modified_path_with_regex(f)
                file_name = f[f.rfind("/") + 1:]

                path_exists_on_NAS = __sftp_exists(
                    os.path.join(self.sftp_path, new_path))

                self.sftp.rename(os.path.join(self.sftp_backup_path, f),
                                 os.path.join(self.sftp_path, new_path))

                pync.notify(
                    f"✅  Bonne nouvelle ! \n{len(paths)} fichier(s) sauvegardé(s) sur le NAS.", title="AutoMove 🔁", actions="Close")

        except FileNotFoundError:
            pync.notify(f"❓ Oups! Soucis de path pour la sauvegarde sur le NAS...\nCliquer pour debug",
                        title="AutoMove 🔁", actions="Close", execute=f'code "/Users/clementsicard/Developer/GitHub/Automove"')

    def __get_files_to_upload(self, folder: str) -> List[str]:
        to_return = []

        folder_path = os.path.join(self.sftp_backup_path, folder)

        if self.__sftp_exists(folder_path):
            for f in self.sftp.listdir(folder_path):
                if fnmatch(f, "*.*"):
                    to_return.append(os.path.join(folder, f))
            return to_return
        else:
            return []

    def __sftp_exists(self, path: str) -> bool:
        try:
            self.sftp.stat(path)
            return True

        except FileNotFoundError:
            return False

    def __copy_files_to_icloud(self, paths: List[str]):
        try:
            for f in paths:
                new_path = modified_path_with_regex(f)
                file_name = f[f.rfind("/") + 1:]

                path_exists_on_icloud = os.path.exists(
                    os.path.join(self.icloud_path, new_path))

                if not path_exists_on_icloud:
                    try:
                        self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                      os.path.join(self.icloud_path, f))

                        pync.notify(f"❓ Oups! Path inconnu\n{file_name} a été déplacé à la racine du dossier.",
                                    title="AutoMove 🔁", actions="Close", execute=f'open "{os.path.join(self.icloud_path, f)}"')
                    except FileNotFoundError:
                        pync.notify(f"❌ Oups, impossible de déplacer {file_name}.",
                                    title="AutoMove 🔁", actions="Close")

                self.sftp.get(os.path.join(self.sftp_backup_path, f),
                              os.path.join(self.icloud_path, new_path))

                if len(paths) == 1 and new_path != f:
                    if not path_exists_on_icloud:
                        pync.notify(f"✅ {file_name} a été copié depuis le NAS vers iCloud.", title="AutoMove 🔁",
                                    actions="Close", execute=f'open "{os.path.join(self.icloud_path, new_path)}"')
                    else:
                        pync.notify(f"✅ {file_name} a été mis à jour sur iCloud.", title="AutoMove 🔁",
                                    actions="Close", execute=f'open "{os.path.join(self.icloud_path, new_path)}"')

                elif len(paths) > 1 and new_path != f:
                    pync.notify(f"✅  Bonne nouvelle ! \n{len(paths)} fichier(s) copiés sur iCloud.",
                                title="AutoMove 🔁", actions="Close", execute=f'open "{self.icloud_path}"')

                elif new_path == f:
                    pync.notify(f"❓ Oups! Path inconnu\n{file_name} a été déplacé à la racine du dossier.",
                                title="AutoMove 🔁", actions="Close", execute=f'open "{os.path.join(self.icloud_path, new_path)}"')

        except FileNotFoundError:
            pync.notify(f"❓ Oups! Soucis de path sur le NAS...\nCliquer pour debug",
                        title="AutoMove 🔁", actions="Close", execute=f'code "/Users/clementsicard/Developer/GitHub/Automove"')

    def __backup_on_NAS(self, paths: List[str]):
        try:
            for f in paths:
                new_path = modified_path_with_regex(f)
                file_name = f[f.rfind("/") + 1:]

                path_exists_on_NAS = __sftp_exists(
                    os.path.join(self.sftp_path, new_path))

                self.sftp.rename(os.path.join(self.sftp_backup_path, f),
                                 os.path.join(self.sftp_path, new_path))

                pync.notify(
                    f"✅  Bonne nouvelle ! \n{len(paths)} fichier(s) sauvegardé(s) sur le NAS.", title="AutoMove 🔁", actions="Close")

        except FileNotFoundError:
            pync.notify(f"❓ Oups! Soucis de path pour la sauvegarde sur le NAS...\nCliquer pour debug",
                        title="AutoMove 🔁", actions="Close", execute=f'code "/Users/clementsicard/Developer/GitHub/Automove"')

    def close(self):
        self.sftp.close()


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
