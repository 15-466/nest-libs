@echo Setting JAM_TOOLSET and adding %~dp0 to PATH
@set JAM_TOOLSET=VISUALC
@set PATH=%PATH%;%~dp0
@call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
@cd %~dp0/../../../

