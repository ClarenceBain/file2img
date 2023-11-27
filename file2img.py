import base64
import codecs
import io
import math
import os
import time
from pathlib import Path
from PIL import Image, PngImagePlugin

modes = {"encode": 0, "decode": 1}
channels = {"rgb": 3, "rgba": 4}
version = 1.8

# if someone were to stumble across this file lets at least try to hide some of this information (because why not)
# obviously not foolproof but the average user wouldn't be able to tell if they had looked at the png in a text editor
root, ogs, chann, vers = base64.b64encode("root".encode("utf-8")), base64.b64encode("ofs".encode("utf-8")), base64.b64encode("channel".encode("utf-8")), base64.b64encode("version".encode("utf-8"))

# function to get the bytes of the file
def get_bytes(file):
    with open(file, "rb") as data:
        return data.read()

# function to calculate the x dimension of the png
def get_dim(file, channel):
    size = len(get_bytes(file))                                 # get total bytes (file size)
    bits = size * 8                                             # get the total amount of bits, 8 bits per byte
    return math.ceil(math.sqrt(bits / channel))                 # use math.ceil to round up for safety, get the square root of the bits / 3 (3 channels in rgb)

# function to turn an rgb value into bytes
def get_hex(rgb, channel, verz):
    # idk why i didnt just use a ternary before, probably because i hate long one liners
    hex = codecs.decode("{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2]), 'hex_codec') if channel == 3 else codecs.decode("{:02X}{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2], rgb[3]), 'hex_codec')
    if verz > 0:                                                # support for files converted before 1.8        
        tmp = list(hex)
            
        tmp[0], tmp[channel - 1] = tmp[channel - 1], tmp[0]     # unswap bytes
        tmp[0], tmp[1] = tmp[1], tmp[0]                         # unswap bytes
        
        return bytes(tmp)
    else:
        return hex

# function to get an rgb value from bytes
def get_rgb(bytes, channel):
    hex = "".join(f"{byte:02X}" for byte in bytes)                  # converts raw bytes into a hex color string essentially

    while len(hex) % (channel * 2) != 0:                            # if the hex color doesn't contain the respected amount of bytes for its channel then its not complete and needs padding
        hex += "FF"                                                 # pad unfinished hex colors with white (FF)
    
    tmp = [hex[i:i+2] for i in range(0, len(hex), 2)]               # turn byte string into a list
        
    tmp[0], tmp[1] = tmp[1], tmp[0]                                 # swap bytes, add a bit of more obfuscation to avoid someone from converting pixels to bytes on their own time
    tmp[0], tmp[channel - 1] = tmp[channel - 1], tmp[0]             # swap bytes, add a bit of more obfuscation to avoid someone from converting pixels to bytes on their own time
    
    hex = "".join(tmp)
    
    # ternary because cleaner (imo)
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)) if channel == 3 else tuple(int(hex[i:i+2], 16) for i in (0, 2, 4, 6))

# function to print progress and eta
def get_progress(index, total, start):
    percent = index / total * 100                               # the percentage
    
    if percent % 100 != 0:
        overall = (time.time() - start) / (percent / 100)       # the overall amount of time
        remaining = max((start + overall) - time.time(), 0)     # the time remaining until finish
        
        print(f"Progress: {index}/{total} {percent:.2f}% {time.strftime('%I:%M:%S %p', time.localtime(time.time() + remaining))}", end="\r")
    
# function to essentially plot the bytes to the png
def get_pixels(bytes, channel):
    pixels = []
    start = time.time()

    for i in range(0, len(bytes), channel):
        get_progress(i, len(bytes), start)
        pixels.append(get_rgb(bytes[i:i+channel], channel))
    
    return pixels

# main encoding function (turning the file into an image)
def encode(file, name, channel):
    try:
        data = get_bytes(file)                                                                  # the bytes of the file
        pixels = get_pixels(data, channel)                                                      # essentially the plotted pixels on the png
        x = get_dim(file, channel)                                                              # the x dimension of the png
        y = math.ceil(x / 8)                                                                    # the y dimension of the png, divided by 8 to remove unused space
        
        if channel == 4:
            image = Image.new("RGBA", (x, y), color=(255,255,255,255))                          # create a new image with a white background using RGBA
        else:
            image = Image.new("RGB", (x, y), color="white")                                     # create a new image with a white background using RGB (no alpha)
            
        image.putdata(pixels)                                                                   # add the pixels
        
        pinfo = PngImagePlugin.PngInfo()                                                        # since png doesn't use exif we need to use this, tEXt did not work for some reason
        pinfo.add_itxt(root, base64.b64encode(os.path.splitext(file)[1].lower().encode("utf-8")))
        pinfo.add_itxt(ogs, str(len(data)))
        pinfo.add_itxt(chann, str(channel))
        pinfo.add_itxt(vers, str(version))                                                      
        
        if not os.path.exists(str(file).replace(f.name, f"f2i{channel}")):
            os.makedirs(str(file).replace(f.name, f"f2i{channel}"))                             # if the directory doesn't exist, create it (this will store the encoded files)
        
        print()                                                                                 # bad way to stop progress from bleeding into the print below but it works :?
        print(f"Image created with {len(pixels)} pixels","\n")
        image.save(str(file).replace(f.name, f"f2i{channel}/" + name + ".png"), pnginfo=pinfo)  # create the image
    except FileNotFoundError:
        raise FileNotFoundError("File could not be found!")

# main decoding function (turning an f2i image back into a file)
def decode(file, name):
    try:
        data = io.BytesIO()                                                                     # create a buffer to hold bytes
        image = Image.open(file)                                                                # open the image
        pixels = image.getdata()                                                                # get the pixels of the image
        ofs = 0
        channel = 0
        verz = 0
        
        if ogs.decode("utf-8") in image.info and image.info[ogs.decode("utf-8")]:
            ofs = int(image.info[ogs.decode("utf-8")])
        
        if chann.decode("utf-8") in image.info and image.info[chann.decode("utf-8")] is not None:
            channel = int(image.info[chann.decode("utf-8")])
        
        if vers.decode("utf-8") in image.info and image.info[vers.decode("utf-8")] is not None:
            verz = version                                                                      # lazy
                
        if root.decode("utf-8") in image.info and image.info[root.decode("utf-8")] is not None: 
            ext = base64.b64decode(image.info[root.decode("utf-8")]).decode("utf-8")            # get the files original extension 
            start = time.time()
            
            for i, pixel in enumerate(pixels):
                get_progress(i, len(pixels), start)                                                    
                data.write(get_hex(pixel, channel, verz))                                       # turn the pixels into bytes and add them to the buffer we created
        
            length = data.tell()                                                                # get the size of the buffer
            index = 0
                  
            for i, byte in enumerate(reversed(bytearray(data.getvalue()))):                     # cant enumerate through a buffer so we turn it into a bytearray
                if i > ofs:                                                                     # more efficient than previous method, no data loss (checks if any data is past the original files size)
                    index = i - 1
                    break
            
            print()                                                                             # bad way to stop progress from bleeding into the print below but it works :?  
            print(f"Removed {length - index} of excess data", "\n")                          
            data.truncate(index)                                                                # remove all extra data
        
            with open(str(file).replace(file.name, name + ext), "wb") as f:
                f.write(data.getvalue())       
        else:
            print()                                                                             # bad way to stop progress from bleeding into the print below but it works :?  
            print(f"Skipping {str(file.name)} because its not a valid f2i png or its corrupted!", "\n")
        
        data.close()
            
    except FileNotFoundError:
        raise FileNotFoundError("File could not be found!")

print("RGB: Generates a smaller file but with more pixels.\nRGBA: Averagely generates a bigger file but with less pixels.")
print("Program defaults to 'encode' and 'RGB' if nothing is entered!\n")
while True:
    file = input("Path to file/directory (or 'exit' to quit): ")
    if file.lower() == "exit": break
    
    mode = input("Would you like to 'encode' or 'decode'?: ")
    mode = 0 if mode.lower() not in modes else modes.get(mode.lower())
    if not mode == 1:
        channel = input("Use 'RGB' or 'RGBA'?: ")
        channel = 3 if channel.lower() not in channels else channels.get(channel.lower())
        
    if os.path.isdir(file):
        for f in Path(file).iterdir():
            if f.is_file():                
                if os.path.splitext(f)[1].lower() == ".png" and mode == 1:
                    decode(f, f.stem)
                else:
                    if mode == 0: encode(f, f.stem, channel)
    elif os.path.isfile(file):
        name = os.path.splitext(file.name)[0]
        
        if file.lower().endswith(".png") and mode == 1:
            decode(file, name)
        else:
            if mode == 0: encode(file, name, channel)
    else:
        print("File or directory not found, please enter a valid path!")
