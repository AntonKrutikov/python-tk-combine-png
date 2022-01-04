import tkinter as tk
from tkinter import ttk
import os
import widget.image_viewer as image_viewer
import widget.vscroll_frame as vscroll_frame
import json
from PIL import Image

default_out_path = './out'

class Viewer(tk.Tk):
    current_file_name = None
    current_file_indx = None
    file_list = []

    def __init__(self, **kwargs):
        tk.Tk.__init__(self, **kwargs)

        self.load_file_list()

        self.title("NFT Viewer")
        self.minsize(900,600)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.nft_viewer = image_viewer.ImageViewer(self, highlightthickness=1, borderwidth=1, relief="groove")
        self.nft_viewer.grid(column=0, row=0, sticky='nwse')

        self.nft_info = vscroll_frame.VerticalScrolledFrame(self, highlightthickness=1, borderwidth=1, relief="groove")
        self.nft_info.grid(column=1, row=0, sticky='nwse')
        self.nft_info.inner.columnconfigure(0, weight=1)
        self.nft_info.inner.columnconfigure(1, weight=1)

        self.nav_frame = tk.Frame(self, pady=10)
        self.nav_frame.grid(column=1, row=2, sticky='ew')
        self.nav_frame.columnconfigure(0, weight=1)
        self.nav_frame.columnconfigure(1, weight=1)

        self.prev_button = tk.Button(self.nav_frame, text='Prev', state='disabled', command=lambda: self.show_prev_item())
        self.prev_button.grid(column=0, row=0, sticky='ew')
        self.has_prev_item()
        self.next_button = tk.Button(self.nav_frame, text='Next', state='disabled', command=lambda: self.show_next_item())
        self.next_button.grid(column=1, row=0, sticky='ew')
        self.has_next_item()
        
    def load_file_list(self, path = default_out_path):
        self.file_list = ["%s/%s" % (path, f) for f in os.listdir(path) if f.endswith('.json')]
        self.file_list.sort(reverse=True)
        if len(self.file_list) > 0:
            self.current_file_name = self.file_list[0]
            self.current_file_indx = 0

    def find_file_by_name(self, name):
        for f in self.file_list:
            if "%s/%s.json" % (default_out_path, name) == f:
                return f
        return None

    def show_item_by_name(self, name=None):
        indx = None
        if (name == None or name == -1) and self.current_file_indx != None:
            indx = self.current_file_indx
        else:
            json_file = self.find_file_by_name(name)
            if json_file == None:
                print("Error: File not found '%s.json' in '%s'" % (name, default_out_path))
                exit() #TODO: hard exit...
            indx = self.file_list.index(json_file)
        self.show_item(indx)

    def show_item(self, indx):
        json_file = self.file_list[indx]
        with open(json_file) as f:
            info = json.load(f)
            if 'name' in info:
                png_path = "%s.png" % json_file.rsplit('.', 1)[0]
                if os.path.isfile(png_path):
                    img = Image.open(png_path)
                    self.nft_viewer.set_image(img)
            if 'attributes' in info:
                self.load_item_attributes(info, png_path)

    def has_next_item(self):
        indx = self.current_file_indx + 1
        if indx < len(self.file_list):
            self.next_button['state'] = 'normal'
            return True
        self.next_button['state'] = 'disabled'
        return False

    def has_prev_item(self):
        indx = self.current_file_indx - 1
        if indx >= 0:
            self.prev_button['state'] = 'normal'
            return True
        self.prev_button['state'] = 'disabled'
        return False

    def show_next_item(self):
        self.current_file_indx += 1
        self.show_item(self.current_file_indx)
        self.has_next_item()
        self.has_prev_item()


    def show_prev_item(self):
        self.current_file_indx -= 1
        self.show_item(self.current_file_indx)
        self.has_prev_item()
        self.has_next_item()

    def load_item_attributes(self, info, filename):  
        for widget in self.nft_info.inner.winfo_children():
            widget.destroy()
        # Name
        label = tk.Label(self.nft_info, text=info['name'], anchor='center', font=('system', 12, 'bold'))
        label.grid(column=0, row=0, sticky='ew', columnspan=2, pady=(0,10))
        # filename
        label = tk.Label(self.nft_info, text='(%s)' % filename, anchor='center', font=('system', 12, 'bold'))
        label.grid(column=0, row=1, sticky='ew', columnspan=2, pady=(0,10))
        if 'attributes' in info and isinstance(info['attributes'], list):
            row = 2
            for a in info['attributes']:
                label = tk.Label(self.nft_info, text=a['trait_type'], anchor='w', font=('system', 12, 'bold'))
                label.grid(column=0, row=row, sticky='ew')
                label = tk.Label(self.nft_info, text=a['value'], anchor='w', font=('system', 12))
                label.grid(column=1, row=row, sticky='ew')
                row+=1
                sep = ttk.Separator(self.nft_info)
                sep.grid(column=0, row=row, columnspan=2, sticky='ew', pady=(0,10))
                row+=1

