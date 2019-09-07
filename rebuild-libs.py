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

tag = "v0.1.pre0"

if 'TRAVIS_TAG' in os.environ:
	tag = os.environ['TRAVIS_TAG']
	print("Set tag from $TRAVIS_TAG to '" + tag + "'")

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
	libpng_filebase = "libpng-1.6.37"
	libpng_url = "http://prdownloads.sourceforge.net/libpng/" + libpng_filebase + ".tar.gz?download"

libogg_filebase = "libogg-1.3.4"
libogg_url = "http://downloads.xiph.org/releases/ogg/" + libogg_filebase + ".tar.gz"

libopus_filebase = "opus-1.3.1"
libopus_url = "https://archive.mozilla.org/pub/opus/" + libopus_filebase + ".tar.gz"

opusfile_filebase = "opusfile-0.11"
opusfile_url = "https://downloads.xiph.org/releases/opus/" + opusfile_filebase + ".tar.gz"

jam_file = 'ftjam-2.5.2-win32.zip'
jam_url = 'https://sourceforge.net/projects/freetype/files/ftjam/2.5.2/' + jam_file + '/download'

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
			"msbuild",
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
				'--disable-esd',
				'--disable-pulseaudio',
				'--disable-arts',
				'--disable-nas',
				'--disable-diskaudio',
				'--disable-dummyaudio',
				'--disable-sndio',
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
	shutil.copytree(glm_dir + "/glm/", target + "/glm/include/glm/")

	#process the "manual.md" file to extract the license notice section:
	with open(glm_dir + "/manual.md", 'r') as infile:
		with open(target + "/glm/README-glm.txt", 'w') as outfile:
			in_licenses = False
			for line in infile:
				if 'name="section0"></a> Licenses' in line:
					in_licenses = True
					outfile.write("GLM is distributed under the following licenses:\n")
				elif 'name="section1"' in line:
					in_licenses = False
				elif '<div style="page-break-after: always;"> </div>' == line.strip():
					pass
				elif '![](./doc/manual/frontpage1.png)' == line.strip():
					pass
				elif '![](./doc/manual/frontpage2.png)' == line.strip():
					pass
				elif '---' == line.strip():
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
		with open(libpng_dir + "/scripts/makefile.vcwin32", "r") as f:
			with open(libpng_dir + "/scripts/makefile.vcwin32.patched", "w") as o:
				for line in f:
					line = line.replace("-I..\\zlib","-I..\\..\\windows\\zlib\\include")
					line = line.replace("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
					o.write(line)
		run_command([
			'nmake',
			'-f',
			'scripts/makefile.vcwin32.patched'
		], cwd=libpng_dir)
	else:
		prefix = os.getcwd() + '/' + libpng_dir + '/out';
		env = os.environ.copy()
		env['CPPFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		env['CFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
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
		shutil.copy(libpng_dir + "/LICENSE", target + "/libpng/README-libpng.txt")
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
		pass
		#fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".zip")
		#unzip_file(work_folder + "/" + libpng_filebase + ".zip", work_folder)
	else:
		fetch_file(libogg_url, work_folder + "/" + libogg_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libogg_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		pass
#		#Patch makefile:
#		with open(libpng_dir + "/scripts/makefile.vcwin32", "r") as f:
#			with open(libpng_dir + "/scripts/makefile.vcwin32.patched", "w") as o:
#				for line in f:
#					line = line.replace("-I..\\zlib","-I..\\..\\windows\\zlib\\include")
#					line = line.replace("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
#					o.write(line)
#		run_command([
#			'nmake',
#			'-f',
#			'scripts/makefile.vcwin32.patched'
#		], cwd=libpng_dir)
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		#env['CPPFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		#env['CFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
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
		pass
#		shutil.copy(libpng_dir + "/libpng.lib", target + "/libpng/lib/")
#		shutil.copy(libpng_dir + "/png.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pngconf.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pnglibconf.h", target + "/libpng/include/")
	else:
		shutil.copy(lib_dir + "/out/include/ogg/config_types.h", target + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/ogg.h", target + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/os_types.h", target + "/" + lib_name + "/include/ogg/")
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
		pass
		#fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".zip")
		#unzip_file(work_folder + "/" + libpng_filebase + ".zip", work_folder)
	else:
		fetch_file(libopus_url, work_folder + "/" + libopus_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', libopus_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		pass
#		#Patch makefile:
#		with open(libpng_dir + "/scripts/makefile.vcwin32", "r") as f:
#			with open(libpng_dir + "/scripts/makefile.vcwin32.patched", "w") as o:
#				for line in f:
#					line = line.replace("-I..\\zlib","-I..\\..\\windows\\zlib\\include")
#					line = line.replace("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
#					o.write(line)
#		run_command([
#			'nmake',
#			'-f',
#			'scripts/makefile.vcwin32.patched'
#		], cwd=libpng_dir)
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		#env['CPPFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		#env['CFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		if target == 'macos':
			env['CPPFLAGS'] = env['CPPFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
			env['CFLAGS'] = env['CFLAGS'] + ' -mmacosx-version-min=' + min_osx_version
		#env['LDFLAGS'] = '-L../../' + target + '/zlib/lib'
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
		pass
#		shutil.copy(libpng_dir + "/libpng.lib", target + "/libpng/lib/")
#		shutil.copy(libpng_dir + "/png.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pngconf.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pnglibconf.h", target + "/libpng/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opus.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_multistream.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_types.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_defines.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_projection.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopus.a", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/COPYING", target + "/" + lib_name + "/dist/README-libopus.txt")



def build_opusfile():
	lib_name = "opusfile"
	lib_dir = work_folder + "/" + opusfile_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		pass
		#fetch_file(libpng_url, work_folder + "/" + libpng_filebase + ".zip")
		#unzip_file(work_folder + "/" + libpng_filebase + ".zip", work_folder)
	else:
		fetch_file(opusfile_url, work_folder + "/" + opusfile_filebase + ".tar.gz")
		run_command([ 'tar', 'xfz', opusfile_filebase + ".tar.gz" ], cwd=work_folder)

	print("Building " + lib_name + "...")
	if target == 'windows':
		pass
#		#Patch makefile:
#		with open(libpng_dir + "/scripts/makefile.vcwin32", "r") as f:
#			with open(libpng_dir + "/scripts/makefile.vcwin32.patched", "w") as o:
#				for line in f:
#					line = line.replace("-I..\\zlib","-I..\\..\\windows\\zlib\\include")
#					line = line.replace("-..\\zlib\\zlib.lib","..\\..\\windows\\zlib\\lib\\zlib.lib")
#					o.write(line)
#		run_command([
#			'nmake',
#			'-f',
#			'scripts/makefile.vcwin32.patched'
#		], cwd=libpng_dir)
	else:
		prefix = os.getcwd() + '/' + lib_dir + '/out';
		env = os.environ.copy()
		#env['CPPFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
		#env['CFLAGS'] = '-L../../' + target + '/zlib/lib -I../../' + target + '/zlib/include'
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
		pass
#		shutil.copy(libpng_dir + "/libpng.lib", target + "/libpng/lib/")
#		shutil.copy(libpng_dir + "/png.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pngconf.h", target + "/libpng/include/")
#		shutil.copy(libpng_dir + "/pnglibconf.h", target + "/libpng/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opusfile.h", target + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopusfile.a", target + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/out/share/doc/opusfile/COPYING", target + "/" + lib_name + "/dist/README-opusfile.txt")
		


def fetch_jam():
	assert(target == 'windows')
	remove_if_exists(work_folder + "/jam.exe")
	remove_if_exists("windows/jam/jam.exe")

	fetch_file(jam_url, work_folder + "/" + jam_file)
	unzip_file(work_folder + "/" + jam_file, work_folder)
	shutil.copy(work_folder + "/jam.exe", "windows/jam/")

def make_package():
	print("Packaging...")
	listfile = work_folder + '/listfile'
	with open(listfile, 'w') as l:
		l.write('nest-libs/README.md\n')
		for (dirpath, dirnames, filenames) in os.walk(target):
			for fn in filenames:
				l.write('nest-libs/' + dirpath + '/' + fn + '\n')
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

if "all" in to_build:
	to_build = ["SDL2", "glm", "zlib", "libpng", "libogg", "libopus", "opusfile"]
	if target == 'windows':
		to_build.append("jam")
	if "package" in sys.argv[1:]:
		to_build.append("package")

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

if "jam" in to_build:
	fetch_jam()

if "package" in to_build:
	make_package()
