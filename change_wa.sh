#!/bin/sh -
# =============================================
# This script is to change weight w_a
# 
# By Xuan Liu
# April 13, 2014
#
# =============================================

snet_type=$1

origin_weight='0.2_0.8_1_0_0_1_0'

src_folder=$snet_type-10vn-v-$origin_weight
prefix="param"

echo $src_folder

# make a copy
#cp -r $src_folder $snet_type
mkdir $snet_type
cp $src_folder/*.dat $snet_type/.
cp $src_folder/$snet_type-v-10.txt $snet_type/.
cp $src_folder/$snet_type-v-10.mat $snet_type/.


a1=1.0
a2=0.0
new_weight=$a1'_'$a2'_1_0_0_1_0'
for ampl_datafile in $snet_type/$snet_type-v-10_*.dat
do	
	
	OIFS=$IFS
	IFS='_'
	spo_array=($ampl_datafile)
	IFS=$OIFS
	#echo ${spo_array[*]}
	new_data=${spo_array[0]}'_'${spo_array[1]}'_'$a1'_'$a2'_1_0_0_1_0_'${spo_array[9]}'_'${spo_array[10]}'_'${spo_array[11]}
	echo "new: " $new_data
	echo "old: " $ampl_datafile

	orig_a1=`grep "$prefix a1" $ampl_datafile | awk {'print $4'}`
	orig_a2=`grep "$prefix a2" $ampl_datafile | awk {'print $4'}`
	echo "original weight: " $orig_a1 $orig_a2 
	tmp_file=$snet_type/tmp.dat
	awk '/param a1/{gsub(/'$orig_a1'/, '$a1')};{print}' $ampl_datafile > $new_data
    awk '/param a2/{gsub(/'$orig_a2'/, '$a2')};{print}' $new_data > $tmp_file
    cp $tmp_file $new_data
    rm $ampl_datafile
    rm $tmp_file


done

/bin/bash lp_gen.sh $snet_type
/bin/bash cplex_run.sh $snet_type

mv $snet_type $snet_type-10vn-v-$new_weight
