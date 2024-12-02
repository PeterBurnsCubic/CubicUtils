#!/bin/python3

import os
import subprocess
import re

srcdir   = "/usr/local/src/gitserver/TfL_LCP3_Gate/"
builddir = "Gate_Common/lcp3_e2gate/build/i386-linux-gnu/lcp3_e2gate_release_i386-linux-gnu/"
exec     = srcdir + builddir + "e2gate"
rxsoname = re.compile("[^\s/]+\.so[^\s/]*")  # regex for shared library names (anywhere in the string)
rxpkname = re.compile("^[^\s/]+:i386")       # regex for i386 package names (at the start of the string)

if not os.path.isfile(exec):
    raise Exception("{} not found".format(exec))
print("Creating shared library version list for {}".format(exec))

# find shared libs by running ldd
pkgset = set()
ldd_lines = subprocess.check_output(["ldd", exec], text=True).splitlines()
for ldd_line in ldd_lines:
    sonames = rxsoname.findall(ldd_line)
    if len(sonames) < 1:
        print('Could not find library name in "{}'.format(ldd_line))
    else:
        # for each lib, find the i386 package it belongs to by running "dpkg -S"
        try:
            dpkg_lines = subprocess.check_output(['dpkg', '-S', sonames[0]], text=True).splitlines()
            found = False
            for dpkg_line in dpkg_lines:
                pkglist = rxpkname.findall(dpkg_line)
                if len(pkglist) > 0:
                    pkgset.add(pkglist[0])
                    found = True
            if not found:
                print('No package found for {}'.format(sonames[0]))
        except:
            print('No package found for {}'.format(sonames[0]))
print('found {} packages from {} libs'.format(len(pkgset), len(ldd_lines)))
print('-------------------------------')

# for each package, find the version from the output of "dpkg -l"
for pkg in pkgset:
    dpkg_lines = subprocess.check_output(["dpkg", "-l", pkg], text=True).splitlines()
    pkg_fields = dpkg_lines[-1].split()
    print('{}/{}'.format(pkg[:-5], pkg_fields[2]))
