#! python3

""" 
Downloads youtube video form a list of stream optioans
Muxes audio stream when video stream contains no audio
"""

import os, sys, subprocess, time
from pytube import YouTube


HELP = 'Usage: ytdownloader <YouTube URL>'
OUTPATH = 'C:' + os.environ["HOMEPATH"] + '\\Desktop'

# TODO Refactor as class

def main():
    link = get_inputs()
    try:
        print('Loading...')
        yt = YouTube(link)
        if yt.title == 'YouTube':
            while yt.title == 'YouTube':
                yt = YouTube(link)
    except KeyError:
        sys.exit(f'\nError: video could not be extracted due to copyright encryption.')
    title = yt.title
    print(f'\n{title}')
    streams = list(yt.streams)
    choice = choose_download(streams)
    global PROCESS 
    PROCESS = (f'Downloading \'{title}\'... ')
    download_video(yt, choice)
    if check_audio(title + '.mp4') is False:
        options = options_dict(streams)
        PROCESS = 'Downloading audio file... ' 
        download_audio(yt, options)
        print('\nMuxing audio...')
        mux_av(title + '.mp4')
    print('Done')
    
def get_inputs():
    # Ensure proper inputs
    try:
        link = sys.argv[1]
        if link.lower() == 'help':
            sys.exit(HELP)
        if not (link.startswith('https://www.youtu') or link.startswith('https://youtu')):
            sys.exit(f'Please enter a valid YouTube URL.\n{HELP}')
    except IndexError:
        sys.exit(f'Missing YouTube URL.\n{HELP}')
    return link

def replace_all(text, dct):
    # Replaces (key) text in a string with dct items
    for i, j in dct.items():
        text = text.replace(i, j)
    return text

def options_dict(stream_list):
    # Create a list of dicts from stream items string
    op_list = []
    for stream in stream_list:
        stream = str(stream)[9:]
        stream = stream[:-1]
        stream = stream.replace('"', '')
        op_dict = dict(x.split('=') for x in stream.split(' '))
        op_list.append(op_dict)
    return op_list

def choose_download(streams):
    # Formats stream info to be more redable
    replacements = {'mime_type=': '- Type : ', 'res=': '  Resolution : ', 'fps=': '  FPS : ', 'vcodec=': '  Codec : ', 'acodec=': '  Codec : ', 'abr=': '  SampleRate : ', 'progressive="False"':'', 'progressive="True"':'', 'type=':'  A/V : '}
    options_list = []
    stream_list = []
    for counter, stream in enumerate(streams):
        stream_list = str(stream).split()
        del stream_list[:2]
        stream_list.insert(0, counter)
        stream = '{0:>2} {1:<25} {2:15} {3:15}'.format(*stream_list)
        option = replace_all(str(stream), replacements)
        options_list.append(option)
    # Print options
    print('\nChoose a download quality from the following options:')
    for option in options_list:
        print(option)
    print('Type \'exit\' to exit.\n')
    choice = None
    # Choose download option
    while choice not in range(len(options_list)-1):
        print(f'Please enter a value between 0 and {len(streams)-1}')
        try:
            choice = input('Which stream to download? ')
            choice = int(choice)
        except:
            if choice == 'exit':
                sys.exit()
            continue
    return choice

def on_progress(stream, chunk, bytes_remaining):
    # Progress bar
    size = stream.filesize
    bytes_downloaded = size - bytes_remaining
    perc_completed = bytes_downloaded / size * 100
    print(f'{PROCESS}{round(perc_completed)}%', end='\r', flush=True)

def download_video(ytobj, choice):
    try:
        ytobj.register_on_progress_callback(on_progress) # Progress bar
        ytobj.streams[choice].download(OUTPATH)
    except Exception as e:
        print(f'Connection Error: {e}')
    return

def check_audio(filename):
    # Checks if the downloaded video contains an audio track, returns boolean
    cmd = 'ffprobe -i "' + OUTPATH + '\\' + filename + '" -show_streams -select_streams a -loglevel error'
    audio_present = os.popen(cmd).read()
    if audio_present != '':
        return True
    print('\nNo audio present in video file.')
    return False

def download_audio(ytobj, stream_list):
    # Find audio stream
    choice = None
    for stream in stream_list:
        try:
            if stream['mime_type'] == 'audio/mp4' and stream['acodec'].startswith('mp4a'):
                choice = stream_list.index(stream)
        except IndexError:
            continue
    if choice is None:
        sys.exit('\nCould not find audio file for muxing.')
    else:
        # Download audio
        ytobj.streams[choice].download(filename='_missing_audio')
    return

def mux_av(vidfile):
    # Create temp vid file
    if os.path.isfile(OUTPATH + '\\_video_no_audio.mp4'):
        os.remove(OUTPATH + '\\_video_no_audio.mp4')
    os.rename(r'' + OUTPATH + '\\' + vidfile, r''+ OUTPATH + '\\_video_no_audio.mp4')
    
    # Mux the temp video and audio files
    cmd = 'ffmpeg -i "' + OUTPATH + '\\_video_no_audio.mp4" -i _missing_audio.mp4 -c:v copy -c:a aac "' + OUTPATH + '\\' + vidfile + '"'
    FNULL = open(os.devnull, 'w') # Supress console output of ffmpeg module
    subprocess.call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
    
    # Remove temp files
    os.remove(OUTPATH + '\\_video_no_audio.mp4')
    os.remove('_missing_audio.mp4')
    return

if __name__ == '__main__':
    main()