# ESXi-Shutdown-Check
This script monitors if an IP can be reached, through ping. If not, it shuts down all the VMs and the host machine gracefully. It works on ESXi 6.5.

Don't forget to set the ipToCheck variable inside the script to the IP you want to monitor.
