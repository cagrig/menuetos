import base64, bz2, sys, os, time
from FATtools import Volume, mkfat

import hashlib
import json
import subprocess


def get_files(folder_path, ext, exclude=None):
    ext = ext.lower().lstrip('.')
    matches = []
    
    if exclude is None:
        exclude = []
    
    # Normalize exclude list: convert to lowercase and absolute paths
    exclude_set = {os.path.abspath(x).lower() for x in exclude}

    for root, dirs, files in os.walk(folder_path):
        root = os.path.normpath(root)
        for file in files:
            if file.lower().endswith(f".{ext}"):
                full_path = os.path.abspath(os.path.join(root, file)).lower()
                if full_path not in exclude_set:
                    matches.append(os.path.join(root, file))
    
    return matches


BUILD_DIR = '../build'
KERNEL_DIR = 'K086B'
APP_DIR = 'A086B'

source_exclude = [
    '../src/' + APP_DIR + '/filelib.asm',
    '../src/' + APP_DIR + '/memlib.asm',
    '../src/' + APP_DIR + '/jpeglib.asm',
    '../src/' + APP_DIR + '/jpegdat.asm'
]

SOURCE_FILES = [*get_files('../src/' + APP_DIR, '.ASM', source_exclude)]
COPY_FILES = [
    *get_files('../src/' + APP_DIR, '.BMP'),
    *get_files('../src/' + APP_DIR, '.HTM'),
    *get_files('../src/' + APP_DIR, '.DAT'),
    *get_files('../src/' + APP_DIR, '.DTP'),
    *get_files('../src/' + APP_DIR, '.JPG'),
    *get_files('../src/' + APP_DIR, '.TXT'),
    *get_files('../src/' + APP_DIR, '.MP3'),
    *get_files('../src/' + APP_DIR, '.MT'),
    *get_files('../src/' + APP_DIR, '.PCX'),
    *get_files('../src/' + APP_DIR, '.RAW'),
    *get_files('../src/' + APP_DIR, '.LST'),
]
BOOT_SRC = '../src/BOOTMOSF.ASM'
BOOT_BIN = BUILD_DIR + '/BOOTMOSF.BIN'
KERNEL_SRC = '../src/' + KERNEL_DIR + '/KERNEL.ASM'
KERNEL_BIN = BUILD_DIR + '/' + KERNEL_DIR + '/KERNEL.MNT'
HASH_FILE = '.build_hash.json'
IMG_FILE = 'menuetos.img'
FLOPPY_SIZE = 1474560  # 1.44MB

def get_file_content(file_path):
    # Read the file content
    with open(file_path, 'rb') as f:
        file_data = f.read()

    # Compress using bz2
    compressed_data = bz2.compress(file_data)
    # print(compressed_data)

    # Encode to base64
    encoded_data = base64.b64encode(compressed_data)

    # Convert bytes to string (if needed) [bzipped then base64 encoded]
    return encoded_data.decode('utf-8')



def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()

def load_previous_hashes():
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE, 'r') as f:
        return json.load(f)

def save_hashes(hashes):
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

def any_file_changed(current_hashes, previous_hashes):
    for path, current_hash in current_hashes.items():
        if previous_hashes.get(path) != current_hash:
            return True
    return False

def compile_bootloader():
    print("Compiling %s.", BOOT_SRC)
    subprocess.check_call(['fasm', BOOT_SRC, BOOT_BIN])

def compile_kernel():
    print("Compiling %s.", KERNEL_SRC)
    subprocess.check_call(['fasm', KERNEL_SRC, KERNEL_BIN])
    return ["KERNEL.MNT", KERNEL_BIN]

def compile_source(src):
    print("Compiling %s.", src)
    if src.lower().endswith(".asm"):
        # filename = src[:-4]
        filename = os.path.splitext(os.path.basename(src))[0]
        bin = BUILD_DIR + '/' + APP_DIR + '/' + filename + ".BIN"
        try:
            res = subprocess.check_call(['fasm', src, bin])
            if res != 0:
                raise ValueError
            fs_filename = filename + "."
            return [fs_filename, bin]
        except Exception as e:
            print('Compile error: %s', src)
            return []


DEBUG=int(os.getenv('FATTOOLS_DEBUG', '0'))

if DEBUG:
    import logging
    logging.basicConfig(level=logging.DEBUG, filename='floppy.log', filemode='w')

def write_bootloader():

    OS = 'MenuetOS'

    floppy_size = 1440<<10

    print('Creating a %d KiB bootable floppy with %s'%(floppy_size//1024, OS))

    # Make floppy image
    f = open(IMG_FILE,'wb'); f.seek(floppy_size); f.truncate(); f.close()

    # Format & add boot code
    f = Volume.vopen(IMG_FILE, 'r+b', 'disk')
    mkfat.fat_mkfs(f, floppy_size)
    # Step 2: Read the current boot sector
    f.seek(0)
    boot = bytearray(f.read(512))  # Use bytearray to allow mutation

    # Step 3: Decode the bootloader binary (assumed base64-encoded bzipped)
    bootcode = bz2.decompress(base64.b64decode(get_file_content(BOOT_BIN)))

    # Step 4: Patch boot sector
    boot[0:3] = bootcode[0:3]     # Copy JMP + NOP
    boot[3:11] = bootcode[3:11]   # Copy OEM label (8 bytes)
    boot[11:510] = bootcode[11:510]  # Copy rest of bootloader, up to boot signature

    # Step 5: Preserve boot signature (0x55AA)
    boot[510:512] = b'\x55\xAA'

    print(boot[0:3], boot[3:11])

    # Step 6: Write back patched boot sector
    f.seek(0)
    f.write(boot)
    f.close()


def main():

    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR + '/' + KERNEL_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR + '/' + APP_DIR, exist_ok=True)

    # 1. Compute hashes for all source files
    ALL_SOURCE_FILES = [BOOT_SRC, KERNEL_SRC] + SOURCE_FILES
    current_hashes = {f: sha256_file(f) for f in ALL_SOURCE_FILES}
    previous_hashes = load_previous_hashes()

    f_img = None
    changed = False

    for path, current_hash in current_hashes.items():
        if previous_hashes.get(path) != current_hash or True:
            changed = True
            if (path == BOOT_SRC):
                compile_bootloader()
                write_bootloader()
            else:
                if path == KERNEL_SRC:
                    compiled = compile_kernel()
                else:
                    compiled = compile_source(path)
                
                if f_img == None:
                    f_img = Volume.vopen(IMG_FILE, 'r+b')

                if len(compiled) > 0:
                    h = f_img.create(compiled[0])
                    content = get_file_content(compiled[1])
                    buf = bz2.decompress(base64.b64decode(content))
                    print('%s, %d bytes' % (compiled[0], len(buf)))
                    h.write(buf)
                    h.Entry.chDOSPerms = 1 | 2 | 4 # Hidden, System, Read-Only
                    h.Entry.wCDate = 0
                    h.Entry.wCTime = 0
                    h.Entry.wADate = 0
                    h.close()

    if changed == True:
        save_hashes(current_hashes)

    time.sleep(5)

    current_copy_hashes = {f: sha256_file(f) for f in COPY_FILES}
    previous_hashes = load_previous_hashes()
    changed = False

    for path, current_hash in current_copy_hashes.items():
        if previous_hashes.get(path) != current_hash or True:
            changed = True
            isFile = os.path.isfile(path)
            print (path + " : " + str(isFile))
            if f_img == None:
                f_img = Volume.vopen(IMG_FILE, 'r+b')
                p = path.replace("\\", "/")
                Volume.copy_in([path], f_img)
            else:
                Volume.copy_in([path], f_img)

    if f_img != None:
        f_img.close()

    save_hashes({**current_hashes, **current_copy_hashes})

if __name__ == "__main__":
    main()