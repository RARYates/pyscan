# /usr/bin/env Python3

# Simple comment for show

## Imports
import psutil
import time
import json
import datetime
from pathlib import Path
import csv
import argparse

## Argument Parser - Grab flags from Command Line
parser = argparse.ArgumentParser(description='Scans the System and Logs Metrics to a CSV File')
parser.add_argument('-l', '--logdir', help='Log Directory', default='./log.csv')
parser.add_argument('-i', '--interval', type=int, help='Interval in Seconds', default=5)
parser.add_argument('-v', '--verbose', help='Verbose Output', action="store_true", default=False)
parser.add_argument('-b', '--bandwidth', type=float, help='Total Network Bandwidth in GB',required=True)

args = parser.parse_args()
bandwidth_bytes = args.bandwidth * 1000000000
logdir = args.logdir
interval = args.interval
verbose = args.verbose

## Pre-Step - Generate Log File if it does not exist
logfile = Path(logdir)
if not logfile.is_file():
    log = open(logdir, 'w')
    log.write('Time, CPU Utilization, Memory (Used), Memory (Available), Network Utilization, Disk Utilization')
    log.write("\n")
    log.close()

## Function - Convert Bytes to Human Readable Format
def get_size(bytes):
    """
    Returns size of bytes in a nice format
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

## Continually Run on the Interval - while true loops, time.sleep pauses the loop for the interval
while True:
    time.sleep(interval)

    ## Produce Simple Metrics - Time, CPU and Memory Information
    now = datetime.datetime.now()
    cpu_utilization = psutil.cpu_percent(interval=1)
    cpu_formatted = f"{cpu_utilization}%"
    memory = psutil.virtual_memory()
    mem_available = memory.available
    mem_available_formatted = get_size(mem_available)
    mem_used = memory.used
    mem_used_formatted = get_size(mem_used)
    
    ## Network Utilization
    
    ### MEASURE: get the network I/O stats from psutil on each network interface by setting `pernic` to `True`, sleeping and regathering the next second to measure 1 second difference
    io = psutil.net_io_counters(pernic=True)
    time.sleep(1)
    io_2 = psutil.net_io_counters(pernic=True)
    
    ### FORMAT: Compare and Contrast our two dictionaries to make a 1 second Download/Upload Speed
    data = []
    for iface, iface_io in io.items():
        upload_speed, download_speed = io_2[iface].bytes_sent - iface_io.bytes_sent, io_2[iface].bytes_recv - iface_io.bytes_recv
        data.append({
            "iface": f"{iface} -",
            "Utilization": f"{(upload_speed + download_speed * 8) / (bandwidth_bytes) * 100}%",
            "Download Speed": f"{get_size(download_speed / 1)}/s",
            "Upload Speed": f"{get_size(upload_speed / 1)}/s",
            "Upload": get_size(io_2[iface].bytes_sent),
            "Download": get_size(io_2[iface].bytes_recv),
        })
    
    ### FORMAT: Show Data and remove JSON Formatting - \r\n is required for CSVs to allow multiline cells
    net_formatted = json.dumps(data).replace('"','').replace("}", "\r\n").replace("[", "").replace("]", "").replace("{", "").replace(",","")
    
    ### MEASURE: get the disk I/O stats from psutil on each disk by setting `perdisk` to `True`, sleeping and regathering the next second to measure 1 second difference
    disk_info = psutil.disk_io_counters(perdisk=True)
    time.sleep(1)
    disk_info2 = psutil.disk_io_counters(perdisk=True)
    
    ### FORMAT: Compare and Contrast our two dictionaries to make a 1 second Download/Upload Speed
    diskdata = []
    for disk, disk_io in disk_info.items():
        read_speed, write_speed = disk_info2[disk].read_bytes - disk_io.read_bytes, disk_info2[disk].write_bytes - disk_io.write_bytes
        diskdata.append({
            "disk": f"{disk} -",
            "IOPS": (read_speed + write_speed),
            "Read Speed": f"{get_size(read_speed / 1)}/s",
            "Write Speed": f"{get_size(write_speed / 1)}/s",
            "Reads": disk_info2[disk].read_count,
            "Writes": disk_info2[disk].write_count,
        })
    
    ### FORMAT: Show Data and remove JSON Formatting - \r\n is required for CSVs to allow multiline cells
    diskdata_formatted = json.dumps(diskdata).replace('"','').replace("}", "\r\n").replace("[", "").replace("]", "").replace("{", "").replace(",","")
    
    ## PRESENT: Write to CSV and print to stdout if '-v' flag is used
    with open(logdir, 'a', newline='') as outfile:
        log = csv.writer(outfile, dialect='excel')
        log.writerow([now,cpu_formatted,mem_available_formatted,mem_used_formatted,net_formatted,diskdata_formatted])
        if verbose == True:
            print(now,"\n",cpu_formatted,"CPU Utilization\n",mem_available_formatted,"Mem Avail ",mem_used_formatted, "In Use\n", net_formatted,"\n",diskdata_formatted)