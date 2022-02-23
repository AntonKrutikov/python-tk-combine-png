import tkinter as tk

from typing import List
from tkinter import ttk
from tkinter import font
from typing import Optional

from sklearn.metrics import consensus_score

from nft.collection import TraitCollection, TraitCollectionState
from nft.trait import TraitType
from nft.trait import Trait
from nft.merge import Merge
from nft.nft import NFT
from nft.widget.image_viewer import ImageViewer
from nft.widget.vscroll_frame import VerticalScrolledFrame

class ExcludeButton(tk.Label):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icon= tk.PhotoImage(file='assets/exclude.png', master=master)
        self.configure(image=self.icon)

class Editor(tk.Tk):
    def __init__(self, collection_list:List[TraitCollection], collection_index:int, merge:Merge, skip_invalid:bool = False, **kwargs ):
        super().__init__(**kwargs)

        self.collection_list = collection_list
        collection = collection_list[collection_index]
        if len(collection.error_messages) > 0:
            print('\n'.join(collection.error_messages))
        
        self.skip_invalid = tk.BooleanVar(master=self)
        self.skip_invalid.set(skip_invalid)

        # Mode activates on exclude button near Trait name clicked
        self.exclusion_trait:Optional[Trait] = None

        self.traits = TraitCollectionState(collection)

        self.merge = merge

        self.title("Manual NFT Generator")
        self.minsize(900,600)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.image_viewer = ImageViewer(master=self, highlightthickness=1, borderwidth=1, relief="groove")
        self.image_viewer.grid(row=0, column=0, sticky='nwse', rowspan=2)
        
        self.image_viewer.set_image(self.merge.combine(self.traits))

        self.choice_options = tk.Frame(master=self)
        self.choice_options.grid(row=0,column=1, sticky='we')
        self.choice_cb_skip_invalid = tk.Checkbutton(master=self.choice_options, text='Skip invalid', onvalue=True, offvalue=False, var=self.skip_invalid)
        self.choice_cb_skip_invalid.grid()

        self.choice_frame = VerticalScrolledFrame(master=self, highlightthickness=1, borderwidth=1, relief="groove", width=250)
        self.choice_frame.grid(row=1,column=1, sticky='nwes')
        self.choice_frame.columnconfigure(0, weight=1)
        self.choice_frame.inner.columnconfigure(0, weight=1)
        for group in self.traits.current_state:
            self.add_to_choice(group)

        self.bind('<Button 1>', lambda e: self.onClick())

        self.show_viewer_button = tk.Button(text="NFT Viewer") #command binded from App
        self.show_viewer_button.grid(column=0, row=2, sticky='w', padx=10)

        self.save_button = tk.Button(master=self, text="Save" ,command=self.save)
        self.save_button.grid(row=2, column=1, sticky='nwes', pady=(5,10), padx=30)

        self.saved_info = tk.Label(master=self)
        self.saved_info.grid(row=2, column=0)

        self.recheck_states()

    def onClick(self):
        self.exclusion_trait = None
        self.choice_frame.configure(cursor="arrow")

    def add_to_choice(self, trait_type:TraitType):
        """Add selector for each traits group"""
        trait, file = self.traits.current(trait_type)
        
        font = ('system', 12)
        font_bold = ('system', 12, 'bold')
        lbl_width = 20

        choice = tk.Frame(master=self.choice_frame.inner, name=trait_type.name)
        choice.group = trait_type #save ref for group instance
        choice.columnconfigure(1, weight=1)
        title = tk.Label(master=choice, text="%s" % trait_type.name, width=lbl_width, borderwidth = 3, font=font_bold, anchor='w')
        btn_exclude = ExcludeButton(master=choice, borderwidth = 3)
        counter = tk.Label(master=choice, font=('system', 10), foreground="#666666", name="counter_lbl")
        filename = tk.Label(master=choice, width=lbl_width, font=font, name="filename_lbl")
        self.set_text(filename, trait.name, 18)
        condition_frm = tk.Frame(master=choice, name="conditions_frm")
        exclude_frm = tk.Frame(master=choice, name="excludes_frm")
        mod_available = tk.Label(master=choice, name="mod_available_frm")
        separator=ttk.Separator(master=choice, orient='horizontal')
        prev = tk.Button(master=choice, text="<",  width=1, name="prev_btn", command=lambda: self.prev_trait(trait_type, choice))
        next = tk.Button(master=choice, text=">", width=1, name="next_btn", command=lambda: self.next_trait(trait_type, choice))

        title.grid(row=0, column=0, columnspan=3,  sticky="ew")
        counter.grid(row=0, column=3)
        prev.grid(row=1, column=0, sticky='e', padx=5)
        filename.grid(row=1, column=1, sticky='we')
        btn_exclude.grid(row=1, column=2)
        next.grid(row=1, column=3, sticky='w', padx=10)

        mod_available.grid(row=2, column=1, sticky='we', columnspan=2)
        condition_frm.grid(row=3, column=1, sticky='we', columnspan=2)
        exclude_frm.grid(row=4, column=1, sticky='we',  columnspan=2)

        separator.grid(row=5, column=0, columnspan=4, pady=(10,0), sticky="we")

        choice.grid(column=0, sticky='ew')

        filename.bind("<Button 1>", lambda e: self.onTraitNameClick(trait_type))
        btn_exclude.bind("<Button 1>", lambda e: self.onExcludeClick(trait_type))

        self.update_counter(trait_type)

    def onExcludeClick(self, trait_type:TraitType):
        self.choice_frame.configure(cursor="cross")
        self.exclusion_trait = self.traits.current(trait_type)[0]
        return "break"
    def onTraitNameClick(self, trait_type:TraitType):
        if self.exclusion_trait is not None:
            target = self.traits.current(trait_type)[0]
            trait = self.exclusion_trait
            if trait.name != target.name:
                self.traits.addExclusion(trait, target.name)
                self.recheck_states()
            self.exclusion_trait = None

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

    def update_counter(self, group:TraitType) -> None:
        total = len(group.traits)
        current, file = self.traits.current(group)
        index = group.traits.index(current)

        total_files = len(current.files)
        index_file = current.files.index(file)
        for choice in self.choice_frame.inner.winfo_children():
            if choice.group == group:
                counter:tk.Label = choice.children['counter_lbl'] 
                counter.configure(text="T:%s/%s F:%s/%s" % (index + 1, total, index_file + 1, total_files))

    def next_trait(self, group:TraitType, choice: tk.Frame):
        trait, file = self.traits.next(group, skip_invalid=self.skip_invalid.get())
        if trait is not None or file is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.merge.combine(self.traits))
            self.update_counter(group)
            self.recheck_states()

    def prev_trait(self, group:TraitType, choice: tk.Frame):
        trait, file = self.traits.prev(group, skip_invalid=self.skip_invalid.get())
        if trait is not None or file is not None:
            self.set_text(choice.children['filename_lbl'], trait.name)
            self.image_viewer.set_image(self.merge.combine(self.traits))
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
                        container = tk.Frame(master=excludes_frm)
                        container.pack()
                        label = tk.Label(master=container, text=name, font=('system', 12), foreground='#BF360C')
                        label.grid(column=0, row=0)
                        label_remove = tk.Label(master=container, text='-', font=('system', 12), foreground='#2E7D32')
                        label_remove.grid(column=1, row=0)
                        label_remove.bind("<Button 1>", lambda e, trait=trait, exclusion_name=name: self.removeExclusion(trait, exclusion_name))

    def removeExclusion(self, trait:Trait, exclusion_name:str):
        self.traits.removeExclusion(trait, exclusion_name)
        self.recheck_states()

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
            self.choice_cb_skip_invalid.configure(state= 'normal')
        else:
            self.save_button.configure(state = 'disabled')
            self.choice_cb_skip_invalid.configure(state= 'disabled')


    def recheck_states(self):
        """Update all condiitons, excludes, adaptions and save states"""
        self.recheck_conditions()
        self.recheck_excludes()
        self.recheck_adaptions()
        self.recheck_save_button_state()
        self.saved_info.configure(text='')

    def save(self):
        """Create new NFT instance and try to save it"""
        attributes = []
        order = self.traits.collection.order.json_order
        for json_group in order:
            for group in self.traits.current_state:
                if group.name == json_group:
                    trait, _ = self.traits.current(group)
                    attributes.append({"trait_type": group.name, "value": trait.name})

        # Add groups count to attributes too
        for group, count in self.traits.groups().items():
            attributes.append({"group": group, "value": count})

        nft = NFT(image=self.image_viewer.source_image, attributes=attributes)
        if self.traits.collection.name_prefix != '':
            nft.name_prefix = self.traits.collection.name_prefix
        ok, msg = nft.save(self.traits.collection.blueprint_template)

        self.saved_info.configure(text=msg, foreground='#BF360C' if not ok else '#000000')