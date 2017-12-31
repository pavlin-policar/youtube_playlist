from argparse import ArgumentParser
from os.path import expanduser, isdir, join

from youtube_dl import YoutubeDL

from youtube_playlist.youtube_playlist import PLAYLISTS, PLAYLISTS_DIR, \
    Playlist, check

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
        'name', metavar='name', type=str, choices=PLAYLISTS.keys(),
        help='playlist name',
    )
    parser.add_argument(
        '--dir', default=PLAYLISTS_DIR,
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

    playlist = Playlist.from_title(args.name, args.dir, ytl)
    ACTIONS[args.action](playlist)


if __name__ == '__main__':
    main()
