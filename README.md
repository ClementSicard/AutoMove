# AutoMove

Python script running in background to automatically move files from OneDrive directory to an iCloud directory.

You will need the following libraries to be able to use it :

```python
configparser
shutil
os
glob
time
```


You just have to fill your `config.ini` file with the corresponding paths to your directories, and fill in the `PATH_TO_INI_FILE` in the `automove.py` file, and the job will be done!