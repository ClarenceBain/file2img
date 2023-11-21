import codecs
import io
import math
import os
import time
from pathlib import Path
from PIL import Image, PngImagePlugin

# function to get the bytes of the file
def get_bytes(file):
    with open(file, "rb") as data:
        return data.read()

# function to calculate the x dimension of the png
def get_dim(file):
    size = len(get_bytes(file))                                 # get total bytes (file size)
    bits = size * 8                                             # get the total amount of bits, 8 bits per byte
    return math.ceil(math.sqrt(bits / 3))                       # use math.ceil to round up for safety, get the square root of the bits / 3 (3 channels in rgb)

# function to turn an rgb value into bytes
def get_hex(rgb):
    return codecs.decode("{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2]), 'hex_codec')

# function to get an rgb value from bytes
def get_rgb(bytes):
    hex = "".join(f"{byte:02X}" for byte in bytes)              # converts raw bytes into a hex color string essentially
    
    while len(hex) % 6 != 0:                                    # if the hex color doesn't contain 3 bytes (length of 6) its not complete and needs padding
        hex += "FF"                                             # pad unfinished hex colors with white (FF)
    
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))        # convert the hex color string into (r, g, b) value

# function to print progress and eta
def get_progress(index, total, start):
    percent = index / total * 100                               # the percentage
    
    if percent % 100 != 0:
        overall = (time.time() - start) / (percent / 100)       # the overall amount of time
        remaining = max((start + overall) - time.time(), 0)     # the time remaining until finish
        
        print(f"Progress: {index}/{total} {percent:.2f}% {time.strftime('%I:%M:%S %p', time.localtime(time.time() + remaining))}", end="\r")

# function to essentially plot the bytes to the png
def get_pixels(bytes):
    pixels = []
    start = time.time()

    for i in range(0, len(bytes), 3):
        get_progress(i, len(bytes), start)
        pixels.append(get_rgb(bytes[i:i+3]))
    
    return pixels

# main encoding function (turning the file into an image)
def encode(file, name):
    try:
        data = get_bytes(file)                                                                  # the bytes of the file
        pixels = get_pixels(data)                                                               # essentially the plotted pixels on the png
        x = get_dim(file)                                                                       # the x dimension of the png
        y = math.ceil(x / 8)                                                                    # the y dimension of the png, divided by 8 to remove unused space
        
        image = Image.new("RGB", (x, y), color="white")                                         # create a new image with a white background using RGB (no alpha)
        image.putdata(pixels)                                                                   # add the pixels
        
        pinfo = PngImagePlugin.PngInfo()                                                        # since png doesn't use exif we need to use this
        pinfo.add_itxt("root", os.path.splitext(file)[1].lower())                               # store the original files extension, tEXt for some reason did not work
        
        if not os.path.exists(str(file).replace(f.name, "f2i")):
            os.makedirs(str(file).replace(f.name, "f2i"))                                       # if the directory "f2i" doesn't exist, create it (this will store the encoded files)
        
        image.save(str(file).replace(f.name, "f2i/" + name + ".png"), pnginfo=pinfo)            # create the image
    except FileNotFoundError:
        raise FileNotFoundError("File could not be found!")

# main decoding function (turning an f2i image back into a file)
def decode(file, name):
    try:
        data = io.BytesIO()                                                                     # create a buffer to hold bytes
        image = Image.open(file)                                                                # open the image
        pixels = image.getdata()                                                                # get the pixels of the image
        
        if image.info["root"] is not None:                                                      # check if the png we are interacting with was created with f2i
            ext = image.info["root"]                                                            # get the files original extension 
            start = time.time()
            
            for p in pixels:
                get_progress(p, len(pixels), start)                                                    
                data.write(get_hex(p))                                                          # turn the pixels into bytes and add them to the buffer we created
        
            length = data.tell()                                                                # get the size of the buffer
            index = 0

            for i, byte in enumerate(reversed(bytearray(data.getvalue()))):                     # cant enumerate through a buffer so we turn it into a bytearray
                if byte != 0xFF:                                                                # reading the bytes backwards (from the end) the first instance that isn't FF is likely our real data
                    index = i                                                                   # get the index of the end of our real data
                    break
        
            print(f"Removing {length - index} of excess data...")                               # debug..
            data.truncate(length - index)                                                       # remove all padding (all the FF's at the end)
        
            with open(str(file).replace(file.name, name + ext), "wb") as f:
                f.write(data.getvalue())
        
    except FileNotFoundError:
        raise FileNotFoundError("File could not be found!")    

while True:
    file = input("Path to file/directory (or 'exit' to quit): ")
    if file.lower() == 'exit': break
    
    mode = input("Would you like to 'encode' or 'decode'?: ")
    if mode.lower() == 'encode':
        mode = 0
    elif mode.lower() == 'decode':
        mode = 1
    else:
        print("Only valid modes are 'encode' or 'decode', setting to encode by default!")
        mode = 0
    
    if os.path.isdir(file):
        for f in Path(file).iterdir():
            if f.is_file():                
                if os.path.splitext(f)[1].lower() == ".png" and mode == 1:
                    decode(f, f.stem)
                else:
                    if mode == 0: encode(f, f.stem)
    elif os.path.isfile(file):
        name = os.path.splitext(file.name)[0]
        
        if file.lower().endswith(".png") and mode == 1:
            decode(file, name)
        else:
            if mode == 0: encode(file, name)
    else:
        print("File or directory not found, please enter a valid path!")