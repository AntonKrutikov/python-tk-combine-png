from io import BytesIO
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkinter.constants import LEFT
from PIL import Image, ImageTk
from cairosvg import svg2png
from widget_vscroll import VerticalScrolledFrame
import argparse
import traits
import widget_viewer
from window_result import ResultViewWindow

description="""NFT manual generator

Compare your png or svg images to resulting NFT
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
parser.add_argument('--viewer', help='Starts in viewer mode', nargs='?', const=-1, default=None)
args = parser.parse_args()

result_viewer_instance = False
result_viewer = None
def show_result_viewer():
    global result_viewer_instance
    global result_viewer
    if not result_viewer_instance:
        result_viewer = ResultViewWindow()
        result_viewer_instance = True
        def on_close():
            global result_viewer_instance
            result_viewer_instance = False
            result_viewer.destroy()
        
        result_viewer.protocol("WM_DELETE_WINDOW", on_close)
        result_viewer.load_file_list()
        result_viewer.show_item_by_name(args.viewer)
        return result_viewer

# viewer mode
if args.viewer != None:
    show_result_viewer().mainloop()
    exit()
# viewer mode end

svg_default_width = args.svg_width
svg_default_height = args.svg_height

traits_file = 'traits.json'
layers = traits.load(traits_file)

window = tk.Tk()
window.title("Manual NFT Generator")
window.minsize(900,600)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

def open_img_file(file):
    fullpath = file
    if file.endswith('.svg'):
        new_bites = svg2png(file_obj=open(fullpath, "rb"), unsafe=True, write_to=None, parent_width=svg_default_width, parent_height=svg_default_height)
        return Image.open(BytesIO(new_bites))
    return Image.open(fullpath)

def update_image(viewer: widget_viewer.Viewer):
    global svg_default_width
    global svg_default_height
    #open background (first layer) if exists
    if 'current' in layers[0]:
        #For now background cant be SVG, because we need sizing
        background = Image.open( layers[0]['current']['file'][0]).convert('RGBA')
        svg_default_width = background.width
        svg_default_height = background.height

        for layer in layers[1:]:
            if 'current' in layer:
                files = layer['current']['file']
                for path in files:
                    img = open_img_file(path)
                    aimg = Image.new('RGBA', background.size)
                    aimg.paste(img, (0,0))
                    background = Image.alpha_composite(background, aimg)

    viewer.set_image(background)



viewer = widget_viewer.Viewer(master=window, highlightthickness=1, borderwidth=1, relief="groove")
viewer.grid(row=0, column=0, sticky='nwse')
update_image(viewer)

frame = VerticalScrolledFrame(master=window, highlightthickness=1, borderwidth=1, relief="groove", width=250)
frame.grid(row=0,column=1, sticky='nwes')
frame.columnconfigure(1, weight=1)
frame.inner.columnconfigure(1, weight=1)

view_results_button = tk.Button(text="results", command=lambda: show_result_viewer())
view_results_button.grid(column=0, row=1, sticky='w')

## load json template
blueprint = {}
with open(args.blueprint) as json_file:
    blueprint = json.load(json_file)

def save():
    results = [f for f in os.listdir("./out") if f.endswith('.png') and not f.endswith('.min.png')]
    sorted_results = sorted(results, key=lambda x:int(x.split('.')[0]) if x.split('.')[0].isdigit() else -1, reverse=True)

    file_index = 0
    for file in sorted_results:
        try : 
            file_index = int(file.split('.')[0])
            break
        except ValueError as e :
            print("Warning: Filenames in output folders must by valid numbers (%s)" % file)
            continue
    file_index+=1
    img = viewer.source_image
    img.save('./out/%s.png' % file_index)
    optimized = img.convert('P')
    optimized.save('./out/%s.min.png' % file_index)

    result_layers = []
    for layer in layers:
        if 'current' in layer:
            data = layer.copy()
            data.pop('files', None)
            result_layers.append(data)
    blueprint['name'] = "%s.png" % file_index
    blueprint['attributes'] = []
    for layer in result_layers:
        blueprint['attributes'].append({"trait_type": layer['group'], "value": layer['current']['title']})

    with open('./out/%s.json' % file_index, 'w') as outfile:
        json.dump(blueprint, outfile)

    lbl_saved['text'] = 'File saved to ./out/%s.png' % file_index

btn_save = tk.Button(master=window, text="Save" ,command=save)
btn_save.grid(row=1, column=1, sticky='nwes', pady=(5,10), padx=30)

condition_labels = []
exclude_labels = []
adapted_available_labels = []

def set_text(current, lbl_file):
    lbl_file['anchor'] = 'center'
    title = current['title']
    if len(title) > 18:
        title = title[0:18]+'...'
        lbl_file['anchor'] = 'w'
    lbl_file['text'] = title

def update_conditional_labels():
    global layers
    global condition_labels
    for condition in condition_labels:
        frame = condition['frame']
        group = condition['layer']['current']
        for child in frame.winfo_children():
            child.destroy()
        tk.Frame(frame, height=1, width=1).pack() #hack to resize frame after cleanup
        if 'adapted-to' in group:
            label = tk.Label(master=frame, text='adapted to', font=('system italic', 12), foreground="#757575", pady=10)
            f = font.Font(label, label.cget('font'))
            f.configure(slant='italic')
            label['font'] = f
            label.pack()

            for cond in group['adapted-to']:
                label = tk.Label(master=frame, text=cond, font=('system', 12), foreground="#757575")
                if traits.check_condition([cond], layers) == True:
                    label['foreground'] = '#2E7D32'
                else:
                    label['foreground'] = '#BF360C'
                label.pack()

def update_excluded_labels():
    global layers
    global exclude_labels
    for exclude in exclude_labels:
        frame = exclude['frame']
        group = exclude['layer']['current']
        for child in frame.winfo_children():
            child.destroy()
        tk.Frame(frame, height=1, width=1).pack() #hack to resize frame after cleanup
        if 'exclude' in group and traits.check_exclude(group['exclude'], layers):
            label = tk.Label(master=frame, text='exclude', font=('system italic', 12), foreground="#757575", pady=10)
            f = font.Font(label, label.cget('font'))
            f.configure(slant='italic')
            label['font'] = f
            label.pack()

            for cond in group['exclude']:
                if traits.check_exclude([cond], layers):
                    label = tk.Label(master=frame, text=cond, font=('system', 12), foreground="#757575")
                    label['foreground'] = '#BF360C'
                label.pack()

def update_adapted_available_labels():
    global layers
    for available in adapted_available_labels:
        group = available['layer']
        current = group['current']
        frame = available['frame']
        for child in frame.winfo_children():
            child.destroy()
        tk.Frame(frame, height=1, width=1).pack() #hack to resize frame after cleanup
        ok, cond = traits.check_adapted_exists(current, group, layers)
        if ok == True:
            label = tk.Label(master=frame, text='mod available for', font=('system', 12), foreground="#BF360C", pady=10)
            label.pack()
            for c in cond:
                label_cond = tk.Label(master=frame, text=c, font=('system', 12), foreground="#757575")
                label_cond.pack() 


def update_save_button_state(btn):
    excluded = False
    not_adapted = False
    adapted_exists = False
    for layer in layers:
        if 'current' in layer:
            current = layer['current']
            if 'exclude' in current and traits.check_exclude(current['exclude'], layers):
                excluded = True
            if 'adapted-to' in current and not traits.check_condition(current['adapted-to'], layers):
                not_adapted = True
            ok, adapted = traits.check_adapted_exists(current, layer, layers)
            if ok:
                adapted_exists = True
    if excluded or not_adapted or adapted_exists:
        btn['state'] = 'disabled'
    else:
        btn['state'] = 'normal'


def btn_left_handler(label, layer):
    indx = layer['traits'].index(layer['current'])
    layer['current'] = layer['traits'][indx-1]
    set_text(layer['current'], label)
    update_conditional_labels()
    update_excluded_labels()
    update_adapted_available_labels()
    update_save_button_state(btn_save)
    frame.inner.update()
    lbl_saved['text'] = ''
    update_image(viewer)

def btn_right_handler(label, layer):
    indx = layer['traits'].index(layer['current'])
    indx = 0 if indx == len(layer['traits'])-1 else indx+1
    layer['current'] = layer['traits'][indx]
    set_text(layer['current'], label)
    update_conditional_labels()
    update_excluded_labels()
    update_adapted_available_labels()
    update_save_button_state(btn_save)

    frame.inner.update()
    lbl_saved['text'] = ''
    update_image(viewer)


i=0
label_width = 20
for layer in layers:
    if 'current' in layer:
        
        lbl_layer_title = tk.Label(master=frame, text="%s" % layer['group'], width=label_width, borderwidth = 3, font=('system', 12, 'bold'), anchor='w')
        lbl_filename = tk.Label(master=frame, width=label_width, font=('system', 12))
        frame_conditions = tk.Frame(master=frame)
        frame_excludes = tk.Frame(master=frame)
        frame_adapted_available = tk.Label(master=frame)
        separator=ttk.Separator(master=frame,orient='horizontal')
        btn_left = tk.Button(master=frame,text="<",  width=1, command=lambda arg1=lbl_filename, arg2=layer: btn_left_handler(arg1, arg2))
        btn_right = tk.Button(master=frame,text=">", width=1, command=lambda arg1=lbl_filename, arg2=layer: btn_right_handler(arg1,arg2))

        lbl_layer_title.grid(row=i, column=0, columnspan=3, sticky="ew")
        i+=1

        btn_left.grid(row=i, column=0, sticky='e', padx=5)
        lbl_filename.grid(row=i, column=1, sticky='we')
        btn_right.grid(row=i, column=2, sticky='w', padx=10)
        i+=1

        frame_adapted_available.grid(row=i, column=1, sticky='we')
        adapted_available_labels.append({'layer': layer, 'frame': frame_adapted_available})
        i+=1

        frame_conditions.grid(row=i, column=1, sticky='we')
        condition_labels.append({'layer': layer, 'frame': frame_conditions})
        i+=1
        
        frame_excludes.grid(row=i, column=1, sticky='we')
        exclude_labels.append({'layer': layer, 'frame': frame_excludes})
        i+=1

        separator.grid(row=i, column=0, columnspan=3, pady=(10,0), sticky="we")
        i+=1

        set_text(layer['current'], lbl_filename)
update_conditional_labels()
update_excluded_labels()
update_adapted_available_labels()



update_save_button_state(btn_save)

lbl_saved = tk.Label(master=window)
lbl_saved.grid(row=1, column=0)



window.mainloop()