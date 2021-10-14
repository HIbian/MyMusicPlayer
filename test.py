import configparser
import os.path

config = configparser.ConfigParser()
config.read('setting.ini')
music_path = config.get('MusicPlayer', 'path')
print(music_path)
os.listdir(music_path)

for music in os.listdir(music_path):
    if music.split('.')[-1] in ('mp3','m4a'):
        print(os.path.join(music_path, music))
