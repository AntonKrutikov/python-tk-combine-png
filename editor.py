import tkinter as tk
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
from cairosvg import svg2png
from io import BytesIO
from typing import Optional
import os
import json
import traits
from widget.image_viewer import ImageViewer
from widget.vscroll_frame import VerticalScrolledFrame
from trait.collection import TraitCollection, TraitCollectionState
from trait.group import TraitGroup

class Editor(tk.Tk):
    svg_options = { "default": { "width": 1080, "height": 1080 } }
    name_prefix = ""

    def __init__(self, args, **kwargs):
        tk.Tk.__init__(self, **kwargs)

        self.load_traits('traits.json')
        self.load_blueprint_template(args.blueprint)

        self.svg_options['default']['width'] = args.svg_width
        self.svg_options['default']['height'] = args.svg_height
        self.name_prefix = args.nft_name_prefix

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
    
    def load_traits(self, file):
        traits = TraitCollection()
        traits.load_from_file(file)
        self.traits = TraitCollectionState(traits)

    def load_blueprint_template(self, file):
        with open(file) as json_file:
            self.blueprint_template = json.load(json_file)

    def add_to_choice(self, group:TraitGroup):
        trait, file = self.traits.current(group)
        
        font = ('system', 12)
        font_bold = ('system', 12, 'bold')
        lbl_width = 20

        choice = tk.Frame(master=self.choice_frame.inner, name=group.name)
        choice.group = group #save ref for group instance
        choice.columnconfigure(1, weight=1)
        title = tk.Label(master=choice, text="%s" % group.name, width=lbl_width, borderwidth = 3, font=font_bold, anchor='w')
        filename = tk.Label(master=choice, width=lbl_width, font=font, name="filename_lbl")
        self.set_text(filename, trait.name, 18)
        condition_frm = tk.Frame(master=choice, name="conditions_frm")
        exclude_frm = tk.Frame(master=choice, name="excludes_frm")
        mod_available = tk.Label(master=choice, name="mod_available_frm")
        separator=ttk.Separator(master=choice, orient='horizontal')
        prev = tk.Button(master=choice, text="<",  width=1, name="prev_btn", command=lambda: self.prev_trait(group, choice))
        next = tk.Button(master=choice, text=">", width=1, name="next_btn", command=lambda: self.next_trait(group, choice))

        title.grid(row=0, column=0, columnspan=3, sticky="ew")
        prev.grid(row=1, column=0, sticky='e', padx=5)
        filename.grid(row=1, column=1, sticky='we')
        next.grid(row=1, column=2, sticky='w', padx=10)

        mod_available.grid(row=2, column=1, sticky='we')
        condition_frm.grid(row=3, column=1, sticky='we')
        exclude_frm.grid(row=4, column=1, sticky='we')

        separator.grid(row=5, column=0, columnspan=3, pady=(10,0), sticky="we")

        choice.grid(column=0, sticky='ew')

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


    # def next_trait_index(self, trait) -> Optional[int]:
    #     indx = trait['traits'].index(trait['current']) + 1
    #     if indx < len(trait['traits']):
    #         return indx
    #     return 0

    # def prev_trait_index(self, trait) -> Optional[int]:
    #     indx = trait['traits'].index(trait['current']) - 1
    #     if indx >= 0:
    #         return indx
    #     return -1

    def next_trait(self, group:TraitGroup, choice: tk.Frame):
        trait, file = self.traits.next(group)
        if trait is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.combine_image(self.traits))
        self.recheck_states()
        # indx = self.next_trait_index(trait)
        # if indx != None:
        #     trait['current'] = trait['traits'][indx]
        #     self.set_text(choice.children['filename_lbl'], trait['current']['title'])
        #     self.image_viewer.set_image(self.combine_image(self.traits))
        #     self.recheck_states()

        # if self.prev_trait_index(trait) != None:
        #     choice.children['prev_btn'].configure(state='normal')
        # if self.next_trait_index(trait) == None:
        #     choice.children['next_btn'].configure(state='disabled')

    
    def prev_trait(self, group:TraitGroup, choice: tk.Frame):
        trait, file = self.traits.prev(group)
        if trait is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.combine_image(self.traits))
        self.recheck_states()
        # indx = self.prev_trait_index(trait)
        # if indx != None:
        #     trait['current'] = trait['traits'][indx]
        #     self.set_text(choice.children['filename_lbl'], trait['current']['title'])
        #     self.image_viewer.set_image(self.combine_image(self.traits))
        #     self.recheck_states()

        # if self.next_trait_index(trait) != None:
        #     choice.children['next_btn'].configure(state='normal')
        # if self.prev_trait_index(trait) == None:
        #     choice.children['prev_btn'].configure(state='disabled')


    def recheck_conditions(self):
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

    def recheck_mod_available(self):
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
        enabled = True

        conditions = self.traits.conditions()
        excludes = self.traits.excludes()
        adaptions = self.traits.adaptions()

        for _, condition in conditions.items():
            if any(not ok for _,ok in condition):
                enabled = False
        
        for _, exclude in excludes.items():
            if any(ok for _,ok in exclude):
                print("EXCLUDED")
                enabled = False

        for _, adaption in adaptions.items():
            if len(adaption)>0:
                enabled = False
        
        if enabled:
            self.save_button.configure(state = 'normal')
        else:
            self.save_button.configure(state = 'disabled')
        # for trait in self.traits:
        #     if 'current' in trait:
        #         current = trait['current']
        #         if 'exclude' in current and traits.check_exclude(current['exclude'], self.traits):
        #             excluded = True
        #         if 'adapted-to' in current and not traits.check_condition(current['adapted-to'], self.traits):
        #             not_adapted = True
        #         ok, adapted = traits.check_adapted_exists(current, trait, self.traits)
        #         if ok:
        #             adapted_exists = True
        # if excluded or not_adapted or adapted_exists:
        #     self.save_button.configure(state = 'disabled')
        # else:
        #     self.save_button.configure(state = 'normal')

    def recheck_states(self):
        pass
        self.recheck_conditions()
        self.recheck_excludes()
        self.recheck_mod_available()
        self.recheck_save_button_state()
        # self.saved_info.configure(text='')

    def open_image(self, file) -> Image.Image:
        if file.endswith('.svg'):
            new_bites = svg2png(file_obj=open(file, "rb"), unsafe=True, write_to=None, scale=1, output_width=self.svg_options['default']['width'], output_height=self.svg_options['default']['height'])
            return Image.open(BytesIO(new_bites)).convert('RGBA')
        return Image.open(file).convert('RGBA')

    def combine_image(self, traits:TraitCollectionState) -> Optional[Image.Image]:
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

    def out_file_list(self):
        """Return png file list from out folder with numeric names, sorted desc"""

        files = [f for f in os.listdir("./out") if f.endswith('.png') and not f.endswith('.min.png')]
        return sorted(files, key=lambda x:int(x.split('.')[0]) if x.split('.')[0].isdigit() else -1, reverse=True)

    def next_out_file_index(self):
        list = self.out_file_list()
        if len(list) == 0:
            return 1
        else:
            last = list[0]
            indx = int(last.split('.')[0])
            return indx + 1
    
    def save(self):
        file_index = self.next_out_file_index()

        img = self.image_viewer.source_image
        img.save('./out/%s.png' % file_index)
        optimized = img.convert('P')
        optimized.save('./out/%s.min.png' % file_index)

        self.blueprint_template['name'] = "%s%s" % (self.name_prefix, file_index)
        self.blueprint_template['attributes'] = []
        traits = []
        for trait in self.traits:
            if 'current' in trait:
                data = trait.copy()
                data.pop('files', None)
                traits.append(data)
            self.blueprint_template['attributes'].append({"trait_type": trait['group'], "value": trait['current']['title']})

        with open('./out/%s.json' % file_index, 'w') as outfile:
            json.dump(self.blueprint_template, outfile)

        self.saved_info.configure(text='File saved to ./out/%s.png' % file_index)