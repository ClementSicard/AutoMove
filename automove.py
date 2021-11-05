import paramiko
import configparser
import shutil
import os
import glob
import time
import configparser
import pync
import re
from paramiko import SFTPClient
from fnmatch import fnmatch
from typing import List, Dict, Union
from helper import *


class AutoMove:
    args: Dict[str, Union[str, bool]]
    sftp_bool: bool
    sftp: SFTPClient
    sftp_backup_path: str
    sftp_path: str
    icloud_path: str
    new_paths: List[str]
    tmp_paths: List[str]
    onedrive_path: str
    host: str
    port: int
    account: str
    verbose: bool
    pw: str

    def __init__(self, args: Dict[str, Union[str, bool]]):
        """Creates a new `AutoMove` object

        Args:
            `args` (`Dict[str, Union[str, bool]]`): The arguments gathered by the `argparse.parse_args()` function in `main.py`
        """

        config = configparser.ConfigParser()
        config.read(PATH_TO_INI_FILE)

        self.args = args
        self.verbose = self.args["verbose"]
        self.sftp_bool = self.args["sftp"]

        success, pid = checkPID()
        if success and self.verbose:
            print(f"AutoMove started with PID [{pid}].\n")

        self.icloud_path = config["PATHS"]["icloud_path"]
        self.onedrive_path = config["PATHS"]["onedrive_path"]

        if self.sftp_bool:
            self.sftp_path = config["PATHS"]["sftp_path"]
            self.sftp_backup_path = config["PATHS"]["sftp_backup_path"]
            self.host = config["SFTP"]["sftp_host"]
            self.port = int(config["SFTP"]["sftp_port"])
            self.account = config["SFTP"]["sftp_account"]
            self.pw = config["SFTP"]["sftp_pw"]
            self.sftp = self.__connect_to_SFTP()
            self.sftp.chdir(self.sftp_backup_path)

        send_notification(
            message="✅ AutoMove a démarré !",
            important=True,
        )

    def run(self):
        """Contains the main `while True` loop of the app"""

        nothing = False
        try:
            while True:
                icloud_folders = [folder for folder in next(os.walk(self.icloud_path))[
                    1] if folder[0] != "."]

                self.tmp_paths = []
                self.new_paths = []

                for folder in icloud_folders:
                    files_to_upload_by_folder = self.__get_files_to_upload(
                        folder)

                    if files_to_upload_by_folder:
                        self.tmp_paths.extend(files_to_upload_by_folder)

                if self.tmp_paths:
                    print(f'{len(self.tmp_paths)} new files to upload.')
                    nothing = False

                    self.__copy_files_to_icloud()
                    print("\t\tDone copying to iCloud")

                    if self.sftp_bool:
                        self.__backup_files_on_NAS()
                        print("Done backing up files to NAS")

                elif not nothing:
                    print('0 new file to upload.')
                    nothing = True

                time.sleep(1)

        except paramiko.ssh_exception.SSHException:
            print("Connection lost.")
            connected = False

            while not connected:
                try:
                    self.sftp = self.__connect_to_SFTP()
                    connected = False
                except:
                    time.sleep(5)

    def __connect_to_SFTP(self) -> SFTPClient:
        """Connects AutoMove to the distant NAS server via SFTP

        Returns:
            `SFTPClient`: The SFTP client object
        """

        transport = paramiko.Transport((self.host, self.port))
        transport.connect(None, self.account, self.pw)
        client = SFTPClient.from_transport(transport)
        print(
            f"\n[SFTP] Connected to NAS via SFTP on {self.host} on port {self.port}.")
        print()

        return client

    def __get_files_to_upload(self, folder: str) -> List[str]:
        """Gets the list of files to upload from the temporary folder on the NAS

        Args:
            `folder` (`str`): Name of the folder (not the path)

        Returns:
            `List[str]`: The list of file names in `folder`
        """

        to_return = []

        folder_path = os.path.join(self.sftp_backup_path, folder) if self.sftp_bool else os.path.join(
            self.onedrive_path, folder)

        if self.__sftp_exists(folder_path) if self.sftp_bool else os.path.exists(folder_path):
            for f in self.sftp.listdir(folder_path) if self.sftp_bool else os.listdir(folder_path):
                if fnmatch(f, "*.pdf") and not f.startswith("."):
                    to_return.append(os.path.join(folder, f))
            return to_return
        else:
            return []

    def __sftp_exists(self, path: str) -> bool:
        """Checks whether a certain path exists on the remote server via SFTP

        Args:
            path (`str`): Path we want to check

        Returns:
            `bool`: `True` if the path exists, `False` otherwise
        """

        try:
            self.sftp.stat(path)
            return True

        except FileNotFoundError:
            return False

    def __copy_files_to_icloud(self) -> None:
        """Helper function to copy the files in `self.tmp_paths` to iCloud
        """

        silent = len(self.tmp_paths) > 1
        err = False

        for f in self.tmp_paths:
            new_path = modified_path_with_regex(f)
            self.new_paths.append(new_path)

            if self.verbose:
                print()
                print(f'\nFile: {f}')
                print(f'\tNew path: {new_path}')

            file_name = f[f.rfind("/") + 1:]

            test_icloud_path = os.path.join(self.icloud_path, new_path)
            path_exists_on_icloud = os.path.exists(test_icloud_path)

            if not path_exists_on_icloud:

                if self.verbose:
                    print(f"\tPath doesn't exist on iCloud.")

                if new_path == f:
                    try:
                        if self.sftp_bool:
                            self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                          os.path.join(self.icloud_path, f))
                            if self.verbose:
                                print(
                                    f'\t\tWell copied from NAS to iCloud, but to root since name was not recognized by Regexps.')
                        else:
                            shutil.move(os.path.join(self.onedrive_path, f),
                                        os.path.join(self.icloud_path, f))
                            if self.verbose:
                                print(
                                    f'\t\tWell copied from OneDrive to iCloud, but to root since name was not recognized by Regexps.')

                        if not silent:
                            send_notification(
                                message="❓ Oops... Path inconnu",
                                content=f"{file_name} a été déplacé à la racine du dossier.",
                            )
                    except FileNotFoundError:
                        if self.verbose:
                            print(
                                f'\t\t[ERROR]: {new_path} could not be moved.')
                            print("="*30)

                        err = True
                        send_notification(
                            message=f"🚨 Oups, impossible de déplacer ce fichier",
                            content=f"{file_name}",
                            error=True,
                        )
                else:
                    try:
                        if self.sftp_bool:
                            from_path = os.path.join(
                                self.sftp_backup_path, f)
                            dest_path = os.path.join(
                                self.icloud_path, new_path)

                            self.sftp.get(from_path,
                                          dest_path)

                            if self.verbose:
                                print(
                                    f'\t✅ {from_path} -> {dest_path}')
                        else:
                            from_path = os.path.join(self.onedrive_path, f)
                            dest_path = os.path.join(
                                self.icloud_path, new_path)

                            shutil.move(from_path, dest_path)

                            if self.verbose:
                                print(
                                    f'\t✅ {from_path} -> {dest_path}')

                        if not silent:
                            send_notification(
                                message=f"✅ {file_name} a bien été déplacé {'du NAS' if self.sftp_bool else 'OneDrive'} vers iCloud !",
                            )

                    except FileNotFoundError:
                        if self.verbose:
                            print(
                                f'\t\t[ERROR] FileNotFoud: {f} could not be moved to {new_path}.')
                            print("="*30)

                        err = True
                        send_notification(
                            message=f"🚨 Oups, impossible de déplacer ce fichier",
                            content=f"{file_name}",
                            error=True,
                        )

            else:
                if self.verbose:
                    print(f"\tPath exists on iCloud.")
                try:

                    if self.sftp_bool:
                        self.sftp.get(os.path.join(self.sftp_backup_path, f),
                                      os.path.join(self.icloud_path, new_path))

                    else:
                        shutil.move(os.path.join(self.onedrive_path, f),
                                    os.path.join(self.icloud_path, new_path))

                    if not silent:
                        send_notification(
                            message=f"✅ {file_name} a été mis à jour sur iCloud.",
                        )

                except FileNotFoundError:
                    if self.verbose:
                        print(
                            f'\t\t[ERROR]: {new_path} could not be updated on iCloud.')
                        print("="*30)

                    err = True
                    send_notification(
                        message=f"🚨 Oups... Impossible de déplacer un ficher",
                        content=f"{file_name}",
                        error=True,
                    )

        if silent and not err:
            send_notification(
                message=f"✅  Bonne nouvelle !",
                content=f"{len(self.tmp_paths)} fichier(s) copiés sur iCloud.",
            )

        elif silent and err:
            send_notification(
                message=f"🚨 Oups, il y a eu une erreur pendant la sauvegarde des fichiers sur iCloud.",
                error=True,
            )

    def __backup_files_on_NAS(self) -> None:
        """Backs up a list of files to the NAS, respecting the infered arborescent structure.
        """

        self.new_paths = [modified_path_with_regex(
            path) for path in self.tmp_paths]

        for tmp_path, new_path in zip(self.tmp_paths, self.new_paths):
            self.__backup_on_NAS(tmp_path, new_path)

    def __backup_on_NAS(self, tmp_path: str, new_path: str) -> None:
        """Helper function to backup a file from a path on a NAS to another, using SFTP

        Args:
            `tmp_path` (`str`): 'From' path

            `new_path` (`str`): 'To' path
        """

        try:
            from_path = os.path.join(self.sftp_backup_path, tmp_path)
            dest_path = os.path.join(self.sftp_path, new_path)

            self.sftp.posix_rename(from_path, dest_path)

        except FileNotFoundError:
            if self.verbose:
                print(
                    f"\t\t[ERROR] - FileNotFound : Could not save {from_path} to {dest_path} on NAS.")
                print("=" * 30)
                print()

            send_notification(
                message=f"❓ Oups! Soucis de path pour la sauvegarde sur le NAS...",
                error=True
            )

    def close(self):
        """Closes cleanly the SFTP client in order to end the app.
        """
        self.sftp.close()
