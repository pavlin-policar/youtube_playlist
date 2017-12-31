from setuptools import setup, find_packages

MAJOR_VERSION = '0'
MINOR_VERSION = '1'
MICRO_VERSION = '0'
VERSION = "{}.{}.{}".format(MAJOR_VERSION, MINOR_VERSION, MICRO_VERSION)

setup(
    name='youtube-playlist',
    version=VERSION,
    description='Keep your youtube playlists in sync with your local fs.',
    author='Pavlin Poličar',
    author_email='pavlin.g.p@gmail.com',
    url='https://github.com/pavlin-policar/youtube_playlist',
    install_requires=[
        'youtube-dl==2017.12.23',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'youtube-playlist = youtube_playlist.__main__:main',
        ],
    },
    license='mit',
    packages=find_packages(),
)
