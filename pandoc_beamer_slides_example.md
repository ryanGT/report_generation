# Outline

## Main Point

- Raspberry Pi does not need to be scary
- you can do a lot of cool stuff with the RPi, but you can just
  use the `jupyter-notebook` and serial
    - exactly like we have already been doing in lab
- I have already done the hard work of proper configuration
- you need to install a VNC client, log in, and start the `jupyter-notebook`
  
## Outline/Overview

- install VNC client
    - probably Real VNC Viewer
- use static IP to log into RPi over VNC
- use `git` to update software if needed
- launch `jupyter-notebook`
- use serial in `jupyter-notebook` as usual

# VNC

## Real VNC Viewer

- should be a free download
- available on any device/OS
- you do not need to create an account with them
- Google `vnc viewer`
    - should take you to here: 
	
<https://www.realvnc.com/en/connect/download/viewer/>


## VNC Viewer: First Time

- go to File > New connection
- provide IP and give a name for the connection

# Terminal

## Open a Terminal

- I will record another video on basic terminal usage soon
- the terminal is a powerful tool
- take advantage to tab completion and the up arrow

# Git

## Git Pull

- if I email you to say I have updated something, use `git` to
  get the latest software
- two steps:
    1. change to the directory that contains my provided software:
	    - `cd SBR_git`
	2. use the `git pull` command to retrieve any updates:
	    - `git pull origin master`
		
- `git` should warn you if this would overwrite any of your changes
- if you want to modify the `jupyter` notebook, you should probably make
  a copy

## Launching the Jupyter-Notebook

- `cd` back to your home directory
- launch the notebook with this command:
    - `jupyter-notebook`

# Demo

## Quick Demo

- I will walk through these steps on my line following robot
