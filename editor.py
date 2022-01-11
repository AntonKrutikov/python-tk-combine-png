import tkinter as tk
from tkinter import ttk
from tkinter import font
from PIL import Image
from cairosvg import svg2png
from io import BytesIO
from typing import Optional
from nft import NFT
from widget.image_viewer import ImageViewer
from widget.vscroll_frame import VerticalScrolledFrame
from trait.collection import TraitCollection, TraitCollectionState
from trait.group import TraitGroup

class Editor(tk.Tk):
    svg_options = { "default": { "width": 1080, "height": 1080 } }
    name_prefix = ""

    def __init__(self, args, **kwargs):
        tk.Tk.__init__(self, **kwargs)

        traits = TraitCollection()
        traits.load_from_file('traits.json')
        self.traits = TraitCollectionState(traits)

        self.svg_options['default']['width'] = args.svg_width
        self.svg_options['default']['height'] = args.svg_height

        self.title("Manual NFT Generator")
        self.minsize(900,600)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.image_viewer = ImageViewer(master=self, highlightthickness=1, borderwidth=1, relief="groove")
        self.image_viewer.grid(row=0, column=0, sticky='nwse')
        self.image_viewer.set_image(self.combine_image(self.traits))

        self.choice_frame = VerticalScrolledFrame(master=self, highlightthickness=1, borderwidth=1, relief="groove", width=250)
        self.choice_frame.grid(row=0,column=1, sticky='nwes')
        self.choice_frame.columnconfigure(0, weight=1)
        self.choice_frame.inner.columnconfigure(0, weight=1)
        for group in self.traits.groups:
            self.add_to_choice(group)

        self.show_viewer_button = tk.Button(text="NFT Viewer") #command binded from App
        self.show_viewer_button.grid(column=0, row=1, sticky='w', padx=10)

        self.save_button = tk.Button(master=self, text="Save" ,command=self.save)
        self.save_button.grid(row=1, column=1, sticky='nwes', pady=(5,10), padx=30)

        self.saved_info = tk.Label(master=self)
        self.saved_info.grid(row=1, column=0)

        self.recheck_states()

    def add_to_choice(self, group:TraitGroup):
        """Add selector for each traits group"""
        trait, file = self.traits.current(group)
        
        font = ('system', 12)
        font_bold = ('system', 12, 'bold')
        lbl_width = 20

        choice = tk.Frame(master=self.choice_frame.inner, name=group.name)
        choice.group = group #save ref for group instance
        choice.columnconfigure(1, weight=1)
        title = tk.Label(master=choice, text="%s" % group.name, width=lbl_width, borderwidth = 3, font=font_bold, anchor='w')
        counter = tk.Label(master=choice, font=('system', 10), foreground="#666666", name="counter_lbl")
        filename = tk.Label(master=choice, width=lbl_width, font=font, name="filename_lbl")
        self.set_text(filename, trait.name, 18)
        condition_frm = tk.Frame(master=choice, name="conditions_frm")
        exclude_frm = tk.Frame(master=choice, name="excludes_frm")
        mod_available = tk.Label(master=choice, name="mod_available_frm")
        separator=ttk.Separator(master=choice, orient='horizontal')
        prev = tk.Button(master=choice, text="<",  width=1, name="prev_btn", command=lambda: self.prev_trait(group, choice))
        next = tk.Button(master=choice, text=">", width=1, name="next_btn", command=lambda: self.next_trait(group, choice))

        title.grid(row=0, column=0, columnspan=2,  sticky="ew")
        counter.grid(row=0, column=2)
        prev.grid(row=1, column=0, sticky='e', padx=5)
        filename.grid(row=1, column=1, sticky='we')
        next.grid(row=1, column=2, sticky='w', padx=10)

        mod_available.grid(row=2, column=1, sticky='we')
        condition_frm.grid(row=3, column=1, sticky='we')
        exclude_frm.grid(row=4, column=1, sticky='we')

        separator.grid(row=5, column=0, columnspan=3, pady=(10,0), sticky="we")

        choice.grid(column=0, sticky='ew')

        self.update_counter(group)

    def set_text(self, label: tk.Label, text: str, max_chars: int = None) -> None:
        if max_chars != None and len(text) > max_chars:
            text = text[0:max_chars]+'...'
            label.configure(text=text, anchor='w')
        else:
            label.configure(text=text, anchor='center')

    def clear_frame(self, frame:tk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()
        tk.Frame(frame, height=1, width=1).pack()

    def update_counter(self, group:TraitGroup) -> None:
        total = len(group.traits)
        current, file = self.traits.current(group)
        index = group.traits.index(current)

        total_files = len(current.files)
        index_file = current.files.index(file)
        for choice in self.choice_frame.inner.winfo_children():
            if choice.group == group:
                counter:tk.Label = choice.children['counter_lbl'] 
                counter.configure(text="T:%s/%s F:%s/%s" % (index + 1, total, index_file + 1, total_files))

    def next_trait(self, group:TraitGroup, choice: tk.Frame):
        trait, file = self.traits.next(group)
        if trait is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.combine_image(self.traits))
        self.update_counter(group)
        self.recheck_states()

    def prev_trait(self, group:TraitGroup, choice: tk.Frame):
        trait, file = self.traits.prev(group)
        if trait is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.combine_image(self.traits))
        self.update_counter(group)
        self.recheck_states()

    def recheck_conditions(self):
        """Add notify frame if trait adapted or not for one or more selected trait in other groups"""
        conditions = self.traits.conditions()
        for choice in self.choice_frame.inner.winfo_children():
            condition_frm:tk.Frame = choice.children['conditions_frm'] 
            self.clear_frame(condition_frm)
            
            trait, file = self.traits.current(choice.group)
            match = conditions.get(trait, None)
            if match is not None:
                label = tk.Label(master=condition_frm, text='adapted to', font=('system italic', 12), foreground="#757575", pady=10)
                f = tk.font.Font(label, label.cget('font'))
                f.configure(slant='italic')
                label.configure(font=f)
                label.pack()

                for name,ok in match:
                    label = tk.Label(master=condition_frm, text=name, font=('system', 12), foreground="#757575")
                    if ok:
                        label['foreground'] = '#2E7D32'
                    else:
                        label['foreground'] = '#BF360C'
                    label.pack()

    def recheck_excludes(self):
        """Add notify frame if trait excludes for one or more of selected trait in other groups"""
        excludes = self.traits.excludes()
        for choice in self.choice_frame.inner.winfo_children():
            excludes_frm: tk.Frame = choice.children['excludes_frm'] 
            self.clear_frame(excludes_frm)

            trait, file = self.traits.current(choice.group)
            match = excludes.get(trait, None)
            if match is not None and any(ok for name,ok in match):
                label = tk.Label(master=excludes_frm, text='exclude', font=('system italic', 12), foreground="#757575", pady=10)
                f = tk.font.Font(label, label.cget('font'))
                f.configure(slant='italic')
                label.configure(font=f)
                label.pack()

                for name,ok in match:        
                    if ok:
                        label = tk.Label(master=excludes_frm, text=name, font=('system', 12), foreground='#BF360C')
                        label.pack()

    def recheck_adaptions(self):
        """Add notify frame to each group if modified version available for selected traits in other groups"""
        adaptions = self.traits.adaptions()
        for choice in self.choice_frame.inner.winfo_children():
            mod_available_frm: tk.Frame = choice.children['mod_available_frm'] 
            self.clear_frame(mod_available_frm)

            trait, file = self.traits.current(choice.group)
            match = adaptions.get(trait, None)
            if match is not None and any(ok for name,ok in match):
                label = tk.Label(master=mod_available_frm, text='mod available for', font=('system', 12), foreground="#BF360C", pady=10)
                label.pack()
                for name, ok in match:
                    label_cond = tk.Label(master=mod_available_frm, text=name, font=('system', 12), foreground="#757575")
                    label_cond.pack() 

    def recheck_save_button_state(self):
        """Enable or disable save button based on checks"""
        enabled = True

        conditions = self.traits.conditions()
        excludes = self.traits.excludes()
        adaptions = self.traits.adaptions()

        for _, condition in conditions.items():
            if all(not ok for _,ok in condition):
                enabled = False
        
        for _, exclude in excludes.items():
            if any(ok for _,ok in exclude):
                enabled = False

        for _, adaption in adaptions.items():
            if len(adaption) > 0:
                enabled = False
        
        if enabled:
            self.save_button.configure(state = 'normal')
        else:
            self.save_button.configure(state = 'disabled')

    def recheck_states(self):
        """Update all condiitons, excludes, adaptions and save states"""
        self.recheck_conditions()
        self.recheck_excludes()
        self.recheck_adaptions()
        self.recheck_save_button_state()
        self.saved_info.configure(text='')

    def open_image(self, file) -> Image.Image:
        """Open image or svg file and returns Image instance"""
        if file.endswith('.svg'):
            new_bites = svg2png(file_obj=open(file, "rb"), unsafe=True, write_to=None, scale=1, output_width=self.svg_options['default']['width'], output_height=self.svg_options['default']['height'])
            return Image.open(BytesIO(new_bites)).convert('RGBA')
        return Image.open(file).convert('RGBA')

    def combine_image(self, traits:TraitCollectionState) -> Optional[Image.Image]:
        """Combine resulting Image based on current selected trait and file in each group"""
        result = None
        for group in traits.groups:
                trait, files = traits.current(group)
                for file in files.paths:
                    img = self.open_image(file)
                    if result == None:
                        result = img
                        self.svg_options['default']['width'] = img.width
                        self.svg_options['default']['height'] = img.height
                    else:
                        aimg = Image.new('RGBA', result.size)
                        aimg.paste(img, (0,0))
                        result = Image.alpha_composite(result, aimg)

        return result

    def save(self):
        """Create new NFT instance and try to save it"""
        attributes = []
        order = self.traits.traits.out_order
        for group in self.traits.groups:
            trait, file = self.traits.current(group)
            if not (trait.hidden or (self.traits.traits.out_order_hide_other and group.name not in order)):
                attributes.append({"trait_type": trait.group, "value": trait.name})
 
        attributes.sort(key=lambda a: order.index(a["trait_type"]) if a["trait_type"] in order else len(order))

        nft = NFT(image=self.image_viewer.source_image, attributes=attributes)
        ok, msg = nft.save()

        self.saved_info.configure(text=msg, foreground='#BF360C' if not ok else '#000000')