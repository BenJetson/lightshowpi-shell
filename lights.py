#!/usr/bin/env python3

import glob
import subprocess

WORKING_DIR = "/home/pi/lightshowpi"
MUSIC_DIR = WORKING_DIR + "/music"
PLAYLIST_DIR = WORKING_DIR + "/playlists"
LIGHTSHOWPI = WORKING_DIR + "/py/synchronized_lights.py"
COL_WIDTH = 50
MODES = {
    "now playing": 0,
    "play song": 1,
    "play playlist": 2,
    "stop": 3,
    "make playlist": 4,
    "reload files": 5,
    "exit": 6
}


class Song:
    def __init__(self, path, extension=".mp3", delimiter="-"):
        self.type = "song"

        self.path = path
        self.path_tree = path.split("/")

        self.filename = path[len(path) - 1]

        self.title = self.filename[:(-1 * len(extension))].replace(delimiter, " ").title()

        self.process = None

    def play(self):
        self.process = subprocess.Popen(["sudo", LIGHTSHOWPI, "--file=" + self.path])

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None


class Playlist:

    def __init__(self, path, extension=".playlist", delimiter="-"):
        self.type = "playlist"
        self.path = path
        self.path_tree = path.split("/")

        self.filename = path[len(path) - 1]

        self.title = self.filename[:(-1 * len(extension))].replace(delimiter, " ").title()

        self.songs = []
        self.is_saved = False
        self.process = None

        try:
            self.load()
        except IOError:
            self.save()

    def play(self):
        self.process = subprocess.Popen(["sudo", LIGHTSHOWPI, "--playlist" + self.path])

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            self.process = None

    def add(self, song):
        self.songs.append(song)
        self.is_saved = False

    def remove(self, song):
        self.songs.remove(song)
        self.is_saved = False

    def remove_by_index(self, index):
        self.songs.remove(self.songs[index])
        self.is_saved = False

    def save(self):

        with open(self.path, "w+") as outfile:
            for song in self.songs:
                outfile.write("{}\t{}\n".format(song.title, song.path))

        self.is_saved = True

    def load(self):

        self.songs = []

        with open(self.path, "r") as infile:
            for line in infile.readlines():
                parts = line.split("\t")
                self.songs.append(Song(parts[1]))

        self.is_saved = True


def print_item_list(items):

    length = len(items) // 2

    if len(items) % 2 == 0:
        length += 1

    for i in range(length):

        item1 = items[i].title

        i2 = i + length

        if i2 < len(items):
            item2 = items[i2].title
        else:
            i2 = ""
            item2 = ""

        gap = COL_WIDTH - len(item1)

        if i < 10:
            item1 = " " + item1

        print("{}. {}{}{}. {}".format(i+1, item1, gap, i2+1, item2))


def validate_numeric(num, low, high):
    if isinstance(num, str) and num.isnumeric():
        num = int(num)
        if low <= num <= high:
            return True
    return False


def choose(item_desc, items):
    prev_ok = True

    done = False
    while not done:
        print_item_list(items)

        if not prev_ok:
            print("Previous input was invalid. Try again.")

        print("\nWhich {} to play? (type 'done' to return to menu)".format(item_desc))
        choice = input(">>>")

        if validate_numeric(choice, 1, len(items)):
            return items[int(choice) - 1]
        elif choice == "done":
            return None
        else:
            prev_ok = False
            print("Invalid.")


def make_playlist(songs):

    named = False
    name = ""
    while not named:
        print("/nEnter a name for this playlist. (alphanumeric characters legal)")
        name = input(">>>")

        if name.isalnum():
            named = True
        else:
            print("Invalid.")

    new_playlist = Playlist(PLAYLIST_DIR + "/" + name + ".playlist")

    adding_songs = True
    prev_ok = True

    while adding_songs:

        print_item_list(songs)

        if not prev_ok:
            print("ERROR: previous choice invalid.")
            print("  Either it was already on the playlist, or choice not on list.")

        print("/nWhich song to add? (type 'done' when finished)")
        choice = input(">>>")

        if validate_numeric(choice, 1, len(songs)):
            choice = int(choice)
            selected_song = songs[choice - 1]

            if selected_song not in new_playlist.songs:
                new_playlist.add(selected_song)
                prev_ok = True
            else:
                prev_ok = False
        elif choice.casefold() == "done":
            adding_songs = False
        else:
            prev_ok = False

    new_playlist.save()

    return new_playlist


def whats_playing(item):
    if item is not None and item.poll() is not None:
        print("The {} entitled \"{}\" is playing.".format(item.type, item.title))
    else:
        print("Nothing is playing!")


def menu():
    while True:
        print("""
---LightShowPi Menu---
 0. See what's playing
 1. Play a song
 2. Play a playlist
 3. Stop playing
 4. Make a playlist
 5. Refresh file index
 6. Exit
 """)
        print("What to do?")
        choice = input(">>>")

        if validate_numeric(choice, 1, 6):
            return int(choice)


def get_songs():
    files = sorted(glob.glob(MUSIC_DIR + "/*.mp3"))
    songs = []

    for item in files:
        songs.append(Song(item))

    return songs


def get_playlists():
    files = sorted(glob.glob(MUSIC_DIR + "/*.playlist"))
    playlists = []

    for item in files:
        playlists.append(Playlist(item))

    return playlists


running = True
now_playing = None
mode = 0
all_songs = get_songs()
all_playlists = get_playlists()


while running:

    mode = menu()
    print(mode)

    if mode == MODES["now playing"]:
        whats_playing(now_playing)

    elif mode == MODES["play song"]:
        finished = False

        while not finished:
            now_playing = choose("song", all_songs)
            if now_playing is not None:
                now_playing.play()
            else:
                finished = True

    elif mode == MODES["play playlist"]:
        finished = False

        while not finished:
            now_playing = choose("playlist", all_playlists)
            if now_playing is not None:
                now_playing.play()
            else:
                finished = True

    elif mode == MODES["stop"]:
        if now_playing is not None:
            now_playing.stop()
            now_playing = None

    elif mode == MODES["make playlist"]:
        all_playlists.append(make_playlist(all_songs))

    elif mode == MODES["reload files"]:
        all_songs = get_songs()
        all_playlists = get_playlists()

    elif mode == MODES["exit"]:
        if now_playing is not None:
            now_playing.stop()
        running = False

print("Goodbye!")
