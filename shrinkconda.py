#script to shrink conda install
import sys
import subprocess
import glob
import shutil
import os
import glob2

from contextlib import contextmanager


CONDA_RUNTIME = "/tmp/conda/condaruntime"

def get_size():
    o = subprocess.check_output("du -s {}".format(CONDA_RUNTIME), shell=True)
    return int(o.split("\t")[0])


phases = []
@contextmanager
def measure(phase_name):
    size_before = get_size()
    yield 
    size_after  = get_size()
    phases.append((phase_name, size_before, size_after))



with measure("delete non-avx2 mkl"):

    # for AVX
    for g in ["*_mc.so", "*_mc2.so",  "*_mc3.so",  "*_avx512*", "*_avx.*"]:
        for f in glob2.glob(CONDA_RUNTIME + "/lib/" + g):
            print "removing", f
            os.remove(f)
    shutil.rmtree("/tmp/conda/condaruntime/pkgs/mkl-11.3.3-0/", ignore_errors=True)
    print "after extra lib removal", get_size()

with measure("strip shared libs (gcc)"):

    for so_filename in glob2.glob("{}/**/*.so".format(CONDA_RUNTIME)):
        try: 
            print "stripping", so_filename
            o = subprocess.check_output("strip --strip-all {}".format(so_filename), shell=True)
        except subprocess.CalledProcessError as e:
            print "whoops", so_filename
            pass

with measure("conda clean"):
    subprocess.check_output("{}/bin/conda clean --all".format(CONDA_RUNTIME), 
                                                              shell=True)

with measure("delete *.pyc"):

    for pyc_filename in glob2.glob("{}/**/*.pyc".format(CONDA_RUNTIME)):
        os.remove(pyc_filename)

                            
for phase, before, after in phases:
    print "{:18s} : {:6.1f}M   -> {:6.1f}M".format(phase, before/1e3, after/1e3)
