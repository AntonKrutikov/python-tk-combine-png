from doctest import master
import tkinter as tk
from tkinter import FLAT, PhotoImage, ttk
import os
from tkinter.messagebox import NO
from turtle import st
import widget.image_viewer as image_viewer
from widget.vscroll_frame import VerticalScrolledFrame
import json
from PIL import Image,ImageTk
from nft import NFT
from typing import List

# default_out_path = './out'

class DeleteButton(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icon= tk.PhotoImage(file='ui/delete.png', master=master)
        self.configure(image=self.icon)

class RepairButton(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icon= tk.PhotoImage(file='ui/fix.png', master=master)
        self.configure(image=self.icon)

class ShuffleNamesButton(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icon= tk.PhotoImage(file='ui/shuffle.png', master=master)
        self.configure(image=self.icon)

class ShuffleButton(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icon= tk.PhotoImage(file='ui/shuffle-bold.png', master=master)
        self.configure(image=self.icon)

class InfoFrame(VerticalScrolledFrame):
    def __init__(self, master, nft:NFT, **kwargs):
        super().__init__(master, highlightthickness=1, borderwidth=1, relief="groove", **kwargs)
        self.nft = nft

        self.inner.columnconfigure(0, weight=0)
        self.inner.columnconfigure(1, weight=1)

        nft_name_lbl = tk.Label(self, text=nft.name, anchor='center', font=('system', 12, 'bold'))
        nft_name_lbl.grid(column=1, row=0, sticky='ew', pady=(0,10))

        delete_btn = DeleteButton(self)
        delete_btn.grid(column=2, row=0, sticky='ew')
        delete_btn.bind('<Button-1>', lambda e: self.event_generate('<<Delete>>'))

        nft_filename_btn = tk.Label(self, text='(%s.png)' % nft.file_name, anchor='center', font=('system', 12, 'bold'))
        nft_filename_btn.grid(column=1, row=1, sticky='ew', pady=(0,10))

        row = 2
        for a in nft.attributes:
            if 'trait_type' in a:
                type_lbl = tk.Label(self, text="%s:" % a['trait_type'], anchor='w', font=('system', 12, 'bold'))
                type_lbl.grid(column=0, row=row, sticky='ew')

                value_lbl = tk.Label(self, text=a['value'], anchor='w', font=('system', 12))
                value_lbl.grid(column=1, row=row, sticky='ew')
                row+=1
                ttk.Separator(self).grid(column=0, row=row, columnspan=3, sticky='ew', pady=(0,10))
                row+=1

class Viewer(tk.Tk):
    nft_list:List[NFT] = []
    nft_index:int = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.nft_list = NFT.list()
        if len(self.nft_list) > 0:
            self.nft_index = 0

        self.title("NFT Viewer")
        self.minsize(900,600)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.nft_viewer = image_viewer.ImageViewer(self, highlightthickness=1, borderwidth=1, relief="groove")
        self.nft_viewer.grid(column=0, row=0, sticky='nwse')

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
        self.nft_counter_current = tk.Entry(self.nft_counter, border=0, highlightthickness=0, width=3, justify='center', disabledforeground='#222222', state='disabled')
        self.nft_counter_current.grid(column=0, row=0, sticky='nsew')
        self.nft_counter_current.bind('<FocusIn>', lambda e: self.nft_counter_current.select_range(0,tk.END))
        self.nft_counter_current.bind('<Button-1>', lambda e: self.nft_counter_current.configure(state='normal'))
        self.nft_counter_current.bind('<Return>', self.counter_set_current)

        tk.Label(self.nft_counter, text='/', width=1).grid(column=1, row=0)

        self.nft_counter_total = tk.Entry(self.nft_counter, border=0, highlightthickness=0, width=3, state='disabled',  justify='center', disabledforeground='#222222')
        self.nft_counter_total.grid(column=2, row=0, sticky='nsew')

        self.next_button = tk.Button(self.nav_frame, text='Next', command=lambda: self.next_item())
        self.next_button.grid(column=2, row=0, sticky='ew')

        self.tool_frm = tk.Frame(self)
        self.tool_frm.grid(column=0, row=3, sticky='ew', padx=10)

        self.repair_btn = RepairButton(self.tool_frm)
        self.repair_btn.grid(row=0, column=0, sticky='ew', padx=(10,0))
        self.repair_btn.bind('<Button-1>', lambda e: self.repair())
        tk.Label(self.tool_frm, text='repair', anchor='center').grid(row=1, column=0, padx=(10,0))

        shuffle_names_btn = ShuffleNamesButton(self.tool_frm)
        shuffle_names_btn.grid(column=1, row=0, sticky='ew', padx=(10,0))
        shuffle_names_btn.bind('<Button-1>', lambda e: self.shuffle_names())
        tk.Label(self.tool_frm, text='shuffle names', anchor='center').grid(row=1, column=1, padx=(10,0))


        shuffle_names_btn = ShuffleButton(self.tool_frm)
        shuffle_names_btn.grid(column=2, row=0, sticky='ew', padx=(10,0))
        shuffle_names_btn.bind('<Button-1>', lambda e: self.shuffle())
        tk.Label(self.tool_frm, text='shuffle all', anchor='center').grid(row=1, column=2, padx=(10,0))


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

        info = InfoFrame(self, nft = nft)
        info.bind('<<Delete>>', lambda e: self.delete_item(nft))
        info.grid(column=1, row=0, sticky='nwse')

    def delete_item(self, nft:NFT):
        nft.delete()
        self.nft_list.remove(nft)
        if len(self.nft_list) == 0:
            tk.Frame(self).grid(column=1, row=0, sticky='nwse')
            self.nft_index = -1
            self.nft_viewer.set_image(None)
        else:
            self.prev_item()
        self.update_counter()

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

    def repair(self):
        self.nft_list = NFT.repair()
        self.nft_index = 0
        self.show_item()

    def shuffle_names(self):
        self.nft_list = NFT.shuffle_names()
        self.nft_index = 0
        self.show_item()

    def shuffle(self):
        self.nft_list = NFT.shuffle()
        self.nft_index = 0
        self.show_item()

