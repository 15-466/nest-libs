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

work_folder = "work"
SDL2_filebase = "SDL2-2.0.10"
SDL2_urlbase = "https://www.libsdl.org/release/" + SDL2_filebase

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

	remove_if_exists("windows/lib/SDL2.lib")
	remove_if_exists("windows/lib/SDL2main.lib")
	remove_if_exists("windows/dist/README-SDL.txt")
	remove_if_exists("windows/dist/SDL2.dll")
	remove_if_exists("windows/include/SDL2/")

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
	os.makedirs("windows/lib", exist_ok=True)
	os.makedirs("windows/dist", exist_ok=True)
	os.makedirs("windows/include", exist_ok=True)
	shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.lib", "windows/lib/")
	shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2main.lib", "windows/lib/")
	shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.dll", "windows/dist/")
	shutil.copy(SDL2_dir + "/README-SDL.txt", "windows/dist/")
	shutil.copytree(SDL2_dir + "/include", "windows/include/SDL2/")



if "SDL2" in sys.argv[1:]:
	build_SDL2();
