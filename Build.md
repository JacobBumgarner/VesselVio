---
layout: default
title: "Build Instructions"
rank: 3
---

If you are unable to run the packaged VesselVio app, or if the packaged app versions are newer than your computer's OS version, this page is for you. Below are instructions detailing how to install the needed files to run VesselVio from the terminal or to build your own version of a stand-alone VesselVio application.

If you're using a Mac, follow the [MacOS Build Instructions](#macos-build-instructions) guide.

If you're using a PC, follow the [Windows Build Instructions](#windows-build-instructions) guide.


## MacOS Build Instructions
First you'll need to install python 3.8.8. This can be <a href="https://xkcd.com/1987/" target="_blank">messy</a> if you've got python installed elsewhere or if you don't have an environment manager.

We typically use an environment manager: pyenv. We build it using Homebrew. If you've already got a python environment setup, skip to step 3.

1. Install [Homebrew](https://brew.sh) as instructed by the developers.

2. Install [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) as instructed by the developers or by pasting the following code into a terminal window.
```markdown
install pyenv
install pyenv-virtualenv
```
   - Configure your shell's environment for pyenv (here we use Zsh). Enter the following commands into your terminal to modify the .zprofile.
```markdown
echo 'eval "$(pyenv init --path)"' >> ~/.zprofile
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
   - Next adjust the .zshrc
```markdown
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
```
   - Restart your terminal.
   - Ensure pyenv is set up by typing `pyenv` into a new terminal window. You should see a list of commands.

3. Now install the correct version of python (3.8.8) by pasting the following command
```markdown
pyenv install 3.8.8
```
   - If you want to build your own version of the app using pyinstaller, paste the following command
```markdown
sudo env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.8.8
```
   - Create a new virtual environment
```markdown
pyenv virtualenv 3.8.8 VV
```

4. Activate your virtual environment. If you're planning on running VesselVio from the terminal, you'll need to do this every time as well as navigate to the VesselVio directory before executing the VVTerminal.py or VesselVio.py files from the terminal.
```markdown
pyenv activate VV
```
   - Install all of the required python packages. First navigate to the VesselVio directory (folder; example below)
```markdown
cd desktop/VesselVio
```
   - Update your pip version
```markdown
pip install -U pip
```
   - Then paste the following command into your terminal
```markdown
pip install -r requirements.txt
```

5. If you want to run the application from your terminal, navigate to the directory location where the VesselVio source-code is located. The source-code can be downloaded from our [GitHub page](https://github.com/JacobBumgarner/VesselVio). Make sure VV has been activated before trying to execute any files!
   - Navigate to your folder (example below)
```markdown
cd desktop/VesselVio
```
   - Build the application using the following command.
```markdown
python VesselVio.py
```
   - Or, if you're using and IDE to create videos or modifying the source-code, execute the following
```markdown
python VVTerminal.py
```
6. If you want to build a local version of the application, paste the following code into your terminal:
```markdown
pyinstaller \
--add-data=./Library:Library \
--additional-hooks-dir=./Hooks \
--hidden-import=matplotlib \
--windowed \
VesselVio.py
```
 
You should now be able to use VesselVio for dataset analysis and visualization!


## Windows Build Instructions
First you'll need to install python 3.8.8. This can be <a href="https://xkcd.com/1987/" target="_blank">messy</a> if you've got python installed elsewhere or if you don't have an environment manager.

We typically use an environment manager: pyenv. For Windows, we install pyenv using Git. If you've already got a python environment setup, skip to step 4.

1. Install [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) as directed by the developers.

2. Install [pyenv-winows](https://github.com/pyenv-win/pyenv-win) as directed by the developers or by following the instructions below.
   - Paste the following code into your command prompt
```markdown
git clone https://github.com/pyenv-win/pyenv-win.git "%USERPROFILE%\.pyenv"
```
   - In a powershell, paste the following commands:
``` markdown
[System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv\pyenv-win\bin;" + $env:USERPROFILE + "\.pyenv\pyenv-win\shims;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
```
   - Restart your terminal, and type the following to ensure pyenv was installed correctly.
```markdown
pyenv --version
```
   - If installation was successful, type the following into your terminal
```markdown
pyenv rehash
```

3. Install python 3.8.8
```markdown
pyenv install 3.8.8 
```
   - Activate the 3.8.8 version. You'll have to do this each time before running VesselVio from the terminal!

4. Navigate to the VesselVio file directory to install the needed python packages. The source-code can be downloaded from our [GitHub page](https://github.com/JacobBumgarner/VesselVio).
   - For example, if the directory is located on your desktop, type the following:
```markdown
cd desktop/VesselVio
```
   - Activate python 3.8.8 as directed above, then update your pip installer.
```markdown
pip install -U pip
```
   - Install the necessary python packages
```markdown
pip install -r requirements.txt
```

5. You should now be able to execute the VesselVio files.
   - If you want to run the application from the terminal, use the following code after activating python 3.8.8 and navigating to the source-code directory
```markdown
python VesselVio.py
```
   - If you are planning on creating videos or customizing the source-code using an IDE, run the following code for terminal executions
```markdown
python VVTerminal.py
```

6. If you want to build a local stand-alone VesselVio application, follow these instructions.
   - Copy the pyinstaller .exe from your .pyenv folder created in step 2 into your VesselVio directory
   - Navigate to the VesselVio folder
   - Activate python 3.8.8 using pyenv
   - Execute the following command in your terminal.
```markdown
pyinstaller --add-data=Library;Library --additional-hooks-dir=Hooks --hidden-import=matplotlib VesselVio.py --windowed
```

You should now be able to successfuly use VesselVio on your PC either from the terminal or as a local stand-alone application!
