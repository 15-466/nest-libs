echo BEFORE choco install
choco install visualstudio2019buildtools
choco install visualstudio2019-workload-vctools
choco install python3
choco install 7zip
echo BEFORE refreshenv
refreshenv
echo BEFORE vcvars
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
echo AFTER vcvars
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat" -host_arch=amd64 -arch=amd64
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools\VsDevCmd.bat" -test
echo AFTER vsdevcmd
C:\Python37\python rebuild-libs.py all package
echo AFTER rebuild-libs
