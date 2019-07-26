stach
====

`stach` is a wrapper around slurm and dtach/tmux. It runs sessions on a compute node under a slurm job and takes care of deternining which compute node the job is on and running ssh to reattach to sessions.

It is based on the
[smux tool](https://gitlab.erc.monash.edu.au/hpc-team/smux). Almost
all of the credit goes to the smux project.

`stach` supports a lot of slurm `sbatch` options but not all of them.

Installation
============

`pip install --user git+https://github.com/lawremi/stach`

You probably want to create a virutalenv (say /usr/local/stach/0.0.1)
before you do this.

If you don't increment the version in `setup.py` you may want to

`pip install --user --upgrade --force-reinstall git+https://github.com/lawremi/stach`

Basic Usage
============

Start a new session:
```
stach new
```

Attach to running session:
```
stach attach
```

