#!/usr/bin/env python3

import sys

if len(sys.argv) == 1:
	print("********************************************************")
	print("* if you just want to use this package, grab a release *")
	print("* from https://github.com/ixchow/kit-libs-win/releases *")
	print("*    This rebuild script may be full of ugly hacks!    *")
	print("********************************************************")
	exit(0)

import urllib.request
import os
import subprocess
import shutil
import platform
import re

if platform.system() == 'Linux':
	target = 'linux'
elif platform.system() == 'Darwin':
	target = 'macos'
elif platform.system() == 'Windows':
	target = 'windows'
else:
	exit("Unknown system '" + platform.system() + "'")

print("Will build for '" + target + "'")

work_folder = "work"

SDL2_filebase = "SDL2-2.0.10"
SDL2_urlbase = "https://www.libsdl.org/release/" + SDL2_filebase

glm_filebase = "glm-0.9.9.5"
glm_urlbase = "https://github.com/g-truc/glm/releases/download/0.9.9.5/" + glm_filebase

zlib_filebase = "zlib-1.2.11"
if target == 'windows':
	#for whatever reason, zipfile releases are named oddly:
	zlib_url = "http://zlib.net/zlib" +re.sub(r'[^0-9]','', zlib_filebase) + ".zip"
else:
	zlib_url = "http://zlib.net/" + zlib_filebase + ".tar.gz"

if target == 'windows':
	libpng_filebase = "lpng1637"
	libpng_url = "http://prdownloads.sourceforge.net/libpng/" + libpng_filebase + ".zip?download"
else:
	#TODO: files for *nix build
	pass

if not os.path.exists(work_folder):
	print("Creating work folder '" + work_folder + "'")
	os.mkdir(work_folder)

def run_command(args,cwd=None):
	print("  Running `\"" + '" "'.join(args) + "\"`")
	subprocess.run(args,cwd=cwd,check=True)

def remove_if_exists(path):
	if not os.path.exists(path):
		return
	if os.path.isdir(path):
		shutil.rmtree(path)
	else:
		os.remove(path)

def unzip_file(filename, folder):
	assert(target == 'windows')
	run_command([
		"C:\\Program Files\\7-Zip\\7z.exe",
		"x",
		"-o" + folder,
		filename
	])

def fetch_file(url, filename, checksum=None):
	if os.path.exists(filename):
		print("  File '" + filename + "' exists; TODO: check checksum.")
		return
	print("  Fetching '" + url + "' => '" + filename + "'")
	urllib.request.urlretrieve(url, filename)

def build_SDL2():
	SDL2_dir = work_folder + "/" + SDL2_filebase

	print("Cleaning any existing SDL2...")
	remove_if_exists(SDL2_dir)
	remove_if_exists(target + "/SDL2/")

	print("Fetching SDL2...")

	fetch_file(SDL2_urlbase + ".zip", work_folder + "/" + SDL2_filebase + ".zip")
	unzip_file(work_folder + "/" + SDL2_filebase + ".zip", work_folder)

	print("Building SDL2...")
	run_command([
		"msbuild",
		"SDL.sln",
		"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
		"/t:SDL2,SDL2main"
	], cwd=SDL2_dir + "/VisualC")


	print("Copying SDL2 files...")
	os.makedirs(target + "/SDL2/lib", exist_ok=True)
	os.makedirs(target + "/SDL2/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.lib", target + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2main.lib", target + "/SDL2/lib/")
	shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.dll", target + "/SDL2/dist/")
	shutil.copy(SDL2_dir + "/README-SDL.txt", target + "/SDL2/dist/")
	shutil.copytree(SDL2_dir + "/include/", target + "/SDL2/include/")

def build_glm():
	glm_dir = work_folder + "/glm"
	print("Cleaning any existing glm...")
	remove_if_exists(glm_dir)
	remove_if_exists(target + "/glm/")

	print("Fetching glm...")
	fetch_file(glm_urlbase + ".zip", work_folder + "/" + glm_filebase + ".zip")
	unzip_file(work_folder + "/" + glm_filebase + ".zip", work_folder)

	print("Copying glm files...")
	os.makedirs(target + "/glm/include", exist_ok=True)
	shutil.copytree(glm_dir + "/glm/", target + "/glm/include/glm/")

def build_zlib():
	zlib_dir = work_folder + "/" + zlib_filebase
	print("Cleaning any existing zlib...")
	remove_if_exists(zlib_dir)
	remove_if_exists(target + "/zlib/")

	print("Fetching zlib...")
	fetch_file(zlib_url, work_folder + "/" + zlib_filebase + ".zip")
	unzip_file(work_folder + "/" + zlib_filebase + ".zip", work_folder)

	print("Building zlib...")
	run_command([
		'nmake',
		'-f',
		'win32/Makefile.msc'
	], cwd=zlib_dir)

	print("Copying zlib files...")
	os.makedirs(target + "/zlib/lib", exist_ok=True)
	os.makedirs(target + "/zlib/include", exist_ok=True)
	if target == 'windows':
		shutil.copy(zlib_dir + "/zlib.lib", target + "/zlib/lib/")
		shutil.copy(zlib_dir + "/zlib.pdb", target + "/zlib/lib/")
	shutil.copy(zlib_dir + "/zconf.h", target + "/zlib/include/")
	shutil.copy(zlib_dir + "/zlib.h", target + "/zlib/include/")

def build_libpng():
	libpng_dir = work_folder + "/" + libpng_filebase

	print("Cleaning any existing libpng...")
	remove_if_exists(libpng_dir)
	remove_if_exists(target + "/libpng/")

	print("Fetching libpng...")
	fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".zip")
	unzip_file(work_folder + "/" + libpng_filebase + ".zip", work_folder)

	print("Building libpng...")
	#Patch makefile:
	with open(libpng_dir + "/scripts/makefile.vcwin32", "r") as f:
		with open(libpng_dir + "/scripts/makefile.vcwin32.patched", "w") as o:
			for line in f:
				line = line.replace("-I..\\zlib","-I..\\..\\windows\\zlib\\include")
				line = line.replace("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
				o.write(line)

	print("Building libpng...")
	run_command([
		'nmake',
		'-f',
		'scripts/makefile.vcwin32.patched'
	], cwd=libpng_dir)


	print("Copying libpng files...")
	os.makedirs(target + "/libpng/lib", exist_ok=True)
	os.makedirs(target + "/libpng/include", exist_ok=True)
	if target == 'windows':
		shutil.copy(libpng_dir + "/libpng.lib", target + "/libpng/lib/")
	shutil.copy(libpng_dir + "/png.h", target + "/libpng/include/")
	shutil.copy(libpng_dir + "/pngconf.h", target + "/libpng/include/")
	shutil.copy(libpng_dir + "/pnglibconf.h", target + "/libpng/include/")

to_build = sys.argv[1:]

if "all" in to_build:
	to_build = ["SDL2", "glm", "zlib", "libpng"]

if "SDL2" in to_build:
	build_SDL2();

if "glm" in to_build:
	build_glm();

if "zlib" in to_build:
	build_zlib();

if "libpng" in to_build:
	build_libpng();
