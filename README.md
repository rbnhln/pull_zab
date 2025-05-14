# pull_zab (zfs-autoback helper script)

This is a wrapper script that simplifies the use of [zfs_autobackup](https://github.com/psy0rz/zfs_autobackup).

To do this, the parameters and variables at the top of the script must be adjusted. 
The script then executes a zfs_autobackup pull. 

- Notification via [healtchecks](https://github.com/healthchecks/healthchecks) possible
- Logfile is written

Example systemd and ssh config files for automation are included,but must be customized.

## Prerequisites

    - zfs_autobackup is installed (I would recommend an installation in a Python-venv)
    - the ZFS datasets on the source system are tagged with the correct ZFS tags 
    - a passwordless login via ssh is possible (example in additional files) 
    - current Python3 version is available 

## Compatible zfs_autobacup versions

    - 3.2
    - 3.3  