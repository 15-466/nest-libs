choco install visualstudio2019buildtools
choco install visualstudio2019-workload-vctools
choco install python3
choco install 7zip
refreshenv
@call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
C:\Python37\python rebuild-libs.py all package
