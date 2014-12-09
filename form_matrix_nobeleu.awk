BEGIN{
    FS=","
    column_counter = 0
    last = 0
} {
  split($1,a,"_")
  #print a[10], a[12],a[2], last, $2
  if ( NR % 5 == 1 ) {
     column_counter++
  }
  if (a[2] != last) {
     column_counter = 1
  }
  #print "index" a[2], a[10],column_counter, $2
  matrix[a[2],a[10],column_counter] = $2
  last = a[2]

} END {
  for (i=8;i<=12;i++) {
     
     #print "i = ", i
     
     for (j=1;j<=5;j++) {
         m = 2*j-1
         #print "m=", m
         for (k=1;k<=10;k++) {
             #print "check: ", i,m,k
             printf("%f,",matrix[i,m,k])
         }
         printf("\n")
     }
     #printf("\n")
     i++
  }
}


