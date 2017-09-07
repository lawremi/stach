#!/usr/bin/python
import os
import sys
import subprocess
import argparse
import getpass


class SlurmJob():
    jobid=None
    jobname=None
    jobstate=None

    def __init__(self,jobid,jobname,jobstate):
        self.jobid=jobid
        self.jobname=jobname
        self.jobstate=jobstate

class Smux():
    slurm_script="""#!/bin/bash
tmux new-session -d -s $SLURM_JOB_NAME bash
# determine the process id of the tmux server
pid=$( /bin/ps x | /bin/grep -i "[t]mux new-session -d -s" | sed 's/^\ *//' | cut -f 1 -d " " )
ps x
# Sleep until the tmux server exits
while [ -e /proc/$pid ]; do sleep 5; done
"""
    ALLUSERS=False
    programname='smux'
    @classmethod
    def get_node(cls,jobid):
        output = subprocess.check_output(['squeue','--job',"%s"%jobid,'-o','%B','-h'])
        return output.strip()

    @classmethod
    def get_job_name(cls,jobid):
        output = subprocess.check_output(['squeue','--job',"%s"%jobid,'-o','%j','-h'])
        return output.strip()
        
    @classmethod
    def whyAreWeWaiting(cls,args):
        print("Sorry, I haven't written this function yet")


    @classmethod
    def get_job_list(cls):
        user=getpass.getuser()
        if not cls.ALLUSERS:
            p = subprocess.Popen(['squeue','-u','{}'.format(user),'--noheader','-o','%A,%j,%t'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(['squeue','--noheader','-o','%A,%j,%t'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = p.communicate()
        jobs=[]
        for l in stdout.splitlines():
            data = l.split(',')
            jobs.append(SlurmJob(data[0],data[1],data[2]))
        return jobs

    @classmethod
    def listJobs(cls,user,args):
        joblist = cls.get_job_list()
        print("")
        print("You have the following running jobs:")
        print("Job ID\tJob Name")
        for j in filter(lambda x: x.jobstate=='R', joblist):
            print("{}\t{}").format(j.jobid,j.jobname)
        print("")
        print("You have the following not yet started jobs:")
        print("Job ID\tJob Name")
        for j in filter(lambda x: not (x.jobstate=='R'), joblist):
            print("{}\t{}").format(j.jobid,j.jobname)
        print("")
        print("Use the command {} attach-session <jobid> or {} attach-session <jobname> to connect".format(cls.programname,cls.programname))
        print("Or use the command {} new-session to start a new interactive session".format(cls.programname))
        print("Or use the command {} why-are-we-waiting <jobid> to find out why a session hasn't started yet".format(cls.programname))

    @classmethod
    def newJob(cls,args):
        import time
        command = ['sbatch',
                "--ntasks={}".format(args.ntasks[0]),
                "-J {}".format(args.jobname[0])
                ]
        if args.partition[0] != None:
            command.append("--partition={}".format(args.partition[0]))
        if args.reservation[0] != None:
            command.append("--reservation={}".format(args.reservation[0]))
        if args.cpuspertask[0] != None:
            command.append("--cpus-per-task={}".format(args.cpuspertask[0]))
        if args.nodes[0] != None:
            command.append("--nodes={}".format(args.nodes[0]))
        if args.gres[0] != None:
            command.append("--gres={}".format(args.gres[0]))
        p = subprocess.Popen(command, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = p.communicate(cls.slurm_script)
        print(stdout)
        print(stderr)
        jobs = cls.get_job_list()
        if len(jobs) == 1:
            time.sleep(2)
            jobs = cls.get_job_list()
            if jobs[0].jobstate == 'R':
                cls.connect_job(jobs[0].jobid)
            else:
                print("I can't connect you straight to your session because it hasn't started yet")
                print("use smux list-sessions to determine when it starts and")
                print("smux attach-session <jobid> to connect once it has started")
        else:
            print("I can't connect you straight to your session because you have more than one session running")
            print("use smux list-sessions to list your sessions")
            print("smux attach-session <jobid> to connect to the correct session")


    @classmethod
    def connect_job(cls,jobid):
        node=cls.get_node(jobid)
        name=cls.get_job_name(jobid)
        os.execv("/usr/bin/ssh",["ssh",node,"-t","tmux attach-session -t %s"%name])

    @classmethod
    def connectJob(cls,args):
        jobid=args.jobid[0]
        cls.connect_job(jobid)

    @classmethod
    def jobid(cls,user,string):
        if not cls.ALLUSERS:
            output=subprocess.check_output(['squeue','-u',user,'-h','-o','%i %j']).splitlines()
        else:
            output=subprocess.check_output(['squeue','-h','-o','%i %j']).splitlines()
        for l in output:
            if string in l:
                jobid=l.split(' ')[0]
                return jobid
        msg="%s is not a job id or a job name"%string
        raise argparse.ArgumentTypeError(msg)

    @classmethod
    def main(cls):
        import os
        import textwrap
        import sys
        import getpass
        import argparse
        cls.programname=os.path.basename(sys.argv[0])
        cls.ALLUSERS=False
        user=getpass.getuser()
        parser=argparse.ArgumentParser(prog=cls.programname,formatter_class=argparse.RawDescriptionHelpFormatter,
                description=textwrap.dedent('''\
                A tool to created and reconnect to interactive sessions

                Use "%(prog)s new-session" to create a new session
                Use "%(prog)s list-sessions" to list existing sessions
                Use "%(prog)s attach-session <ID>" to connect to an existing session

                When in a session, use the keys control+b then press d to dettach from the session
                '''))
        subparser = parser.add_subparsers()
        connect=subparser.add_parser('attach-session')
        connect.add_argument('jobid',metavar="<jobid>", type=lambda x: Smux.jobid(user,x),nargs=1,help="A job ID or job name")
        connect.set_defaults(func=Smux.connectJob)
        new=subparser.add_parser('new-session')
        new.add_argument('--ntasks',type=int, default=[1], metavar="<n>",nargs=1,help="The number of tasks you will launch")
        new.add_argument('--nodes',type=int, default=[None], metavar="<n>",nargs=1,help="The number of nodes you need")
        new.add_argument('--cpuspertask',type=int, default=[None], metavar="<n>",nargs=1,help="The number of cpus needed for each task")
        new.add_argument('-J','--jobname', default=["interactive_session"], metavar="<n>",nargs=1,help="The number of cpus to request")
        new.add_argument('-p','--partition',default=[None],nargs=1,help="The partition to execute on")
        new.add_argument('-r','--reservation',default=[None],nargs=1,help="The reserveration to use")
        new.add_argument('--gres',default=[None], metavar="<n>",nargs=1,help="The type and number of gpus needed for each task")
        new.set_defaults(func=Smux.newJob)
        listjobs=subparser.add_parser('list-sessions')
        listjobs.set_defaults(func=lambda x: Smux.listJobs(user,x))
        waiting=subparser.add_parser('why-are-we-waiting')
        waiting.add_argument('jobid',metavar="<jobid>", type=lambda x: Smux.jobid(user,x),nargs=1,help="A job ID or job name")
        waiting.set_defaults(func=Smux.whyAreWeWaiting)
        
        args=parser.parse_args()
        args.func(args)
