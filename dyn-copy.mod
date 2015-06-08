# 
# ampl mod file
#
# This is the ampl model file for dynamic  
# networking reconfiguration mathematical model 
# 
# The objective function is modified to be composited objective equation
# The first two components are the cost functions, the second part is to minimize the
# resource utilizatin on each substrate node
# 
# By Xuan Liu <xuan.liu@mail.umkc.edu>
# Created on Mar. 6, 2014
# Modified on May 11, 2014
# Adding link-path constraints on Sep. 24, 2014


##### Index bound Declaration ####
param num_pr > 0 integer;       # the number of physical routers on the substrate
param num_vn > 0 integer;       # the number of virtual networks




# ========== Set declaration ============= #


# the set of phyiscal resources (CPU & RAM)
set RES;

# the set of physical routers --------- (R)
set PRouter = 1 .. num_pr by 1;                

# the set of virtual networks overlay over the substrate ------- (G)
set VNet = 1 .. num_vn by 1;

# the number of ports on a physical router  
param num_p {i in PRouter} > 0 integer;       

# the set of physical ports on the physical rouer i ------- (P_{i})
set Port{i in PRouter} = 1 .. num_p[i] by 1;    

# the number of virtual interfaces on a virtual router r_{i,j} 
param num_viface {i in PRouter, j in VNet} > 0 integer;  

# the set of virtual interfaces on a virtual router r_{i,j}  -------- (M^j_i)
set VIface {i in PRouter, j in VNet} = 1 .. num_viface[i,j] by 1; 

# the set of failed virtual router r_{i,j} ----- (F^j)
set Fail {VNet};    

# the set of virtual links in virtual network j  
#set VLink {j in VNet, i in PRouter, k in PRouter: i <> k};

# the set of physical links on the substrate
#set PLink { i in PRouter, k in PRouter: i <> k};   

#### Parameter Declaration ####
# The available bw of port p on physical router i ---- (b_{i,p})
param b {i in PRouter, p in Port[i]} >= 0;

# Indecates whether a virtual router r_{i,j} is connected ------- (alpha^j_i)
param alpha {i in PRouter, j in VNet} binary;

# Indicating whether a virtual router r_{i,j} is failed ------- (beta^j_i)
param beta {i in PRouter, j in VNet} binary;

# Indicating mapping relation between virtual interface m and potential connected remote virtual router r_{j,k}  ------- (gamma^{j,f}_{i,m,k})
param gamma { j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter} = if m = k then 1 else 0;


# the upper limit on how many S-VRs can be created on a substrate node ---------- (h_i)
param limit {i in PRouter} >=0 integer;


# Indicating whether a virtual router r_{i,j} is a standby ------- (delta^j_i)
param delta {i in PRouter, j in VNet} binary;

# number of failed router in virtual network j ------ (n^j)
param num_fail {j in VNet} = card {Fail[j]} >= 0;

# indicating whether r_{i,j} and r_{k,j} is connected (equals to 1) ------- (e^j_{i,k})
param e { j in VNet, i in PRouter, k in PRouter: i <> k} binary;

# requested bw on the virtual interface m of standby virtual router r_{i,j} ------- (c^{j,f}_{i,m,k}) 
param c { j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k} >= 0;


##  Start Link-Path Formulation ----------

# number of substrate links
param L > 0 integer;

# the set of substrate links
set slink := 1 .. L by 1;

# number of demands
param D > 0 integer;

# the demand set in terms of index
set demand := 1 .. D by 1;

# number of paths by demand d
param Pd{d in demand} > 0 integer;

# Paths sets per demand tuple
set Q{d in demand} := 1 .. Pd[d] by 1;

# slink parameters
param slink_src{l in slink} within PRouter;
param slink_dst{l in slink} within PRouter;
param slink_capacity{l in slink} >= 0;

# demand parameters
param demand_src{d in demand} within PRouter;
param demand_dst{d in demand} within PRouter;
param demand_vn{d in demand} within VNet; 
param demand_fnode{f in demand} within PRouter;

# demand volumn: c[j,f,i,m,k]
param demand_c{d in demand} > 0;

# Paths set
set paths{d in demand, q in Q[d]} within slink;

# link-path indicator, set to 1 if path q for demand tuple d uses link l, otherwise is 0;

param Delta{d in demand, q in Q[d], l in slink} = if l in paths[d,q] then 1 else 0;

# Flow amount on path q for demand d 
var x{d in demand, q in Q[d]} >= 0; 


## END Link-Path formulation ----------


#### Cost Function Parameters ####

### virtual interface operation cost ###
# the cost of enabling an interface   ----- (s^-)
param enable >= 0;

# the cost of disabling an interface  ----- (s^+)
param disable >= 0;

# the cost of configure IP addresses  ----- (l)
param ipConfig >= 0;

# the bool value that indicates whether IP configure is needed on a remote virtual router r^j_k (failed VR's neighbor)----- (tao_{j,k})
param tau{k in PRouter, j in VNet} binary;


### Virtual router connection cost ###
# distance between two routers    ------ (d_{i,k})
param dist{i in PRouter, k in PRouter: i <> k} >= 0;

# round trip time between two routers  ------ (rtt_{i,k})
param rtt {i in PRouter, k in PRouter: i <> k} >= 0;

# loss rate between two routers 
param pktloss {i in PRouter, k in PRouter: i <> k} := 0;

# weight parameters for type-II cost function
param a1 >= 0;
param a2 >= 0;
param b1 >= 0;
param b2 >= 0;
param b3 >= 0;

### residual physical resource
# residual hardware resources (i.e. CPU, Memory) ------ res_{i,r}
param res {i in PRouter, r in RES} >=0;

# weight parameters for hardware -- Type-III cost function
param h {r in RES} >= 0;


# the available resources on physical router i
# param xi {i in PRouter} = (sum{r in RES} h[r] * res[i,r]) * sum {p in Port[i]} b[i,p];
param xi {i in PRouter} = sum {p in Port[i]} b[i,p];


# the cost of connecting a virtual router r_{k,j} to standby r_{i,j}   ---- (sigma^{j,f}_{i,m,k})
param sigma {j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f && k <> f} 
   =  b1 * (a1 * dist[i,f] + a2 * dist[i,k]) + b2 * rtt[i,k] + b3 * pktloss[i,k];

# the cost of enable virtual interface m  ------ (eta^{j,f}_{i,m,f})
param eta {j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f}
   = 2 * (disable + enable) + tau[k,j] * ipConfig;

# check how many s-vr created on a substrate router
param sum_delta{i in PRouter} := sum{j in VNet, f in Fail[j]} delta[i,j];

#### objective function weight parameter ####
param m1 >= 0;
param m2 >= 0;
param m3 >= 0;

#### Varaibles Declaration ####

# Indicate whether a virtual router r_{i,j} is selected to replace failed router r_{f,j}  ------ u^{j,f}_{i}
var u {j in VNet, f in Fail[j], i in PRouter} binary;

# indicate whether connected virtual router r_{k,j} is connected to standby router r_{i,j}  -------- v^{j,f}_{i,m,k}
var v {j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f} binary;

# indicate resource utilization  ------- r
var RR >= 0;
# Indicate whether a virtual interface m on standby router r_{i,j}, is connected to r_{k,j}  ------ NOT USED
# var w {j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f} binary;

#### objective function #####

minimize Total_Cost:
#    sum { j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f && k <> f} 
#        (m1 * eta[j,f,i,m,k] + m2 * sigma[j,f,i,m,k]) * delta[i,j] * gamma[j,f,i,m,k] * v[j,f,i,m,k]
#    - m3 * sum {i in PRouter} xi[i] * (sum {j in VNet, f in Fail[j]: i <> f} delta[i,j] * u[j,f,i]);

   sum { j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f && k <> f} 
        (m1 * eta[j,f,i,m,k] + m2 * sigma[j,f,i,m,k]) * delta[i,j] * gamma[j,f,i,m,k] * v[j,f,i,m,k]
    + m3 * RR;

# Constraint (1)
subject to IsStandby {j in VNet, f in Fail[j], i in PRouter: delta[i,j] == 1}:
    u[j,f,i] <= delta[i,j]*(1 - beta[i,j]);

# Constraint (2)
subject to IsSelect {j in VNet, f in Fail[j], i in PRouter, m in VIface[i,j], k in PRouter: i <> k && i <> f && f <> k && delta[i,j] == 1 && e[j,f,k] == 1 && gamma[j,f,i,m,k] == 1}:
    v[j,f,i,m,k] <= u[j,f,i];

# Constraint (3)
subject to OneSPerF {j in VNet, f in Fail[j]}:
sum{i in PRouter} delta[i,j] * u[j,f,i] = 1;

# Constraint (4)
subject to OneFPerS {i in PRouter, j in VNet: delta[i,j]==1}:
sum{f in Fail[j]} delta[i,j] * u[j,f,i] <= 1;

# Constraint (5)
subject to max_select {i in PRouter}:
    sum{j in VNet, f in Fail[j]} delta[i,j] * u[j,f,i] <= limit[i];

# Constraint (6)
subject to IsConnect {j in VNet, f in Fail[j], i in PRouter: delta[i,j] == 1 && i <> f}:
    sum{m in VIface[i,j], k in PRouter: k <> f && k <> i} e[j,f,k] * gamma[j,f,i,m,k] * v[j,f,i,m,k] - sum{k in PRouter: k <> i && k <> f} e[j,f,k] * beta[f,j] * u[j,f,i]= 0;

# Constraint (7)
subject to bw {i in PRouter, j in VNet, f in Fail[j]: delta[i,j] == 1 && i <> f}:
    sum {m in VIface[i,j], k in PRouter: i <> k && k <> f}
        delta[i,j] * c[j,f,i,m,k] * gamma[j,f,i,m,k] * v[j,f,i,m,k] <= sum {p in Port[i]} delta[i,j] * b[i,p] * u[j,f,i];

# Constraint (8)
subject to res_util {i in PRouter: sum_delta[i] > 0}:
    sum {j in VNet, f in Fail[j]: i <> f} delta[i,j] * u[j,f,i] * sum {k in PRouter, m in VIface[i,j]: k <> i && k <> f} gamma[j,f,i,m,k] * c[j,f,i,m,k] <= sum {p in Port[i]} b[i,p] * RR;

# Constraint (9)
subject to d_pair{d in demand, j in VNet, f in Fail[j], i in PRouter: i<>f && delta[i,j] == 1 && demand_fnode[d] == f && demand_vn[d] == j && demand_src[d] == i}: sum{q in Q[d]} x[d,q] = demand_c[d] * u[j,f,i];

# Constraint (10)
subject to cl{l in slink}: sum{d in demand, q in Q[d]} Delta[d,q,l] * x[d,q] <= slink_capacity[l];

subject to upRRbd:
    RR <= 0.8;









