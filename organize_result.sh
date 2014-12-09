#!/bin/sh -
# =====================================
# This script is to create sepearte 
# sub-folders 
# 
# By Xuan Liu
# April 21, 2014
# =====================================

# Treat unset variables as an error
set -o nounset

fail_type=v 

for snet_type in germany
do
	for seed in 37 79 101 239 919 191 359 557 881 1021 
	do
		main_dir=$snet_type-$seed
		for w_m in '0_0_1' '0_0.02_0.98' '0_1_0'
		do
			for w_a in '0.2_0.8' #'1_0' '0.2_0.8' '0.5_0.5' '0.8_0.2' '0_1'
			do
				new_dir=$main_dir-10vn-$fail_type-$w_a'_1_0_'$w_m
				#echo $new_dir
				mkdir $new_dir
				cp $main_dir/*'_'$w_a'_1_0_'$w_m'_'* $new_dir/.
				grep $w_a'_1_0_'$w_m $main_dir/$snet_type'_'optimal.txt > $new_dir/$snet_type'_'optimal.txt
				grep $w_a'_1_0_'$w_m $main_dir/$snet_type-heuristic.txt > $new_dir/$snet_type-heuristic.txt
			done
		done
	/bin/bash matrix_gen_byseed.sh $snet_type $fail_type $seed
	done
done


