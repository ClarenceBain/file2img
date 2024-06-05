import base64
import codecs
import io
import math
import os
import random
import tkinter as tk
from tkinter import filedialog
import dearpygui.dearpygui as dpg
from PIL import Image, PngImagePlugin

color_channels = ["RGB", "RGBA"]
current_channel = 3
max_image_pixels = None
should_encode = True
obfuscate_pixels = True
script_version = 2
example_hex = "AABBCC"
example_swapped_hex = "AABBCC"

swap = None
swap_information = None

select_file = None
select_file_version = None
file_channel = "ccu"
file_ext = "ext"
file_size_og = "ofs"
file_swap = "csd"
file_version = "ver"


Image.MAX_IMAGE_PIXELS = max_image_pixels

def Log(info):
    current = dpg.get_value("easy_logger")
    dpg.set_value("easy_logger", current + "\n" + info)

def GetCurrentChannelString():
    if current_channel == 3:
        channel = "RGB"
    elif current_channel == 4:
        channel = "RGBA"
    else:
        channel = "RGB"
   
    return channel

def OpenFile():
    global select_file
    global select_file_version
    global swap
    global swap_information
    global example_hex
    global example_swapped_hex
    
    select_file_version = None
    swap = None
    swap_information = None
    example_hex = "AABBCC" if current_channel == 3 else "AABBCCDD"
    example_swapped_hex = "AABBCC" if current_channel == 3 else "AABBCCDD"
    dpg.set_value("current_swapinfo_text", "Swap Information: " + str(swap_information))
    dpg.set_value("easy_logger", "")
    dpg.set_value("ex_swap_hex", example_hex + " becomes " + example_swapped_hex)

    root = tk.Tk()
    root.withdraw()
    select_file = filedialog.askopenfilename()
    if select_file == "" or select_file is None:
        select_file = None
        root.destroy()
        return
    root.destroy()
    
    dpg.set_value("current_file_text", "File: " + select_file + "\nFile Size: " + str(len(GetFileBytes(select_file))))
    dpg.show_item("convert_or_decode_button")
    dpg.show_item("current_swapinfo_text")
    dpg.show_item("easy_logger")
    dpg.show_item("information_logger")
    dpg.show_item("reswap_button")
    dpg.show_item("ex_swap_hex")
    
    if ".png" in os.path.basename(select_file):
        image = Image.open(select_file)
        pixels = image.getdata()
        dpg.set_value("current_file_text", "Image: " + select_file + "\nImage Size: " + str(len(GetFileBytes(select_file))) + "\nImage Pixels: " + str(len(pixels)))
        if "ZXh0" in image.info and image.info.get("ZXh0") is not None or "ext" in image.info and image.info.get("ext") is not None:
            if "dmVy" in image.info and image.info.get("dmVy") is not None or "ver" in image.info and image.info.get("ver") is not None:
                version = b64decode(image.info.get("dmVy")) or image.info.get("ver")
            dpg.set_value("current_file_text", "Image: " + select_file + "\nImage Size: " + str(len(GetFileBytes(select_file))) + "\nImage Pixels: " + str(len(pixels)) + "\nfile2img Version: " + version or "None")
            dpg.set_item_label("convert_or_decode_button", "Revert")
            dpg.set_item_callback("convert_or_decode_button", ImageToFile)
            dpg.hide_item("ex_swap_hex")
            dpg.hide_item("reswap_button")
            select_file_version = int(version)
        elif "cm9vdA==" in image.info and image.info.get("cm9vdA==") is not None:
             if "dmVyc2lvbg==" in image.info and image.info.get("dmVyc2lvbg==") is not None:
                 version = "1"
                 select_file_version = 1 # there only ever was 1.8..
             elif "b2Zz" in image.info and image.info.get("b2Zz") is not None:
                 version = "-1 (converted before versions were stored with f2i images)"
                 select_file_version = 0
                 dpg.hide_item("current_swapinfo_text")
                 dpg.hide_item("ex_swap_hex")
                 dpg.hide_item("reswap_button")
             dpg.set_value("current_file_text", "Image: " + select_file + "\nImage Size: " + str(len(GetFileBytes(select_file))) + "\nImage Pixels: " + str(len(pixels)) + "\nfile2img Version: " + version or "None")
             dpg.set_item_label("convert_or_decode_button", "Revert")
             dpg.set_item_callback("convert_or_decode_button", ImageToFile)
             dpg.hide_item("ex_swap_hex")
             dpg.hide_item("reswap_button")
             
        if select_file_version is not None and select_file_version >= 2:
            dpg.set_value("current_swapinfo_text", "Swap Information: " + (b64decode(image.info.get("Y3Nk")) if image.info.get("Y3Nk") is not None else image.info.get("csd") if image.info.get("csd") is not None else "None"))
       
        image.close()
    else:
        dpg.set_value("current_file_text", "File: " + select_file + "\nFile Size: " + str(len(GetFileBytes(select_file))))
        dpg.set_item_label("convert_or_decode_button", "Convert")
        dpg.set_item_callback("convert_or_decode_button", FileToImage)
            
def UpdateChannel(Sender):
    global current_channel
    global example_hex
    global example_swapped_hex

    if dpg.get_value(Sender) == "RGB":
        current_channel = 3
        example_hex = "AABBCC"
        example_swapped_hex = "AABBCC"
    if dpg.get_value(Sender) == "RGBA":
        current_channel = 4
        example_hex = "AABBCCDD"
        example_swapped_hex = "AABBCCDD"
    else:
        current_channel = 3
        example_hex = "AABBCC"
        example_swapped_hex = "AABBCC"
    
    dpg.set_value("ex_swap_hex", example_hex + " becomes " + example_swapped_hex)
    dpg.set_value("current_channel_text", "Current Channel: " + GetCurrentChannelString())

def UpdateEncode(Sender):
    global should_encode
    
    should_encode = dpg.get_value("base64_checkbox")
    dpg.set_value("current_encodeb_text", "Is Encoding File Information: " + str(should_encode))

def UpdateMaxImagePixel(Sender):
    global max_image_pixels
    
    if dpg.get_value(Sender) <= -1:
        max_image_pixels = None
        dpg.set_value(Sender, -1)
    elif dpg.get_value(Sender) == 0:
        max_image_pixels = 1
        dpg.set_value(Sender, 1)
    else:
        max_image_pixels = dpg.get_value(Sender)
    
    Image.MAX_IMAGE_PIXELS = max_image_pixels
    dpg.set_value("current_mppi_text", "Max Pixels Per Image: " + str(Image.MAX_IMAGE_PIXELS))

def UpdateObs(Sender):
    global obfuscate_pixels
    
    obfuscate_pixels = dpg.get_value("obs_checkbox")
    dpg.set_value("current_obs_text", "Is Obsfuscating Pixels: " + str(obfuscate_pixels))

def b64decode(b64):
    try:
        return base64.b64decode(b64).decode("utf-8")
    except TypeError:
        return None
        
    
## image stuff

def Swap():
    global swap
    global swap_information
    global example_swapped_hex
    
    swap = None
    swap_information = None
    
    pseudo = example_hex
    tmp = []
    swap = []
    
    for byte in range(0, len(pseudo), 2):
        tmp.append(pseudo[byte:byte+2])
        
    while len(swap) == 0:
        swap.clear()
        for original in range(len(tmp)):
            new = random.randint(0, len(tmp) - 1)
            swap.append((original, new))
        for original, new in swap:
            tmp[original], tmp[new] = tmp[new], tmp[original]
            
    swap_information = ",".join([f"{original}->{new}" for original, new in swap])
    example_swapped_hex = "".join(tmp)

    dpg.set_value("current_swapinfo_text", "Swap Information: " + str(swap_information))
    dpg.set_value("ex_swap_hex", example_hex + " becomes " + example_swapped_hex)
    

def GetFileBytes(file):
    with open(file, "rb") as data:
        return data.read()

def GetNewImageDimensions(file):
    size = len(GetFileBytes(file))
    bits = size * 8
    
    x = math.ceil(math.sqrt(bits / current_channel))
    y = math.ceil(x / 8)
    
    return x,y

def ColorToBytes(rgb, channel, version, swapinfo):
    if channel == 3:
        rgb_bytes = codecs.decode("{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2]), 'hex_codec')
    elif channel == 4:
        rgb_bytes = codecs.decode("{:02X}{:02X}{:02X}{:02X}".format(rgb[0], rgb[1], rgb[2], rgb[3]), 'hex_codec')
    
    if version == 1:
        tmp = list(rgb_bytes)
               
        tmp[0], tmp[channel - 1] = tmp[channel - 1], tmp[0] 
        tmp[0], tmp[1] = tmp[1], tmp[0]

        return bytes(tmp)
    elif version >= 2 and swapinfo is not None:
        swaps = []
        swapsplit = swapinfo.split(",")
        tmp = list(rgb_bytes)
        
        for sw in swapsplit:
            o,n = sw.split("->")
            swaps.append((int(n), int(o)))
        
        for new, original in reversed(swaps):
            tmp[new], tmp[original] = tmp[original], tmp[new]

        return bytes(tmp)
    else:
        return rgb_bytes

def HexToColorTuple(hex_color):
    color = []
    
    if current_channel == 3:
        for i in (0, 2, 4):
            color.append(int(hex_color[i:i+2], 16))
    elif current_channel == 4:
         for i in (0, 2, 4, 6):
            color.append(int(hex_color[i:i+2], 16))   
    
    return tuple(color)

def BytesToColor(byte_data):
    global swap
    global swap_information
    
    hex_color = "".join(f"{byte:02X}" for byte in byte_data)
    
    while len(hex_color) % (current_channel * 2) != 0:
        hex_color += "FF"
    
    tmp = []
    
    for byte in range(0, len(hex_color), 2):
        tmp.append(hex_color[byte:byte+2])
            
    if swap == None and obfuscate_pixels:
        while example_hex == example_swapped_hex:
            Swap()
        for original, new in swap:
            tmp[original], tmp[new] = tmp[new], tmp[original]
    elif swap and obfuscate_pixels:
        for original, new in swap:
            tmp[original], tmp[new] = tmp[new], tmp[original]
    
    if obfuscate_pixels and swap_information == None:
        swap_information = ",".join([f"{original}->{new}" for original, new in swap])
    dpg.set_value("current_swapinfo_text", "Swap Information: " + str(swap_information))
                
    hex_color = "".join(tmp)

    return HexToColorTuple(hex_color)

def PlotPixels(byte_data):
    pixels = []
    
    for i in range(0, len(byte_data), current_channel):
        pixels.append(BytesToColor(byte_data[i:i+current_channel]))
        dpg.set_value("information_logger", str(i + 1) + "/" + str(len(byte_data)) + "\n" + (str(math.ceil((i + 1) / len(byte_data) * 100))) + "%")
    
    return pixels

def FileToImage():
    global file_channel
    global file_ext
    global file_size_og
    global file_swap
    global file_version
    global swap
    
    if select_file is not None:
        file_data = GetFileBytes(select_file)
        Log("Starting conversion for " + os.path.basename(select_file))
        dpg.hide_item("reswap_button")
        x, y = GetNewImageDimensions(select_file)
        Log("Creating picture with dimensions: " + str(x) + "x" + str(y))
        file_extension = os.path.splitext(select_file)[1].lower()
        Log("Plotting pixels, this may take some time..")
        pixels = PlotPixels(file_data)
        
        if current_channel == 3:
            image = Image.new("RGB", (x, y), color="white")
        elif current_channel == 4:
            image = Image.new("RGBA", (x, y), color=(255,255,255,255))
         
        image.putdata(pixels)
        
        png_info = PngImagePlugin.PngInfo()
        
        if should_encode:
            Log("Encoding..")
            file_channel = base64.b64encode(file_channel.encode("utf-8"))
            file_ext = base64.b64encode(file_ext.encode("utf-8"))
            file_size_og = base64.b64encode(file_size_og.encode("utf-8"))
            file_swap = base64.b64encode(file_swap.encode("utf-8"))
            file_version = base64.b64encode(file_version.encode("utf-8"))
            
        png_info.add_itxt(file_channel, base64.b64encode(str(current_channel).encode("utf-8")) if should_encode else str(current_channel))
        png_info.add_itxt(file_ext, base64.b64encode(file_extension.encode("utf-8")) if should_encode else file_extension)
        png_info.add_itxt(file_size_og, base64.b64encode(str(len(file_data)).encode("utf-8")) if should_encode else str(len(file_data)))
        if obfuscate_pixels:
            png_info.add_itxt(file_swap, base64.b64encode(swap_information.encode("utf-8")) if should_encode else swap_information)
        png_info.add_itxt(file_version, base64.b64encode(str(script_version).encode("utf-8")) if should_encode else str(script_version))
        
        file_channel = "ccu"
        file_ext = "ext"
        file_size_og = "ofs"
        file_swap = "csd"
        file_version = "ver"
        swap = None

        if not os.path.exists(select_file.replace(os.path.basename(select_file), f"f2i{current_channel}")):
            os.makedirs(select_file.replace(os.path.basename(select_file), f"f2i{current_channel}"))
        
        image.save(select_file.replace(os.path.basename(select_file), f"f2i{current_channel}/" + os.path.basename(select_file) + ".png"), pnginfo=png_info)
        Log("Finished.")
        dpg.show_item("reswap_button")
        image.close()

def ImageToFile():
    if ".png" in os.path.basename(select_file) and select_file_version is not None:
        Log("Starting reversion for " + os.path.basename(select_file))
        file_data = io.BytesIO()
        image = Image.open(select_file)
        pixels = image.getdata()
        version = select_file_version
        Log("file2img version: " + str(version))
        channel = image.info.get("Y2hhbm5lbA==") or b64decode(image.info.get("Y2N1")) or image.info.get("ccu")
        Log("Channel used: " + str(channel))
        ofs = image.info.get("b2Zz") if version < 2 else b64decode(image.info.get("b2Zz")) or image.info.get("ofs")
        Log("File size: " + str(ofs))
        ext = b64decode(image.info.get("cm9vdA==")) or b64decode(image.info.get("ZXh0")) or image.info.get("ext")
        Log("Extension: " + ext)
        swapinfo = None
        
        if select_file_version >= 2:
            swapinfo = b64decode(image.info.get("Y3Nk")) or image.info.get("csd")
            Log("Swap: " + swapinfo)
        
        if channel and ofs and ext:
            Log("Converting pixels back to data..")
            for i, pixel in enumerate(pixels):
                file_data.write(ColorToBytes(pixel, int(channel), int(version), swapinfo))
                dpg.set_value("information_logger", str(i + 1) + "/" + str(len(pixels)) + "\n" + (str(math.ceil((i + 1) / len(pixels) * 100))) + "%")
                
            length = file_data.tell()
            index = 0
            
            for i, byte in enumerate(reversed(bytearray(file_data.getvalue()))):
                if i > int(ofs):
                    index = i - 1
                    Log("Removing padding after " + str(index))
                    break
                
            file_data.truncate(index)
            
            with open(select_file.replace(os.path.basename(select_file), os.path.basename(select_file).replace(".png", "") + ext), "wb") as f:
                f.write(file_data.getvalue())
        
        Log("Finished.")
        file_data.close()
            
dpg.create_context()
dpg.create_viewport(title="file2img", resizable=False, width=600, height=540)
dpg.setup_dearpygui()

with dpg.window(tag="main"):
    
    with dpg.menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Open..", callback=OpenFile)
            
    with dpg.tab_bar(tag="main_tb"):
        with dpg.tab(label="Home"):
            dpg.add_text("There is currently no file selected. Go to File -> Open.. to select a file.", tag="current_file_text")
            dpg.add_text("Swap Information: " + str(swap_information), tag="current_swapinfo_text")
            dpg.add_text(example_hex + " becomes " + example_swapped_hex, tag="ex_swap_hex")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Convert", callback=FileToImage, tag="convert_or_decode_button")
                dpg.add_button(label="Pre-Swap", callback=Swap, tag="reswap_button")
            dpg.add_input_text(tag="easy_logger", multiline=True, width=580, height=300, readonly=True)
            dpg.add_text("", tag="information_logger")
            dpg.hide_item("convert_or_decode_button")
            dpg.hide_item("current_swapinfo_text")
            dpg.hide_item("easy_logger")
            dpg.hide_item("information_logger")
            dpg.hide_item("reswap_button")
            dpg.hide_item("ex_swap_hex")
                    
        with dpg.tab(label="Settings"):
            dpg.add_text("Current Channel: " + GetCurrentChannelString(), tag="current_channel_text")
            dpg.add_text("Max Pixels Per Image: " + str(Image.MAX_IMAGE_PIXELS), tag="current_mppi_text")
            dpg.add_text("Is Encoding File Information: " + str(should_encode), tag="current_encodeb_text")
            dpg.add_text("Is Obsfuscating Pixels: " + str(obfuscate_pixels), tag="current_obs_text")
            dpg.add_separator()
            dpg.add_spacer(height=10)
            dpg.add_text("Color Channel Settings")
            dpg.add_listbox(label="Color Channels", num_items=2, items=color_channels, callback=UpdateChannel)
            with dpg.collapsing_header(label="Channel Information", default_open=False):
                with dpg.table(header_row=True):
                    dpg.add_table_column(label="Channel")
                    dpg.add_table_column(label="Description")
                    with dpg.table_row():
                        dpg.add_text("RGB")
                        dpg.add_text("Utilizes the Red, Green, and Blue channels to generate the image. \n\nTypically returns a smaller file size but contains more pixels.", wrap=280)
                    with dpg.table_row():
                        dpg.add_text("RGBA")
                        dpg.add_text("Utilizes the Red, Green, Blue, and Alpha channels to generate the image with the inclusion of opacity. \n\nTypically returns a bigger file size but contains less pixels.", wrap=280)
            dpg.add_spacer(height=5)
            dpg.add_text("Image Settings")
            dpg.add_input_int(label="Max Pixels Per Image", step=0, default_value=(Image.MAX_IMAGE_PIXELS if Image.MAX_IMAGE_PIXELS is not None else -1), callback=UpdateMaxImagePixel)
            dpg.add_checkbox(label="Base64 Encode File Information", default_value=True, tag="base64_checkbox", callback=UpdateEncode)
            dpg.add_checkbox(label="Obfuscate Pixels", default_value=True, tag="obs_checkbox", callback=UpdateObs)
            with dpg.collapsing_header(label="Image Settings Information", default_open=False):
                dpg.add_text("It is recommended to keep the Max Pixels Per Image set to -1 unless you fully know what you are doing. Changing this could break the script/conversion.", wrap=570)
                dpg.add_text("\nEncoding file information makes it so that information from the original file like extension, byte size, and more are unreadable until decoded. This is not foolproof protection but just a small layer of obfuscation if someone were to look at the images data.", wrap=570)
                dpg.add_text("\nObfuscating Pixels swaps RGB or RGBA values around so that someone trying to manually convert the pixels to byte information would get jibberish unless they knew what they were looking for -- but at this stage they would just use this script.", wrap=570)

dpg.show_viewport()
dpg.set_primary_window("main", True)
dpg.start_dearpygui()
dpg.destroy_context()