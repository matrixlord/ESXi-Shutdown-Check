#! /usr/bin/python
import subprocess, os, sys, re, time

# This script checks if an IP can be reached, if not it shuts down all the VMs
# and the host machine gracefully. It works on ESXi 6.5.

# Set the IP to check.
ipToCheck = "192.168.1.1"
############################################

# Helper variables to check script is not already running.
pid = str(os.getpid())
pidfile = "/tmp/mydaemon.pid"

# Check script is not running.
def checkIsNotRunning():
    if os.path.isfile(pidfile):
        sys.exit()
    return;

# Get VMs.
def getVms():
    vms = []
    # Get vms.
    cmd = "vim-cmd vmsvc/getallvms | grep -Eo '^[0-9].'"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    for vm in proc.stdout.readlines():
        vms.append(int(re.search(r'\d+', str(vm)).group()))

    return vms;

# Get VM state.
def getVmState(vm):
    cmd = "vim-cmd vmsvc/power.getstate " + str(vm)
    response = subprocess.check_output(cmd, shell=True)
    if "Powered on" in str(response):
        return 1;
    else:
        return 0;

# Get all VMs are off.
def getAllVmsAreOff():
    vms = getVms()
    # VMs that are stil on.
    onVms = []
    for vm in vms:
        if getVmState(vm) == 1:
            onVms.append(1)

    if len(onVms) > 0:
        return 0;
    else:
        return 1;

# Shutdown VMs.
def shutdownVms():
    vms = getVms()
    for vm in vms:
        if getVmState(vm) == 1:
            cmd = "vim-cmd vmsvc/power.shutdown " + str(vm)
            subprocess.check_output(cmd, shell=True)
            time.sleep(30)

# Create empty list of failures.
failures = []

# Try to ping.
checkIsNotRunning()
# Create file on start up.
open(pidfile, 'w').write(pid)
for x in range(0, 5):
    try:
        subprocess.check_output("ping -c 1 " + ipToCheck, shell=True)
    except subprocess.CalledProcessError as e:
        failures.append('failed')

try:
    # Count failures and shutdown VMs.
    if len(failures) > 4:
        shutdownVms()

        # Check VMs have shut down.
        # Helper function to get if VMs are on or off.
        vmsOn = 1
        # Time out counter.
        timeout = 600
        # Current wait time
        currentWait = 0
        while vmsOn == 1 and currentWait < timeout:
            if getAllVmsAreOff() == 0:
                currentWait = currentWait + 20
                time.sleep(20)
            else:
                vmsOn = 0
                currentWait = timeout

        os.unlink(pidfile)
        cmd = "poweroff"
        subprocess.check_output(cmd, shell=True)
finally:
    if os.path.isfile(pidfile):
        os.unlink(pidfile)
