from io import BytesIO
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import font
from PIL import Image, ImageTk
from cairosvg import svg2png
from widget_vscroll import VerticalScrolledFrame
import argparse
import traits

description="""NFT manual generator

Compare your png or svg images to resulting NFT
"""
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--svg-width', help='Default svg width when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--svg-height', help='Default svg height when convert to png, if svg used as background layer', default=1080, type=int)
parser.add_argument('--blueprint', help='JSON template for generating output json file', default='blueprint.json')
args = parser.parse_args()

svg_default_width = args.svg_width
svg_default_height = args.svg_height

traits_file = 'traits.json'
layers = traits.load(traits_file)

window = tk.Tk()
window.title("Manual NFT Generator")

frame_canvas = tk.Frame(highlightthickness=1, borderwidth=2, relief="groove")
frame_canvas.grid(row=0, column=0, sticky='nwse')

frame_canvas.columnconfigure(0, weight=1)
frame_canvas.rowconfigure(0, weight=1)


canvas = tk.Canvas(frame_canvas)
canvas.grid(row=0, column=0, sticky='nwse')

scroll_x = tk.Scrollbar(frame_canvas, orient="horizontal", command=canvas.xview)
scroll_x.grid(row=1, column=0, sticky="ew")

scroll_y = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
scroll_y.grid(row=0, column=1, sticky="ns")

canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

#Method to resize and center image inside canvas when parent container resized
def resize_canvas(e=None):
    img_width = canvas.pil_image.width
    img_height = canvas.pil_image.height
    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    if img_width < canvas_width:
        canvas.coords('result', (canvas_width - img_width) / 2, canvas.coords('result')[1])
    if img_height < canvas_height:
        canvas.coords('result', canvas.coords('result')[0], (canvas_height - img_height)/2)

canvas.bind('<Configure>', resize_canvas)

def open_img_file(file):
    fullpath = file
    if file.endswith('.svg'):
        new_bites = svg2png(file_obj=open(fullpath, "rb"), unsafe=True, write_to=None, parent_width=svg_default_width, parent_height=svg_default_height)
        return Image.open(BytesIO(new_bites))
    return Image.open(fullpath)


def update_image(canvas):
    global svg_default_width
    global svg_default_height
    canvas.delete('all')
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

    result = ImageTk.PhotoImage(background)

    canvas.create_image(0, 0, image=result, tag="result")
    
    canvas.image=result
    canvas.pil_image = background

    resize_canvas()
    canvas.configure(scrollregion=[-background.width/2,-background.height/2,background.width/2, background.height/2])
    canvas.yview_moveto('0')
    canvas.xview_moveto('0')


update_image(canvas)

frame = VerticalScrolledFrame(master=window, highlightthickness=1, borderwidth=1, relief="groove", width=250)
frame.grid(row=0,column=1, sticky='nwes')

frame.columnconfigure(1, weight=1)

frame.inner.columnconfigure(1, weight=1)

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
    img = canvas.pil_image
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
        if 'condition' in group:
            label = tk.Label(master=frame, text='adapted to', font=('system italic', 12), foreground="#757575", pady=10)
            f = font.Font(label, label.cget('font'))
            f.configure(slant='italic')
            label['font'] = f
            label.pack()

            for cond in group['condition']:
                label = tk.Label(master=frame, text=cond, font=('system', 12), foreground="#757575")
                if traits.check_condition([cond], layers):
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
        if 'excluded' in group:
            label = tk.Label(master=frame, text='excluded', font=('system italic', 12), foreground="#757575", pady=10)
            f = font.Font(label, label.cget('font'))
            f.configure(slant='italic')
            label['font'] = f
            label.pack()

            for cond in group['excluded']:
                label = tk.Label(master=frame, text=cond, font=('system', 12), foreground="#757575")
                if traits.check_exclude([cond], layers):
                    label['foreground'] = '#BF360C'
                else:
                    label['foreground'] = '#757575'
                label.pack()

def update_save_button_state(btn):
    excluded = False
    not_adapted = False
    for layer in layers:
        current = layer['current']
        if 'excluded' in current and traits.check_exclude(current['excluded'], layers):
            excluded = True
        if 'condition' in current and not traits.check_condition(current['condition'], layers):
            not_adapted = True
    if excluded or not_adapted:
        btn['state'] = 'disabled'
    else:
        btn['state'] = 'normal'


def btn_left_handler(label, layer):
    indx = layer['traits'].index(layer['current'])
    layer['current'] = layer['traits'][indx-1]
    set_text(layer['current'], label)
    update_conditional_labels()
    update_excluded_labels()
    update_save_button_state(btn_save)
    frame.inner.update()
    lbl_saved['text'] = ''
    update_image(canvas)

def btn_right_handler(label, layer):
    indx = layer['traits'].index(layer['current'])
    indx = 0 if indx == len(layer['traits'])-1 else indx+1
    layer['current'] = layer['traits'][indx]
    set_text(layer['current'], label)
    update_conditional_labels()
    update_excluded_labels()
    update_save_button_state(btn_save)

    frame.inner.update()
    lbl_saved['text'] = ''
    update_image(canvas)


i=0
label_width = 20
for layer in layers:
    if 'current' in layer:
        
        lbl_layer_title = tk.Label(master=frame, text="%s" % layer['group'], width=label_width, borderwidth = 3, font=('system', 12, 'bold'), anchor='w')
        lbl_filename = tk.Label(master=frame, width=label_width, font=('system', 12))
        frame_conditions = tk.Frame(master=frame)
        frame_excludes = tk.Frame(master=frame)
        separator=ttk.Separator(master=frame,orient='horizontal')
        btn_left = tk.Button(master=frame,text="<",  width=1, command=lambda arg1=lbl_filename, arg2=layer: btn_left_handler(arg1, arg2))
        btn_right = tk.Button(master=frame,text=">", width=1, command=lambda arg1=lbl_filename, arg2=layer: btn_right_handler(arg1,arg2))

        lbl_layer_title.grid(row=i, column=0, columnspan=3, sticky="ew")
        i+=1

        btn_left.grid(row=i, column=0, sticky='e', padx=5)
        lbl_filename.grid(row=i, column=1, sticky='we')
        btn_right.grid(row=i, column=2, sticky='w', padx=10)
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



update_save_button_state(btn_save)

lbl_saved = tk.Label(master=window)
lbl_saved.grid(row=1, column=0)

window.minsize(900,600)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

window.mainloop()