#! /usr/bin/python3
import shlex
import subprocess
import argparse
import logging
from logging.handlers import RotatingFileHandler
import requests
import sys

##
# Runs pull cmd for zfs_autobackup

############ Links
# https://realpython.com/python-logging/
# https://realpython.com/python-subprocess/#communication-with-processes
# https://realpython.com/command-line-interfaces-python-argparse/

############ Variables
# add remote server name, see ssh config
remote_server = "REMOTE_SERVER"
# flag for healthcheck, default: True
hc = True
# add healthcheck url, see healthchecks.io
hc_url = "https://HC_URL/ping/ID/" # with /
# path of zfs-autobackup
zab_path = "/PATH/pyvenvs/zab/bin/zfs-autobackup"
zab_default_flags = "--clear-mountpoint --compress --keep-source=3 --keep-target=10,1d1w,1w1m,1m1y"
# list of datasets to backup, see zfs-autobackup for more informations
source_list =["offsite1", "offsite2"]
# destination ZFS pool
dest_pool = "POOL/backup"
log_path = "/PATH/logs"
log_name = "zab_" + remote_server

############ Args
parser = argparse.ArgumentParser(
    prog="zab-pull",
    description="Wrapper for zfs-autobackup with error handling and healtcheck notification.",
    )
additional = parser.add_argument_group("additional zfs-autobackup flags")
additional.add_argument("-a", "--additional-zab-flags", action="append")
args = parser.parse_args()
 
########### Logs
# Creates custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handerls
#pwd = str(getenv("PWD"))
logFile = log_path + "/" + log_name + ".log"

c_handler = logging.StreamHandler()
f_handler = RotatingFileHandler(logFile, mode="a", maxBytes=5*1024*1024, backupCount=2, encoding="utf-8")

c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handerls
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

########### Process
def perform_zab(cmd : str) -> subprocess.CompletedProcess | None:
    try:    
        proc = subprocess.run(shlex.split(cmd), check=True, capture_output=True, encoding="utf-8")
        return proc
    except FileNotFoundError as exc:
        logger.exception("Exception occurred")
    except subprocess.CalledProcessError as exc:
        logger.exception("Exception occurred")
    except subprocess.TimeoutExpired as exc:
        logger.exception("Exception occurred")
    return None
    

def notify_hc(code : str) -> None:
    if hc:
        url = hc_url + code
        try:
            requests.get(url, timeout=10)
        except requests.RequestException as exp:
            logger.exception("Healthcheck exception occurred.")


# add additional flags to cmd
flags = ""
if args.additional_zab_flags:
    for item in args.additional_zab_flags:
        if len(item) < 2:
            flags += "-" + item + " "
        else:
            flags += "--" + item + " "

############ run zab
logger.debug("===Starting zab pull===")
# Notfiy healthchecks
notify_hc("start")

list_of_rcs = []
for item in source_list:
    # run zab and log errors
    logger.debug(f"Starting process for %s", item)
    cmd = zab_path + " " + zab_default_flags + " " + flags +  " " + "--ssh-source " + remote_server + " " + item + " " +  dest_pool
    logger.debug(f"With cmd: %s", cmd)
    zab_p = perform_zab(cmd)    
    if zab_p is None: 
        rc = 1 # Assign a non-zero return code for errors
        logger.error(f"Process for %s failed to execute or timed out.", item)
    else:
        rc = zab_p.returncode
        logger.debug(f"First run closed with return code %s", str(rc))
        if len(zab_p.stdout) > 0:
            logger.debug(zab_p.stdout)
        if len(zab_p.stderr) > 0:
            logger.error(zab_p.stderr)
    
    if rc == 0:
        logger.debug("ZAB finished normally.")
    list_of_rcs.append(rc)


all_zeros = True
for rc in list_of_rcs:
    if rc != 0:
        all_zeros = False
    
if all_zeros == True:
    notify_hc("0")
else:
    notify_hc("1")

