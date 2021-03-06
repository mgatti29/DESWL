#!/usr/bin/env python
# Program to loop over exposures and run a given command
#
# The file argument expects a file containing a list of expnum such as:
#     
#    232382
#    232383
#    232395
#    240551
#    241144
#    241146
# 
# The command argument is the name of exectuation that is expected 
# to take a --exps arcument to specify which exposure(s) to run.
# 

from __future__ import print_function

import argparse,os,re
import time
import numpy
import datetime
import numpy as np


parser = argparse.ArgumentParser(description='Run single file')
parser.add_argument('--file', default='',
                    help='list of run/exposures')
parser.add_argument('--submit_dir',default=None,
                    help='where to put submit files')
parser.add_argument('--cmd',
                    default='/direct/astro+u/mjarvis/rmjarvis/DESWL/psf/run_piff_condor.sh',
                    help='command to run for each exposure')
parser.add_argument('--mem', default=2000,
                    help='memory required in MBytes')
parser.add_argument('--tag', default='',
                    help='tag for the version being run')

args = parser.parse_args()


top_txt="""

Universe        = vanilla

Notification    = Never

# Run this exe with these args
Executable      = {cmd}

Image_Size       = {mem}

GetEnv = True

kill_sig        = SIGINT

#requirements = (cpu_experiment == "star") || (cpu_experiment == "phenix")
requirements = (cpu_experiment == "phenix")

+Experiment     = "astro"

"""

job_txt="""
+job_name = {name}
Arguments = {tag} {exp} /gpfs/mnt/gpfs01/astro/workarea/mjarvis/y3_piff/{tag} /gpfs/mnt/gpfs01/astro/workarea/mjarvis/y3_piff/{tag}/logs/{name}.log
Output = /gpfs/mnt/gpfs01/astro/workarea/mjarvis/y3_piff/{tag}/output/{name}.out
Queue

"""


if args.submit_dir is None:
    date = datetime.date.today()
    submit_dir = '~/work/condor_%d%02d%02d_%s'%(date.year,date.month,date.day,args.tag)
else:
    submit_dir = args.submit_dir

submit_dir = os.path.expanduser(submit_dir)
print('submit_dir = ',submit_dir)
if not os.path.isdir(submit_dir): os.makedirs(submit_dir)

# Read in the runs, exps from the input file
print('Read file ',args.file)
with open(args.file) as fin:
    lines = [ line for line in fin if line[0] != '#' ]
nexps = len(lines)
print('Exposures file has %d lines'%nexps)
lines = np.unique(lines)
if nexps != len(lines):
    nexps = len(lines)
    print('Warning: the exposure list has duplicate entries!')
    print('Only %d unique exposures'%nexps)

exps = [ line.strip() for line in lines ]
nexp = len(exps)
print('nexp = ',nexp)

nbatch = len(exps) // 1000 + 1
print('nbatch = ',nbatch)

output_dir = '/gpfs/mnt/gpfs01/astro/workarea/mjarvis/y3_piff/{tag}/output/'.format(tag=args.tag)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for batch_num in range(nbatch):
    k0 = nexp * batch_num // nbatch
    k1 = nexp * (batch_num+1) // nbatch
    print('First batch has exposures numbered %d..%d'%(k0,k1))

    condor_script = top_txt.format(cmd=args.cmd, mem=args.mem*1024)

    for exp in exps[k0:k1]:
        name = 'run_piff_%s_%s'%(args.tag, exp)
        condor_script = condor_script + job_txt.format(name=name, exp=exp, tag=args.tag)

    condor_file = os.path.join(submit_dir, 'run_piff_%d.condor'%batch_num)
    with open(condor_file,'w') as fout:
        fout.write(condor_script)
    print('Wrote ',condor_file)

print('To submit all jobs, do')
print()
for batch_num in range(nbatch):
    condor_file = os.path.join(submit_dir, 'run_piff_%d.condor'%batch_num)
    print('    condor_submit %s'%condor_file)
print()
print("Or, use Erin's incremental submitter")
print()
print('    condor-incsub %s/run_piff*.condor'%submit_dir)

