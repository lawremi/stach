#!/usr/bin/python
from __future__ import print_function

import os
import sys
import subprocess
import argparse
import getpass

import abc


class SlurmJob():
    jobid=None
    jobname=None
    jobstate=None

    def __init__(self,jobid,jobname,jobstate):
        self.jobid=jobid
        self.jobname=jobname
        self.jobstate=jobstate

class SmuxConnectionError(Exception):
    pass

class SessionDriver():
    @abc.abstractmethod
    def get_new_session_script(self):
        return

    @abc.abstractmethod
    def get_attach_command(self, name):
        return

class DtachDriver(SessionDriver):
    dtach_socket_dir=os.path.expanduser("~/.local/share/stach")
    dtach_socket=os.path.join(dtach_socket_dir, "$SLURM_JOB_NAME")
    slurm_script="""#!/bin/bash
dtach -n "{0}" bash
# Sleep until the dtach server exits
while [ -e "{0}" ]; do sleep 5; done
""".format(dtach_socket).encode()

    def get_new_session_script(self):
        if not os.path.exists(self.dtach_socket_dir):
            os.makedirs(self.dtach_socket_dir)
        return self.slurm_script

    def get_attach_command(self, name):
        return "dtach -a %s" % os.path.join(self.dtach_socket_dir, name)

class TmuxDriver(SessionDriver):
    slurm_script=b"""#!/bin/bash
tmux new-session -d -s $SLURM_JOB_NAME bash
# determine the process id of the tmux server
pid=$( /bin/ps x | /bin/grep -i "[t]mux new-session -d -s" | sed 's/^\ *//' | cut -f 1 -d " " )
ps x
# Sleep until the tmux server exits
while [ -e /proc/$pid ]; do sleep 5; done
"""
    def get_new_session_script(self):
        return slurm_script

    def get_attach_command(self, name):
        "tmux attach-session -t %s"%name

class Smux():
    ALLUSERS=False
    programname='smux'
    @classmethod
    def get_node(cls,jobid):
        output = subprocess.check_output(['squeue','--job',"%s"%jobid,'-o','%B','-h'])
        return output.decode('utf-8').strip()

    @classmethod
    def get_job_name(cls,jobid):
        output = subprocess.check_output(['squeue','--job',"%s"%jobid,'-o','%j','-h'])
        return output.decode('utf-8').strip()
        
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
            data = l.decode("utf-8").split(',')
            jobs.append(SlurmJob(data[0],data[1],data[2]))
        return jobs

    @classmethod
    def listJobs(cls,user,args):
        joblist = cls.get_job_list()
        print("")
        print("You have the following running jobs:")
        print("Job ID\tJob Name")
        for j in filter(lambda x: x.jobstate=='R', joblist):
            print("{}\t{}".format(j.jobid,j.jobname))
        print("")
        print("You have the following not yet started jobs:")
        print("Job ID\tJob Name")
        for j in filter(lambda x: not (x.jobstate=='R'), joblist):
            print("{}\t{}".format(j.jobid,j.jobname))
        print("")
        print("Use the command {} attach-session <jobid> or {} attach-session <jobname> to connect".format(cls.programname,cls.programname))
        print("Or use the command {} new-session to start a new interactive session".format(cls.programname))
        print("Or use the command {} why-are-we-waiting <jobid> to find out why a session hasn't started yet".format(cls.programname))

    @classmethod
    def newJob(cls,args):
        import time
        import sys
        command = ['sbatch',
                "--ntasks={}".format(args.ntasks[0]),
                "-J {}".format(args.jobname[0])
                ]
        if args.account[0] != None:
            command.append("--account={}".format(args.account[0]))
        if args.partition[0] != None:
            command.append("--partition={}".format(args.partition[0]))
        if args.reservation[0] != None:
            command.append("--reservation={}".format(args.reservation[0]))
        if args.cpuspertask[0] != None:
            command.append("--cpus-per-task={}".format(args.cpuspertask[0]))
        if args.nodes[0] != None:
            command.append("--nodes={}".format(args.nodes[0]))
        if args.mem[0] != None:
            command.append("--mem={}".format(args.mem[0]))
        if args.gres[0] != None:
            command.append("--gres={}".format(args.gres[0]))
        if args.qos[0] != None:
            command.append("--qos={}".format(args.qos[0]))
        if args.time[0] != None:
            command.append("--time={}".format(args.time[0]))

        '''This section appends the --output and --error to the command'''

        command.append("--output={}".format(args.output[0]))
        command.append("--error={}".format(args.error[0]))

        '''Now we start!'''

        p = subprocess.Popen(command, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (stdout,stderr) = p.communicate(args.driver[0].get_new_session_script())
        print("Requesting an interactive session")
        if stderr is not None and len(stderr) > 0:
            print(stderr.decode())
        jobs = cls.get_job_list()
        if len(jobs) == 0:
            time.sleep(1)
        jobs = cls.get_job_list()
        if len(jobs) == 1:
            print("Waiting to see if your interactive session starts",end='')
            sys.stdout.flush()
            time.sleep(2)
            jobs = cls.get_job_list()
            if jobs[0].jobstate == 'R':
                cls.connect_job(args.driver[0], jobs[0].jobid)
            else:
                # Loop for up to 20 seconds waiting for the job to start
                count=1
                while count<10:
                    jobs = cls.get_job_list()
                    if len(jobs) == 1:
                        if jobs[0].jobstate == 'R':
                            cls.connect_job(args.driver[0], jobs[0].jobid)
                    time.sleep(2)
                    count=count+1
                    print('.',end='')
                    sys.stdout.flush()
                print("")
                print("I can't connect you straight to your session because it hasn't started yet")
                print("use smux list-sessions to determine when it starts and")
                print("smux attach-session <jobid> to connect once it has started")
        elif len(jobs) == 0:
            print("Your job failed to submit for some reason.")
            print("Please look above for any error messages from sbatch")
            print("One possibility is you asked for an invalid combination of resources")
            print("Another option is that you made a typo in the command line")
            print("Either way plese try options one at a time.")
            print("If all else fails submit a help request to help@massive.org.au")
        else:
            print("I can't connect you straight to your session because you have more than one session running")
            print("use smux list-sessions to list your sessions")
            print("smux attach-session <jobid> to connect to the correct session")


    @classmethod
    def connect_job(cls,driver,jobid):
        import time
        node=cls.get_node(jobid)
        name=cls.get_job_name(jobid)
        time.sleep(1)
        os.execv("/usr/bin/ssh",["ssh",node,"-t",
                                 driver.get_attach_command(jobid)])

    @classmethod
    def connectJob(cls,args):
        jobs = cls.get_job_list()
        try:
            jobid=args.jobid[0]
        except:
            try:
                jobid=args.jobid
            except:
                jobid=None
        if jobid != None:
            for j in jobs:
                if str(jobid) in j.jobid and j.jobstate != 'R':
                    raise SmuxConnectionError("Your session hasn't started yet")
        if jobid == None:
            jobs = cls.get_job_list()
            if len(jobs) == 1:
                if jobs[0].jobstate == 'R':
                    jobid=jobs[0].jobid
                else:
                    raise SmuxConnectionError("Your session hasn't started yet")
        if jobid == None:
            raise SmuxConnectionError("I couldn't figure out what you were trying to connect to, try specifying a jobid")
        cls.connect_job(args.driver[0], jobid)

    @classmethod
    def driver(cls,name):
        return globals()[name.capitalize()+"Driver"]()

    @classmethod
    def jobid(cls,user,string):
        if not cls.ALLUSERS:
            output=subprocess.check_output(['squeue','-u',user,'-h','-o','%i %j']).splitlines()
        else:
            output=subprocess.check_output(['squeue','-h','-o','%i %j']).splitlines()
        for lb in output:
            l=lb.decode('utf-8')
            if string in l:
                jobid=l.split(' ')[0]
                return int(jobid)
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

                Use "%(prog)s new" to create a new session
                Use "%(prog)s list" to list existing sessions
                Use "%(prog)s attach -t <ID>" to connect to an existing session

                When in a session, use the keys control+b then press d to dettach from the session

                <ID> is optional if you only have one job.

                For more detailed help on each subcommand you can %(prog)s <subcommand> --help, 
                for example %(prog)s n --help will display additional options for starting a new session
                '''))
        parser.add_argument('-d','--driver',default=[Smux.driver("dtach")],nargs=1,help="The session driver, either 'dtach' or 'tmux'", type=lambda x: Smux.driver(x))
        subparser = parser.add_subparsers()
        connect=subparser.add_parser('attach')
        connect.add_argument('jobid',metavar="<jobid>",default=[None], type=lambda x: Smux.jobid(user,x),nargs='?',help="A job ID or job name")
        connect.add_argument('-t','--target',action='store_true')
        connect.set_defaults(func=Smux.connectJob)
        new=subparser.add_parser('new')
        new.add_argument('--ntasks',type=int, default=[1], metavar="<n>",nargs=1,help="The number of tasks you will launch")
        new.add_argument('--nodes',type=int, default=[None], metavar="<n>",nargs=1,help="The number of nodes you need")
        new.add_argument('--mem', default=[None], metavar="<n>",nargs=1,help="The amount of memory you need")
        new.add_argument('--cpuspertask',type=int, default=[None], metavar="<n>",nargs=1,help="The number of cpus needed for each task")
        new.add_argument('--qos', default=[None], metavar="<n>",nargs=1,help="The QoS (Quality of Service) used for the task (certain QoS are only valid on some partitiotns)")
        new.add_argument('-J','--jobname', default=["interactive_session"], metavar="<n>",nargs=1,help="The name of your job")
        new.add_argument('-A','--account', default=[None], metavar="<n>",nargs=1,help="Specify your account")
        new.add_argument('-p','--partition',default=[None],nargs=1,help="The partition to execute on")
        new.add_argument('-r','--reservation',default=[None],nargs=1,help="The reservation to use")
        new.add_argument('-t','--time',default=[None],nargs=1,help="The amount of time to run for")
        new.add_argument('--gres',default=[None], metavar="<n>",nargs=1,help="The type and number of gpus needed for each task")
        new.add_argument('-o','--output',default=["smux-%j.out"], metavar="<n>",nargs=1,help="Standard output file name")
        new.add_argument('-e','--error', default=["smux-%j.err"], metavar="<n>",nargs=1,help="Error output file name")
        new.set_defaults(func=Smux.newJob)
        listjobs=subparser.add_parser('list')
        listjobs.set_defaults(func=lambda x: Smux.listJobs(user,x))
        waiting=subparser.add_parser('why-are-we-waiting')
        waiting.add_argument('jobid',metavar="<jobid>", type=lambda x: Smux.jobid(user,x),nargs=1,help="A job ID or job name")
        waiting.set_defaults(func=Smux.whyAreWeWaiting)
        
        args=parser.parse_args()
        try:
            args.func(args)
        except SmuxConnectionError as e:
            print(e)
        except Exception as e:
            print(e)
            import traceback
            print(traceback.format_exc())
            parser.print_help()
