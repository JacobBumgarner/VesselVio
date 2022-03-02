---
layout: default
title: "Build Instructions"
rank: 4
---

## Overview
If you are unable to run the bundled VesselVio app or prefer to create the app locally, this page is for you. Below you'll find detailed instructions explaining how to download the necessary files and then run the application from your command prompt/terminal.

We've tried to make this process as streamlined as possible! By the end, you should be able to run the app with a single line of code. Please [contact us](mailto:vesselvio@gmail.com) if you need help or have questions.

If you're using a PC, follow the [Windows Build Instructions](#windows-build-instructions) guide.

If you're using a Mac, follow the [MacOS Build Instructions](#macos-build-instructions) guide.

---
## Windows Command Prompt Instructions
First, you'll need to install python 3.8.8. This can be <a href="https://xkcd.com/1987/" target="_blank">messy</a> if you've got python installed elsewhere or if you don't have an environment manager.

We use the popular python environment manager: pyenv. If you've already got a python environment setup, skip to step 4.

1. Install [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) as directed by the developers.

2. Install [pyenv-winows](https://github.com/pyenv-win/pyenv-win) as directed by the developers or by following the instructions below.
   - Paste the following command into your command prompt
```markdown
git clone https://github.com/pyenv-win/pyenv-win.git "%USERPROFILE%\.pyenv"
```
   - Paste the following commands one-by-one into a powershell.
``` markdown
[System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
[System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv\pyenv-win\bin;" + $env:USERPROFILE + "\.pyenv\pyenv-win\shims;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
```
   - Restart your command prompt, and then paste the command below to ensure pyenv was installed correctly. A version # will show if the installation worked.
```markdown
pyenv --version
```
   - Following successful installation, paste the following into the command prompt to complete the installation.
```markdown
pyenv rehash
```
   - Restart your terminal

3. Install python version 3.8.8.
   - First, paste the following command into your command prompt.
```markdown
pyenv install 3.8.8 
```
   - Then, activate python version 3.8.8 using the following command.
```markdown
pyenv activate 3.8.8
```
   - Lastly, update your pip installer the command below.
```markdown
pip install -U pip
```

4. Download the VesselVio source code from our [GitHub page](https://github.com/JacobBumgarner/VesselVio).
   - On the GitHub page, click the green Code dropdown button, then Download ZIP. 
   - Unzip the package, and place it somewhere accessible to you (e.g., your desktop).

5. Navigate to the vesselVio file directory to install the required python packages.
   - For example, if the directory is located on your desktop, navigate to it by typing the following into your command prompt:
```markdown
cd desktop\VesselVio
```
   - Make sure python 3.8.8 is activated (step 3.1)
   - Install the necessary VesselVio dependency packages
```markdown
pip install -r requirements.txt
```

6. You should now be able to execute the VesselVio.py file to run the application!
   - First make sure you've activated python 3.8.8 in your command prompt.
```markdown
python activate 3.8.8
```
   - Then make sure you've navigated to the VesselVio source code folder (example below).
```markdown
cd desktop\VesselVio
```
   - Finally, run the application by typing the following command into your command prompt.
```markdown
python VesselVio.py
```

#### Windows App Bundling
If you want to build a local standalone VesselVio application, follow these instructions.
   - Copy the pyinstaller .exe from your .pyenv folder created in step 2 into your VesselVio directory
         - Example file location: `.pyenv>pyenv-win>versions>3.8.8>Scripts>pyinstaller.exe`
   - Navigate to the VesselVio directory
   - Activate python 3.8.8
   - Execute the following command in your command prompt:
```markdown
pyinstaller --add-data=Library;Library --additional-hooks-dir=Hooks --icon Icons\icon.ico --windowed VesselVio.py 
```
   - The .exe file will be located in the 'dist' folder in the folder that contains the original source-code. Create a shortcut to this .exe file, and move it wherever you prefer.

You should now be able to successfuly use VesselVio on your PC either from the command prompt or as a local standalone application!

---
## MacOS Terminal Instructions
First, you'll need to install python 3.8.8. This can be <a href="https://xkcd.com/1987/" target="_blank">messy</a> if you've got python installed elsewhere or if you don't have an environment manager.

We use the popular python environment manager: pyenv. If you've already got a python environment setup, skip to step 5.

1. Install [Homebrew](https://brew.sh) as instructed by the developers (a simple copy and paste).

2. Install [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv).
   - First, install the packages by pasting the following commands into your terminal.
```markdown
brew install pyenv
brew install pyenv-virtualenv
```
   - The , configure your shell's environment for pyenv and virtualenv (we use Zsh, see [here](https://github.com/pyenv/pyenv#homebrew-on-macos) if you use Bash or Fish). To do this, paste the following commands into your terminal to modify the .zprofile and .zshrc
```markdown
echo 'eval "$(pyenv init --path)"' >> ~/.zprofile
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
```
   - Restart your terminal.
   - Lastly, ensure pyenv is set up by typing `pyenv` into a new terminal window. If set up correctly, you should see a list of commands.

3. Install the python version 3.8.8.
   - Paste the following into the terminal
```markdown
pyenv install 3.8.8
``` 
   - Make sure pip is up to date by typing in.
```markdown
pip install -U pip
```

4. Create a new virtual environment called 'VV' (or whatever name you prefer), and activate this environment.
   - Create the environment by pasting the following command into your terminal. Replace 'VV' if you prefer a different name.
```markdown
pyenv virtualenv 3.8.8 VV
```
   - Activate the environment by typing the following into your terminal
```markdown
pyenv activate VV
```

5. Download the VesselVio source code from our [GitHub page](https://github.com/JacobBumgarner/VesselVio).
   - On the GitHub page, click the green Code dropdown button, then Download ZIP.  
   - Unzip the package, and place it somewhere accessible to you (e.g., your desktop).

6. Then navigate to the VesselVio file directory to install the required python packages.
   - For example, if the directory is located on your desktop, navigate to your directory by typing the following into your terminal:
```markdown
cd desktop/VesselVio
```
   - Make sure your virtual environment is activated (step 4.2, example below)
```markdown
pyenv activate VV
```
   - Install the necessary VesselVio dependency packages using the following command.
```markdown
pip install -r requirements.txt
```

7. You should now be able to execute the VesselVio.py file to run the application!
   - First make sure you've activated your python environment (example below)
```markdown
pyenv activate VV
```
   - Then, navigate to the VesselVio directory (example below)
```markdown
cd desktop/VesselVio
```
   - Finally, run the application by typing the following command into your terminal.
```markdown
python VesselVio.py
```

#### MacOS App Bundling
To build a local version of the application, you'll first have to reinstall python 3.8.8 with an updated framework configuration.
```markdown
sudo env PYTHON_CONFIGURE_OPTS="--enable-framework" pyenv install 3.8.8
```
   - Then, to build the app, paste the following code into your terminal:
```markdown
pyinstaller \
--add-data=./Library:Library \
--additional-hooks-dir=./Hooks \
--icon Icons/icon.icns
--windowed \
VesselVio.py
```
   - The app will be located in the 'dist' folder in the folder that contains the original source code.

You should now be able to successfuly use VesselVio on your Mac either from the terminal or as a local standalone application!
