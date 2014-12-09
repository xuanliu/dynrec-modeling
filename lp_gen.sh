#!/bin/sh
# ==========================================================
# This script is to generate cplex file from ampl data
#
# By Xuan Liu
# April 13, 2014
# 
# ==========================================================


# treat unset variables as an error
set -o nounset

# arguments
snet_type=$1


ResultFolder=$snet_type
#echo ResultFolder $ResultFolder


# Ampl model file
ampl_model_file=dyn.mod
#echo "AMPL Model File" ampl_model_file

# get home dictionary
HomeD=`pwd`

# set data collecting file
Collect=$HomeD/$ResultFolder/$snet_type"_result.txt"

for ampl_data_file in $ResultFolder/$snet_type-*.dat
do 
	#echo $ampl_data_file
	filename_base="${ampl_data_file%.*}"
	
	if [[ $filename_base =~ "fail" ]]
	then
		#echo $filename_base	
		ampl_expand_file=$filename_base"_expand.txt"
		#echo $ampl_expand_file
		cplex_file=$filename_base".lp"
		#echo $cplex_file
		( echo "model dyn.mod;"; echo "data $ampl_data_file;"; echo "expand;"; echo "quit;") | ampl > $ampl_expand_file
		#( echo "model dyn-old.mod;"; echo "data $ampl_data_file;"; echo "expand;"; echo "quit;") | ampl > $ampl_expand_file
		python convert_ampl.py -r $ampl_expand_file -w $cplex_file  -b "['u','v']"
		rm $ampl_expand_file
	fi 
done



