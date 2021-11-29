#dependency: python3-tk, pillow
import tkinter as tk
import os
from PIL import Image, ImageTk

data = {}

#Get all layears folders:
layers = [f for f in os.listdir('./') if f.startswith('layer')]
for layer in layers:
    data[layer] = {
        'files': [f for f in os.listdir("./%s" % layer) if f.endswith('.png')],
        'current': None
    }
    data[layer]['files'].sort()
    data[layer]['current'] = data[layer]['files'][0]

layer1 = next(iter(data))
window = tk.Tk()

label = tk.Label()
label.pack(side=tk.LEFT)

frame = tk.Frame()
frame.pack(side=tk.RIGHT)

def update_image():
    #open backgrounf
    background = Image.open("./%s/%s" % (layer1, data[layer1]['current']))

    for layer in list(data)[1:]:
        img = Image.open("./%s/%s" % (layer, data[layer]['current']))
        background.paste(img, (0,0), img)

    result = ImageTk.PhotoImage(background)

    label.configure(image=result)
    label.image=result
    label.pil_image = background

update_image()

def btn_left_handler(lbl, layer):
    indx = data[layer]['files'].index(lbl["text"])
    filename = data[layer]['files'][indx-1]
    data[layer]['current'] = filename
    lbl['text'] = filename
    update_image()

def btn_right_handler(label, layer):
    indx = data[layer]['files'].index(label["text"])
    indx = 0 if indx == len(data[layer]) else indx+1
    filename = data[layer]['files'][indx]
    data[layer]['current'] = filename
    label['text'] = filename
    update_image()

for layer in data:
    chooser = tk.Frame(master=frame)
    chooser.pack(side=tk.TOP)
    lbl_filename = tk.Label(master=chooser,text=data[layer]['current'])
    btn_left = tk.Button(master=chooser,text="<", command=lambda arg1=lbl_filename,arg2=layer:btn_left_handler(arg1,arg2))
    btn_right = tk.Button(master=chooser,text=">", command=lambda arg1=lbl_filename,arg2=layer:btn_right_handler(arg1,arg2))

    btn_left.pack(side=tk.LEFT)
    lbl_filename.pack(side=tk.LEFT)
    btn_right.pack(side=tk.RIGHT)

def save():
    img = label.pil_image
    img.save('./out/result.png')


btn_save = tk.Button(master=window, text="save", command=save)
btn_save.pack(side=tk.BOTTOM)


window.bind


window.mainloop()