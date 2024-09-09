import codecs
import enum
import io
import math
import queue
import random
import os
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import dearpygui.dearpygui as dpg
from PIL import Image

# versions >= 4 will not support prior versions, version 3 will always be available for legacy files on the github releases

example_hex = "AABBCCDD"
example_swapped_hex = "AABBCCDD"

swap = []
swap_info_raw = None
swap_info = None

sfile = None
sext = None
ssize = None
isdirectory = False
queue = []

Image.MAX_IMAGE_PIXELS = None

def UpdateDir():
    global isdirectory
    
    isdirectory = dpg.get_value("fulldirectory")

def DirectoryConvert():
    global queue
    
    for i in range(len(queue)):
        Open(queue[i])
    
    queue.clear()

def Open(filep = None):
    global sfile
    global swap
    global swap_info_raw
    global swap_info
    global example_hex
    global example_swapped_hex
    global sext
    global ssize
    global queue
    
    sfile = None
    sext = None
    ssize = None
    
    swap = None
    swap_info_raw = None
    swap_info = None
    example_hex = "AABBCCDD"
    example_swapped_hex = "AABBCCDD"
    
    root = tk.Tk()
    root.withdraw()

    if len(queue) <= 0 or isdirectory == False:
        filep = None

    if filep is not None:
        sfile = filep
    else:
        sfile = filedialog.askopenfilename() if isdirectory == False else filedialog.askdirectory()    
    
    if sfile == "" or sfile is None:
        sfile = None
        root.destroy()
        return
    
    root.destroy()
    
    if os.path.isdir(sfile) and isdirectory == True:
        queue = [str(file) for file in Path(sfile).rglob('*') if file.is_file()]
        
        dpg.set_value("current_file_text", "You are in directory mode and will convert/revert everything inside of: \n" + sfile)            
        dpg.set_item_label("convert_or_decode_button", "Start")
        dpg.set_item_callback("convert_or_decode_button", DirectoryConvert)
        dpg.show_item("convert_or_decode_button")
        dpg.hide_item("changelog_title")
        dpg.hide_item("changelog_body")           
        return
    
    if ".png" in os.path.basename(sfile):
        image = Image.open(sfile)
        pixels = image.getdata()
        
        embedindexes = []
        swap = []
        tmp = []

        for i in range(len(pixels)):
            if pixels[i] == (1,2,3,4):
                embedindexes.append(i)
        
        if len(embedindexes) == 4:
            for i in range(embedindexes[0] + 1, embedindexes[1]):
                swap.append((pixels[i][0],pixels[i][1]))
        
            swap_info_raw = ",".join([f"{o}->{new}" for o, new in swap])
            
            for i in range(embedindexes[1], embedindexes[2]):
                if embedindexes[1] < i < embedindexes[2]:
                    for x in range(len(pixels[i])):
                        if pixels[i][x] != 255:
                            tmp.append(pixels[i][x])
                                    
            sext = "".join(map(chr, tmp))
            tmp.clear()
        
            for i in range(embedindexes[2], embedindexes[3]):
                if embedindexes[2] < i < embedindexes[3]:
                    for x in range(len(pixels[i])):
                        if pixels[i][x] != 255:
                            tmp.append(pixels[i][x])    
        
            ssize = int("".join(map(chr, tmp)))
            tmp.clear()
            
            if isdirectory:
                image.close()
                print("Reverting file: " + sfile)
                ImageToFile()
                return

            dpg.set_value("current_file_text", "Image: " + sfile + "\nImage Size: " + str(len(GetFileBytes(sfile))) + "\nImage Pixels: " + str(len(pixels)) + "\nOriginal Extension: " + sext + "\nOriginal Size: " + str(ssize))
            dpg.set_item_label("convert_or_decode_button", "Revert")
            dpg.set_item_callback("convert_or_decode_button", ImageToFile)
            dpg.show_item("convert_or_decode_button")
        else:
            if isdirectory:
                image.close()                
                print("Converting file: " + sfile)
                FileToImage()
                return            
            dpg.set_value("current_file_text", "Image: " + sfile + "\nImage Size: " + str(len(GetFileBytes(sfile))) + "\nImage Pixels: " + str(len(pixels)))            
            dpg.set_item_label("convert_or_decode_button", "Convert")
            dpg.set_item_callback("convert_or_decode_button", FileToImage)
            dpg.show_item("convert_or_decode_button")
        
        image.close()
        dpg.hide_item("changelog_title")
        dpg.hide_item("changelog_body")        
    else:
        if isdirectory:             
            print("Converting file: " + sfile)
            FileToImage()
            return             
        dpg.set_value("current_file_text", "File: " + sfile + "\nFile Size: " + str(len(GetFileBytes(sfile))))
        dpg.set_item_label("convert_or_decode_button", "Convert")
        dpg.set_item_callback("convert_or_decode_button", FileToImage)
        dpg.show_item("convert_or_decode_button")
        dpg.show_item("ex_swap_hex")
        dpg.hide_item("changelog_title")
        dpg.hide_item("changelog_body")
        
def Swap():
    global swap
    global swap_info
    global swap_info_raw
    global example_swapped_hex
    
    pseudo = example_hex
    tmp = []
    swap = []
    swap_info_raw = None
    
    for byte in range(0, len(pseudo), 2):
        tmp.append(pseudo[byte:byte+2])
        
    while len(swap) == 0:
        swap.clear()
        for o in range(len(tmp)):
            new = random.randint(0, len(tmp) - 1)
            swap.append((o, new))
        for o, new in swap:
            tmp[o], tmp[new] = tmp[new], tmp[o]
    
    swap_info_raw = ",".join([f"{o}->{new}" for o, new in swap])
    swaps = [tuple(map(int, s.split("->"))) for s in swap_info_raw.split(",")]
    example_swapped_hex = "".join(tmp)
    
    swap_info = []
    for o, new in swaps:
        pixel = (o, new, 255, 255)
        swap_info.append(pixel)
        
def GetFileBytes(file):
    with open(file, "rb") as data:
        return data.read()

def CreateImageDimensions(pixels):
    size = len(pixels) * 4
    bits = size * 8
    
    x = math.ceil(math.sqrt(bits / 4))
    y = math.ceil(x / 8)
    
    return x,y

def ColorByte(rgb):
    rgb_bytes = codecs.decode("{:02X}{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2], rgb[3]), 'hex_codec')
    tmp = list(rgb_bytes)
    
    for new, o in reversed(swap):
        tmp[new], tmp[o] = tmp[o], tmp[new]
    
    return bytes(tmp)
        
def ByteColor(data):
    global example_hex
    global example_swapped_hex
    
    hex_color = "".join(f"{byte:02X}" for byte in data)
    
    while len(hex_color) % 8 != 0:
        hex_color += "FF"
        
    tmp = []
    
    for byte in range(0, len(hex_color), 2):
        tmp.append(hex_color[byte:byte+2])
    
    while example_hex == example_swapped_hex:
        Swap()
    
    dpg.set_value("ex_swap_hex", example_hex + " becomes " + example_swapped_hex)

    for o, new in swap:
        tmp[o], tmp[new] = tmp[new], tmp[o]
     
    return HexToRGBA("".join(tmp))[0]

def ByteColorNoSwap(data):
    hex_color = "".join(f"{byte:02X}" for byte in data)
    
    while len(hex_color) % 8 != 0:
        hex_color += "FF"
        
    tmp = []
    
    for byte in range(0, len(hex_color), 2):
        tmp.append(hex_color[byte:byte+2])
        
    return HexToRGBA("".join(tmp))
        
def HexToRGBA(hex_color):
    colors = []
    
    for i in range(0, len(hex_color), 8):
        rgba = []
        for x in range(0, 8, 2):
            rgba.append(int(hex_color[i+x:i+x+2], 16))
        colors.append(tuple(rgba))
    
    return colors

def CreateDataPixels(data):
    return [ByteColor(data[i:i+4]) for i in range(0, len(data), 4)]

def EmbedData(file, pixels):
    tmp = 0
    extension = os.path.splitext(file)[1]
    size = str(len(GetFileBytes(file)))
    
    extension = ByteColorNoSwap(extension.encode("utf-8"))
    size = ByteColorNoSwap(size.encode("utf-8"))

    embedspace = (len(swap_info) + len(extension) + len(size) + 4)
    
    pixels.extend([(255,255,255,255)] * embedspace)
    pixels[len(pixels) - embedspace] = (1,2,3,4)

    for i in range(len(swap_info)):
        pos = len(pixels) - embedspace + 1 + i
        pixels[pos] = swap_info[i]
        if i == len(swap_info) - 1:
            pixels[pos + 1] = (1,2,3,4)
            tmp = pos + 2
            
    for i in range(len(extension)):
        pixels[tmp + i] = extension[i]
        if i == len(extension) - 1:
            pixels[tmp + i + 1] = (1,2,3,4)
            tmp = tmp + i + 2
                
    for i in range(len(size)):
        pixels[tmp + i] = size[i]
        if i == len(size) - 1:
            pixels[tmp + i + 1] = (1,2,3,4)
            tmp = 0
   
    return pixels

def FileToImage():
    global swap
    
    file = sfile

    if file is not None:
        fname = os.path.splitext(os.path.basename(file))[0]
        foutput = os.path.join(os.path.dirname(file), f"f2i{4}")
        fdata = GetFileBytes(file)
        
        print("Converting file. This may take awhile.")
        pixels = CreateDataPixels(fdata)
        pixels = EmbedData(file, pixels)
        x,y = CreateImageDimensions(pixels)
        
        image = Image.new("RGBA", (x,y), color=(255,255,255,255))
        image.putdata(pixels)
        
        if not os.path.exists(foutput):
            os.makedirs(foutput)
        
        image.save(os.path.join(foutput, fname + ".png"))
        image.close()
        print("Done.")

def ImageToFile():
    nfile = io.BytesIO()
    image = Image.open(sfile)
    pixels = image.getdata()
    index = 0
    
    for i, pixel in enumerate(pixels):
        nfile.write(ColorByte(pixel))
        if i % 10 == 0:
            print(str(i + 1) + "/" + str(len(pixels)) + " " + (str(math.ceil((i + 1) / len(pixels) * 100))) + "%")
    
    length = nfile.tell()
    index = 0
    
    for i, byte in enumerate(reversed(bytearray(nfile.getvalue()))):
        if i > ssize:
            index = i - 1
            break
        
    nfile.truncate(index)
    
    with open(sfile.replace(os.path.basename(sfile), os.path.basename(sfile).replace(".png", "") + sext), "wb") as f:
        f.write(nfile.getvalue())
        
    nfile.close()
    image.close()

dpg.create_context()
dpg.create_viewport(title="file2img 4.0", resizable=False, width=600, height=275)
dpg.setup_dearpygui()

with dpg.window(tag="main"):
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Open..", callback=Open)
            dpg.add_checkbox(label="Full Directory", default_value=False, tag="fulldirectory", callback=UpdateDir)
            
    with dpg.tab_bar(tag="main_tb"):
        with dpg.tab(label="Home"):
            dpg.add_text("There is currently no file selected. Go to File -> Open.. to select a file.", tag="current_file_text")
            dpg.add_text(example_hex + " becomes " + example_swapped_hex, tag="ex_swap_hex")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Convert", callback=FileToImage, tag="convert_or_decode_button")
            dpg.add_separator()
            dpg.add_text("CHANGELOG:", tag="changelog_title")
            dpg.add_text("+ Soft rewrite\n+ Removed bloat\n+ Speed improvements\n+ Bulk conversion/deconversions\n+ Changelog on start\n\n- Decided to only use RGBA\n- Dropped legacy support for versions >= 4\n- Pixels will always be obfuscated going forward (>= 4)", tag="changelog_body")
            dpg.hide_item("convert_or_decode_button")
            dpg.hide_item("ex_swap_hex")            

dpg.show_viewport()
dpg.set_primary_window("main", True)
dpg.start_dearpygui()
dpg.destroy_context()