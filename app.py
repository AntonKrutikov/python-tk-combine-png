import os
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from widget_vscroll import VerticalScrolledFrame

layers = []

#index.json must contain array of items {folder:'', title:''}
#All not real paths - ignored, layers without folder - ignored
with open('index.json') as json_file:
    try:
        parsed = json.load(json_file)
        if isinstance(parsed, list): #we want array from json file
            for i in parsed:
                if isinstance(i, dict) and 'folder' in i: #item must have 'folder' field
                    if os.path.isdir(i['folder']): #check path is real, if not - warning and ignore
                        layers.append(i)
                    else:
                        print("Warning in index.json file: [%s] is not a real path" % i['folder'])
    except:
        print('Error in parsing layers from index.json') #TODO: differen exception handling

#collect all files info in each layer
#search for index.json in layer folder
for layer in layers:
    path = "./%s/index.json" % layer['folder']
    if os.path.isfile(path):
        with open(path) as json_file:
            try:
                parsed = json.load(json_file)
                layer['files'] = []
                for i in parsed:
                    if isinstance(i, dict) and 'file' in i: #item must have 'file' field
                        filepath = "./%s/%s" % (layer['folder'],i['file'])
                        if os.path.isfile(filepath): #check file exists, if not - warning and ignore
                            layer['files'].append(i)
                            if 'current' not in layer:
                                layer['current'] = i
                        else:
                            print("Warning in %s file: [%s] is not a real file" % (path, filepath))
            except:
                print('Error in parsing files from index.json in path=%s' % path)



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

def update_image(e=None):
    canvas.delete('all')
    #open background (first layer) if exists
    if 'current' in layers[0]:
        background = Image.open("./%s/%s" % (layers[0]['folder'],layers[0]['current']['file']))

        for layer in layers[1:]:
            if 'current' in layer:
                img = Image.open("./%s/%s" % (layer['folder'], layer['current']['file']))
                background.paste(img, (0,0), img)

        result = ImageTk.PhotoImage(background)

        canvas.create_image(0, 0, image=result, tag="result")
        
        canvas.image=result
        canvas.pil_image = background

        resize_canvas()
        canvas.configure(scrollregion=[-background.width/2,-background.height/2,background.width/2, background.height/2])
        canvas.yview_moveto('0')
        canvas.xview_moveto('0')


update_image()

frame = VerticalScrolledFrame(master=window, highlightthickness=1, borderwidth=1, relief="groove", width=250)
frame.grid(row=0,column=1, sticky='nwes')

frame.columnconfigure(1, weight=1)

frame.inner.columnconfigure(1, weight=1)


def btn_left_handler(label, layer):
    indx = layer['files'].index(layer['current'])
    layer['current'] = layer['files'][indx-1]
    file_title = layer['current']['title'] if 'title' in layer['current'] else layer['current']['file']
    file_title = file_title[0:20]+'...' if len(file_title) > 20 else file_title
    label['text'] = file_title
    lbl_saved['text'] = ''
    update_image()

def btn_right_handler(label, layer):
    indx = layer['files'].index(layer['current'])
    indx = 0 if indx == len(layer['files'])-1 else indx+1
    layer['current'] = layer['files'][indx]
    file_title = layer['current']['title'] if 'title' in layer['current'] else layer['current']['file']
    file_title = file_title[0:20]+'...' if len(file_title) > 20 else file_title
    label['text'] = file_title
    lbl_saved['text'] = ''
    update_image()

#draw choosers on right pane
i=0
for layer in layers:
    if 'current' in layer: #show only layers with minimum 1 file exists
        #Use folder title from json file or folder name as fallback
        layer_title = layer['title'] if 'title' in layer else layer['folder']
        lbl_layer_title = tk.Label(master=frame, text="%s" % layer_title, width=20, borderwidth = 3, font=("Arial bold", 12), anchor='w')
        separator=ttk.Separator(master=frame,orient='horizontal')

        #Use file title from json file or file name as fallback
        file_title = layer['current']['title'] if 'title' in layer['current'] else layer['current']['file']
        file_title = file_title[0:10] if len(file_title) > 10 else file_title
        print(file_title)
        lbl_filename = tk.Label(master=frame,text=file_title, width=20, font=("Arial", 16))

        btn_left = tk.Button(master=frame,text="<", command=lambda arg1=lbl_filename, arg2=layer:btn_left_handler(arg1, arg2), width=1)
        btn_right = tk.Button(master=frame,text=">", command=lambda arg1=lbl_filename, arg2=layer:btn_right_handler(arg1,arg2), width=1)

        lbl_layer_title.grid(row=i, column=0, columnspan=3, sticky="ew")
        i+=1

        btn_left.grid(row=i, column=0, sticky='e', padx=5)
        lbl_filename.grid(row=i, column=1, sticky='we')
        btn_right.grid(row=i, column=2, sticky='w', padx=5)
        i+=1

        separator.grid(row=i, column=0, columnspan=3, pady=(10,0), sticky="we")
        i+=1

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
    with open('./out/%s.json' % file_index, 'w') as outfile:
        json.dump(result_layers, outfile)

    lbl_saved['text'] = 'File saved to ./out/%s.png' % file_index

btn_save = tk.Button(master=window, text="Save" ,command=save)
btn_save.grid(row=1, column=1, sticky='nwes', pady=(5,10), padx=2)

lbl_saved = tk.Label(master=window)
lbl_saved.grid(row=1, column=0)

window.minsize(900,600)
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

window.mainloop()