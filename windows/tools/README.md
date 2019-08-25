# VS Command Prompt + jam

The `cmd.exe + x64 VS2019 + jam.lnk` shortcut will launch a cmd.exe prompt with a proper setup for using jam and visual studio 2019. In order to use this shortcut, you'll need to edit `Properties > Shortcut > Start in:` to point to this folder.

The shortcut uses the batch file `vcvars64_and_jam.bat` which sets the PATH and JAM_TOOLSET variables, and then calls vcvars64.bat from the default install location of Visual Studio. If you installed visual studio at a non-standard path, you'll need to edit the batch file.
