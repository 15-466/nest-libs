# Nest-libs: Pre-compiled binaries for 15-466

This repository's releases section contains pre-compiled library packages for our target systems: Linux, Windows, and MacOS.

Contents:
 - [SDL2](http://libsdl.org/)
 - [glm](https://glm.g-truc.net/)

## Usage:

The course's base-code Jamfile are set up to work properly if the `nest-libs/` directory has the same parent as the `15-466-f19-baseN` directory:

```
15-466-stuff/ #or whatever you call it
	nest-libs/
		...
	15-466-f19-base0/
		...
	your-game0/
		...
```

## Windows Notes:

Libraries compiled with, and intended to be used with, Visual Studio Community 2019.

Windows releases also include ftjam (`jam.exe`) and a convenient script to launch a VS2019 command prompt with jam in the path and `JAM_TOOLSET`. See [windows/tools](windows/tools).
