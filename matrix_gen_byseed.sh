# =====================================
# This script is to run awk script to 
# create matrix for both optimal value 
# and heuristic values
# Three inputs, snet_type, fail_tpye,
# seed
# Called by organize_result.sh
# 
# By Xuan Liu
# April 21, 2014
# =====================================

# Treat unset variables as an error
set -o nounset

snet_type=$1
fail_type=$2
seed=$3

awk_script=form_matrix'_'$snet_type'.awk'
echo $awk_script
for result_dir in $snet_type-$seed-10vn-$fail_type-*
do
	echo $result_dir
	awk -f $awk_script $result_dir/$snet_type'_optimal.txt' > results/$result_dir-'opt.csv'
	awk -f $awk_script $result_dir/$snet_type'-heuristic.txt' > results/$result_dir-'heuristic.csv'
done
