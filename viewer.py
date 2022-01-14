import tkinter as tk
from tkinter import ttk
import os
from turtle import st
import widget.image_viewer as image_viewer
import widget.vscroll_frame as vscroll_frame
import json
from PIL import Image
from nft import NFT
from typing import List

default_out_path = './out'

class Viewer(tk.Tk):
    nft_list:List[NFT] = []
    nft_index:int = None

    def __init__(self, **kwargs):
        tk.Tk.__init__(self, **kwargs)

        self.nft_list = NFT.list()
        if len(self.nft_list) > 0:
            self.nft_index = 0

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
        self.nav_frame.grid(column=1, row=3, sticky='ew')
        self.nav_frame.columnconfigure(0, weight=1)
        self.nav_frame.columnconfigure(1, weight=1)
        self.nav_frame.columnconfigure(2, weight=1)

        self.prev_button = tk.Button(self.nav_frame, text='Prev', command=lambda: self.prev_item())
        self.prev_button.grid(column=0, row=0, sticky='ew')

        self.nft_counter = tk.Frame(self.nav_frame)
        self.nft_counter.grid(column=1, row=0)
        self.nft_counter.columnconfigure(0, weight=1)
        self.nft_counter.columnconfigure(2, weight=1)
        self.nft_counter_current = tk.Entry(self.nft_counter, border=0, highlightthickness=0, width=3, justify='center', disabledforeground='#222222')
        self.nft_counter_current.grid(column=0, row=0, sticky='nsew')
        self.nft_counter_current.bind('<FocusIn>', lambda e: self.nft_counter_current.select_range(0,tk.END))
        self.nft_counter_current.bind('<Button-1>', lambda e: self.nft_counter_current.configure(state='normal'))
        self.nft_counter_current.bind('<Return>', self.counter_set_current)

        tk.Label(self.nft_counter, text='/', width=1).grid(column=1, row=0)

        self.nft_counter_total = tk.Entry(self.nft_counter, border=0, highlightthickness=0, width=3, state='disabled',  justify='center', disabledforeground='#222222')
        self.nft_counter_total.grid(column=2, row=0, sticky='nsew')

        self.next_button = tk.Button(self.nav_frame, text='Next', command=lambda: self.next_item())
        self.next_button.grid(column=2, row=0, sticky='ew')


    def show_item_by_file_name(self, name=None):
        for index, nft in enumerate(self.nft_list):
            if nft.file_name == str(name):
                self.nft_index = index
                break
        self.show_item()

    def show_item(self):
        if self.nft_index is not None:
            nft = self.nft_list[self.nft_index]
            if os.path.isfile(nft.png_path):
                img = Image.open(nft.png_path)
                self.nft_viewer.set_image(img)
            else:
                print('Error: missing nft png file %s' % nft.png_path)
            self.show_item_attributes()
            self.update_counter()

    def next_item(self):
        if self.nft_index + 1 < len(self.nft_list):
            self.nft_index += 1
        else:
            self.nft_index = 0
        self.show_item()

    def prev_item(self):
        if self.nft_index - 1 >= 0:
            self.nft_index -= 1
        else:
            self.nft_index = len(self.nft_list) - 1

        self.show_item()

    def show_item_attributes(self):  
        nft = self.nft_list[self.nft_index]

        for widget in self.nft_info.inner.winfo_children():
            widget.destroy()
        # Name
        label = tk.Label(self.nft_info, text=nft.name, anchor='center', font=('system', 12, 'bold'))
        label.grid(column=0, row=0, sticky='ew', columnspan=2, pady=(0,10))
        # filename
        label = tk.Label(self.nft_info, text='(%s.png)' % nft.file_name, anchor='center', font=('system', 12, 'bold'))
        label.grid(column=0, row=1, sticky='ew', columnspan=2, pady=(0,10))

        row = 2
        for a in nft.attributes:
            label = tk.Label(self.nft_info, text=a['trait_type'], anchor='w', font=('system', 12, 'bold'))
            label.grid(column=0, row=row, sticky='ew')
            label = tk.Label(self.nft_info, text=a['value'], anchor='w', font=('system', 12))
            label.grid(column=1, row=row, sticky='ew')
            row+=1
            sep = ttk.Separator(self.nft_info)
            sep.grid(column=0, row=row, columnspan=2, sticky='ew', pady=(0,10))
            row+=1

    def update_counter(self):
        self.nft_counter_current.configure(state='normal')
        self.nft_counter_current.delete(0, tk.END)
        self.nft_counter_current.insert(0, self.nft_index + 1)
        self.nft_counter.focus_set()
        self.nft_counter_current.configure(state='disabled')
        
        self.nft_counter_total.configure(state='normal')
        self.nft_counter_total.delete(0, tk.END)
        self.nft_counter_total.insert(0, len(self.nft_list))
        self.nft_counter_total.configure(state='disabled')

    def counter_set_current(self, e):
        val = self.nft_counter_current.get()
        if not val.isnumeric() or int(val) < 1 or int(val) > len(self.nft_list):
            return
        else:
            self.nft_index = int(val) - 1
            self.show_item()

