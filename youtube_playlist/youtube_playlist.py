import logging
import os
import pickle
import sys
from os.path import join, exists, basename
from typing import Dict

import notify2 as notify
from youtube_dl import YoutubeDL
from youtube_dl.utils import sanitize_filename, ExtractorError

notify.init('Youtube Playlist')


def _print_progress(current_idx, total_songs, song_title):
    # Clear the line from the previous download
    sys.stdout.write('\r' + ' ' * 80)
    sys.stdout.flush()

    # Truncate the song title to fit into console
    if len(song_title) > 80:
        # Remove 12 because 3 for ellipsis and 9 for progress format
        song_title = '%s...' % song_title[:80 - 12]

    # We show the currently being downloaded song
    sys.stdout.write(
        '\r[%3d/%3d] %s' % (current_idx, total_songs, song_title)
    )
    sys.stdout.flush()


def _print_message(message):
    sys.stdout.write('\r' + ' ' * 80)
    sys.stdout.flush()
    sys.stdout.write('\r%s\n' % message)
    sys.stdout.flush()


class Playlist:
    DATA_FILE_NAME = 'data.p'

    def __init__(self, playlist_info, directory, ytl):
        # type: (Dict, str, YoutubeDL) -> None
        self.id = playlist_info['id']
        self.name = playlist_info['title']
        self.uploader = playlist_info['uploader']
        self.directory = join(directory, self.name)
        self.data_file = join(self.directory, self.DATA_FILE_NAME)

        self._upstream_data = {
            entry['id']: Song(entry, ytl, playlist=self)
            for entry in playlist_info['entries']
        }

        self.__ytl = ytl

        self._local_data = self.__get_local_data()
        self.non_tracked_songs = self.__check_for_non_tracked_songs()

        self.__local_ids = set(self._local_data.keys())
        self.__upstream_ids = set(self._upstream_data.keys())

        self.__synced_song_ids = self.__upstream_ids & self.__local_ids
        self.__to_remove_song_ids = self.__local_ids - self.__upstream_ids
        self.__to_download_song_ids = self.__upstream_ids - self.__local_ids

    def __get_local_data(self):
        local_data = {}

        # Attempt to read pickled list of song data from fs, otherwise assume
        # no songs have been downloaded
        try:
            with open(self.data_file, 'rb') as file:
                loaded_data = pickle.load(file)

            # Check that the loaded playlist is the same as this one
            assert loaded_data['id'] == self.id
            assert loaded_data['name'] == self.name

        except FileNotFoundError:
            logging.info('Data file not found. Assume empty local data.')

        # If the data is corrupt, there's nothing we can do, so remove it
        except (EOFError, TypeError):
            logging.warning('Unable to read data file. Removing...')
            os.remove(self.data_file)

        except AssertionError:
            logging.warning('The data file contains data for different '
                            'playlist. Removing...')
            os.remove(self.data_file)

        # Process the local data file and set up the `local_data`
        try:
            for song_id in loaded_data['songs']:
                song = Song.from_info(
                    loaded_data['songs'][song_id], self.__ytl, playlist=self
                )
                # Check if the song actually exists on the file system, if it
                # does, add it to the local data. Also keep the song in local
                # data if it has been copyrighted
                if exists(song.file_path) or song.copyrighted:
                    local_data[song_id] = song
                else:
                    logging.info('%s found in data file, but not on disk. '
                                 'Removing from data...' % song.title)

        # `loaded_data` only exists when parsing the data file succeeded. This
        # is in a separate try/except to make logging simpler.
        except UnboundLocalError:
            pass

        return local_data

    def __check_for_non_tracked_songs(self):
        """List all mp3 files that are not being tracked."""
        all_files = os.listdir(self.directory)
        all_files = filter(lambda f: '.mp3' in f, all_files)

        tracked_songs = {
            basename(song.file_path) for song in self._local_data.values()
        }
        non_tracked_songs = []

        for file in all_files:
            if file not in tracked_songs:
                non_tracked_songs.append(file)

        return non_tracked_songs

    @property
    def synced(self):
        """Synced tracks include all tracks that have been downloaded."""
        return [self._local_data[song_id] for song_id in self._local_data
                if song_id in self.__synced_song_ids and
                not self._local_data[song_id].copyrighted]

    @property
    def copyrighted(self):
        """Copyrighted tracks have been synced, but can't be downloaded."""
        return [self._local_data[song_id] for song_id in self._local_data
                if song_id in self.__synced_song_ids and
                self._local_data[song_id].copyrighted]

    @property
    def to_remove(self):
        return [self._local_data[song_id] for song_id in self._local_data
                if song_id in self.__to_remove_song_ids]

    @property
    def to_download(self):
        return [self._upstream_data[song_id] for song_id in self._upstream_data
                if song_id in self.__to_download_song_ids]

    def sync(self):
        if len(self.to_remove):
            print('Deleting removed tracks from local file system.')
            self._remove_songs()
            print('\n')

        if len(self.to_download):
            print('Downloading added tracks to local file system.')
            self._download_songs()
            print('\n')

        # Show a notification if anything was done
        if len(self.to_remove) or len(self.to_download):
            notify_message = 'Synchronization complete. Playlist contains ' \
                             '%d tracks.\n' % len(self._local_data)
            if len(self.to_remove):
                notify_message += 'Removed %d tracks.\n' % len(self.to_remove)
            if len(self.to_download):
                notify_message += 'Downloaded %d tracks.\n' % len(
                    self.to_download)
            notification = notify.Notification(
                summary='%s Sync Complete' % self.name,
                message=notify_message,
            )
            notification.set_urgency(notify.URGENCY_LOW)
            notification.show()

    def _remove_songs(self):
        for idx, song in enumerate(self.to_remove):
            _print_progress(idx + 1, len(self.to_remove), song.title)
            os.remove(song.file_path)

    def _download_songs(self):
        for idx, song in enumerate(self.to_download):
            _print_progress(idx + 1, len(self.to_download), song.title)

            # Perform download if necessary
            if exists(song.file_path):
                _print_message('`%s` already exists. Skipping download.' %
                               song.title)
                logging.info('%s was not found in data file, but already '
                             'existed on file system. Skipping download')
            else:
                try:
                    song.download()
                except ExtractorError as e:
                    if 'copyright grounds' in str(e):
                        song.copyrighted = True
                        _print_message(
                            'Unable to download `%s` due to copyright '
                            'restrictions' % song.title
                        )
                    # If we don't know why it failed, better to throw again
                    else:
                        raise e

            self._local_data[song.id] = song

            with open(self.data_file, 'wb') as file:
                pickle.dump(self.info(), file)

    def info(self):
        return {
            'id': self.id,
            'name': self.name,
            'songs': {
                song_id: self._local_data[song_id].info()
                for song_id in self._local_data
            },
        }

    @classmethod
    def from_id(cls, playlist_id, directory, ytl):
        # type: (str, str, YoutubeDL) -> Playlist
        """Create playlist instance from the given playlist name."""
        ie = ytl.get_info_extractor('YoutubePlaylist')

        assert ie.suitable(playlist_id), \
            'The info extractor is not suitable for the given URL. Are you ' \
            'sure you provided a valid playlist id?'

        playlist_info = ie.extract(playlist_id)
        playlist_info['entries'] = list(playlist_info['entries'])

        return cls(playlist_info, directory, ytl)


class Song:
    def __init__(self, song_info, ytl, playlist):
        # type: (Dict, YoutubeDL, Playlist) -> None
        self.id = song_info['id']
        self.title = sanitize_filename(song_info['title'])
        self.url = song_info['url']
        self.playlist = playlist
        self.file_path = join(playlist.directory, '%s.mp3' % self.title)
        self.copyrighted = song_info.get('copyright', False)

        self.__data = song_info
        self.__ytl = ytl

    def download(self):
        info_extractor = self.__ytl.get_info_extractor(self.__data['ie_key'])

        assert info_extractor.suitable(self.url), \
            'Info extractor is not suitable for song %s' % self.url

        ie_result = info_extractor.extract(self.url)

        self.__ytl.add_extra_info(ie_result, {'playlist': self.playlist.name})

        self.__ytl.process_video_result(ie_result, download=True)

    def info(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'copyright': self.copyrighted,
        }

    @classmethod
    def from_info(cls, info: Dict, ytl: YoutubeDL, playlist: Playlist = None):
        return cls(info, ytl, playlist)


def check(playlist):
    print('%s by %s' % (playlist.name, playlist.uploader))
    print('-' * 80)
    print('Synced songs: %d' % len(playlist.synced))

    print('Songs to remove: %d' % len(playlist.to_remove))
    for song in playlist.to_remove:
        print('\t%s' % song.title)

    print('Songs to download: %d' % len(playlist.to_download))
    for song in playlist.to_download:
        print('\t%s' % song.title)

    print('Untracked songs: %d' % len(playlist.non_tracked_songs))
    for file_name in playlist.non_tracked_songs:
        print('\t%s' % file_name)

    print('Copyrighted songs: %d (not downloaded)' % len(playlist.copyrighted))
    for song in playlist.copyrighted:
        print('\t%s' % song.title)
