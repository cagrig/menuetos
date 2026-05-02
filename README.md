# MenuetOS-086b

## What is MenuetOS?
MenuetOS is a very small, lightweight operating system written almost entirely in assembly language. It started as a 32-bit system (often just called MenuetOS), and later a separate 64-bit version was developed.

Key characteristics:

- Written in assembly language (FASM), making it extremely compact and fast.
- Very small footprint (can fit on a floppy-sized image in older versions).
- Includes a graphical user interface (GUI), multitasking, and basic applications.
- Runs directly on hardware (bare metal), without needing Linux or Windows underneath.

In short, MenuetOS is a proof-of-concept operating system showing how a full GUI OS can be built with minimal size and very low-level programming.

## Why this repository exists?

This repository contains the source tree and build support for [MenuetOS](https://menuetos.net). MenuetOS website has 32-bit release (v0.86b) and floppy image. However, compiling that released source code is not directly possible due to the errors. After fixing compile errors, I have seen that built image is not properly functioning and it is not same with released v0.86b image. To build, reproducible MenuetOS 32-bit v0.86b; I did following changes:

- Fix compile errors in these files: `CALC.ASM`, `JPEGDAT.ASM`, `JPEGLIB.ASM`, `JPEGVIEW.ASM`, `MIXER.ASM`, `PIC4.ASM`, `TERMINAL.ASM`, `TFTPC.ASM`, `launcher.ASM`.
- Replaced .raw files `BASE.RAW`, `LEFT.RAW`, `OPER.RAW` with released images' ones.
- Updated start menu (mpanel) and desktop app lists (`MPANEL.DAT` and `ICON.LST`). Removed not existing applications from lists. Also, added missing BMP icons (Copied from released image).

With above changes, baseline source code and image of MenuetOS 32-bit v0.86b can be found in releases page.

## Repository layout

- `src/`
  - Assembly source files for the bootloader, kernel, and user-space applications.
  - Two main source subdirectories: `A086B/` for applications and `K086B/` for the kernel.
- `build/`
  - Output directory for build artifacts and generated image files.
- `build_tools/`
  - Build scripts and requirements.
- `misc/`
  - Miscellaneous files and backup data.

## Build tools

- `build_tools/build_image.py`
  - Python build script that compiles assembly sources using `fasm`.
  - Creates a bootable floppy image `build/menuetos.img`.
  - Uses `FATtools` to format the image and add compiled files.
- `build_tools/requirements.txt`
  - Python dependency list for the build environment.

## Dependencies

- `fasm` assembler available on the system path.
- Python 3.x.
- Python package: `FATtools==1.1.6`.

## Usage

1. Install the Python dependency:

   ```powershell
   python -m pip install -r build_tools/requirements.txt
   ```

2. Run the build script from `build_tools/`:

   ```powershell
   python .\build_image.py
   ```

3. The floppy image is generated at:

   ```text
   build/menuetos.img
   ```

## Notes

- The Python build script currently compiles all assembly sources in `src/A086B/` and `src/K086B/` and writes the resulting binaries into the image.
- This repository is based on original source code of MenuetOS-32 0.86b.

## File locations

- Bootloader source: `src/BOOTMOSF.ASM`
- Kernel source: `src/K086B/KERNEL.ASM`
- Application sources: `src/A086B/*.ASM`
- Output image: `build/menuetos.img`
- Build hash metadata: `build/.build_hash.json`
