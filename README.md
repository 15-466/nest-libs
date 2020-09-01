# Nest-libs: Pre-compiled libraries for 15-466

This repository's releases section contains pre-compiled library packages for our target systems: Linux, Windows, and MacOS.

Contents:
 - [SDL2](http://libsdl.org/)
 - [glm](https://glm.g-truc.net/)
 - [libpng](http://www.libpng.org/pub/png/libpng.html) (static)
 - [zlib](http://www.zlib.net/) (static, required for libpng)
 - [libogg](https://xiph.org/) (static, required for opusfile)
 - [libopus](https://opus-codec.org/) (static, required for opusfile)
 - [opusfile](https://opus-codec.org/) (static)
 - [libopusenc](https://opus-codec.org/) (static, required for opus-tools)
 - [opus-tools](https://opus-codec.org/) -- just to have a reference build
 - [freetype](https://freetype.org/)
 - [harfbuzz](https://harfbuzz.github.io/)

## Usage

The course's base-code `Jamfile`s are set up to work properly if the `nest-libs/` directory has the same parent as your clone of the `15-466-f*-base*` directory:

```
15-466-stuff/ #or whatever you call it
	nest-libs/
		...
	your-game0/
		...
```

## Windows Notes

Libraries compiled with, and intended to be used with, Visual Studio Community 2019.

Windows releases also include ftjam (`jam.exe`) and a convenient script to launch a VS2019 command prompt with jam in the path and `JAM_TOOLSET`. See [windows/jam](windows/jam). You may need to edit the shortcut and/or bat file to match your particular installation of Visual Studio.

## TODO

 - libjpeg-turbo, perhaps?
