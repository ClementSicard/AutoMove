import os

print(f'__file__: {__file__}')
print(f'Parent folder: {os.path.dirname(__file__)}')
print(f'Files in parent folder: {os.listdir(os.path.dirname(__file__))}')
