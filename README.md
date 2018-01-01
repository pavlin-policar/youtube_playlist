# Youtube Playlist

Keep your Youtube playlists synchronized on your local file system.

## Installation

Clone the repository and run `python setup.py install`.

## Description

If you're like me, you keep your music playlists on Youtube, since it's very easy to find new songs, add and remove them at will. But sometimes, we simply don't have access to the Internet or would like to save on some mobile data. This project provides a quick and easy to use synchronization tool so that your youtube playlists will be downloaded and synchronized on your local file system.

This is a thin wrapper around [youtube-dl](https://github.com/rg3/youtube-dl/) that keeps track of already downloaded songs and syncs them with the ones in your playlists.

With every synchronization, `youtube-playlist` will check for any songs you may have added to your playlist on youtube, and download them. It will also check for any songs you may have removed online and also remove them from the directory. You can also place your own songs into the playlist directory and the script will not touch them. They will be "non-tracked". You can also remove all the non-tracked files from the directory with the `remove-untracked` command.

```
youtube-playlist [options] <action> <playlist_name>
```

## Options

```
Actions:
  sync                  Synchronize the playlist, download any newly added songs and
                        remove any removed songs.
                        
  check                 Provides a short summary of the synchronization status.
  
  remove-untracked      Removes all the files in the playlist directory that are
                        not being tracked.

Playlist_name:
  name         A playlist name must be provided. The playlist names must be
               specified in the config file.

optional arguments:
  -h, --help   Show this help message and exit
  --dir DIR    Specify the directory where playlists are located
  --log LEVEL  Specify log level
```

## Configuration
The configuration file contains the required data to sync your playlists.

Example:
```yaml
# Specify the location where the playlists will be stored
directory: ~/Music
# Specify the playlists you want to keep track of here
playlists:
  # <playlist_name>: <playlist_id>
  # The playlist id can be found on the playlist webpage e.g. Youtube Weekly Top 50
  # https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG
  weekly-50: PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG
```

The configuration file must be named `.youtube-playlist.yaml` and can is searched for in the following order: `$PWD`, `$HOME`, `$HOME/.config/`.

## Notes
- The playlist must be a public playlist.
- You can add your own audio files to the folder. They will be registered as non tracked files and will not be touched.
- Some tracks are copyright protected, and therefore, cannot be downloaded. The script will notify you of such a track, and a full list of these tracks can be obtained with `youtube-playlist check <playlist_name>`.
