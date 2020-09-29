#!/usr/bin/env python3

import sys

if len(sys.argv) == 1:
	print("********************************************************")
	print("* if you just want to use this package, grab a release *")
	print("*   from https://github.com/15-466/nest-libs/releases  *")
	print("*    This rebuild script may be full of ugly hacks!    *")
	print("********************************************************")
	exit(0)

import urllib.request
import os
import subprocess
import shutil
import platform
import re

tag = "vUNKNOWN"

if 'TAG_NAME' in os.environ and os.environ['TAG_NAME'] != '':
	tag = os.environ['TAG_NAME']
	print("Set tag from $TAG_NAME to '" + tag + "'")
elif 'GITHUB_SHA' in os.environ:
	tag = os.environ['GITHUB_SHA'][0:8]
	print("Set tag from $TAG_NAME to '" + tag + "'")

min_osx_version='10.7'

if platform.system() == 'Linux':
	target = 'linux'
elif platform.system() == 'Darwin':
	target = 'macos'
elif platform.system() == 'Windows':
	target = 'windows'
else:
	exit("Unknown system '" + platform.system() + "'")

print("Will build for '" + target + "'")

if target == 'macos':
	if os.path.exists('/usr/local/bin/ranlib'):
		print(" *** WARNING: having brew binutils installed breaks things badly *** ")
		sleep(1)

work_folder = "work"

SDL2_filebase = "SDL2-2.0.12"
SDL2_urlbase = "https://www.libsdl.org/release/" + SDL2_filebase

glm_filebase = "glm-0.9.9.8"
glm_urlbase = "https://github.com/g-truc/glm/releases/download/0.9.9.8/" + glm_filebase

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
	libpng_filebase = "libpng-1.6.37"
	libpng_url = "http://prdownloads.sourceforge.net/libpng/" + libpng_filebase + ".tar.gz?download"

libogg_filebase = "libogg-1.3.4"
libogg_urlbase = "http://downloads.xiph.org/releases/ogg/" + libogg_filebase

libopus_filebase = "opus-1.3.1"
libopus_url = "https://archive.mozilla.org/pub/opus/" + libopus_filebase + ".tar.gz"

opusfile_filebase = "opusfile-0.12"
opusfile_url = "https://downloads.xiph.org/releases/opus/" + opusfile_filebase + ".tar.gz"

libopusenc_filebase = "libopusenc-0.2.1"
libopusenc_url = "https://archive.mozilla.org/pub/opus/" + libopusenc_filebase + ".tar.gz"

opustools_filebase = "opus-tools-0.2"
opustools_url = "https://archive.mozilla.org/pub/opus/" + opustools_filebase + ".tar.gz"

jam_file = 'ftjam-2.5.2-win32.zip'
jam_url = 'https://sourceforge.net/projects/freetype/files/ftjam/2.5.2/' + jam_file + '/download'

freetype_filebase = 'freetype-2.10.2'
freetype_url = 'https://download.savannah.gnu.org/releases/freetype/' + freetype_filebase + '.tar.gz'

harfbuzz_filebase = '2.7.2'
harfbuzz_urlbase = 'https://github.com/harfbuzz/harfbuzz/archive/' + harfbuzz_filebase

if not os.path.exists(work_folder):
	print("Creating work folder '" + work_folder + "'")
	os.mkdir(work_folder)

def run_command(args,cwd=None,env=None):
	print("  Running `\"" + '" "'.join(args) + "\"`")
	subprocess.run(args,cwd=cwd,check=True,env=env)

def remove_if_exists(path):
	if not os.path.exists(path):
		return
	if os.path.isdir(path):
		shutil.rmtree(path)
	else:
		os.remove(path)

def unzip_file(filename, folder):
	if target == 'windows':
		run_command([
			"C:\\Program Files\\7-Zip\\7z.exe",
			"x",
			"-o" + folder,
			filename
		])
	else:
		run_command([
			"unzip",
			"-q",
			filename,
			"-d", folder
		])

def replace_in_file(filename, replacements):
	os.rename(filename, filename + ".before")
	with open(filename + ".before", "r") as f:
		with open(filename, "w") as o:
			for line in f:
				for r in replacements:
					line = line.replace(r[0], r[1])
				o.write(line)

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
	if target == 'windows':
		fetch_file(SDL2_urlbase + ".zip", work_folder + "/" + SDL2_filebase + ".zip")
		unzip_file(work_folder + "/" + SDL2_filebase + ".zip", work_folder)
	else:
		fetch_file(SDL2_urlbase + ".tar.gz", work_folder + "/" + SDL2_filebase + ".tar.gz")
		run_command([
			'tar',
			'xfz',
			SDL2_filebase + ".tar.gz"
		], cwd=work_folder)

	print("Building SDL2...")
	if target == 'windows':
		run_command([
			"msbuild", "/m",
			"SDL.sln",
			"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
			"/t:SDL2,SDL2main"
		], cwd=SDL2_dir + "/VisualC")
	else:
		os.mkdir(SDL2_dir + '/build')
		env = os.environ.copy()
		prefix = os.getcwd() + '/' + SDL2_dir + '/out'
		if target == 'macos':
			env['CFLAGS'] = '-mmacosx-version-min=' + min_osx_version
			run_command(['../configure', '--prefix=' + prefix,
				'--disable-shared', '--enable-static',
				'--disable-render',
				#'--disable-haptic', #force feedback framework required by joystick code anyway
				#'--disable-file', '--disable-filesystem', #can't disable without link errors
				'--disable-loadso', '--disable-power',
				'--enable-sse2',
				'--disable-oss',
				'--disable-alsa',
				'--enable-alsa-shared',
				'--disable-jack',
				'--enable-jack-shared',
				'--disable-esd',
				'--disable-pulseaudio',
				'--enable-pulseaudio-shared',
				'--disable-arts',
				'--enable-arts-shared',
				'--disable-nas',
				'--disable-diskaudio',
				'--disable-dummyaudio',
				'--disable-sndio',
				'--disable-sndio-shared',
				'--disable-fusionsound',
				'--disable-fusionsound-shared',
				'--disable-video-x11',
				'--enable-video-cocoa',
				'--disable-video-directfb',
				'--disable-video-vulkan',
				'--disable-video-dummy',
				'--enable-video-opengl',
				'--disable-video-opengles',
				'--disable-input-tslib',
				'--enable-pthreads',
				'--enable-pthread-sem',
				'--disable-directx',
				'--disable-render',
				'--enable-sdl-dlopen',
			],env=env,cwd=SDL2_dir + '/build')
		else:
			run_command(['../configure', '--prefix=' + prefix,
				'--disable-shared', '--enable-static',
				'--disable-render', '--disable-haptic', '--disable-file', '--disable-filesystem', '--disable-loadso', '--disable-power',
				'--enable-sse2',
				'--disable-oss',
				'--enable-alsa',
				'--disable-esd',
				'--disable-pulseaudio',
				'--disable-arts',
				'--disable-nas',
				'--disable-diskaudio',
				'--disable-dummyaudio',
				'--disable-sndio',
				'--enable-video-x11',
				'--disable-video-cocoa',
				'--disable-video-directfb',
				'--disable-video-vulkan',
				'--disable-video-dummy',
				'--enable-video-opengl',
				'--disable-video-opengles',
				'--disable-input-tslib',
				'--enable-pthreads',
				'--enable-pthread-sem',
				'--disable-directx',
				'--disable-render',
				'--enable-sdl-dlopen',
			],env=env,cwd=SDL2_dir + '/build')
		run_command(['make'], cwd=SDL2_dir + '/build')
		run_command(['make', 'install'], cwd=SDL2_dir + '/build')

	print("Copying SDL2 files...")
	os.makedirs(target + "/SDL2/lib", exist_ok=True)
	os.makedirs(target + "/SDL2/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.lib", target + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2main.lib", target + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.dll", target + "/SDL2/dist/")
		shutil.copytree(SDL2_dir + "/include/", target + "/SDL2/include/")
	else:
		os.makedirs(target + "/SDL2/bin", exist_ok=True)
		with open(SDL2_dir + '/out/bin/sdl2-config', 'r') as i:
			with open(target + '/SDL2/bin/sdl2-config', 'w') as o:
				found_prefix = False
				for line in i:
					if re.match('^prefix=.*$', line) != None:
						assert(not found_prefix)
						o.write("prefix=../nest-libs/" + target + "/SDL2\n")
						found_prefix = True
					else:
						o.write(line)
				assert(found_prefix)
		os.chmod(target + '/SDL2/bin/sdl2-config', 0o744)
		shutil.copy(SDL2_dir + "/out/lib/libSDL2.a", target + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/out/lib/libSDL2main.a", target + "/SDL2/lib/")
		shutil.copytree(SDL2_dir + "/out/include/SDL2/", target + "/SDL2/include/SDL2/")
	shutil.copy(SDL2_dir + "/README-SDL.txt", target + "/SDL2/dist/")


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
	os.makedirs(target + "/glm/dist", exist_ok=True)
	shutil.copytree(glm_dir + "/glm/", target + "/glm/include/glm/")

	#process the "manual.md" file to extract the license notice section:
	with open(glm_dir + "/manual.md", 'rb') as infile:
		with open(target + "/glm/dist/README-glm.txt", 'wb') as outfile:
			in_licenses = False
			for line in infile:
				if b'name="section0"></a> Licenses' in line:
					in_licenses = True
					outfile.write(b"GLM is distributed under the following licenses:\n")
				elif b'name="section1"' in line:
					in_licenses = False
				elif b'<div style="page-break-after: always;"> </div>' == line.strip():
					pass
				elif b'![](./doc/manual/frontpage1.png)' == line.strip():
					pass
				elif b'![](./doc/manual/frontpage2.png)' == line.strip():
					pass
				elif b'---' == line.strip():
					pass
				elif in_licenses:
					outfile.write(line)


def build_zlib():
	zlib_dir = work_folder + "/" + zlib_filebase
	print("Cleaning any existing zlib...")
	remove_if_exists(zlib_dir)
	remove_if_exists(target + "/zlib/")

	print("Fetching zlib...")
	if target == 'windows':
		fetch_file(zlib_url, work_folder + "/" + zlib_filebase + ".zip")
		unzip_file(work_folder + "/" + zlib_filebase + ".zip", work_folder)
	else:
		fetch_file(zlib_url, work_folder + "/" + zlib_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', zlib_filebase + ".tar.gz" ], cwd=work_folder)


	print("Building zlib...")
	if target == 'windows':
		run_command([ 'nmake', '-f', 'win32/Makefile.msc' ], cwd=zlib_dir)
	else:
		env = os.environ.copy()
		env['prefix'] = 'out'
		if target == 'macos':
			env['CFLAGS'] = '-mmacosx-version-min=' + min_osx_version
		run_command(['./configure', '--static'], env=env, cwd=zlib_dir)
		run_command(['make'], cwd=zlib_dir)
		run_command(['make', 'install'], cwd=zlib_dir)

	print("Copying zlib files...")
	os.makedirs(target + "/zlib/lib", exist_ok=True)
	os.makedirs(target + "/zlib/include", exist_ok=True)
	if target == 'windows':
		shutil.copy(zlib_dir + "/zlib.lib", target + "/zlib/lib/")
		shutil.copy(zlib_dir + "/zlib.pdb", target + "/zlib/lib/")
		shutil.copy(zlib_dir + "/zconf.h", target + "/zlib/include/")
		shutil.copy(zlib_dir + "/zlib.h", target + "/zlib/include/")
	else:
		shutil.copy(zlib_dir + "/out/include/zconf.h", target + "/zlib/include/")
		shutil.copy(zlib_dir + "/out/include/zlib.h", target + "/zlib/include/")
		shutil.copy(zlib_dir + "/out/lib/libz.a", target + "/zlib/lib/")


def build_libpng():
	libpng_dir = work_folder + "/" + libpng_filebase

	print("Cleaning any existing libpng...")
	remove_if_exists(target + "/libpng/")
	remove_if_exists(libpng_dir)

	print("Fetching libpng...")
	if target == 'windows':
		fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".zip")
		unzip_file(work_folder + "/" + libpng_filebase + ".zip", work_folder)
	else:
		fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libpng_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building libpng...")
	if target == 'windows':
		#Patch makefile:
		replace_in_file(libpng_dir + "/scripts/makefile.vcwin32", [
			("-I..\\zlib","-I..\\..\\windows\\zlib\\include"),
			("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
		])
		run_command([
			'nmake',
			'-f',
			'scripts/makefile.vcwin32'
		], cwd=libpng_dir)
	else:
		prefix = os.getcwd() + '/' + libpng_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2 -L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		env['CFLAGS'] = '-O2 -L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		env['LDFLAGS'] = '-L../../' + target + '/zlib/lib'
		run_command(['./configure',
			'--prefix=' + prefix,
			'--with-zlib-prefix=../../' + target + '/zlib',
			'--disable-shared'], env=env, cwd=libpng_dir);
		run_command(['make'], cwd=libpng_dir)
		run_command(['make', 'install'], cwd=libpng_dir)

	print("Copying libpng files...")
	os.makedirs(target + "/libpng/lib", exist_ok=True)
	os.makedirs(target + "/libpng/include", exist_ok=True)
	os.makedirs(target + "/libpng/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(libpng_dir + "/libpng.lib", target + "/libpng/lib/")
		shutil.copy(libpng_dir + "/png.h", target + "/libpng/include/")
		shutil.copy(libpng_dir + "/pngconf.h", target + "/libpng/include/")
		shutil.copy(libpng_dir + "/pnglibconf.h", target + "/libpng/include/")
	else:
		shutil.copy(libpng_dir + "/out/include/libpng16/png.h", target + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/include/libpng16/pngconf.h", target + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/include/libpng16/pnglibconf.h", target + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/lib/libpng16.a", target + "/libpng/lib/")
		os.symlink("libpng16.a", target + "/libpng/lib/libpng.a")
	shutil.copy(libpng_dir + "/LICENSE", target + "/libpng/dist/README-libpng.txt")

def build_libogg():
	lib_name = "libogg"
	lib_dir = work_folder + "/" + libogg_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(libogg_urlbase + ".zip", work_folder + "/" + libogg_filebase + ".zip")
		unzip_file(work_folder + "/" + libogg_filebase + ".zip", work_folder)
	else:
		fetch_file(libogg_urlbase + ".tar.gz", work_folder + "/" + libogg_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libogg_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		#patch vcxproj to remove "WindowsTargetPlatformVersion" key:
		replace_in_file(lib_dir + "/win32/VS2015/libogg.vcxproj", [
			('<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>','')
		])
		run_command([
			"msbuild", "/m",
			"libogg.sln",
			"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
			"/t:libogg"
		], cwd=lib_dir + "/win32/VS2015")
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2'
		env['CFLAGS'] = '-O2'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		#env['LDFLAGS'] = '-L../../' + target + '/zlib/lib'
		run_command(['./configure',
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)
	print("Copying " + lib_name + " files...")
	os.makedirs(target + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/include/ogg", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/libogg.lib", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/ogg/ogg.h", target + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/include/ogg/os_types.h", target + "/" + lib_name + "/include/ogg/")
	else:
		shutil.copy(lib_dir + "/out/include/ogg/config_types.h", target + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/ogg.h", target + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/os_types.h", target + "/" + lib_name + "/include/ogg/")
		if target == 'macos':
			replace_in_file(target + "/" + lib_name + "/include/ogg/os_types.h", [
				("#  include <sys/types.h>", "#include <stdint.h>")
			])
		shutil.copy(lib_dir + "/out/lib/libogg.a", target + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + "/" + lib_name + "/dist/README-libogg.txt")

def build_libopus():
	lib_name = "libopus"
	lib_dir = work_folder + "/" + libopus_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(libopus_url, work_folder + "/" + libopus_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + libopus_filebase + ".tar")
		unzip_file(work_folder + "/" + libopus_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + libopus_filebase + ".tar", work_folder)
	else:
		fetch_file(libopus_url, work_folder + "/" + libopus_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libopus_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		#patch vcxproj to remove "WindowsTargetPlatformVersion" key:
		replace_in_file(lib_dir + "/win32/VS2015/opus.vcxproj", [
			('<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>','')
		])
		run_command([
			"msbuild", "/m",
			"opus.sln",
			"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
			"/t:opus"
		], cwd=lib_dir + "/win32/VS2015")
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2'
		env['CFLAGS'] = '-O2'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		run_command(['./configure',
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			'--disable-doc',
			'--disable-extra-programs'
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)
	
	print("Copying " + lib_name + " files...")
	os.makedirs(target + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opus.lib", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opus.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_multistream.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_types.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_defines.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_projection.h", target + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opus.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_multistream.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_types.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_defines.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_projection.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopus.a", target + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + "/" + lib_name + "/dist/README-libopus.txt")

def build_libopusenc():
	lib_name = "libopusenc"
	lib_dir = work_folder + "/" + libopusenc_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(libopusenc_url, work_folder + "/" + libopusenc_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + libopusenc_filebase + ".tar")
		unzip_file(work_folder + "/" + libopusenc_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + libopusenc_filebase + ".tar", work_folder)
	else:
		fetch_file(libopusenc_url, work_folder + "/" + libopusenc_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libopusenc_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		#patch vcxproj to adjust library paths:
		replace_in_file(lib_dir + "/win32/VS2015/opusenc.vcxproj", [
			("..\\..\\..\\opus\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libopus\\lib")
		])
		#patch props to adjust include paths:
		replace_in_file(lib_dir + "/win32/VS2015/common.props", [
			("..\\..\\..\\opus\\include",
			 "..\\..\\..\\..\\windows\\libopus\\include")
		])

		run_command([
			"msbuild", "/m",
			"opusenc.sln",
			"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
			"/t:opusenc"
		], cwd=lib_dir + "/win32/VS2015")
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2'
		env['CFLAGS'] = '-O2'
		env['DEPS_CFLAGS'] = '-I../../' + target + '/libogg/include -I../../' + target + '/libopus/include'
		env['DEPS_LIBS'] = '-L../../' + target + '/libogg/lib -L../../' + target + '/libopus/lib -lopus'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		run_command(['./configure',
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			'--disable-doc',
			'--disable-examples'
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)
	
	print("Copying " + lib_name + " files...")
	os.makedirs(target + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusenc.lib", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opusenc.h", target + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opusenc.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopusenc.a", target + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + "/" + lib_name + "/dist/README-libopusenc.txt")



def build_opusfile():
	lib_name = "opusfile"
	lib_dir = work_folder + "/" + opusfile_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(opusfile_url, work_folder + "/" + opusfile_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + opusfile_filebase + ".tar")
		unzip_file(work_folder + "/" + opusfile_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + opusfile_filebase + ".tar", work_folder)
	else:
		fetch_file(opusfile_url, work_folder + "/" + opusfile_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', opusfile_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		#patch vcxproj to adjust library and include paths:
		replace_in_file(lib_dir + "/win32/VS2015/opusfile.vcxproj", [
			("..\\..\\..\\opus\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libopus\\lib"),
			("..\\..\\..\\opus\\include",
			 "..\\..\\..\\..\\windows\\libopus\\include"),
			("..\\..\\..\\ogg\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libogg\\lib"),
			("..\\..\\..\\ogg\\include",
			 "..\\..\\..\\..\\windows\\libogg\\include")
		])
		run_command([
			"msbuild", "/m",
			"opusfile.sln",
			"/p:PlatformToolset=v142,Configuration=Release-NoHTTP,Platform=x64",
			"/t:opusfile"
		], cwd=lib_dir + "/win32/VS2015")
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2'
		env['CFLAGS'] = '-O2'
		env['DEPS_CFLAGS'] = '-I../../' + target + '/libogg/include -I../../' + target + '/libopus/include'
		env['DEPS_LIBS'] = '-L../../' + target + '/libogg/lib -L../../' + target + '/libopus/lib'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		#env['LDFLAGS'] = '-L../../' + target + '/zlib/lib'
		run_command(['./configure',
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			'--disable-http',
			'--disable-examples',
			'--disable-doc'
			#'--with-zlib-prefix=../../' + target + '/zlib',
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)

	print("Copying " + lib_name + " files...")
	os.makedirs(target + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release-NoHTTP/opusfile.lib", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opusfile.h", target + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opusfile.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopusfile.a", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/out/lib/libopusurl.a", target + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + "/" + lib_name + "/dist/README-opusfile.txt")

def build_opustools():
	lib_name = "opus-tools"
	lib_dir = work_folder + "/" + opustools_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(opustools_url, work_folder + "/" + opustools_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + opustools_filebase + ".tar")
		unzip_file(work_folder + "/" + opustools_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + opustools_filebase + ".tar", work_folder)
	else:
		fetch_file(opustools_url, work_folder + "/" + opustools_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', opustools_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		#patch config to remove libFLAC:
		replace_in_file(lib_dir + "/win32/config.h", [
			('#define HAVE_LIBFLAC','//#define HAVE_LIBFLAC')
		])

		#patch vcxproj to adjust library and include paths:
		replace_in_file(lib_dir + "/win32/VS2015/generate_version.vcxproj", [
			('<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>','')
		])
		replace_in_file(lib_dir + "/win32/VS2015/opus-tools.props", [
			("..\\..\\..\\opus\\include",
			 "..\\..\\..\\..\\windows\\libopus\\include"),
			("..\\..\\..\\ogg\\include",
			 "..\\..\\..\\..\\windows\\libogg\\include"),
			("..\\..\\..\\libopusenc\\include",
			 "..\\..\\..\\..\\windows\\libopusenc\\include"),
			("..\\..\\..\\opusfile\\include",
			 "..\\..\\..\\..\\windows\\opusfile\\include"),
			("..\\..\\..\\opus\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libopus\\lib"),
			("..\\..\\..\\ogg\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libogg\\lib"),
			("..\\..\\..\\libopusenc\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\libopusenc\\lib"),
			("..\\..\\..\\opusfile\\win32\\VS2015\\$(Platform)\\$(Configuration)",
			 "..\\..\\..\\..\\windows\\opusfile\\lib"),
			("libogg_static.lib", "libogg.lib"),
			(";libeay32.lib", ""),
			(";ssleay32.lib", ""),
			(";ws2_32.lib", ""),
			(";crypt32.lib", ""),
			(";libFLAC_static.lib", "")
		])
		run_command([
			"msbuild", "/m",
			"opus-tools.sln",
			"/p:PlatformToolset=v142,Configuration=Release,Platform=x64",
			"/t:opusdec,opusenc,opusinfo"
		], cwd=lib_dir + "/win32/VS2015")
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-O2'
		env['CFLAGS'] = '-O2'
		env['LIBS'] = ''
		env['OGG_CFLAGS'] = '-I../../' + target + '/libogg/include'
		env['OGG_LIBS'] = '-L../../' + target + '/libogg/lib -logg'
		env['OPUS_CFLAGS'] = '-I../../' + target + '/libopus/include'
		env['OPUS_LIBS'] = '-L../../' + target + '/libopus/lib -lopus -lm'
		env['OPUSFILE_CFLAGS'] = '-I../../' + target + '/opusfile/include'
		env['OPUSFILE_LIBS'] = '-L../../' + target + '/opusfile/lib -lopusfile' + ' ' + env['OGG_LIBS']
		env['OPUSURL_CFLAGS'] = '-I../../' + target + '/opusfile/include'
		env['OPUSURL_LIBS'] = '-L../../' + target + '/opusfile/lib -lopusurl -lopusfile' +  ' ' + env['OGG_LIBS']
		env['LIBOPUSENC_CFLAGS'] = '-I../../' + target + '/libopusenc/include'
		env['LIBOPUSENC_LIBS'] = '-L../../' + target + '/libopusenc/lib -lopusenc'
		env['HAVE_PKG_CONFIG'] = 'no'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version

		#seems like with no pkg config, the values of these variables are not respected, so they need to be added to CFLAGS/LIBS directly:
		env['CFLAGS'] = (env['CFLAGS']
			+ ' ' + env['OGG_CFLAGS']
			+ ' ' + env['OPUS_CFLAGS']
			+ ' ' + env['OPUSFILE_CFLAGS']
			+ ' ' + env['OPUSURL_CFLAGS']
			+ ' ' + env['LIBOPUSENC_CFLAGS'] )
		env['LIBS'] = (env['LIBS']  + ' ' + env['OGG_LIBS']
			+ ' ' + env['LIBOPUSENC_LIBS']
			+ ' ' + env['OGG_LIBS']
			+ ' ' + env['OPUS_LIBS']
			+ ' ' + env['OPUSFILE_LIBS']
			+ ' ' + env['OPUSURL_LIBS'] )

		run_command(['./configure',
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--without-flac',
			'--enable-sse',
			'--disable-oggtest',
			'--disable-opustest',
			'--disable-opusfiletest',
			'--disable-libopusenctest',
		#	'--enable-static',
		#	'--disable-shared',
		#	'--disable-doc',
		#	'--disable-examples'
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)
	
	print("Copying " + lib_name + " files...")
	os.makedirs(target + "/" + lib_name + "/bin", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusenc.exe", target + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusdec.exe", target + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusinfo.exe", target + "/" + lib_name + "/bin/")
	else:
		shutil.copy(lib_dir + "/out/bin/opusenc", target + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/out/bin/opusdec", target + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/out/bin/opusinfo", target + "/" + lib_name + "/bin/")


def fetch_jam():
	assert(target == 'windows')
	remove_if_exists(work_folder + "/jam.exe")
	remove_if_exists("windows/jam/jam.exe")

	fetch_file(jam_url, work_folder + "/" + jam_file)
	unzip_file(work_folder + "/" + jam_file, work_folder)
	shutil.copy(work_folder + "/jam.exe", "windows/jam/")


def build_harfbuzz():
	lib_name = "harfbuzz"
	lib_dir = work_folder + "/harfbuzz-" + harfbuzz_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	#if target == 'windows':
	fetch_file(harfbuzz_urlbase + ".zip", work_folder + "/" + harfbuzz_filebase + ".zip")
	unzip_file(work_folder + "/" + harfbuzz_filebase + ".zip", work_folder)
	#else:
	#	fetch_file(harfbuzz_urlbase + ".zip", work_folder + "/" + harfbuzz_filebase + ".zip")
	#	unzip_file(work_folder + "/" + harfbuzz_filebase + ".zip", work_folder)
	#	pass
	
	print("Building " + lib_name + "...")
	if target == 'windows':
		env = os.environ.copy()
		os.makedirs(lib_dir + "/build", exist_ok=True)
		run_command([
			"cmake", "..",
			"-DHB_HAVE_FREETYPE=ON",
			"-DFREETYPE_INCLUDE_DIRS=..\\..\\" + target + "\\freetype\\include",
			"-DFREETYPE_LIBRARY=..\\..\\..\\" + target + "\\freetype\\lib\\freetype",
		], env=env, cwd=lib_dir + "/build")
		run_command([
			"msbuild", "/m",
			"harfbuzz.sln",
			"/t:ALL_BUILD",
			"/p:Configuration=RelWithDebInfo"
		],env=env, cwd=lib_dir + "/build")
	else:
		env = os.environ.copy()
		os.makedirs(lib_dir + "/build", exist_ok=True)
		run_command([
			"cmake", "..",
			"-DCMAKE_BUILD_TYPE=RelWithDebInfo",
			"-DHB_HAVE_FREETYPE=ON",
			"-DFREETYPE_INCLUDE_DIRS=../../" + target + "/freetype/include",
			"-DFREETYPE_LIBRARIES=-L../../../" + target + "/freetype/lib/ -lfreetype",
		], env=env, cwd=lib_dir + "/build")
		run_command([
			"make", "-j3", "harfbuzz"
		],env=env, cwd=lib_dir + "/build")

	print("copying " + lib_name + " files...")
	os.makedirs(target + "/harfbuzz/lib", exist_ok=True)
	os.makedirs(target + "/harfbuzz/include", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/build/RelWithDebInfo/harfbuzz.lib", target + "/harfbuzz/lib/")
	else:
		shutil.copy(lib_dir + "/build/libharfbuzz.a", target + "/harfbuzz/lib/")

	for header in [
		"hb-aat.h",
		"hb-aat-layout.h",
		"hb-blob.h",
		"hb-buffer.h",
		"hb-common.h",
		"hb-coretext.h",
		"hb-deprecated.h",
		"hb-directwrite.h",
		"hb-draw.h",
		"hb-face.h",
		"hb-font.h",
		"hb-ft.h",
		"hb-gdi.h",
		"hb-glib.h",
		"hb-gobject.h",
		"hb-gobject-structs.h",
		"hb-graphite2.h",
		"hb.h",
		"hb-icu.h",
		"hb-map.h",
		"hb-ot-color.h",
		"hb-ot-deprecated.h",
		"hb-ot-font.h",
		"hb-ot.h",
		"hb-ot-layout.h",
		"hb-ot-math.h",
		"hb-ot-meta.h",
		"hb-ot-metrics.h",
		"hb-ot-name.h",
		"hb-ot-shape.h",
		"hb-ot-var.h",
		"hb-set.h",
		"hb-shape.h",
		"hb-shape-plan.h",
		"hb-style.h",
		"hb-subset.h",
		"hb-unicode.h",
		"hb-uniscribe.h",
		"hb-version.h"
		]:
		shutil.copy(lib_dir + "/src/" + header, target + "/harfbuzz/include/")
	shutil.copy(lib_dir + "/COPYING", target + "/freetype/dist/README-harfbuzz.txt")


def build_freetype():
	lib_name = "freetype"
	lib_dir = work_folder + "/" + freetype_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(freetype_url, work_folder + "/" + freetype_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + freetype_filebase + ".tar")
		unzip_file(work_folder + "/" + freetype_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + freetype_filebase + ".tar", work_folder)
	else:
		fetch_file(freetype_url, work_folder + "/" + freetype_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', freetype_filebase + ".tar.gz" ], cwd=work_folder)
	
	print("Building " + lib_name + "...")
	#patch config to trim a few extra modules / features:
	replace_in_file(lib_dir + "/include/freetype/config/ftoption.h", [
		('#define FT_CONFIG_OPTION_USE_LZW', '//#define FT_CONFIG_OPTION_USE_LZW'),
		('#define FT_CONFIG_OPTION_USE_ZLIB', '//#define FT_CONFIG_OPTION_USE_ZLIB'),
		('#define FT_CONFIG_OPTION_ENVIRONMENT_PROPERTIES', '//#define FT_CONFIG_OPTION_ENVIRONMENT_PROPERTIES'),
		('#define FT_CONFIG_OPTION_MAC_FONTS', '//#define FT_CONFIG_OPTION_MAC_FONTS'),
		('#define FT_CONFIG_OPTION_OPTION_BYTECODE_INTERPRETER', '//#define FT_CONFIG_OPTION_OPTION_BYTECODE_INTERPRETER'),
	])
	if target == 'windows':
		env = os.environ.copy()
		env['JAM_TOOLSET'] = 'VISUALC'
		run_command([
			"windows/jam/jam.exe",
		], env=env, cwd=lib_dir)
	else:
		run_command([
			"jam",
		], cwd=lib_dir)
	
	print("copying " + lib_name + " files...")
	os.makedirs(target + "/freetype/lib", exist_ok=True)
	os.makedirs(target + "/freetype/include", exist_ok=True)
	os.makedirs(target + "/freetype/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/objs/freetype.lib", target + "/freetype/lib/")
	else:
		#todo: check what gets build on other oses:
		shutil.copy(lib_dir + "/objs/libfreetype.a", target + "/freetype/lib/")
	shutil.copy(lib_dir + "/include/ft2build.h", target + "/freetype/include/")
	shutil.copytree(lib_dir + "/include/freetype/", target + "/freetype/include/freetype/")
	#This isn't quite right, since the FTL only requires acknowledgement in documentation:
	#shutil.copy(lib_dir + "/doc/FTL.TXT", target + "/freetype/dist/")
	f = open(target + '/freetype/dist/README-freetype.txt', 'wb')
	f.write('Freetype used under the provisions of the FTL.\n\nPortions of this software are copyright \u00A9 2020 The FreeType Project (www.freetype.org).  All rights reserved.\n'.encode('utf8'))
	f.close()



def make_package():
	print("Packaging...")
	#Create a list of files to compress for release builds:
	listfile = work_folder + '/listfile'
	with open(listfile, 'w') as l:
		l.write('nest-libs/README.md\n')
		for (dirpath, dirnames, filenames) in os.walk(target):
			for fn in filenames:
				l.write('nest-libs/' + dirpath + '/' + fn + '\n')
	#Eventually might do this:
	#Also create a package directory because of the unique way in which artifact uploads work :-/
	#remove_if_exists(target + "/package/")
	#os.makedirs(work_folder + "/package")
	#shutil.copy('README.md', work_folder + "/package/")
	#shutil.copytree(target + "/", work_folder + "/package/target/")
	
	if target == 'windows':
		run_command([
			"C:\\Program Files\\7-Zip\\7z.exe",
			"a",
			"nest-libs\\nest-libs-" + target + "-" + tag + ".zip",
			"@nest-libs\\work\\listfile"
		], cwd='..')
	else:
		run_command([
			'tar',
			'cfz',
			'nest-libs/nest-libs-' + target + "-" + tag + ".tar.gz",
			"--files-from", "nest-libs/work/listfile"
		], cwd='..')
		

to_build = sys.argv[1:]

print("To build: " + ", ".join(to_build))

if "all" in to_build:
	to_build = [ "harfbuzz", "freetype", "SDL2", "glm", "zlib", "libpng", "libogg", "libopus", "opusfile", "libopusenc", "opus-tools"]
	if target == 'windows':
		to_build.append("jam")
	if "package" in sys.argv[1:]:
		to_build.append("package")

if "jam" in to_build:
	fetch_jam()

if "freetype" in to_build:
	build_freetype()

if "harfbuzz" in to_build:
	build_harfbuzz()

if "SDL2" in to_build:
	build_SDL2()

if "glm" in to_build:
	build_glm()

if "zlib" in to_build:
	build_zlib()

if "libpng" in to_build:
	build_libpng()

if "libopus" in to_build:
	build_libopus()

if "libogg" in to_build:
	build_libogg()

if "opusfile" in to_build:
	build_opusfile()

if "libopusenc" in to_build:
	build_libopusenc()

if "opus-tools" in to_build:
	build_opustools()

if "package" in to_build:
	make_package()
