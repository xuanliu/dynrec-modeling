#!/bin/sh -
# =============================================
# This script is to collect results by
# running the cplex
# 
# By Xuan Liu
# April 13, 2014
#
# =============================================


# Treat unset variables as an error
set -o nounset

# argument
snet_type=$1

#
ResultFolder=$snet_type
echo ResultFolder $ResultFolder

cplex_log=cplex.log 
echo "cplex log" $cplex_log

llog=$ResultFolder/run_$$.log

echo llog $llog

collect=$ResultFolder/$snet_type"_out.txt"

rm -f $cplex_log
combine_heuristic_file=$ResultFolder/$snet_type-"heuristic.txt"
for item in $ResultFolder/$snet_type-*.txt
do
    cat $item | grep "$snet_type" >> $combine_heuristic_file
done

while read line
do
    IFS=,
    set $line
    #array+=("$1")

#for ((i=0;i<${#array[*]};i++))
#do 
#    ampl_data="${array[i]}"
    ampl_data="$1"
    filename_base="${ampl_data%.*}"
    #echo $filename_base
    if [[ $filename_base =~ "$snet_type" ]]
        then
        #echo $filename_base
        lp_file=$filename_base".lp"
    
#for lp_file in $ResultFolder/abilene-*.lp
#do
	#echo $lp_file
	( echo "read $lp_file"; echo optimize; echo "dis sol var -") | cplex >> $llog
    grep Problem $llog >> $collect
    #grep Objective $llog >> $collect
    grep "MIP - Integer" $llog >> $collect
    grep "Solution time" $llog >> $collect
    grep "Solution value" $llog >> $collect
    grep RR $llog >> $collect
    grep u_ $llog >> $collect
    grep v_ $llog >> $collect
    grep x_ $llog >> $collect
    
    # create tmp file
    echo $lp_file >> $ResultFolder/xx.$$
    fgrep u_ cplex.log >> $ResultFolder/xx.$$
    fgrep v_ cplex.log >> $ResultFolder/xx.$$
    fgrep x_ cplex.log >> $ResultFolder/xx.$$
    fgrep IsStandby $lp_file | grep "<= 1" >> $ResultFolder/xx.$$
    # combine results
    awk -f combine_result.awk $ResultFolder/xx.$$ >> $collect
    rm -f cplex.log
    rm -f $ResultFolder/xx.$$ $llog
    echo " " >> $collect
    fi
#done
done < $combine_heuristic_file

optimal_result=$ResultFolder/$snet_type"_optimal.txt"
egrep "Problem|MIP|Solution " $collect | awk -f optimal_heuristic_combine.awk >> $optimal_result

final_report=$ResultFolder/$snet_type"_final.csv"
paste $optimal_result $combine_heuristic_file >> $final_report 

#mat_file=$ResultFolder/$network-$vnet"_obj.mat"
#python get_obj_value.py -m $mat_file -f $collect