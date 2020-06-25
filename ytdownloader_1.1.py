#! python3
"""
GUI : Downloads YouTube video or audio dependent on user parameters
from a list of available resolutions and formats.
"""
import os, sys, subprocess
import tkinter as tk
import threading
import time
from tkinter import filedialog
from tkinter import StringVar
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import ttk
from pytube import YouTube

# pyinstaller --onefile -n YTDownloader --windowed --icon=logo.ico ytdownloader_1.1.py
# For some reason the icon doesn't work, might need to remove this command when compiling

# Currently requires ffmpeg to be installed
# TODO ffmpeg -i cpv.mp4 -i cpa.mp4 -c:v copy -c:a aac av.mp4
# TODO find python module way of muxing audio stream as to not require users to install ffmpeg
# TODO can include ffmpeg in directory?


class YTDownloader():
    def __init__(self):
        # Attributes
        self.yt = None
        self.filesize = None
        self.choice = None
        self.options = None
        self.codec = None
        self.video_lists = []
        self.audio_lists = []
        self.outpath = 'C:' + os.environ["HOMEPATH"] + '\\Desktop'
        
        # Combo box content initialize
        self.vtype_list = []
        self.atype_list = []
        self.res_list = []
        self.abr_list = []
        self.fps_list = []
        self.acodec_list = []

        # Window
        self.window = tk.Tk()
        self.window.title('YouTube Downloader')
        self.window.geometry('480x230')

        # Labels
        url_label = tk.Label(self.window, text='YouTube URL', height=2, width=12)
        url_label.grid(row=0, column=0, pady=5, sticky='E')
        self.title_label = tk.Label(self.window)
        self.title_label.grid(column=0, row=3, columnspan=6)
        outpath_label = tk.Label(self.window, text='Outpath', height=2, width=12)
        outpath_label.grid(row=5, column=0, sticky='E')

        # Progress bar
        self.progressbar = ttk.Progressbar(self.window, orient='horizontal', length=460, mode='determinate')
        self.progressbar.grid(row=6, column=0, columnspan=7, padx=10, pady=10)
        self.progressbar['value'] = 0
        self.progressbar['maximum'] = 100
        self.load_percent = tk.Label(self.window, text='', bg='#E6E6E6', font=('Arial', 8)) # TODO Transparent 
        self.load_percent.grid(row=6, column=0, columnspan=7)
        
        # Entry box
        self.url_box = tk.Entry(self.window, width=50)
        self.url_box.grid(column=1, row=0, columnspan=4, pady=5, sticky='W')
        self.out_box = Entry(self.window, width=50)
        self.out_box.grid(column=1, row=5, columnspan=4, sticky='W')
        self.out_box.insert(0, self.outpath)
        
        # Buttons
        load_button = tk.Button(self.window, text='Load', command=self.load_click, width=7)
        load_button.grid(column=4, row=0, pady=5, padx=5, sticky='E')
        browse_button = tk.Button(self.window, text='Browse', command=self.browse_click, width=7)
        browse_button.grid(column=4, row=5, padx=5, sticky='E')
        download_button = tk.Button(self.window, text='Download', command=self.dl_click)
        download_button.grid(column=0, row=8, columnspan=10, pady=2)
        
        # Radio buttons
        self.av_rad = tk.IntVar()
        self.av_rad.set(1)
        vid_rad = tk.Radiobutton(self.window, text='Video', variable=self.av_rad, value=1, command=self.__rad_selected__)
        vid_rad.grid(column=0, row=4, padx=10, pady=10)
        aud_rad = tk.Radiobutton(self.window, text='Audio', variable=self.av_rad, value=2, command=self.__rad_selected__)
        aud_rad.grid(column=1, row=4)
        
        # Combo box setup
        self.type_combo = Combobox(self.window, width=10)
        self.type_combo.grid(column=2, row=4, padx=10)
        self.type_combo['values'] = ('Type')
        self.type_combo.current(0)
        self.res_combo = Combobox(self.window, width=10)
        self.res_combo.grid(column=3, row=4, padx=10)
        self.res_combo['values'] = ('Resolution')
        self.res_combo.current(0)
        self.fps_combo = Combobox(self.window, width=10)
        self.fps_combo.grid(column=4, row=4, padx=10)
        self.fps_combo['values'] = ('FPS')
        self.fps_combo.current(0)

    def load_click(self):
        # Issue with clearing the old title when reloading a URL. Setting a blank string or using
        # the .destroy() or .grid_remove() methods and recreating the Label does not work, neither
        # does using a StringVar as the textvariable. Instead I opted to overwrite with a buncha blank.
        # Do not like this method but I have spent way too many hours on this issue, and this is less
        # resource intensive than other methods.
        self.title_label.config(text='                                                                   Loading...                                                                     ')
        self.title_label.update_idletasks()

        # Ensure proper URL
        link = self.url_box.get() # Doesn't reload without calling .get() again
        if not (link.startswith('https://youtu.be') or link.startswith('https://www.youtube.com')):
            self.url_box.configure(text='')
            self.title_label.config(text='')
            messagebox.showinfo('Incorrect URL', 'Please enter a valid YouTube URL.')
            return
        
        # Get metadata
        try:
            self.yt = YouTube(link)
        except Exception as e:
            self.reset_values()
            messagebox.showinfo('Could Not Load Data', f'Source could not be loaded due to copyright incription. Error : {e}')
            return
        title = self.yt.title
        # The title 'YouTube' is returned when pytube doesn't fetch the title correctly.
        # Fetching the metadata again usually corrects this
        for attempt in range(10):
            if attempt > 9:
                messagebox.showinfo('Connection Timeout', 'Could not fetch title. Try loading content again.')
                return
            if title == 'YouTube':
                link = self.url_box.get() # Doesn't reload without calling .get() again
                self.yt = YouTube(link)
                title = self.yt.title
            else:
                break

        # If title is too long, shorten and add elipses
        if len(title) > 75:
            title = title[:75] + '...'
        self.title_label.config(text=title)
        streams = list(self.yt.streams)
        self.options = options_dict(streams)
        
        # Create Combobox lists
        self.vtype_list = []
        self.atype_list = []
        type_list = combo_list(self.options, 'mime_type')
        for lst in type_list:
            if lst.startswith('video'):
                self.vtype_list.append(lst)
            else:
                self.atype_list.append(lst)
        res_list = combo_list(self.options, 'res')
        self.res_list = sort_best_resolution(res_list, 'p')
        abr_list = combo_list(self.options, 'abr')
        self.abr_list = sort_best_resolution(abr_list, 'kbps')
        self.fps_list = combo_list(self.options, 'fps')
        self.acodec_list = combo_list(self.options, 'acodec')
        self.video_lists = [self.vtype_list, self.res_list, self.fps_list]
        self.audio_lists = [self.atype_list, self.abr_list, self.acodec_list]
        
        # Populate combo boxes based on radio button selection
        self.__rad_selected__()

    def __rad_selected__(self):
        # Check which radio button is selected and populate combo boxes
        if self.av_rad.get() == 2:
            self.__set_combo__(self.audio_lists)
        else:
            self.__set_combo__(self.video_lists)

    def __set_combo__(self, avlist):
        # Set items in combo boxes using a list of 3 lists depending on radio button selection
        self.type_combo['values'] = avlist[0]
        self.type_combo.current(0)

        self.res_combo['values'] = avlist[1]
        self.res_combo.current(0)
        
        self.fps_combo['values'] = avlist[2]
        self.fps_combo.current(0)
        
    def browse_click(self):
        # Open the file browser
        self.outpath = filedialog.askdirectory(initialdir=self.outpath, title='Select a directory')
        self.outpath = self.outpath.replace('/', '\\')
        self.__update_out_box__()

    def __update_out_box__(self):
        # Text in the out_box Entry box
        self.out_box.delete(0, 'end')
        self.out_box.insert(0, self.outpath)

    def dl_click(self):
        # Find correct download option
        mime = self.type_combo.get()
        res = self.res_combo.get()
        fps = self.fps_combo.get()
        av = self.av_rad.get()
        self.codec = mime.split('/')[1]
        
        # Compare stream options with combo_box choices
        for option in self.options:
            if option['mime_type'] == mime:
                if av == 1: # Video radio button selected
                    if option['res'] == res:
                        if option['fps'] == fps:
                           self.choice = self.options.index(option)
                else: # Audio radio button selected
                    if option['abr'] == res:
                        if option['acodec'] == fps:
                            self.choice = self.options.index(option)
        if self.choice is None:
            messagebox.showinfo('Option Not Found', 'Quality option not available. Please select a different, type, resolution and fps combinitaion.')
        else:
            # Download video
            self.filesize = self.yt.streams[self.choice].filesize
            threading.Thread(target=self.yt.register_on_progress_callback(self.__show_progress_bar__)).start()
            threading.Thread(target=self.download_video).start()

    def __show_progress_bar__(self, stream=None, chunk=None, bytes_remaining=None):
        # Progress bar
        progInt = int(100 - (100*(bytes_remaining/self.filesize)))
        progress = str(progInt) + '%'
        self.progressbar['value'] = progInt
        self.load_percent.config(text=progress)
        #print(f'Downloading... {progress}', end='\r', flush=True)

    def __reset_progress_bar__(self):
        self.progressbar['value'] = 0
        self.load_percent.config(text='')
    
    def download_video(self):
        try:
            self.yt.streams[self.choice].download(self.outpath)
            #print('Downloading... Done')
            self.load_percent.config(text='Complete')
            time.sleep(1)
            self.__reset_progress_bar__()
            if self.check_audio() is False:
                self.download_audio()
        except Exception as e:
            messagebox.showinfo('Download Error', f'Failed to download. {e}')    

    def check_audio(self):
        # Checks if the downloaded video contains an audio track, returns boolean
        cmd = 'ffprobe -i "' + self.outpath + '\\' + self.yt.title + '.' + self.codec + '" -show_streams -select_streams a -loglevel error'
        audio_present = os.popen(cmd).read()
        if audio_present != '':
            return True
        else:
            print('\nNo audio present in video file.')
            return False

    def download_audio(self):
        # Find audio stream
        self.load_percent.config(text='Downloading audio')
        time.sleep(1)
        choice = None
        for stream in self.options:
            try:
                if stream['mime_type'] == 'audio/mp4' and stream['acodec'].startswith('mp4a'):
                    choice = self.options.index(stream)
            except IndexError:
                continue
        if choice is None:
            sys.exit('\nCould not find audio file for muxing.')
        else:
            # Download audio
            #print('Downloading audio...')
            self.__reset_progress_bar__()
            self.yt.streams[choice].download(filename='_missing_audio')
            self.mux_av()
            self.load_percent.config(text='Complete')
            time.sleep(1)
            self.__reset_progress_bar__()

    def mux_av(self):
        # Create temp vid file
        #print('Muxing audio...')
        if os.path.isfile(self.outpath + '\\_video_no_audio.mp4'):
            os.remove(self.outpath + '\\_video_no_audio.mp4')
        vidfile = self.yt.title + '.' + self.codec
        os.rename(r'' + self.outpath + '\\' + vidfile, r''+ self.outpath + '\\_video_no_audio.mp4')
        
        # Mux the temp video and audio files
        cmd = 'ffmpeg -i "' + self.outpath + '\\_video_no_audio.mp4" -i _missing_audio.mp4 -c:v copy -c:a aac "' + self.outpath + '\\' + vidfile + '"'
        FNULL = open(os.devnull, 'w') # Supress console output of ffmpeg module
        subprocess.call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
        
        # Remove temp files
        os.remove(self.outpath + '\\_video_no_audio.mp4')
        os.remove('_missing_audio.mp4')
        #print('Done')

def options_dict(stream_list):
    # Create a list of dicts from stream items string
    op_list = []
    for stream in stream_list:
        stream = str(stream)[9:] # Remove the word 'Stream:' from the string
        stream = stream[:-1]
        stream = stream.replace('"', '')
        op_dict = dict(x.split('=') for x in stream.split(' '))
        op_list.append(op_dict)
    return op_list

def sort_best_resolution(reslist, suffix):
    # Sort resolution by highest number
    intlist = []
    strlist = []
    for res in reslist:
        if res != 'None':
            resInt = int(res.split(suffix)[0])
            intlist.append(resInt)
    intlist.sort(reverse=True)
    for num in intlist:
        resStr = str(num) + suffix
        strlist.append(resStr)
    return strlist

def combo_list(dct, key):
    # Create a list of items from dict key
    t_list = []
    for option in dct:
        try:
            item = option[key]
            if item not in t_list: # No duplicates
                t_list.append(item)
        except KeyError:
            pass
    return t_list


if __name__ == '__main__':
    app = YTDownloader()
    app.window.mainloop()
