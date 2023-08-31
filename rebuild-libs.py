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

variant = ''
variant_cflags = { '':'' }
variant_cmake_flags = { '':[''] }
variant_configure_flags = { '':[''] }
variant_env = { '':{} }


jobs = os.cpu_count() + 1
print(f"Using {jobs} threads.");

if platform.system() == 'Linux':
	target = 'linux'
	variants = ['']
elif platform.system() == 'Darwin':
	target = 'macos'
	variant_cflags = {
		'-x86':'-target x86_64-apple-macos10.9 -mmacosx-version-min=10.9',
		'-arm':'-target arm64-apple-macos11 -mmacosx-version-min=11'
	}
	variant_cmake_flags = {
		'-x86':['-DCMAKE_OSX_DEPLOYMENT_TARGET=10.9', '-DCMAKE_APPLE_SILICON_PROCESSOR=x86_64', '-DCMAKE_OSX_DEPLOYMENT_TARGET='],
		'-arm':['-DCMAKE_OSX_DEPLOYMENT_TARGET=11', '-DCMAKE_APPLE_SILICON_PROCESSOR=arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=']
	}
	variant_configure_flags = {
		'-x86':['--host=x86_64-apple-darwin'],
		'-arm':['--host=aarch64-apple-darwin']
	}
	variant_env = {
		'-x86':{'MACOSX_DEPLOYMENT_TARGET':'10.9'},
		'-arm':{'MACOSX_DEPLOYMENT_TARGET':'11'}
	}
	variants = ['-x86','-arm']
elif platform.system() == 'Windows':
	target = 'windows'
	variants = ['']
else:
	exit("Unknown system '" + platform.system() + "'")

print("Will build for '" + target + variant + "'")

if target == 'macos':
	if os.path.exists('/usr/local/bin/ranlib'):
		print(" *** WARNING: having brew binutils installed breaks things badly *** ")
		sleep(1)

work_folder = "work"

SDL2_filebase = "SDL2-2.28.2"
SDL2_urlbase = "https://www.libsdl.org/release/" + SDL2_filebase

glm_filebase = "glm-0.9.9.8"
glm_urlbase = "https://github.com/g-truc/glm/releases/download/0.9.9.8/" + glm_filebase

zlib_filebase = "zlib-1.3"
if target == 'windows':
	#for whatever reason, zipfile releases are named oddly:
	zlib_url = "https://zlib.net/zlib" +re.sub(r'[^0-9]','', zlib_filebase) + ".zip"
else:
	zlib_url = "https://zlib.net/" + zlib_filebase + ".tar.gz"

if target == 'windows':
	libpng_filebase = "lpng1640"
	libpng_url = "http://prdownloads.sourceforge.net/libpng/" + libpng_filebase + ".zip?download"
else:
	libpng_filebase = "libpng-1.6.40"
	libpng_url = "http://prdownloads.sourceforge.net/libpng/" + libpng_filebase + ".tar.gz?download"

libogg_filebase = "libogg-1.3.5"
libogg_urlbase = "http://downloads.xiph.org/releases/ogg/" + libogg_filebase

libopus_filebase = "opus-1.4"
libopus_url = "https://downloads.xiph.org/releases/opus/" + libopus_filebase + ".tar.gz"

opusfile_filebase = "opusfile-0.12"
opusfile_url = "https://downloads.xiph.org/releases/opus/" + opusfile_filebase + ".tar.gz"

libopusenc_filebase = "libopusenc-0.2.1"
libopusenc_url = "https://archive.mozilla.org/pub/opus/" + libopusenc_filebase + ".tar.gz"

opustools_filebase = "opus-tools-0.2"
opustools_url = "https://archive.mozilla.org/pub/opus/" + opustools_filebase + ".tar.gz"

freetype_filebase = 'freetype-2.13.1'
freetype_url = 'https://prdownloads.sourceforge.net/freetype/freetype2/2.13.1/' + freetype_filebase + '.tar.gz?download'

harfbuzz_filebase = '8.1.1'
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
	remove_if_exists(target + variant + "/SDL2/")

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
			env['CFLAGS'] = variant_cflags[variant]
			for key in variant_env[variant].keys():
				env[key] = variant_env[variant][key]
			run_command(['../configure'] + variant_configure_flags[variant] + ['--prefix=' + prefix,
				'--disable-shared', '--enable-static',
				'--disable-render',
				'--enable-haptic', #force feedback framework required by joystick code anyway
				'--disable-file', '--disable-filesystem',
				'--disable-power',
				"--disable-sensor",
				"--disable-hidapi",
				'--enable-loadso', #needed for opengl
				'--enable-sse2',
				'--disable-oss',
				'--disable-alsa',
				'--disable-jack',
				'--disable-esd',
				'--disable-pulseaudio',
				'--disable-arts',
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
				'--disable-video-metal',
				'--disable-video-opengles',
				'--enable-pthreads',
				'--enable-pthread-sem',
				'--disable-directx',
				'--disable-render',
			],env=env,cwd=SDL2_dir + '/build')
			#Handled by a larger-hammer header file combination block later:
			#immintrin_def = "#ifndef __aarch64__\n#define HAVE_IMMINTRIN_H 1\n#endif\n"
			#replace_in_file(SDL2_dir + "/build/include/SDL_config.h", [
			#	("#define HAVE_IMMINTRIN_H 1\n", immintrin_def),
			#	("/* #undef HAVE_IMMINTRIN_H */\n", immintrin_def)
			#])
		else:
			run_command(['../configure'] + variant_configure_flags[variant] + ['--prefix=' + prefix,
				'--disable-shared', '--enable-static',
				'--disable-render', '--disable-haptic', '--disable-file', '--disable-filesystem', '--disable-loadso', '--disable-power', '--disable-sensor', '--disable-hidapi',
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
				'--enable-pthreads',
				'--enable-pthread-sem',
				'--disable-directx',
				'--disable-render',
				'--enable-sdl-dlopen',
			],env=env,cwd=SDL2_dir + '/build')
		run_command(['make', '-j', str(jobs)], cwd=SDL2_dir + '/build')
		run_command(['make', 'install'], cwd=SDL2_dir + '/build')

	print("Copying SDL2 files...")
	os.makedirs(target + variant + "/SDL2/lib", exist_ok=True)
	os.makedirs(target + variant + "/SDL2/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.lib", target + variant + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2main.lib", target + variant + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/VisualC/x64/Release/SDL2.dll", target + variant + "/SDL2/dist/")
		shutil.copytree(SDL2_dir + "/include/", target + variant + "/SDL2/include/")
	else:
		os.makedirs(target + variant + "/SDL2/bin", exist_ok=True)
		with open(SDL2_dir + '/out/bin/sdl2-config', 'r') as i:
			with open(target + variant + '/SDL2/bin/sdl2-config', 'w') as o:
				found_prefix = False
				for line in i:
					if re.match('^prefix=.*$', line) != None:
						assert(not found_prefix)
						if target == 'macos':
							o.write("prefix=../nest-libs/" + target + "/SDL2\n") #will eventually merge into this path
						else:
							o.write("prefix=../nest-libs/" + target + variant + "/SDL2\n")
						found_prefix = True
					else:
						o.write(line)
				assert(found_prefix)
		os.chmod(target + variant + '/SDL2/bin/sdl2-config', 0o744)
		shutil.copy(SDL2_dir + "/out/lib/libSDL2.a", target + variant + "/SDL2/lib/")
		shutil.copy(SDL2_dir + "/out/lib/libSDL2main.a", target + variant + "/SDL2/lib/")
		shutil.copytree(SDL2_dir + "/out/include/SDL2/", target + variant + "/SDL2/include/SDL2/")
	shutil.copy(SDL2_dir + "/README-SDL.txt", target + variant + "/SDL2/dist/")


def build_glm():
	glm_dir = work_folder + "/glm"
	print("Cleaning any existing glm...")
	remove_if_exists(glm_dir)
	remove_if_exists(target + variant + "/glm/")

	print("Fetching glm...")
	fetch_file(glm_urlbase + ".zip", work_folder + "/" + glm_filebase + ".zip")
	unzip_file(work_folder + "/" + glm_filebase + ".zip", work_folder)

	print("Copying glm files...")
	os.makedirs(target + variant + "/glm/include", exist_ok=True)
	os.makedirs(target + variant + "/glm/dist", exist_ok=True)
	shutil.copytree(glm_dir + "/glm/", target + variant + "/glm/include/glm/")

	#process the "manual.md" file to extract the license notice section:
	with open(glm_dir + "/manual.md", 'rb') as infile:
		with open(target + variant + "/glm/dist/README-glm.txt", 'wb') as outfile:
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
	remove_if_exists(target + variant + "/zlib/")

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
		env['CFLAGS'] = variant_cflags[variant]
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		#NOTE: not passing variant_configure_flags because this isn't really a (recent) autoconf script:
		run_command(['./configure', '--static'], env=env, cwd=zlib_dir)
		run_command(['make'], cwd=zlib_dir)
		run_command(['make', 'install'], cwd=zlib_dir)

	print("Copying zlib files...")
	os.makedirs(target + variant + "/zlib/lib", exist_ok=True)
	os.makedirs(target + variant + "/zlib/include", exist_ok=True)
	if target == 'windows':
		shutil.copy(zlib_dir + "/zlib.lib", target + variant + "/zlib/lib/")
		shutil.copy(zlib_dir + "/zlib.pdb", target + variant + "/zlib/lib/")
		shutil.copy(zlib_dir + "/zconf.h", target + variant + "/zlib/include/")
		shutil.copy(zlib_dir + "/zlib.h", target + variant + "/zlib/include/")
	else:
		shutil.copy(zlib_dir + "/out/include/zconf.h", target + variant + "/zlib/include/")
		shutil.copy(zlib_dir + "/out/include/zlib.h", target + variant + "/zlib/include/")
		shutil.copy(zlib_dir + "/out/lib/libz.a", target + variant + "/zlib/lib/")


def build_libpng():
	libpng_dir = work_folder + "/" + libpng_filebase

	print("Cleaning any existing libpng...")
	remove_if_exists(target + variant + "/libpng/")
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
		env['CPPFLAGS'] = '-O2 -L../../' + target + variant + '/zlib/lib -I../../' + target + variant + '/zlib/include'
		env['CFLAGS'] = '-O2 -L../../' + target + variant + '/zlib/lib -I../../' + target + variant + '/zlib/include'
		env['CPPFLAGS'] = env['CPPFLAGS'] + ' ' + variant_cflags[variant]
		env['CFLAGS'] = env['CFLAGS'] + ' ' + variant_cflags[variant]
		env['LDFLAGS'] = '-L../../' + target + variant + '/zlib/lib'
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		run_command(['./configure'] + variant_configure_flags[variant] + [
			'--prefix=' + prefix,
			'--with-zlib-prefix=../../' + target + variant + '/zlib',
			'--disable-shared'], env=env, cwd=libpng_dir);
		run_command(['make'], cwd=libpng_dir)
		run_command(['make', 'install'], cwd=libpng_dir)

	print("Copying libpng files...")
	os.makedirs(target + variant + "/libpng/lib", exist_ok=True)
	os.makedirs(target + variant + "/libpng/include", exist_ok=True)
	os.makedirs(target + variant + "/libpng/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(libpng_dir + "/libpng.lib", target + variant + "/libpng/lib/")
		shutil.copy(libpng_dir + "/png.h", target + variant + "/libpng/include/")
		shutil.copy(libpng_dir + "/pngconf.h", target + variant + "/libpng/include/")
		shutil.copy(libpng_dir + "/pnglibconf.h", target + variant + "/libpng/include/")
	else:
		shutil.copy(libpng_dir + "/out/include/libpng16/png.h", target + variant + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/include/libpng16/pngconf.h", target + variant + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/include/libpng16/pnglibconf.h", target + variant + "/libpng/include/")
		shutil.copy(libpng_dir + "/out/lib/libpng16.a", target + variant + "/libpng/lib/")
		os.symlink("libpng16.a", target + variant + "/libpng/lib/libpng.a")
	shutil.copy(libpng_dir + "/LICENSE", target + variant + "/libpng/dist/README-libpng.txt")

def build_libogg():
	lib_name = "libogg"
	lib_dir = work_folder + "/" + libogg_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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
			('<WindowsTargetPlatformVersion>8.1</WindowsTargetPlatformVersion>',''),
			(">MultiThreaded<", ">MultiThreadedDLL<"),
			("<WholeProgramOptimization>true</WholeProgramOptimization>",
			 "<WholeProgramOptimization>false</WholeProgramOptimization>")
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
		env['CPPFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['CFLAGS'] = '-O2 ' + variant_cflags[variant]
		#env['LDFLAGS'] = '-L../../' + target + variant + '/zlib/lib'
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		run_command(['./configure'] + variant_configure_flags[variant] + [
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)
	print("Copying " + lib_name + " files...")
	os.makedirs(target + variant + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/include/ogg", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/libogg.lib", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/libogg.pdb", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/ogg/ogg.h", target + variant + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/include/ogg/os_types.h", target + variant + "/" + lib_name + "/include/ogg/")
	else:
		shutil.copy(lib_dir + "/out/include/ogg/config_types.h", target + variant + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/ogg.h", target + variant + "/" + lib_name + "/include/ogg/")
		shutil.copy(lib_dir + "/out/include/ogg/os_types.h", target + variant + "/" + lib_name + "/include/ogg/")
		if target == 'macos':
			replace_in_file(target + variant + "/" + lib_name + "/include/ogg/os_types.h", [
				("#  include <sys/types.h>", "#include <stdint.h>")
			])
		shutil.copy(lib_dir + "/out/lib/libogg.a", target + variant + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + variant + "/" + lib_name + "/dist/README-libogg.txt")

def build_libopus():
	lib_name = "libopus"
	lib_dir = work_folder + "/" + libopus_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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
		replace_in_file(lib_dir + "/win32/VS2015/common.props", [
			('>MultiThreaded<','>MultiThreadedDLL<')
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
		env['CPPFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['CFLAGS'] = '-O2 ' + variant_cflags[variant]
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		run_command(['./configure'] + variant_configure_flags[variant] + [
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
	os.makedirs(target + variant + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opus.lib", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opus.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_multistream.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_types.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_defines.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/include/opus_projection.h", target + variant + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opus.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_multistream.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_types.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_defines.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/include/opus/opus_projection.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopus.a", target + variant + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + variant + "/" + lib_name + "/dist/README-libopus.txt")

def build_libopusenc():
	lib_name = "libopusenc"
	lib_dir = work_folder + "/" + libopusenc_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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
		env['CPPFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['CFLAGS'] = '-O2 ' + variant_cflags[variant]

		env['DEPS_CFLAGS'] = '-I../../' + target + variant + '/libogg/include -I../../' + target + variant + '/libopus/include'
		env['DEPS_LIBS'] = '-L../../' + target + variant + '/libogg/lib -L../../' + target + variant + '/libopus/lib -lopus'
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		run_command(['./configure'] + variant_configure_flags[variant] + [
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
	os.makedirs(target + variant + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusenc.lib", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opusenc.h", target + variant + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opusenc.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopusenc.a", target + variant + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + variant + "/" + lib_name + "/dist/README-libopusenc.txt")



def build_opusfile():
	lib_name = "opusfile"
	lib_dir = work_folder + "/" + opusfile_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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
			 "..\\..\\..\\..\\windows\\libogg\\include"),
			("<WholeProgramOptimization>true</WholeProgramOptimization>",
			 "<WholeProgramOptimization>false</WholeProgramOptimization>"),
			("<RuntimeLibrary>MultiThreaded</RuntimeLibrary>",
			 "<RuntimeLibrary>MultiThreadedDLL</RuntimeLibrary>")
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
		env['CPPFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['CFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['DEPS_CFLAGS'] = '-I../../' + target + variant + '/libogg/include -I../../' + target + variant + '/libopus/include'
		env['DEPS_LIBS'] = '-L../../' + target + variant + '/libogg/lib -L../../' + target + variant + '/libopus/lib'
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		#env['LDFLAGS'] = '-L../../' + target + variant + '/zlib/lib'
		run_command(['./configure'] + variant_configure_flags[variant] + [
			'--prefix=' + prefix,
			'--disable-dependency-tracking',
			'--enable-static',
			'--disable-shared',
			'--disable-http',
			'--disable-examples',
			'--disable-doc'
			#'--with-zlib-prefix=../../' + target + variant + '/zlib',
			], env=env, cwd=lib_dir);
		run_command(['make'], cwd=lib_dir)
		run_command(['make', 'install'], cwd=lib_dir)

	print("Copying " + lib_name + " files...")
	os.makedirs(target + variant + "/" + lib_name + "/lib", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/include", exist_ok=True)
	os.makedirs(target + variant + "/" + lib_name + "/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release-NoHTTP/opusfile.lib", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release-NoHTTP/opusfile.pdb", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/include/opusfile.h", target + variant + "/" + lib_name + "/include/")
	else:
		shutil.copy(lib_dir + "/out/include/opus/opusfile.h", target + variant + "/" + lib_name + "/include/")
		shutil.copy(lib_dir + "/out/lib/libopusfile.a", target + variant + "/" + lib_name + "/lib/")
		shutil.copy(lib_dir + "/out/lib/libopusurl.a", target + variant + "/" + lib_name + "/lib/")
	shutil.copy(lib_dir + "/COPYING", target + variant + "/" + lib_name + "/dist/README-opusfile.txt")

def build_opustools():
	lib_name = "opus-tools"
	lib_dir = work_folder + "/" + opustools_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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
		replace_in_file(lib_dir + "/win32/VS2015/common.props", [
			(">MultiThreaded<", ">MultiThreadedDLL<"),
			("<WholeProgramOptimization>true</WholeProgramOptimization>",
			 "<WholeProgramOptimization>false</WholeProgramOptimization>"),
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
		env['CPPFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['CFLAGS'] = '-O2 ' + variant_cflags[variant]
		env['LIBS'] = ''
		env['OGG_CFLAGS'] = '-I../../' + target + variant + '/libogg/include'
		env['OGG_LIBS'] = '-L../../' + target + variant + '/libogg/lib -logg'
		env['OPUS_CFLAGS'] = '-I../../' + target + variant + '/libopus/include'
		env['OPUS_LIBS'] = '-L../../' + target + variant + '/libopus/lib -lopus -lm'
		env['OPUSFILE_CFLAGS'] = '-I../../' + target + variant + '/opusfile/include'
		env['OPUSFILE_LIBS'] = '-L../../' + target + variant + '/opusfile/lib -lopusfile' + ' ' + env['OGG_LIBS']
		env['OPUSURL_CFLAGS'] = '-I../../' + target + variant + '/opusfile/include'
		env['OPUSURL_LIBS'] = '-L../../' + target + variant + '/opusfile/lib -lopusurl -lopusfile' +  ' ' + env['OGG_LIBS']
		env['LIBOPUSENC_CFLAGS'] = '-I../../' + target + variant + '/libopusenc/include'
		env['LIBOPUSENC_LIBS'] = '-L../../' + target + variant + '/libopusenc/lib -lopusenc'
		env['HAVE_PKG_CONFIG'] = 'no'
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]

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

		run_command(['./configure'] + variant_configure_flags[variant] + [
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
	os.makedirs(target + variant + "/" + lib_name + "/bin", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusenc.exe", target + variant + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusdec.exe", target + variant + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/win32/VS2015/x64/Release/opusinfo.exe", target + variant + "/" + lib_name + "/bin/")
	else:
		shutil.copy(lib_dir + "/out/bin/opusenc", target + variant + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/out/bin/opusdec", target + variant + "/" + lib_name + "/bin/")
		shutil.copy(lib_dir + "/out/bin/opusinfo", target + variant + "/" + lib_name + "/bin/")


def build_harfbuzz():
	lib_name = "harfbuzz"
	lib_dir = work_folder + "/harfbuzz-" + harfbuzz_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
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

	#
	replace_in_file(lib_dir + "/CMakeLists.txt", [
		('  include (FindFreetype)', '  #include (FindFreetype)  # <-- hack to avoid picking up system freetype'),
	])
	replace_in_file(lib_dir + "/meson.build", [
		("                            required: get_option('freetype'),", "                             required: false, # <-- hack to avoid freetype search failure"),
		("  if not freetype_dep.found() and not get_option('freetype').disabled()", "  if false # <-- more hack to avoid freetype search"),
		#("if not get_option('freetype').disabled()", "if false # <--- hack to avoid freetype search"),
		("if freetype_dep.found()", "if true # <--- more hack"),
	])


	if target == 'windows':
		env = os.environ.copy()
		run_command([
			"cmake", "-B", "build",
			"-DHB_HAVE_FREETYPE=ON",
			"-DFREETYPE_FOUND=1", #<-- hack!
			"-DFREETYPE_INCLUDE_DIRS=..\\..\\" + target + variant + "\\freetype\\include",
			"-DFREETYPE_LIBRARY=..\\..\\..\\" + target + variant + "\\freetype\\lib\\freetype",
		] + variant_cmake_flags[variant], env=env, cwd=lib_dir)
		run_command([
			"msbuild", "/m",
			"harfbuzz.sln",
			"/t:ALL_BUILD",
			"/p:Configuration=RelWithDebInfo"
		],env=env, cwd=lib_dir + "/build")
	else:
		cross_file = []
		if target == 'macos':
			cross_file = ["--cross-file", "cross.txt"]
			f = open(f"{lib_dir}/cross.txt", 'wb')
			if variant == '-x86':
				#based on https://github.com/mesonbuild/meson/issues/8206
				f.write("""
					[host_machine]
					system = 'darwin'
					cpu_family='x86_64'
					cpu='x86_64'
					endian='little'
					[binaries]
					c=['clang', '-target', 'x86_64-apple-macos10.9', '-mmacosx-version-min=10.9']
					cpp=['clang++', '-target', 'x86_64-apple-macos10.9', '-mmacosx-version-min=10.9']
					strip='strip'
				""".encode('utf8'))
			elif variant == '-arm':
				f.write("""
					[host_machine]
					system = 'darwin'
					cpu_family='x86_64'
					cpu='x86_64'
					endian='little'
					[binaries]
					c=['clang', '-target', 'arm64-apple-macos11', '-mmacosx-version-min=11']
					cpp=['clang++', '-target', 'arm64-apple-macos11', '-mmacosx-version-min=11']
					strip='strip'
				""".encode('utf8'))
			else:
				assert False
			f.close()
		env = os.environ.copy()
		for key in variant_env[variant].keys():
			env[key] = variant_env[variant][key]
		run_command([
			"meson", "setup", "build"]
			+ cross_file + [
			"-Dbuildtype=debugoptimized",
			"-Ddefault_library=static",
			"-Dfreetype=enabled",
			"-Dcpp_args=-I../../../" + target + variant + "/freetype/include",
		], env=env, cwd=lib_dir)
		run_command([
			"meson", "compile", "-C", "build", "harfbuzz"
		], env=env, cwd=lib_dir)

	print("copying " + lib_name + " files...")
	os.makedirs(target + variant + "/harfbuzz/lib", exist_ok=True)
	os.makedirs(target + variant + "/harfbuzz/include", exist_ok=True)
	os.makedirs(target + variant + "/harfbuzz/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/build/RelWithDebInfo/harfbuzz.lib", target + variant + "/harfbuzz/lib/")
		shutil.copy(lib_dir + "/build/RelWithDebInfo/harfbuzz.pdb", target + variant + "/harfbuzz/lib/")
	else:
		shutil.copy(lib_dir + "/build/src/libharfbuzz.a", target + variant + "/harfbuzz/lib/")

	for header in [
		"hb-aat.h",
		"hb-aat-layout.h",
		"hb-blob.h",
		"hb-buffer.h",
		"hb-cairo.h",
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
		"hb-paint.h",
		"hb-set.h",
		"hb-shape.h",
		"hb-shape-plan.h",
		"hb-style.h",
		"hb-subset.h",
		"hb-subset-repacker.h",
		"hb-unicode.h",
		"hb-uniscribe.h",
		"hb-version.h"
		]:
		shutil.copy(lib_dir + "/src/" + header, target + variant + "/harfbuzz/include/")
	shutil.copy(lib_dir + "/COPYING", target + variant + "/harfbuzz/dist/README-harfbuzz.txt")


def build_freetype():
	lib_name = "freetype"
	lib_dir = work_folder + "/" + freetype_filebase

	print("Cleaning any existing " + lib_name + "...")
	remove_if_exists(target + variant + "/" + lib_name + "/")
	remove_if_exists(lib_dir)

	print("Fetching " + lib_name + "...")
	if target == 'windows':
		fetch_file(freetype_url, work_folder + "/" + freetype_filebase + ".tar.gz")
		remove_if_exists(work_folder + "/" + freetype_filebase + ".tar")
		unzip_file(work_folder + "/" + freetype_filebase + ".tar.gz", work_folder)
		unzip_file(work_folder + "/" + freetype_filebase + ".tar", work_folder)
	else:
		fetch_file(freetype_url, work_folder + "/" + freetype_filebase + ".tar.gz")
		run_command([ 'tar', 'xf', freetype_filebase + ".tar.gz" ], cwd=work_folder)
	
	print("Building " + lib_name + "...")
	#patch config to trim a few extra modules / features:
	replace_in_file(lib_dir + "/include/freetype/config/ftoption.h", [
		('#define FT_CONFIG_OPTION_USE_LZW', '//#define FT_CONFIG_OPTION_USE_LZW'),
		('#define FT_CONFIG_OPTION_USE_ZLIB', '//#define FT_CONFIG_OPTION_USE_ZLIB'),
		('#define FT_CONFIG_OPTION_ENVIRONMENT_PROPERTIES', '//#define FT_CONFIG_OPTION_ENVIRONMENT_PROPERTIES'),
		('#define FT_CONFIG_OPTION_MAC_FONTS', '//#define FT_CONFIG_OPTION_MAC_FONTS'),
		#('#define TT_CONFIG_OPTION_BYTECODE_INTERPRETER', '//#define TT_CONFIG_OPTION_BYTECODE_INTERPRETER'), #<-- causes build error; apparently ft wasn't tested with this undefined?
		#but actually enable error strings:
		('/* #define FT_CONFIG_OPTION_ERROR_STRINGS */', '#define FT_CONFIG_OPTION_ERROR_STRINGS'),
	])

	env = os.environ.copy()
	env['CFLAGS'] = variant_cflags[variant]
	env['CXXFLAGS'] = variant_cflags[variant]
	for key in variant_env[variant].keys():
		env[key] = variant_env[variant][key]
	run_command([
		"cmake",
		"-B", "build",
		"-D", "CMAKE_BUILD_TYPE=RelWithDebInfo",
		"-D", "CMAKE_DISABLE_FIND_PACKAGE_ZLIB=TRUE",
		"-D", "CMAKE_DISABLE_FIND_PACKAGE_BZip2=TRUE",
		"-D", "CMAKE_DISABLE_FIND_PACKAGE_PNG=TRUE",
		"-D", "CMAKE_DISABLE_FIND_PACKAGE_HarfBuzz=TRUE",
		"-D", "CMAKE_DISABLE_FIND_PACKAGE_BrotliDec=TRUE"
	] + variant_cmake_flags[variant], cwd=lib_dir, env=env)

	run_command([
		"cmake",
		"--build", "build",
		"--config", "RelWithDebInfo",
		"-j", str(jobs)
	], cwd=lib_dir, env=env)


	print("copying " + lib_name + " files...")
	os.makedirs(target + variant + "/freetype/lib", exist_ok=True)
	os.makedirs(target + variant + "/freetype/include", exist_ok=True)
	os.makedirs(target + variant + "/freetype/dist", exist_ok=True)
	if target == 'windows':
		shutil.copy(lib_dir + "/build/RelWithDebInfo/freetype.lib", target + variant + "/freetype/lib/")
		shutil.copy(lib_dir + "/build/RelWithDebInfo/freetype.pdb", target + variant + "/freetype/lib/")
	else:
		#todo: check what gets build on other oses:
		shutil.copy(lib_dir + "/build/libfreetype.a", target + variant + "/freetype/lib/")
	shutil.copy(lib_dir + "/include/ft2build.h", target + variant + "/freetype/include/")
	shutil.copytree(lib_dir + "/include/freetype/", target + variant + "/freetype/include/freetype/")
	shutil.copy(lib_dir + "/build/include/freetype/config/ftconfig.h", target + variant + "/freetype/include/freetype/config/")
	shutil.copy(lib_dir + "/build/include/freetype/config/ftoption.h", target + variant + "/freetype/include/freetype/config/")
	#This isn't quite right, since the FTL only requires acknowledgement in documentation:
	#shutil.copy(lib_dir + "/doc/FTL.TXT", target + variant + "/freetype/dist/")
	f = open(target + variant + '/freetype/dist/README-freetype.txt', 'wb')
	f.write('Freetype used under the provisions of the FTL.\n\nPortions of this software are copyright \u00A9 2020 The FreeType Project (www.freetype.org).  All rights reserved.\n'.encode('utf8'))
	f.close()



def make_package():
	print("Packaging...")
	if target == 'macos':
		remove_if_exists('macos')

		subprocess.run(['diff', '-r', 'macos-arm', 'macos-x86'],check=False) #DEBUG: what's actually different?
		#merge the -x86 and -arm branches:
		for (armpath, dirnames, filenames) in os.walk(target + '-arm'):
			outpath = re.sub('^macos-arm', 'macos', armpath)
			x86path = re.sub('^macos-arm', 'macos-x86', armpath)
			os.makedirs(outpath, exist_ok=True)
			for fn in filenames:
				if fn.endswith('.a') or fn in {'opusenc','opusdec','opusinfo'}:
					print("To merge: " + armpath + fn + " and " + x86path + fn)
					run_command([
						'lipo', '-create',
						'-output', f"{outpath}/{fn}",
						f"{armpath}/{fn}",
						f"{x86path}/{fn}"
					])
				else:
					with open(f"{armpath}/{fn}", 'rb') as f: arm = f.read()
					with open(f"{x86path}/{fn}", 'rb') as f: x86 = f.read()
					if arm == x86:
						shutil.copy(f"{armpath}/{fn}", f"{outpath}/{fn}")
					elif fn.endswith('.h'):
						print(f"Merged {armpath}/{fn} and {x86path}/{fn}")
						with open(f"{outpath}/{fn}", 'wb') as f:
							f.write(b'#ifdef __aarch64__\n//arm version:\n')
							f.write(arm)
							f.write(b'#else //__aarch64__\n//non-arm version:\n')
							f.write(x86)
							f.write(b'#endif //__aarch64__\n')
					else:
						print(f"ERROR: branch mis-match {armpath}/{fn} and {x86path}/{fn}")
						sys.exit(1)
	
	#create file to reflect version:
	with open(tag, 'w') as v:
		pass

	#Create a list of files to compress for release builds:
	listfile = work_folder + '/listfile'
	with open(listfile, 'w') as l:
		l.write('nest-libs/README.md\n')
		for (dirpath, dirnames, filenames) in os.walk(target):
			for fn in filenames:
				l.write('nest-libs/' + dirpath + '/' + fn + '\n')
	#Eventually might do this:
	#Also create a package directory because of the unique way in which artifact uploads work :-/
	#remove_if_exists(target + variant + "/package/")
	#os.makedirs(work_folder + "/package")
	#shutil.copy('README.md', work_folder + "/package/")
	#shutil.copytree(target + variant + "/", work_folder + "/package/target/")
	
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
	if "package" in sys.argv[1:]:
		to_build.append("package")

if "freetype" in to_build:
	for variant in variants:
		build_freetype()

if "harfbuzz" in to_build:
	for variant in variants:
		build_harfbuzz()

if "SDL2" in to_build:
	for variant in variants:
		build_SDL2()

if "glm" in to_build:
	for variant in variants:
		build_glm()

if "zlib" in to_build:
	for variant in variants:
		build_zlib()

if "libpng" in to_build:
	for variant in variants:
		build_libpng()

if "libopus" in to_build:
	for variant in variants:
		build_libopus()

if "libogg" in to_build:
	for variant in variants:
		build_libogg()

if "opusfile" in to_build:
	for variant in variants:
		build_opusfile()

if "libopusenc" in to_build:
	for variant in variants:
		build_libopusenc()

if "opus-tools" in to_build:
	for variant in variants:
		build_opustools()

if "package" in to_build:
	make_package()
