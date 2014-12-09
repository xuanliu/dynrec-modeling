# Sample input file"
# I2 2
# source LP filename
# IsStandby: u_1_4_2 <= 1
# u_1_4_2       1
#
BEGIN{
	print "Combine Results"
}
{
	# first line in the file
	if (NR == 1) {
		filename = $1
		#print filename
		split($1, res_dir, "/")
		#print res_dir[2]
		split(res_dir[2], info, "-")
		if (info[1] == "abilene")
			num_nodes = 12
		if (info[1] == "geant")
			num_nodes = 22
		if (info[1] == "germany")
			num_nodes = 50
		vnet = 10
		
		print num_nodes " " vnet
	}
	
	if (NR > 1){
	split($1,a,":")
	split(a[1], b, "_")
	#print "Check " $1 " " a[1] " " b[4]
	fail[b[2], b[3]] = 1
	standby[b[2], b[3], b[4]] = 1
	neighbor[b[2], b[3], b[6]] = 1
	}
	
	if (substr($1,1,9) == "IsStandby") {
		candidate[b[2], b[3], b[4]] = 0
		#print b[1] " " b[2] " " b[3] " " b[4]
	}
	if (substr($1,1,2) == "u_") {
		selected[b[2], b[3], b[4]] = $2
		#print $1 " " $2
	}
	if (substr($1,1,2) == "v_") {
		connect[b[2],b[3],b[6]] = $2
		#print "check " $1 " " b[1] " " b[2] " " b[3] " " b[4] " " b[5] " " b[6]
		#print $1 " " $2
	}
	if (substr($1,1,2) == "x_") {
		link_path[c[2],c[3]] = $2
		print $1 " " $2
	}
}

END{
	for (i=1;i<=vnet;i++) {
		for (j=1;j<=num_nodes;j++) {
			#print i"_"j
			if (fail[i,j] == 1) {
				for (k=1;k<=num_nodes;k++) {
					if (standby[i,j,k] == 1) {
						#print i " " j " " k " " standby[i,j,k]
						Option = i"_"j"_"k
						printf("Standby %8s %6d %6d %20s\n",  Option,  \
						candidate[i,j,k], selected[i,j,k], filename)
					}
				}
			}
		}
	}
	for (i=1;i<=vnet;i++) {
		for (j=1;j<=num_nodes;j++) {
			#print i"_"j
			if (fail[i,j] == 1) {
				for (k=1;k<=num_nodes;k++) {
					if (neighbor[i,j,k] == 1){
						#print i " " j " " k " " neighbor[i,j,k]
						Connect = i"_"j"_"k
						printf("Neighbor %8s %6d %20s\n",  Connect,  \
						connect[i,j,k], filename)
					}
				}
			}
		}
	}
}
