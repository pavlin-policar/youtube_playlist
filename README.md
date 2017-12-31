# Youtube Playlist

Keep your Youtube playlists synchronized on your local file system.

## Installation

Clone the repository and run `python setup.py install`.

## Description

If you're like me, you keep your music playlists on Youtube, since it's very easy to find new songs, add and remove them at will. But sometimes, we simply don't have access to the Internet or would like to save on some mobile data. This project provides a quick and easy to use synchronization tool so that your youtube playlists will be downloaded and synchronized on your local file system.

This is a thin wrapper around [youtube-dl](https://github.com/rg3/youtube-dl/) that keeps track of already downloaded songs and syncs them with the ones in your playlists.

```
youtube-playlist [options] <action> <playlist_name>
```

## Options

```
Actions:
  sync        Synchronize the playlist, download any newly added songs and
              remove any removed songs.
  check       Provides a short summary of the synchronization status.

Playlist_name:
  name        A playlist name must be provided. The playlist names must be
              specified in the config file.

optional arguments:
  -h, --help  Show this help message and exit
  --dir DIR   Specify the directory where playlists are located
```

## Configuration
The configuration file contains the required data to sync your playlists.

Example:
```yaml
directory: ~/Music
playlists:
  # name: playlist_id
  # The playlist id can be found on the playlist webpage e.g. Youtube Weekly Top 50
  # https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG
  weekly-50: PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG
```

The configuration file must be named `.youtube-playlist.yaml` and can is searched for in the following order: `$PWD`, `$HOME`, `$HOME/.config/`.

## Notes
- The playlist must be a public playlist.
- You can add your own audio files to the folder. They will be registered as non tracked files and will not be touched.
