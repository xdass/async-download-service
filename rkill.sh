#!/bin/bash

### Current PID, if this script try to self search, then will loop forever
pid=$$

### Recursive function
search()
{
    if [[ $1 == $pid ]]; then
        break
    fi

    pgrep -P $1 |
    while read process; do
        ### echo $process ### Print PID to stdout for debug, replace by your kill command (kill -9, pkill, etc)
        kill -9 $process
        search $process
    done
}

search $1
exit 1