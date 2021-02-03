# AutoMove

Python script running in background to automatically move files from OneDrive directory to an iCloud directory.

You will need the following libraries to be able to use it :

```python
configparser
shutil
os
glob
time
pync
```

You can install all of them using this command :

```
pip install configparser shutil os glob time pync
```


You just have to fill your `config.ini` file with the corresponding paths to your directories, and fill in the `PATH_TO_INI_FILE` in the `automove.py` file, and the job will be done!

To have it running on the background, use the following command from terminal :

```shell
python3 automove.py &
```

You can easily set up an Automator app starting AutoMove automatically when logging in by creating a Shell script-executing app, and insert in it the following command :

```shell
nohup /usr/local/bin/python3 <path to Python script>/automove.py > /dev/null 2>&1 &
```
Just open the Automator app and set it on your device.

The script also automatically sends notifications to Notification Center in macOS when anything happens (copy of a file, multiple files, copy failure, app starting)

