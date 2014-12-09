#!/bin/sh -
# ==========================================
# This script is to automate the runs
# It takes four arguments:
# 	- Substrate network type: 
# 		- abilene
#		- geant
#		- germany
#	- Failure type
#		- virtual failure ('v')
# 		- substrate failure ('s')
# 	- number of virtual networks
# 	- maximum standby vr
#	- standby limit
#
#	By Xuan Liu
#	April 11, 2014
#
# ===========================================

# Treat unset variables as an error
set -o nounset

HomeD=`pwd`


for snet_type in germany #nobeleu #germany #att#
do 
	for seed in 79 #79 101 239 919 191 359 557 881 1021 
	do 
	# create result folder by topology type
	Date=`date +"%m-%d-%y"`
	Time=`date +"%H-%M"`
	run_time=$Date-$Time
	echo "Experiment time: " $run_time
	# declare directory info for results
	result_folder=$snet_type
	echo "Result Folder" $result_folder
	if [ ! -d $result_folder ]
		then 
		echo "create result folder" $result_folder
		mkdir $result_folder
	else
		echo "result folder exists"
	fi 
	
	for fail_type in  s #s 
	do
		
		for num_vn in 30 # 4 5 6 7 8 9
		do
			if [ $snet_type = 'abilene' ] 
				then
				max_svr=6
				min_svr=2
			elif [ $snet_type = 'geant' ]
				then
				max_svr=15
				min_svr=6
			elif [ $snet_type = 'nobeleu' ]
				then
				max_svr=12
				min_svr=8
			elif [ $snet_type = 'germany' ]
				then
				max_svr=25
				min_svr=25
			elif [ $snet_type = 'att' ]
				then
				max_svr=20
				min_svr=18
				
			fi
			#for num_svr in $(seq $min_svr $max_svr)
			#do
				# ampl data file and matlab file
			ampl_datafile=$result_folder/$snet_type-$fail_type-$num_vn-$seed.dat
			mat_file=$result_folder/$snet_type-$fail_type-$num_vn-$seed.mat
			echo "SNET: " $snet_type "VN#: " $num_vn 
			#echo "ampl_datafile: " $ampl_datafile "mat_file: " $mat_file 
			echo `python create_model.py -n $num_vn --bw 0.0005 --maxstandby $max_svr \
					--minstandby $min_svr -f $ampl_datafile \
					-m $mat_file --type $snet_type --ftype $fail_type --limit $num_vn --seed $seed`
			mv $snet_type-$fail_type-$num_vn.txt $result_folder/.
			#done
		done
	done
	/bin/bash lp_gen.sh $snet_type
	/bin/bash cplex_run.sh $snet_type
	mv $snet_type $snet_type-$seed
	done
done



