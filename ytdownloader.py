#! python3


import os, sys
import tkinter as tk
from pytube import YouTube

OUTPATH = 'C:' + os.environ["HOMEPATH"] + '\\Desktop'

# TODO add gui

def main():
    link = get_inputs()
    yt = YouTube(link)
     
    print(yt.title)
    streams = list(yt.streams)
    # op_list = options_dict(streams) # for future gui options
    choice = choose_download(streams)
    download_video(yt, choice)
    print('\nDone')

def get_inputs():
    # Ensure proprt inputs
    try:
        link = sys.argv[1]
        if not link.startswith('https://www.youtu'):
            sys.exit('Please enter a vailid YouTube URL')
    except:
        sys.exit('Missing YouTube URL.')
    return link

def replace_all(text, dic):
    # Replaces (key) text in a string with dic items
    for i, j in dic.items():
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
    while choice not in range(len(options_list)-1) or choice != 'exit':
        print(f'Please enter a value between 0 and {len(streams)-1}')
        try:
            choice = input('Which stream to download? ')
            if choice == 'exit':
                sys.exit()
            choice = int(choice)
            return choice
        except:
            continue
    return None

def on_progress(stream, chunk, bytes_remaining):
    # Progress bar
    size = stream.filesize
    bytes_downloaded = size - bytes_remaining
    perc_completed = bytes_downloaded / size * 100
    print(f'Downloading \'{stream.title}\'... {round(perc_completed)}%', end='\r', flush=True)

def download_video(ytobj, choice):
    try:
        ytobj.register_on_progress_callback(on_progress) # Progress bar
        ytobj.streams[choice].download(OUTPATH)

    except Exception as e:
        print(f'Connection Error: {e}')

def create_gui(text):
    window = tk.Tk()
    window.title('YouTube Downloader')
    label = tk.Label(window, text=text)
    window.mainloop()

if __name__ == '__main__':
    main()

