Installation
============

`pip install https://gitlab.erc.monash.edu.au/hpc-team/smux.git`

You probably want to create a virutalenv (say /usr/local/smux/0.0.1) before you do this
If you don't increment the version in setup.py you may want to 

`pip install --upgrade --force-reinstall https://gitlab.erc.monash.edu.au/hpc-team/smux.git`


Use
===

Use `sbatch ./120gb` to start the session, then `smux attach-session` to attach to it. The sbatch part should be integrated into smux new-session


