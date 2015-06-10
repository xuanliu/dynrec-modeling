# -*- coding: utf-8 -*-
"""
Find the objective cost using a heuristic method
1. Pick the node based on the distance only
2. Pick the node based on the physical resource only

Created on Wed Apr  9 14:19:34 2014

@author: xuanliu
"""
import operator
import copy
import networkx as nx
import time
import random

def operation_cost(tau=0):
    """
    Calculate the operation cost
    By default, we assume each virtual router has enough virtual interfaces,
    and there is no need to 
    """
    iface_on = 0.2
    iface_off = 0.2   
    ipconfig = 2
    reconf_ip_bin = tau
    op_cost = 2 * (iface_on + iface_off) + reconf_ip_bin * ipconfig
    return op_cost
    
def dist_cost(s_vr, failed_vr, neighbor_vr, dist_matrix, w_a1, w_a2):
    """
    Calculate the distance portion in the connectivity cost function
    Inputs are:
    s_vr: the candidate standby virtual router id
    failed_vr: the failed virtual router id
    neighbor_vr: the failed virtual router's neighbor id
    w_a1: the weight parameter for the distance between s_vr and failed_vr
    w_a2: the weight parameter for the distance between s_vr and neighbor_vr
    dist_matrix: the distance matrix for all substrate nodes
    (Note: the first column in the dist_matrix is index)
    """
    #print s_vr, failed_vr, neighbor_vr
    dist_i_f = dist_matrix[s_vr][failed_vr + 1]
    dist_i_k = dist_matrix[s_vr][neighbor_vr + 1]
    dist = w_a1 * float(dist_i_f) + w_a2 * float(dist_i_k)
    #print "d_i_f: ", dist_i_f, ", dist_i_k: ", dist_i_k
    return dist
    
    


    
def rtt_cost(s_vr, neighbor_vr, rtt_matrix):
    """
    Calculate the RTT portion in the connectivity cost function
    Inputs are:
    s_vr: the candidate standby virtual router id
    neighbor_vr: the failed irtual router id
    rtt_matrix: the RTT matrix for all virtual nodes (full mesh)
    (Note: the first column in the RTT_matrix is index)
    """
    rtt = rtt_matrix[s_vr][neighbor_vr + 1]
    #print "rtt_i_k", rtt
    return float(rtt)
    
def connect_cost(dist_cost, rtt_cost, w_b1, w_b2):
    """
    Return the connectivity cost, which includes two parts:
    distance and RTT
    """
    return w_b1 * dist_cost + w_b2 * rtt_cost
    
#def resource_cost(cpu_info, bw_matrix, standby_vr):
def resource_cost(bw_matrix, standby_vr):
    """
    Get the residul capacity on the substrate nodes
    """
    #host_cpu = float(cpu_info[0][standby_vr])
    host_bw = 0
    num_rows = len(bw_matrix)
    #num_cols = len(bw_matrix[1,:])
    for port in range(num_rows):
        if bw_matrix[port][standby_vr] != '.':
            host_bw += float(bw_matrix[port][standby_vr])
        else:
            pass
    #return host_cpu * host_bw
    return host_bw
    
def total_bw(bw_matrix):
    """
    return the total residual bw for each snet node, in the form of list,
    where the index is the node id
    """
    node_bw_list = []
    num_col = len(bw_matrix[0])
    num_row = len(bw_matrix)
    for node_id in range(num_col):
        temp_bw = 0
        for port in range(num_row):
            if bw_matrix[port][node_id] != '.':
                temp_bw += float(bw_matrix[port][node_id])
            else:
                pass
        node_bw_list.append(round(temp_bw, 5))
    return node_bw_list
     
def total_port(model):
    """
    get total number of ports for each node
    """
    snet_info = model.get_snet_info()
    used_bw_list = []
    node_port_list = []
    for node_id in snet_info:
        number_port = snet_info[node_id]['num_iface']
        node_port_list.append(number_port)
        used_bw = number_port - snet_info[node_id]['sum_avail_bw']
        used_bw_list.append(round(used_bw, 5))
    return node_port_list, used_bw_list
        
    
    
#def find_standby(model, limit, w_a, w_b, w_m):
#    """
#    Heuristic algorithm to find the standby virtual routr 
#    for each virtual network
#    """
#    #print "FIND"
#    failed_dict = model.failed_dict
#    #print failed_dict, limit
#    dist_matrix = model.cost_dict['dist']
#    rtt_matrix = model.cost_dict['rtt']
#    bw_matrix = model.cost_dict['bw']
#    #cpu_vector = model.cost_dict['cpu']
#    selected_dict = {}
#    
#    snode_bw_list = total_bw(bw_matrix)
#    #vnet_set = model.vnets
#    sorted_vn = sort_vnet(model)
#    
#    #for vnet in vnet_set:
#    if w_m[2] >= 10*w_m[1]:
#        threshold = 0.3
#    else:
#        threshold = 0.8
#    snode_traffic = {}
#    for vn_traffic in sorted_vn:
#        vnet = vn_traffic[0]
#        failed_vr = failed_dict[vnet.vnet_id]
#        if failed_vr != -1: 
#            # this node is failed
#            standby_list = vnet.get_standby_ids()
#            standby_cost = {}
#            for s_vr in standby_list:
#                dist_f = float(dist_matrix[s_vr][failed_vr + 1])
#                failed_node = vnet.vnodes[failed_vr]
#                vneighbors = failed_node.vneighbors
#                dist_k = 0
#                rtt_k = 0
#                for k in vneighbors:
#                    dist_k += float(dist_matrix[s_vr][k + 1])
#                    rtt_k += float(rtt_matrix[s_vr][k + 1]) 
#                connect_cost = w_b[0] * (w_a[0] * dist_f + w_a[1] * dist_k) +\
#                                w_b[1] * rtt_k
#                res_cost = snode_bw_list[s_vr]
#                req_bw = sum(failed_node.neighbor_traffic.values())
#                total = w_m[1] * connect_cost + w_m[2] * req_bw / res_cost
#                standby_cost[s_vr] = total
#            sorted_x = sorted(standby_cost.iteritems(), key=operator.itemgetter(1))
#            
#            for item in sorted_x:
#                if item[0] not in snode_traffic:
#                    utilization = vn_traffic[1] / total_bw(bw_matrix)[item[0]]
#                else:
#                    utilization = (snode_traffic[item[0]] + vn_traffic[1]) / total_bw(bw_matrix)[item[0]]
#                    
#                # Link-Path selsection add-on
#                    
#                # End link-path block    
#                if selected_dict.values().count(item[0]) < limit:
#                    if utilization < threshold and w_m[2] >= 10*w_m[1]:
#                        if item[0] not in snode_traffic: 
#                            selected_dict[vnet.vnet_id] = item[0]
#                            snode_bw_list[item[0]] -= vn_traffic[1]
#                            snode_traffic[item[0]] = vn_traffic[1]
#                            break;
#                        else:
#                            min_id = find_min(sorted_x, bw_matrix, snode_traffic, vn_traffic[1]) 
#                            if min_id == item[0]:
#                                selected_dict[vnet.vnet_id] = item[0]
#                                snode_bw_list[item[0]] -= vn_traffic[1]
#                                snode_traffic[item[0]] = vn_traffic[1]
#                            #threshold = (threshold + 0.01)/2
#                                break
#                    elif utilization < threshold:
#                        selected_dict[vnet.vnet_id] = item[0]
#                        snode_bw_list[item[0]] -= vn_traffic[1]
#                        snode_traffic[item[0]] = vn_traffic[1]
#                        break
#                    else:
#                        print "does not satisfy the threshold"     
#                else:
#                    pass
#                           
#    return selected_dict   
 
 
def find_random(model,limit, w_a, w_b, w_m, demand_path, demand_dict, slink_dict):
    """
    find random standby
    """
    failed_dict = model.failed_dict
    #print failed_dict, limit
    dist_matrix = model.cost_dict['dist']
    rtt_matrix = model.cost_dict['rtt']
    bw_matrix = model.cost_dict['bw']
    #cpu_vector = model.cost_dict['cpu']
    selected_dict = {}
    
    snode_bw_list = total_bw(bw_matrix)
    #vnet_set = model.vnets
    sorted_vn = sort_vnet(model)
    if w_m[2] >= 10*w_m[1]:
        threshold = 0.3
    else:
        threshold = 0.8
    snode_traffic = {}
    for vn_traffic in sorted_vn:
        vnet = vn_traffic[0]
        failed_vr = failed_dict[vnet.vnet_id]
        if failed_vr != -1: 
            # this node is failed
            standby_list = vnet.get_standby_ids()
            standby_cost = {}
            for s_vr in standby_list:
                dist_f = float(dist_matrix[s_vr][failed_vr + 1])
                failed_node = vnet.vnodes[failed_vr]
                vneighbors = failed_node.vneighbors
                dist_k = 0
                rtt_k = 0
                for k in vneighbors:
                    dist_k += float(dist_matrix[s_vr][k + 1])
                    rtt_k += float(rtt_matrix[s_vr][k + 1])

                connect_cost = w_b[0] * (w_a[0] * dist_f + w_a[1] * dist_k) +\
                                w_b[1] * rtt_k
                res_cost = snode_bw_list[s_vr]
                req_bw = sum(failed_node.neighbor_traffic.values())
                total = w_m[1] * connect_cost + w_m[2] * req_bw / res_cost
                standby_cost[s_vr] = total
            sorted_x  = []
            for item in standby_cost:
                sorted_x.append((item, standby_cost[item]))
            
            random.shuffle(sorted_x)
            for item in sorted_x:
                if item[0] not in snode_traffic:
                    utilization = vn_traffic[1] / total_bw(bw_matrix)[item[0]]
                else:
                    utilization = (snode_traffic[item[0]] + vn_traffic[1]) / total_bw(bw_matrix)[item[0]]
                #print utilization
                # Link-Path selsection add-on
                path_alloc = 1
                for k in vneighbors:
                    demand_id = find_demand_id(demand_dict, vnet.vnet_id, failed_vr + 1,
                                               item[0] + 1, k + 1)
                    demand = demand_dict[demand_id]['capacity']
                    find, path = find_path(demand_path, demand_id, 
                                     slink_dict, demand) 
                    if find == 0:
                        print "No available path between svr and nbr on the substrate network" 
                        path_alloc = 0
                    #print "FIND PATH", find, path
                # End link-path block 
                #print "ALLOCATED: ", path_alloc
                if path_alloc == 1:
                    if selected_dict.values().count(item[0]) < limit:
                        if utilization < threshold and w_m[2] >= 10*w_m[1]:
                            if item[0] not in snode_traffic: 
                                selected_dict[vnet.vnet_id] = item[0]
                                snode_bw_list[item[0]] -= vn_traffic[1]
                                snode_traffic[item[0]] = vn_traffic[1]
                                for slink_id in path:
                                    #print vn_traffic[1], slink_dict[slink_id]['capacity']
                                    slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                    #print slink_dict[slink_id]['capacity']
                                break;
                            else:
                                min_id = find_min(sorted_x, bw_matrix, snode_traffic, vn_traffic[1]) 
                                if min_id == item[0]:
                                    selected_dict[vnet.vnet_id] = item[0]
                                    snode_bw_list[item[0]] -= vn_traffic[1]
                                    snode_traffic[item[0]] = vn_traffic[1]
                                    for slink_id in path:
                                        #print vn_traffic[1],slink_dict[slink_id]['capacity']
                                        slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                        #print slink_dict[slink_id]['capacity']
                                #threshold = (threshold + 0.01)/2
                                    break
                        elif utilization < threshold:
                            selected_dict[vnet.vnet_id] = item[0]
                            snode_bw_list[item[0]] -= vn_traffic[1]
                            snode_traffic[item[0]] = vn_traffic[1]
                            for slink_id in path:
                                #print vn_traffic[1],slink_dict[slink_id]['capacity']
                                slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                #print slink_dict[slink_id]['capacity']
                            break
                        else:
                            print "does not satisfy the threshold"  
                    # if a svr is selected -- item[0]
                        
                        
                        
                else:
                    print "cannot allocate paths"
                   
    #print slink_dict                       
    return selected_dict, slink_dict
 
def find_standby2(model, limit, w_a, w_b, w_m, demand_path, demand_dict, slink_dict):
    """
    Heuristic algorithm to find the standby virtual router
    for each virtual network
    """
    #print slink_dict
    #print "FIND"
    failed_dict = model.failed_dict
    #print failed_dict, limit
    dist_matrix = model.cost_dict['dist']
    rtt_matrix = model.cost_dict['rtt']
    bw_matrix = model.cost_dict['bw']
    #cpu_vector = model.cost_dict['cpu']
    selected_dict = {}
    
    # get aggregated residual bw for all substrate nodes, and store it as a list
    snode_bw_list = total_bw(bw_matrix)
    
    # get total capacity and used bw for each snode
    node_port_list, used_bw_list = total_port(model)
    #vnet_set = model.vnets
    sorted_vn = sort_vnet(model)

    #for vnet in vnet_set:
    if w_m[2] >= 10*w_m[1]:
        threshold = 0.8
    else:
        threshold = 0.8
    snode_traffic = {}
    for vn_traffic in sorted_vn:
        vnet = vn_traffic[0]
        failed_vr = failed_dict[vnet.vnet_id]
        if failed_vr != -1: 
            # this node is failed
            standby_list = vnet.get_standby_ids()
            standby_cost = {}
            for s_vr in standby_list:
                dist_f = float(dist_matrix[s_vr][failed_vr + 1])
                failed_node = vnet.vnodes[failed_vr]
                vneighbors = failed_node.vneighbors
                dist_k = 0
                rtt_k = 0
                for k in vneighbors:
                    dist_k += float(dist_matrix[s_vr][k + 1])
                    rtt_k += float(rtt_matrix[s_vr][k + 1])

                connect_cost = w_b[0] * (w_a[0] * dist_f + w_a[1] * dist_k) +\
                                w_b[1] * rtt_k
                res_cost = snode_bw_list[s_vr]
                req_bw = sum(failed_node.neighbor_traffic.values())
                total = w_m[1] * connect_cost + w_m[2] * req_bw / res_cost
                standby_cost[s_vr] = total
            sorted_x = sorted(standby_cost.iteritems(), key=operator.itemgetter(1))
            #print "SORTED", sorted_x
            
            for item in sorted_x:
                if item[0] not in snode_traffic:
                    #utilization = vn_traffic[1] / total_bw(bw_matrix)[item[0]]
                    utilization = (vn_traffic[1] + used_bw_list[item[0]])/node_port_list[item[0]]
                else:
                    #utilization = (snode_traffic[item[0]] + vn_traffic[1]) / total_bw(bw_matrix)[item[0]]
                    utilization = (snode_traffic[item[0]] + vn_traffic[1] + used_bw_list[item[0]])/node_port_list[item[0]]
                #print utilization
                # Link-Path selsection add-on
                path_alloc = 1
                for k in vneighbors:
                    demand_id = find_demand_id(demand_dict, vnet.vnet_id, failed_vr + 1,
                                               item[0] + 1, k + 1)
                    demand = demand_dict[demand_id]['capacity']
                    find, path = find_path(demand_path, demand_id, 
                                     slink_dict, demand) 
                    if find == 0:
                        print "No available path between svr and nbr on the substrate network" 
                        path_alloc = 0
                    #print "FIND PATH", find, path
                # End link-path block 
                #print "ALLOCATED: ", path_alloc
                if path_alloc == 1:
                    if selected_dict.values().count(item[0]) < limit:
                        if utilization < threshold and w_m[2] >= 10*w_m[1]:
                            if item[0] not in snode_traffic: 
                                selected_dict[vnet.vnet_id] = item[0]
                                snode_bw_list[item[0]] -= vn_traffic[1]
                                snode_traffic[item[0]] = vn_traffic[1]
                                for slink_id in path:
                                    #print vn_traffic[1], slink_dict[slink_id]['capacity']
                                    slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                    #print slink_dict[slink_id]['capacity']
                                break;
                            else:
                                min_id = find_min(sorted_x, bw_matrix, snode_traffic, vn_traffic[1]) 
                                if min_id == item[0]:
                                    selected_dict[vnet.vnet_id] = item[0]
                                    snode_bw_list[item[0]] -= vn_traffic[1]
                                    snode_traffic[item[0]] += vn_traffic[1]
                                    for slink_id in path:
                                        #print vn_traffic[1],slink_dict[slink_id]['capacity']
                                        slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                        #print slink_dict[slink_id]['capacity']
                                #threshold = (threshold + 0.01)/2
                                    break
                        elif utilization < threshold:
                            selected_dict[vnet.vnet_id] = item[0]
                            snode_bw_list[item[0]] -= vn_traffic[1]
                            if item[0] not in snode_traffic: 
                                snode_traffic[item[0]] = vn_traffic[1]
                            else:
                                snode_traffic[item[0]] += vn_traffic[1]
                            for slink_id in path:
                                #print vn_traffic[1],slink_dict[slink_id]['capacity']
                                slink_dict[slink_id]['capacity'] = slink_dict[slink_id]['capacity'] - vn_traffic[1]
                                #print slink_dict[slink_id]['capacity']
                            break
                        else:
                            print "does not satisfy the threshold"  
                    # if a svr is selected -- item[0]
                        
                        
                        
                else:
                    print "cannot allocate paths"
                   
    #print slink_dict                       
    return selected_dict, slink_dict
    
def find_min(sorted_x, bw_matrix, snode_traffic, traffic_req):
    ''' find the minimum utilization '''
    min_id = 0
    min_util = 1
    for item in sorted_x:
        if item[0] not in snode_traffic:
            utilization = traffic_req / total_bw(bw_matrix)[item[0]]
        else:
            utilization = (snode_traffic[item[0]] + traffic_req) / total_bw(bw_matrix)[item[0]]
        if utilization < min_util:
            min_id = item[0]
            min_util = utilization
    return min_id
    
def sort_vnet(model, option='traffic'):
    """
    Sort the virtual network by specific criteria
    """    
    failed_dict = model.failed_dict
    vnet_info = model.get_vnet_info()
    vnets = model.vnets
    vnet_traffic = {}
    for vn in vnets:
        failed_id = failed_dict[vn.vnet_id]
        failed_node_traffic = vnet_info[vn.vnet_id]['traffic'][failed_id][1]
        vnet_traffic[vn] = round(failed_node_traffic, 5)
    sorted_vn = sorted(vnet_traffic.iteritems(), key=operator.itemgetter(1)) 
    sorted_vn.reverse()
    return sorted_vn
    

#def get_obj(model_old, w_a, w_b, theta, s_limit):
#    """
#    get the objective value based on the heuristic selection
#    """
#    
#    model = copy.deepcopy(model_old)
#    
#    #cpu_vector = model.cost_dict['cpu']
#    dist_matrix = model.cost_dict['dist']
#    rtt_matrix = model.cost_dict['rtt']
#    bw_matrix = model.cost_dict['bw']
#    w_a1, w_a2 = w_a
#    w_b1, w_b2 = w_b
#    theta1, theta2, theta3 = theta
#    
#    infeasible = 0
#
#    fail_nodes = model.failed_dict
#    start_time = time.time()
#    select_dict = find_standby(model, s_limit, w_a, w_b, theta)
#    #print "selection takes: ", time.time() - start_time
#    
#    sum_cost_1_2 = 0
#    r_list = {}
#   
#    for vnet in model.vnets:
#        j = vnet.vnet_id
#        f = fail_nodes[j]
#        # only count the failed virtual network
#        if f == -1:
#            pass
#        else:
#            if j in select_dict:
#                i = select_dict[j]
#                failed_node = vnet.vnodes[f]
#                vneighbors = failed_node.vneighbors
#                for k in vneighbors:                
#                    eta = operation_cost()
#                    #print "a1: ", w_a1, "a2: ", w_a2, "b1: ", w_b1, "b2: ", w_b2
#                    dist_c = dist_cost(i, f, k, dist_matrix, w_a1, w_a2)
#                    rtt_c = rtt_cost(i, k, rtt_matrix)
#                    sigma = connect_cost(dist_c, rtt_c, w_b1, w_b2)
#                    sum_cost_1_2 += theta1 * eta + theta2 * sigma
#                xi = resource_cost(bw_matrix, i)
#                req_bw = sum(failed_node.neighbor_traffic.values())
#                util = req_bw / xi
#                if i not in r_list:
#                    r_list[i] = util
#                else:
#                    r_list[i] += util
#                #print sigma, " v_" + str(vnet.vnet_id) + "_" + str(f) + "_" + str(i) + "_" + str(k) + "_" + str(k)
#            else:
#                print "INFEASIBLE at vnet: ", j
#                infeasible = 1
#    #print "DONE"
#    if infeasible == 0:
#        max_util = max(r_list.values())
#        obj = sum_cost_1_2 + theta3 * max_util
#    else:
#        obj = "infeasible"
#        max_util = "none"
#    #print obj
#    used_time = time.time() - start_time
#    return obj, select_dict, max_util, used_time


def find_demand_id(demand_dict, vn_id, fvr_id, svr, nbr):
    """
    find the demand_id for a particular demand
    """
    #print vn_id, fvr_id, svr, nbr
    for demand_id in demand_dict:
        if vn_id == demand_dict[demand_id]['vn_id'] and \
            fvr_id == demand_dict[demand_id]['fnode_id'] and \
            svr == demand_dict[demand_id]['svr'] and \
            nbr == demand_dict[demand_id]['nbr_id']:
            return demand_id
    
def find_path(demand_path, demand_id, slink_dict, demand):
    """
    If find a path with sufficient capacity, return 1, 0 otherwise
    """
    find = 0
    all_paths = demand_path[demand_id]
    #print all_paths
    for path_id in all_paths:
        path = all_paths[path_id]
        #print path
        min_capacity = get_min_capacity_path(path, slink_dict)
        #print demand, min_capacity
        if demand < min_capacity:
            find = 1
            break
    return find, path
    
def get_min_capacity_path(path, slink_dict):
    """
    Get the bottle neck link in the path
    """
    capacity_list = []
    for slink_id in path:
        capacity_list.append(slink_dict[slink_id]['capacity'])
    return min(capacity_list)
    
    
def get_obj_new(model_old, demand_path, slink_dict, demand_dict, w_a, w_b, theta, s_limit):
    """
    get the objective value based on the heuristic selection
    """
    model = copy.deepcopy(model_old)
    
    #cpu_vector = model.cost_dict['cpu']
    dist_matrix = model.cost_dict['dist']
    rtt_matrix = model.cost_dict['rtt']
    #bw_matrix = model.cost_dict['bw']
    w_a1, w_a2 = w_a
    w_b1, w_b2 = w_b
    theta1, theta2, theta3 = theta
    # find total capacity and used bw on substrate nodes
    node_port_list, used_bw_list = total_port(model)
    print "CHECK POINT-1", used_bw_list, node_port_list
    vnet_info = model.get_vnet_info()
    infeasible = 0

    fail_nodes = model.failed_dict
    start_time = time.time()
    select_dict, slink_dict = find_standby2(model, s_limit, w_a, w_b, theta, demand_path, demand_dict, slink_dict)
    # random selection
    #select_dict, slink_dict = find_random(model, s_limit, w_a, w_b, theta, demand_path, demand_dict, slink_dict)
    #print "selection takes: ", time.time() - start_time
    #print "Selected", select_dict
    sum_cost_1_2 = 0
    r_list = {}
    
    for node_id in range(0,len(used_bw_list)):
        r_list[node_id] = used_bw_list[node_id]/node_port_list[node_id]
        print "INITIAL", r_list
    svr_subset = {}
    for vnet in model.vnets:
        j = vnet.vnet_id
        f = fail_nodes[j]
        # only count the failed virtual network
        if f == -1:
            pass
        else:
            for node_id in vnet_info[j]['standby']:
                svr_subset[node_id] = r_list[node_id]
            print "Subset SVR: ", svr_subset
                
            if j in select_dict:
                #print "FEASIBLE FOUND"
                #print vnet_info[j]['standby']
                i = select_dict[j]
                failed_node = vnet.vnodes[f]
                vneighbors = failed_node.vneighbors
                for k in vneighbors:                
                    eta = operation_cost()
                    #print "a1: ", w_a1, "a2: ", w_a2, "b1: ", w_b1, "b2: ", w_b2
                    dist_c = dist_cost(i, f, k, dist_matrix, w_a1, w_a2)
                    rtt_c = rtt_cost(i, k, rtt_matrix)
                    sigma = connect_cost(dist_c, rtt_c, w_b1, w_b2)
                    sum_cost_1_2 += theta1 * eta + theta2 * sigma
                #find residual bw on substrate node
                #xi = resource_cost(bw_matrix, i)
                req_bw = sum(failed_node.neighbor_traffic.values())
                #util = req_bw / xi
                #print req_bw, i, used_bw_list[i], node_port_list[i]
                util = req_bw/node_port_list[i]
                
                if i not in r_list:
                    r_list[i] = util #+ used_bw_list[i]/node_port_list[i]
                else:
                    r_list[i] += util
                
                #print sigma, " v_" + str(vnet.vnet_id) + "_" + str(f) + "_" + str(i) + "_" + str(k) + "_" + str(k)
            else:
                print "INFEASIBLE at vnet: ", j
                infeasible = 1
    #print "DONE"
    
    if infeasible == 0:
        max_util = max(svr_subset.values())
        obj = sum_cost_1_2 + theta3 * max_util
    else:
        obj = "infeasible"
        max_util = "none"
    #print obj
    used_time = time.time() - start_time
    return obj, select_dict, max_util, used_time


    
    

