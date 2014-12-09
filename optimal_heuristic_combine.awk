# ===================================
# This awk script is to combine 
# optimimal result with the heuristic 
# results. 
# 
# 
# By Xuan Liu
# April 14, 2014
# ===================================

BEGIN{
	#print "Optimal v.s. Heuristic"
	x=1
	f = ""
	f2 = ""
	obj_line = 1
}
{
	if ( f != FILENAME ){
		#print "reading", FILENAME;
		f=FILENAME;
	} 
	if (f == FILENAME) {
		if ($2 == "Problem") {
			filename = $3;
			line_num = x;
			#print line_num, " ", filename;
		}
		x++
		if (NR == line_num + 1) {
			#print $4
			if ($4 == "infeasible.") {
				obj_list[obj_line, 1] = filename;
				obj_list[obj_line, 2] = "infeasible";
				#obj_line ++;
			}
			else {
				if ($5 == "tolerance"){
					optimal_obj = $9;
				}
				else{
					optimal_obj = $8;
				}
				#print NR, " ", filename, " ", optimal_obj, obj_line;
				obj_list[obj_line, 1] = filename;
				obj_list[obj_line, 2] = optimal_obj;
				#obj_line ++;
			}
		}
		if (NR == line_num + 2){
			#print NR, filename, obj_line, $4;
			obj_list[obj_line, 3] = $4;
			obj_line ++ ;
		}
	}

}

END{
	for (i = 1; i <= obj_line; i++) {
		printf("%25s, %10s, %10s\n", obj_list[i, 1], obj_list[i, 2], obj_list[i,3])
	}
}


