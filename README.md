smux
====

smux is a wrapper around slurm and tmux. It allows tmux sessions to
run on a compute node under a slurm job and takes care of deternining 
which compute node the job is on and running ssh. Its supposed to be simliar to
tmux, but with slurm job ids or names instead of tmux session names.

It replaces sinteractive.
smux supports a lot of slurm sbatch options but not all of them. You can add them
pretty easily by looking at the code, I've only added the ones asked for


Installation
============

`pip install https://gitlab.erc.monash.edu.au/hpc-team/smux.git`

You probably want to create a virutalenv (say /usr/local/smux/0.0.1) before you do this
If you don't increment the version in setup.py you may want to 

`pip install --upgrade --force-reinstall https://gitlab.erc.monash.edu.au/hpc-team/smux.git`



