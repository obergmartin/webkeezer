#!/bin/ash
#echo $1
sed -i "1 s/^.*$/$1/" /root/keezerparams.txt
