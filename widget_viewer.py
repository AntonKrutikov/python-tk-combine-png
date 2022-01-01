import tkinter as tk
from tkinter import ttk
from tkinter.constants import NO
from PIL import Image, ImageTk


class Viewer(tk.Frame):
    """
    Viewer provide Frame with Canvas, ScrollBars and Options to display Images
    """
    source_image: Image.Image
    source_photo_image: ImageTk.PhotoImage

    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master=master, **kwargs)

        self.canvas = tk.Canvas(self)
        self.canvas.bind('<Configure>', lambda e: self.on_canvas_resize(e))

        self.canvas_fit_image = tk.BooleanVar(master=self)
        self.canvas_fit_image.set(True)

        self.cb_fit_image = tk.Checkbutton(self, text='Fit image', onvalue=True, offvalue=False, var=self.canvas_fit_image, command=self.on_cb_fit_image_changed)
        
        separator = ttk.Separator(self)

        self.scroll_x = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.cb_fit_image.grid(row=0, column=0, sticky='nw')
        separator.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.canvas.grid(row=2, column=0, sticky='nwse')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    
    def set_image(self, img: Image.Image):
        self.source_image = img
        self.canvas_image_resize()
    
    def on_cb_fit_image_changed(self):
        self.canvas_image_resize()

    def on_canvas_resize(self, event):
        self.canvas_image_resize()

    def canvas_image_resize(self):
        """
        Resize image inside canvas based on screen size or fit option
        """ 
        if not hasattr(self,'source_image'):
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        ratio = 1
        img_width, img_height = self.source_image.size
        
        if canvas_width > 1 and img_width > img_height:
            ratio = canvas_width / img_width
        elif canvas_height > 1 and img_height > img_width:
            ratio = canvas_height / img_height

        if self.canvas_fit_image.get() == True:
            img_width = int(ratio * img_width)
            img_height = int(ratio * img_height)
            fit_img = self.source_image.resize((img_width, img_height))
            self.source_photo_image = ImageTk.PhotoImage(fit_img, master=self)
            self.canvas.delete('source_img')
            self.canvas.create_image(canvas_width/2,canvas_height/2, image=self.source_photo_image, tag='source_img')
            self.canvas.configure(scrollregion=[0, 0, canvas_width, canvas_height])
            self.scroll_x.grid_remove()
            self.scroll_y.grid_remove()
        else:
            self.source_photo_image = ImageTk.PhotoImage(self.source_image, master=self)
            x = 0
            y = 0
            if canvas_width>img_width:
                x = (canvas_width - img_width) / 2
            if canvas_height>img_height:
                y = (canvas_height - img_height) /2
            self.canvas.create_image(x,y, image=self.source_photo_image, tag='source_img')
            self.canvas.configure(scrollregion=[-img_width/2,-img_height/2,img_width/2, img_height/2])
            self.canvas.yview_moveto('0')
            self.canvas.xview_moveto('0')
            self.scroll_x.grid(row=3,column=0, sticky='ew')
            self.scroll_y.grid(row=2,column=1, sticky='ns')