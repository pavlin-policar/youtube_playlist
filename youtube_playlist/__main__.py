import os
from argparse import ArgumentParser
from os import path
from os.path import expanduser, isdir, join

import yaml
from youtube_dl import YoutubeDL

from youtube_playlist.youtube_playlist import Playlist, check

# Specify the default config
config = {'playlists': {}, 'directory': join('~', 'Music')}

CONFIG_FILE = '.youtube-playlist.yaml'
# Read registered playlists from config file
config_locations = [
    os.curdir,
    path.expanduser('~'),
    path.expanduser('~/.config/'),
]
for location in config_locations:
    try:
        with open(path.join(location, CONFIG_FILE), 'r') as config_file:
            config.update(yaml.load(config_file))
    except IOError:
        pass

# Playlist names should all be handled as strings
for playlist_name in config['playlists'].keys():
    value = config['playlists'][playlist_name]
    del config['playlists'][playlist_name]
    config['playlists'][str(playlist_name)] = value


ACTIONS = {
    'sync': lambda playlist: playlist.sync(),
    'check': check,
}


def __parse_arguments():
    parser = ArgumentParser(
        description='Keep your local music playlist synchronized with your '
                    'youtube playlists.',
    )
    parser.add_argument(
        'action', metavar='action', type=str, choices=ACTIONS.keys(),
        help='action to perform',
    )
    parser.add_argument(
        'name', metavar='name', type=str, choices=config['playlists'].keys(),
        help='playlist name',
    )
    parser.add_argument(
        '--dir', default=config['directory'],
        help='specify the directory where playlists are located'
    )
    args = parser.parse_args()

    # Convert the ~ to the user path, so that `isdir` works properly
    args.dir = expanduser(args.dir)
    assert isdir(args.dir), 'The path specified is not a valid directory!'

    return args


def main():
    args = __parse_arguments()

    ytl = YoutubeDL({
        'quiet': True,
        'no_warnings': True,
        'outtmpl': join(args.dir, '%(playlist)s/%(title)s.%(ext)s'),
        'nooverwrites': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    })

    playlist = Playlist.from_id(config['playlists'][args.name], args.dir, ytl)
    ACTIONS[args.action](playlist)


if __name__ == '__main__':
    main()