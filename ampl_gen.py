# -*- coding: utf-8 -*-
"""
This module is to generate ampl data file based on the model created
by create_model.py

A sample format of ampl data file is given by toy_example2.dat


Created on Thu Apr  3 15:25:59 2014

@author: xuanliu
"""

from __future__ import division
import random
import scipy
import numpy as np
import topo_type
import textwrap
import scipy.io
import time
import topo_xml

TOPO_PATH = "/Users/xuanliu/Documents/projects/dynrec/modeling/formulation/dynrec-modeling/topology/"

def print_header(ampl_data_file):
    """
    print the description information about the ampl data file
    """
    fopen = open(ampl_data_file, 'w')
    file_timestamp = time.ctime()    
    header = """
    ### -------------------------
    #
    # This is a data file for ampl, it is created
    # based on the model created by create_model.py, which
    # generate multiple virtual networks and determines 
    # failure types. 
    # 
    # By Xuan Liu
    # {0}
    ### ------------------------
    """.format(file_timestamp)
    fopen.write(header)
    fopen.close()
    
def print_index_bound(model, ampl_data_file):
    """
    Print the index bound information
    The input is the model object created in create_model.py
    """
    fopen = open(ampl_data_file, 'a')
    
    to_print = """
    ### ------ Index bound declaration ------- ###
    param num_pr := {0};
    param num_vn := {1};
    """.format(len(model.snet_nodes), len(model.vnets))
    
    fopen.write(to_print)
    fopen.close()



def set_info(model, ampl_data_file):
    ''' print set data specification ''' 
    # get failure node id, one node per network
    failed_dict = model.failed_dict
    failed = failed_dict.values()
    
    failed_set_str = ''
    count = 1
    for vnet_id in failed_dict:
        if count == 1:
            fnode_info = ''
        else:
            fnode_info = '\t'
        if failed_dict[vnet_id] == -1:
            fnode_info += 'set Fail[' + str(vnet_id) + '] := ;\n'
        else:
            fnode_info += 'set Fail[' + str(vnet_id) + '] := ' \
                    + str(failed_dict[vnet_id]+1) + ';\n'
        failed_set_str +=fnode_info 
        count += 1
    
    to_print = """
    ### --- Set Declaration ---- ###
    # the set of physical resources (only consider cpu for now)
    set RES := cpu;
    
    # the set of failed routers
    {0}
    """.format(failed_set_str)

    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
    
    return failed
    #para_beta(failed, model, data_file)
    #return failed 
    

def print_num_ports(model, ampl_data_file):
    """
    print the number of physical ports used on the subtrate nodes
    for example:
    param num_p :=
        1   2
        2   3
        3   4
        4   2
    Note: the first column is substrate node's node_id, 
    the second column is the nubmer of ports used on this node
    """
    
    snode_ports = ''
    
    for node in model.snet_nodes:
        if model.snet_nodes.index(node) == 0:
            node_iface = '\t\t' + str(node.node_id + 1) + '\t\t' + \
                            str(node.num_iface) + '\n'
            snode_ports += node_iface
        else:
            node_iface = '\t\t\t' + str(node.node_id + 1) + '\t\t' + \
                            str(node.num_iface) + '\n'
            snode_ports += node_iface
    to_print = """
    ####  ========================================  ####
    ##    AMPL table index rule:                      ##
    ##    The row labels give the first index and     ##
    ##    the column labels the second index          ##
    ####  ========================================  ####
    
    
    # the number of ports on a physical router i, where i is in PRouter
    param num_p :=
    {0}\t;
    """.format(snode_ports)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()

def print_vnode_viface(model, ampl_data_file):
    """
    print the number of virtual interfaces used on the virtual nodes
    for example:
    column label is the vn id (j), and the row id is substrate node id (i), 
    num_viface[i,j]
    
    param num_viface:   1   2 :=
                    1   9   9
                    2   9   9
                    3   9   9
                    ....
    Note: on the virtual node, the number of viface is equal to the
    total number of substrate nodes. (assume there are enough virtual iface)
    """    
    vnode_viface = ''
    vnet_index = ''
    for vnet in model.vnets:
        vnet_index += '\t\t' + str(vnet.vnet_id)
    
    for node in model.snet_nodes:
        if model.snet_nodes.index(node) == 0:
            temp = '\t\t\t\t' + str(node.node_id + 1) 
        else:
            temp = '\t\t\t\t\t' + str(node.node_id + 1)
        for vnet in model.vnets:
            temp += '\t\t' + str(len(model.snet_nodes))
        temp += '\n'
        vnode_viface += temp
    
    to_print = """
    # the number of virtual interface on virtual route r^j_i: num_viface[i,j]
    # (Column label is the vn j, and the row label is substrate node i)
    param num_viface: {0} :=
    {1}\t;
    """.format(vnet_index, vnode_viface)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
    
    
def print_bw(model, ampl_data_file):
    """
    print available bw information on the substrate nodes' each interface.
    the number of rows equals the maximum number of physical interfaces 
    used by a substrate node.    
    """
    
    snet_info = model.get_snet_info()
    # get the maximum number of interfaces used by a substrate node
    # this maximum number indicates how many rows will be in the matrix    
    iface_by_node = []
    for item in snet_info:
        iface_by_node.append(snet_info[item]['num_iface'])
    max_ifaces = max(iface_by_node)
    
    node_index = []
    for item in snet_info:
        node_index.append(str(item + 1))
    node_index_str = '\t\t'.join(node_index)
    
    matrx_str = ''
    bw_m = []
    for index in range(0, max_ifaces):
        iface_bw_list = []
        for item in snet_info:
            if index < snet_info[item]['num_iface']:
                #iface_bw = round(snet_info[item]['ifaces'][index]['avail_bw'], 5)
                iface_bw = str(round(snet_info[item]['ifaces'][index]['avail_bw'], 5))
            else:
                #iface_bw = 0
                iface_bw = '.'
            iface_bw_list.append(iface_bw)
            #iface_bw_list.append(str(iface_bw))
        if index == 0:
            matrx_str += '\t\t' + str(index + 1) + '\t\t' + '\t\t'.join(iface_bw_list) + '\n'
        else:
            matrx_str += '\t\t\t' + str(index + 1) + '\t\t' + '\t\t'.join(iface_bw_list) + '\n'
        bw_m.append(iface_bw_list)
    

    to_print = """
    ### ---------- Parameter Data ------------ ###
    # the residual bandwidth on port p on physical router i, i is in PRouter
    # and p is in P[i]
    
    param b (tr):       {0} :=
    {1}\t;
    """.format(node_index_str, matrx_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
    #print "bw", bw_m
    return bw_m
    
    
def print_indicator(model, ampl_data_file):
    """
    Print indicator parameters: alpha, indicating the virtual 
    node's status: connected
    """
    vnet_info = model.get_vnet_info()
    
    node_index = []
    for item in range(len(model.snet_nodes)):
        node_index.append(str(item + 1))
    node_index_str = '\t\t'.join(node_index)
    
    alpha_matrix_str = ''
    #delta_matrix_str = ''
    for vnet in vnet_info:
        alpha_list = [str(vnet)]
        #delta_list = [str(vnet)]
        for node_str in node_index:
            node = int(node_str)
            if vnet_info[vnet]['vnode_status'][node - 1] == 1:
                alpha_list.append('1')
                #delta_list.append('0')
#            elif vnet_info[vnet]['vnode_status'][node - 1] == 2:
#                #beta_list.append('0')
#                alpha_list.append('0')
#                delta_list.append('1')
            else:
                alpha_list.append('0')
                #delta_list.append('0')
        if vnet == 1:
            alpha_matrix_str += '\t\t\t' + '\t\t'.join(alpha_list) + '\n'
            #delta_matrix_str += '\t\t\t' + '\t\t'.join(delta_list) + '\n'
        else:
            alpha_matrix_str += '\t\t\t\t' + '\t\t'.join(alpha_list) + '\n'
            #delta_matrix_str += '\t\t\t\t' + '\t\t'.join(delta_list) + '\n'
    
    to_print = """
    # indicator alpha: indicates if a virtual router r^j_i is connected or not
    param alpha (tr):   {0} :=
    {1}\t;
    """.format(node_index_str, alpha_matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
    
def print_delta(model, ampl_data_file):
    """
    Print indicator parameter delta, indicating the standby virtual routers
    """
    vnet_info = model.get_vnet_info()
    
    node_index = []
    for item in range(len(model.snet_nodes)):
        node_index.append(str(item + 1))
    node_index_str = '\t\t'.join(node_index)
    
    delta_matrix_str = ''
    for vnet in vnet_info:
        delta_list = [str(vnet)]
        for node_str in node_index:
            node = int(node_str)
            if vnet_info[vnet]['vnode_status'][node - 1] == 2:
                delta_list.append('1')
            else:
                delta_list.append('0')
        if vnet == 1:
            delta_matrix_str += '\t\t\t' + '\t\t'.join(delta_list) + '\n'
        else:
            delta_matrix_str += '\t\t\t\t' + '\t\t'.join(delta_list) + '\n'

    to_print = """    
    # indicator delta: indicates if a virtual router r^j_i is reserved as a S-VR
    param delta (tr):   {0} :=
    {1}\t;
    """.format(node_index_str, delta_matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
                
def print_beta(model, ampl_data_file):
    """
    print failure indicator beta
    """
    vnet_info = model.get_vnet_info()
    
    node_index = []
    for item in range(len(model.snet_nodes)):
        node_index.append(str(item + 1))
    node_index_str = '\t\t'.join(node_index)
    beta_matrix_str = ''
    for vnet in vnet_info:
        beta_list = [str(vnet)]
        for node_str in node_index:
            node = int(node_str)
            if vnet_info[vnet]['vnode_status'][node - 1] == -1:
                beta_list.append('1')
            else:
                beta_list.append('0')
        if vnet == 1:
            beta_matrix_str += '\t\t\t' + '\t\t'.join(beta_list) + '\n'
        else:
            beta_matrix_str += '\t\t\t\t' + '\t\t'.join(beta_list) + '\n'
    
    to_print = """
    # indicator alpha: indicates if a virtual router r^j_i is connected or not
    param beta (tr):   {0} :=
    {1}\t;
    """.format(node_index_str, beta_matrix_str)
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()
               
def print_limit(model, ampl_data_file, limit='inf'):
    """
    Print the upper limit on how many S-VRs can be selected on substrate node
    h_i
    Option: inf: unlimited, euqals to the number of vnets
            <num>: integer value less than the number of vnets
            rand: random number between 1 and number of vnets
    """
    matrix_str = ''
    for node in model.snet_nodes:
        if node.node_id == 1:
            matrix_str += '\t\t'
        else:
            matrix_str += '\t\t\t'
        if limit == 'inf':
            num_vnet = len(model.vnets)
            matrix_str += '\t\t'.join([str(node.node_id + 1), str(num_vnet)]) + '\n'
        elif limit == 'rand':
            num_vnet = len(model.vnets)
            limit_value = random.randint(1, num_vnet)
            matrix_str += '\t\t'.join([str(node.node_id + 1), str(limit_value)]) + '\n'
        else:
            matrix_str += '\t\t'.join([str(node.node_id + 1), limit]) + '\n'
    
    to_print = """
    # the upper limit on how many S-VRs can be selected on substrate node: h_i
    
    param limit :=
    {0}\t;
    """.format(matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close() 
        
def print_e(model, ampl_data_file):
    ''' print connectivity information e '''
    e_header = 'param e :=\n'
    vn_list = model.vnets
    fopen = open(ampl_data_file, 'a')
    fopen.write(e_header)
    for vnet in vn_list:
        sub_header = ['[' + str(vnet.vnet_id) + ', *, *]:']
        vnodeid = map(str, range(1, len(vnet.vnodes)+1))
        sub_header.extend(vnodeid)
        sub_header.append(':=\n')
        sub_matrix = scipy.zeros((len(vnet.vnodes), len(vnet.vnodes)), 
                                 dtype = object)
        for i in range(len(vnet.vnodes)):
            for j in range(len(vnet.vnodes)):
                if (i,j) in vnet.vtopo.edges():
                    sub_matrix[i][j] = '1'
                    sub_matrix[j][i] = '1'
                elif i == j:
                    sub_matrix[i][j] = '.'
                elif sub_matrix[i][j] == '':
                    sub_matrix[i][j] = '0'
        #print sub_matrix
        #str_index = gen_index_str(len(vnet.vnodes))
        #print str_index
        index =gen_index(len(vnet.vnodes))
        sub_matrix = np.insert(sub_matrix, 0, index, axis=1)
        #print sub_matrix
        sub_matrix = get_str_matrix(sub_matrix)
        fopen.write('\t'.join(sub_header))
        fopen.write("\n".join(["\t".join(r) for r in sub_matrix]))
        if vn_list.index(vnet) == len(vn_list) - 1:
            fopen.write(';\n')
        else:
            fopen.write('\n')
    fopen.close()            
        
def gen_index(stop):
    ''' generate a array of sequential number in str type '''
    index = []
    for i in range(1, stop + 1):
        index.append(i)
    return index

def get_str_matrix(input_matrix):
    """
    convert a matrix into string matrix
    """
    row = input_matrix[:,0]
    col = input_matrix[0,:]
    for i in range(len(row)):
        for j in range(len(col)):
            input_matrix[i][j] = str(input_matrix[i][j])
    return input_matrix 
    
    
def gen_index_str(stop):
    ''' generate a array of sequential number in str type '''
    str_index = []
    for i in range(1, stop + 1):
        str_index.append(str(i))
    return str_index
    
    
def print_c(model, failed, num_vp, data_file):
    ''' print parameter c '''
    c_header = 'param c :=\n'
    vn_list = model.vnets
    fopen = open(data_file, 'a')
    fopen.write(c_header)
    #print "num_standby: ", model.num_standby
    for vnet in vn_list:
        if failed[vn_list.index(vnet)] == -1:
            pass
        else:
            standby_list = vnet.get_standby_ids()
            #print "standby_list", standby_list
            fnode = vnet.vnodes[failed[vnet.vnet_id - 1]] # one failure per virtual network
            #req_bw = fnode.iface_bw
            fnode_nbr_traffic = fnode.neighbor_traffic
            #print fnode_nbr_traffic
            neighbors = fnode.vneighbors
            for viface in range(1, num_vp + 1):
                sub_header = ['[' + str(vnet.vnet_id) \
                                + ', ' + str(failed[vn_list.index(vnet)]+1) \
                                + ', *, ' + str(viface) + ', *]:']
                header_ext = gen_index_str(len(vnet.vnodes))
                sub_header.extend(header_ext)
                sub_header.append(':=\n')
                sub_matrix = scipy.zeros((len(vnet.vnodes), len(vnet.vnodes)), 
                                     dtype = object)
            
                for i in range(len(vnet.vnodes)):
                    if i in standby_list:
                        for j in range(len(vnet.vnodes)):
                            if i == j:
                                sub_matrix[i][j] = '.'
                            elif j in neighbors:
                                #sub_matrix[i][j] = str(req_bw)
                                sub_matrix[i][j] = str(fnode_nbr_traffic[j])
                            else:
                                sub_matrix[i][j] = '0'
                    else:
                        for j in range(len(vnet.vnodes)):
                            if i == j:
                                sub_matrix[i][j] = '.'
                            else:
                                sub_matrix[i][j] = str(sub_matrix[i][j])    
                                      
                index =gen_index(len(vnet.vnodes))
                sub_matrix = np.insert(sub_matrix, 0, index, axis=1)
                sub_matrix = get_str_matrix(sub_matrix)
                fopen.write('\t'.join(sub_header))
                fopen.write("\n".join(["\t".join(r) for r in sub_matrix]))
                fopen.write('\n')
    fopen.write(';\n')
  

    
def norm_data(data_matrix):
    """
    normalize cost into values between 0 and 1
    """
    new_matrix = []
    for item in data_matrix:
        new_item =[]
        for sub_item in item:
            if sub_item == '.':
                new_item.append(0)
            else:
                new_item.append(float(sub_item))
        new_matrix.append(new_item)
    total = scipy.sum(new_matrix)
    
    num_rows = len(data_matrix[:,1])
    num_cols = len(data_matrix[1,:])
    for i in range(num_rows):
        for j in range(num_cols):
            if i == j:
                pass
            else:
                data_matrix[i][j] = str(round(float(data_matrix[i][j])/total,5))
    return data_matrix

def norm_data2(data_matrix):
    """
    normalize cost into values between 0 and 1
    """
    sorted_data = np.sort(data_matrix)
    sorted_data = sorted_data[:,1:]
    max_data = np.max(sorted_data)
    min_data = np.min(sorted_data)
    diff = float(max_data) - float(min_data)
    num_rows = len(data_matrix[:,1])
    num_cols = len(data_matrix[1,:])
    for i in range(num_rows):
        for j in range(num_cols):
            if i == j:
                pass
            else:
                data_matrix[i][j] = str(round((float(data_matrix[i][j]) - 
                float(min_data))/diff,4))
    return data_matrix  
    
def viface_opera_para(data_file):
    ''' print parameters for cost function'''
    fopen = open(data_file, 'a')
    vifop_para = """
    #### Cost Function Parameters ####
    # virtual interface operation parameters
    param enable := {0};
    param disable := {1};
    param ipConfig := {2};
    """.format(0.2,0.2,2)
    vifop_para = textwrap.dedent(vifop_para)
    fopen.write(vifop_para)
    fopen.close()    


def set_rtt(model):
    """
    set rrt for each direct virtual links
    rtt = random value between 0.005 and 0.01 ms
    """
    snodes = model.snet_topo.nodes()
    str_index = gen_index_str(len(snodes))
    rtt_matrix = scipy.zeros((len(snodes), len(snodes)), dtype = object)
    
    for i in range(len(snodes)):
        for j in range(len(snodes)):
            if i == j:
                rtt_matrix[i][j] = '.'
            elif j > i:
                tmp_rtt = round(random.uniform(0.005, 0.01), 4)
                rtt_matrix[i][j] = str(tmp_rtt)
                rtt_matrix[j][i] = str(tmp_rtt)
            else:
                pass
    norm_rtt = norm_data2(rtt_matrix)
    rtt_matrix = np.insert(norm_rtt, 0, str_index, axis=1)
    return rtt_matrix

def print_rtt(model, data_file):
    """
    print rtt information in ampl data file
    """
    rtt_matrix = set_rtt(model)
    #print rtt_matrix
    nodeids = map(str, range(1, len(model.snet_nodes)+1))
    header_for_print = '\t'.join(nodeids)
    rtt_matrix_print = "\n".join(["\t".join(r) for r in rtt_matrix])
    #print header_for_print, rtt_matrix_print
    rtt_para = """
    # round trip time between two direct virtual links (ms)
    param rtt: \t{0} \t:=
    {1}
    ;
    """.format(header_for_print, rtt_matrix_print)
    fopen = open(data_file, 'a')      
    fopen.write(rtt_para)
    fopen.close()
    return rtt_matrix


def geo_dist(model, geo_info):
    ''' get geo-distance matrix with column index '''
    snodes = model.snet_topo.nodes()
    str_index = gen_index_str(len(snodes))
    dist_matrix = scipy.zeros((len(snodes), len(snodes)), 
                                     dtype = object)
    for i in range(len(snodes)):
        for j in range(len(snodes)):
            if i == j:
                dist_matrix[i][j] = '.'
            else:
                lat1, lon1 = geo_info[i]
                lat2, lon2 = geo_info[j]
                dist = round(topo_type.geocalc(lat1, lon1, lat2, lon2)/1000, 4)
                #print "dist", dist
                dist_matrix[i][j] = str(dist)
    #norm_dist = norm_data2(dist_matrix)
    if model.snet_type != 'random':
        dist_matrix = np.insert(dist_matrix, 0, str_index, axis=1)
    #print dist_matrix
    return dist_matrix
    
    
def print_geo_dist(model, data_file):
    ''' print geo distance'''
    if model.snet_type != 'random':
        xml_file = TOPO_PATH + model.snet_type + ".xml"
        node_dict, link_dict, node_dict_new = topo_xml.run(xml_file)
        geo_info = node_dict_new
        
    dist_matrix = geo_dist(model, geo_info)
    #print dist_matrix
    nodeids = map(str, range(1, len(model.snet_nodes)+1))
    header_for_print = '\t'.join(nodeids)
    dist_matrix_print = "\n".join(["\t".join(r) for r in dist_matrix])
    #print header_for_print, dist_matrix_print
    geo_para = """
    # geographcal distance (kkm)
    param dist: \t{0} \t:=
    {1}
    ;
    """.format(header_for_print, dist_matrix_print)
    fopen = open(data_file, 'a')      
    fopen.write(geo_para)
    fopen.close()
    return dist_matrix
    
def print_weight1(w_a,w_b, data_file):
    """
    print weight parameters for connectivity weight parameter 
    a = [a1, a2]
    b = [b1, b2, b3]
    """
    weight_para = """
    param a1 := {0} ;
    param a2 := {1} ;
    param b1 := {2} ;
    param b2 := {3} ;
    param b3 := {4} ;    
    """.format(w_a[0], w_a[1], w_b[0], w_b[1], 0)
    fopen = open(data_file, 'a')      
    weight_para = textwrap.dedent(weight_para)
    fopen.write(weight_para)
    fopen.close()
  
def print_res_info(snet_info, data_file):
    """
    print available resources on phyiscal router i
    currently only consider two types of resources: cpu & ram
    """
    cpu_res = []
    #ram_res = []
    for node_id in snet_info:
        cpu = snet_info[node_id]['cpu']
        #ram = snet_info[node_id]['ram']
        cpu_res.append(str(1-cpu))
        #ram_res.append(str(1-ram))
    str_index = gen_index_str(len(snet_info.keys()))
    index_with_tap = '\t'.join(str_index)   
    res_info = """
    # the available resources on physical router i
    param res (tr):\t{}\t:=
    cpu \t{};
    """.format(index_with_tap,'\t'.join(cpu_res))
    fopen = open(data_file, 'a')      
    res_info = textwrap.dedent(res_info)
    fopen.write(res_info)
    fopen.close()
    res_matrix = [cpu_res]
    return res_matrix
  

  
def print_res_weight(w_h, data_file):
    """
    Print resource weight parameter
    h = [h1, h2]
    h1 is for cpu, and h2 is for ram
    """
    to_print = """
    # The weight for each resource
    param h:= cpu {};
    """.format(w_h[0])
    to_print = textwrap.dedent(to_print)
    fopen = open(data_file, 'a')
    fopen.write(to_print)
    fopen.close()
    
def print_obj_weight(w_m, data_file):
    """
    Print resource weight parameter
    w_m = [w_m1, w_m2]
    w_m1 is for viface operation cost
    w_m2 is for connectivity cost
    w_m3 is for the resource cost
    """
    to_print = """
    #### objective function weight parameter ####
    param m1 := {} ;
    param m2 := {} ;
    param m3 := {} ;
    """.format(w_m[0], w_m[1], w_m[2])
    to_print = textwrap.dedent(to_print)
    fopen = open(data_file, 'a')
    fopen.write(to_print)
    fopen.close()    
    
    
    
    
def print_tau(model, ampl_data_file):
    """
    Print parameter tau. All equals to 0 for now, means that no need to 
    reconfigure IP address
    """
    node_index = []
    for item in range(len(model.snet_nodes)):
        node_index.append(str(item + 1))
    node_index_str = '\t\t'.join(node_index)

    matrix_str = ''
    for vnet in model.vnets:
        tau_list = ['0'] * len(model.snet_nodes)
        tau_list.insert(0, str(vnet.vnet_id))
        if vnet.vnet_id == 1:
            matrix_str += '\t\t'
        else:
            matrix_str += '\t\t\t'
        matrix_str += '\t\t'.join(tau_list) + '\n'

    to_print = """
    param tau (tr) : {}  :=
    {}\t;
    """.format(node_index_str, matrix_str)
    fopen = open(ampl_data_file, 'a')
    fopen.write(to_print)
    fopen.close()

def matrix_str2num(cost_dict):
    """
    convert cost matrix from string to numeric matrix. If it is a '.', 
    then change it to 0
    """        
    mat_dict = {}
    for item in cost_dict:
        #print item
        rows = len(cost_dict[item])
        cols = len(cost_dict[item][0])
        mat_dict[item] = []
        for row_i in range(rows):
            tmp = []
            for col_j in range(cols):
                #print item, row_i, col_j
                if cost_dict[item][row_i][col_j] == '.':
                    tmp.append(0)
                else:
                    tmp.append(float(cost_dict[item][row_i][col_j]))
            mat_dict[item].append(tmp)
    return mat_dict

    
def dryrun(model, ampl_data_file):
    """
    Debug
    """
    snet_info = model.get_snet_info()
    print_header(ampl_data_file)
    print_index_bound(model, ampl_data_file)
    failed = set_info(model, ampl_data_file)
    print_num_ports(model, ampl_data_file)
    print_vnode_viface(model, ampl_data_file)
    print_bw(model, ampl_data_file)
    print_indicator(model, ampl_data_file)
    print_delta(model, ampl_data_file)
    print_limit(model, ampl_data_file)
    print_e(model, ampl_data_file)
    num_viface = len(model.snet_nodes)
    print_c(model, failed, num_viface, ampl_data_file)
    viface_opera_para(ampl_data_file)
    print_tau(model, ampl_data_file)
    dist_matrix = print_geo_dist(model, ampl_data_file)
    rtt_matrix = print_rtt(model, ampl_data_file)
    # set default weight parameters
    w_a = [0.5, 0.5]
    w_b = [1, 0, 0]
    print_weight1(w_a, w_b, ampl_data_file)
    res_matrix = print_res_info(snet_info, ampl_data_file)
    w_h = [1]
    print_res_weight(w_h, ampl_data_file)
    w_m = [0, 0.1, 0.9]
    print_obj_weight(w_m, ampl_data_file)
    
#def run(model, snet_info, ampl_data_file, mat_file):
#    """
#    Program wrapper
#    """
#
#    #snet_info = model.get_snet_info()
#    print_header(ampl_data_file)
#    print_index_bound(model, ampl_data_file)
#    failed = set_info(model, ampl_data_file)
#    print_num_ports(model, ampl_data_file)
#    print_vnode_viface(model, ampl_data_file)
#    bw_matrix = print_bw(model, ampl_data_file)
#    print_indicator(model, ampl_data_file)
#    print_delta(model, ampl_data_file)
#    print_limit(model, ampl_data_file)
#    print_e(model, ampl_data_file)
#    num_viface = len(model.snet_nodes)
#    print_c(model, failed, num_viface, ampl_data_file)
#    viface_opera_para(ampl_data_file)
#    print_tau(model, ampl_data_file)
#    dist_matrix = print_geo_dist(model, ampl_data_file)
#    rtt_matrix = print_rtt(model, ampl_data_file)
#    # set default weight parameters
#    w_a = [0.5, 0.5]
#    w_b = [0.5, 0.5, 0]
#    print_weight1(w_a, w_b, ampl_data_file)
#    res_matrix = print_res_info(snet_info, ampl_data_file)
#    w_h = [1]
#    print_res_weight(w_h, ampl_data_file)
#    w_m = [0.333, 0.333, 0.333]
#    print_obj_weight(w_m, ampl_data_file)
#    # create cost mat file for data process
#    cost_dict = {}
#    cost_dict['bw'] = bw_matrix
#    cost_dict['dist'] = dist_matrix
#    cost_dict['rtt'] = rtt_matrix
#    cost_dict['cpu'] = res_matrix
#    mat_dict = matrix_str2num(cost_dict)
#    scipy.io.savemat(mat_file, mat_dict)
#    return cost_dict #,failed    


def run(model, snet_info, data_file, mat_file):
    ''' program wrapper '''
  
    #failed = set_info(model, ampl_data_file)
    print_header(data_file)
    print_index_bound(model, data_file)
    #failed = set_info(model, data_file)  
    print_num_ports(model, data_file)
    print_vnode_viface(model, data_file)
    bw_matrix = print_bw(model, data_file)
    print_indicator(model, data_file)
    #print_delta(model, data_file)
    #print_limit(model, data_file, standby_limit)
    print_e(model, data_file)
    #para_c(model, failed, num_vp, data_file)
    viface_opera_para(data_file)
    print_tau(model, data_file)
    dist_matrix = print_geo_dist(model, data_file)
    rtt_matrix = print_rtt(model, data_file)   
    res_matrix = print_res_info(snet_info, data_file)
    # create cost mat file for data process
    cost_dict = {}
    cost_dict['bw'] = bw_matrix
    cost_dict['dist'] = dist_matrix
    cost_dict['rtt'] = rtt_matrix
    cost_dict['cpu'] = res_matrix
    #print cost_dict
    mat_dict = matrix_str2num(cost_dict)
    scipy.io.savemat(mat_file, mat_dict)
    scipy.io.savemat(mat_file, mat_dict)
    return cost_dict

def change_limits(model, data_file, standby_limit):
    """
    Print changed information:
    standby_limit
    """
    print_limit(model, data_file, standby_limit)
    

def adjust_run(model_adjust, snet_info, num_vp, data_file):
    """
    Print changed information:
    Set of failure
    param beta, gamma, c
    """
    failed = set_info(model_adjust, data_file)
    print_beta(model_adjust, data_file)
    #para_gamma(model_adjust, failed, num_vp, data_file)
    num_viface = len(model_adjust.snet_nodes)
    print_c(model_adjust, failed, num_viface, data_file)
    return failed
    

def change_weight(w_a, w_b, theta, data_file):
    """
    Change the weight parameters
    """
    # set default weight parameters
#    w_a = [0.5, 0.5]
#    w_b = [0.5, 0.5, 0]
    print_weight1(w_a, w_b, data_file)
    w_h = [1]
    print_res_weight(w_h, data_file)
#    w_m = [0.333, 0.333, 0.333]
    print_obj_weight(theta, data_file)
    
    
def change_standby_num(model, data_file, min_standby, model_f):
    """
    Change the number of standby virtual routers in the virtual networks
    If current required standby_nodes are greater than the minmum standby
    node number, add standby routers to each virtual network
    """
    #print "model.num_standby= ", model.num_standby, "min_standby", min_standby
    if model.num_standby == min_standby:
        print_delta(model, data_file)
    else:
        diff = 2
        new_svr_dict = model.add_standby(diff)
        model_f.add_standby2(new_svr_dict)
        print_delta(model, data_file)
            
def find_link_capacity(snet_info, src_snode, dst_snode):
    ''' Find the link capacity between two nodes '''
    src_info = snet_info[src_snode]
    for nbr_iface in src_info['neighbor']:
        if nbr_iface[0] == dst_snode:
            iface_id = nbr_iface[1]
            break
    slink_capacity = src_info['ifaces'][iface_id]['avail_bw']
    return slink_capacity
    
    
def get_slink_info(model_f):
    ''' collect the substrate link information from the model '''
    slinks = model_f.snet_topo.edges()
    snet_info = model_f.get_snet_info()
    slinks.sort()
    slink_dict = {}
    slink_id = 1
    for slink in slinks:
        slink_dict[slink_id] = {}
        slink_dict[slink_id]['src'] = slink[0] + 1
        slink_dict[slink_id]['dst'] = slink[1] + 1
        slink_dict[slink_id]['capacity'] = find_link_capacity(snet_info, slink[0], slink[1])
        slink_id += 1
    return slink_dict
        
def print_slink_info(model_f, ampl_data_file):
    """
    Print substrate link information in the ample data file, in the form of:
    For example:
    param: slink_src 	slink_dst slink_capacity :=
    1 		2 				1      8.7526
    2 		3				2      0.02124
    3 		4 				3      8.5300
    4 		5 				4      8.1107
    5 		6 				5 	 4.3670 
    6 		7 				6      5.7415
    7 		7 				1      6.3874
    8 		7 				2      8.8389
    9 		6 				3      0.03646
    ;
    """
    slink_dict = get_slink_info(model_f)
    num_slinks = len(slink_dict.keys())
    matrix_str = '\t\t\t'.join([str(1), str(slink_dict[1]['src'] + 1), 
                              str(slink_dict[1]['dst'] + 1), str(slink_dict[1]['capacity'])]) + '\n'
    for index in range(2, num_slinks + 1):
        temp_str = '\t' + '\t\t\t'.join([str(index), str(slink_dict[index]['src'] + 1), 
                              str(slink_dict[index]['dst'] + 1), str(slink_dict[index]['capacity'])]) + '\n'
        matrix_str += temp_str
    
    slink_param = """
    ## -- Define Substrate Link information --
    param L := {0};
    param: slink_src    slink_dst   slink_capacity :=
    {1} \t;
    """.format(num_slinks, matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(slink_param)
    fopen.close()
    return slink_dict
    
    
    
def get_demand_info(model_f):
    """
    Get the bw capacity demand between the S-VR and the faile VR's neighbors
    """
    fail_dict = model_f.failed_dict
    failed = fail_dict.values()
    vnet_info = model_f.get_vnet_info()
    vn_list = model_f.vnets
    demand_c_dict = {}
    demand_id = 1
    for vnet in vn_list:
        vnet_id = vnet.vnet_id
        standby_list = vnet_info[vnet_id]['standby']
        #print "standby_list", standby_list
        fnode = vnet.vnodes[failed[vnet.vnet_id - 1]] # one failure per virtual network
        if fail_dict[vnet_id] == -1:
            pass
        else:
            for svr in standby_list:
                for fnode_nbr in fnode.neighbor_traffic: 
                    demand_c_dict[demand_id] = {}
                    demand_c_dict[demand_id]['vn_id'] = vnet_id
                    demand_c_dict[demand_id]['fnode_id'] = fail_dict[vnet_id] + 1
                    demand_c_dict[demand_id]['svr'] = svr + 1
                    demand_c_dict[demand_id]['nbr_id'] = fnode_nbr + 1
                    demand_c_dict[demand_id]['capacity']= fnode.neighbor_traffic[fnode_nbr]
                    demand_id += 1
    return demand_c_dict
                

def print_demand_c_info(model_f, ampl_data_file):
    """
    Print capacity demand to the substrate link information in the 
    ample data file, in the form of:
    For example:
    param: demand_vn  	demand_fnode 	demand_src 	demand_dst demand_c    Pd:=
    1 		1 			2 			1 		4     0.21        3
    2 		1 			2 			1 		6     0.22        3
    3 		1 			2 			3 		4     0.23        3
    4		1 			2 			3 		6     0.24        3
    ........
    ;
    """
    demand_dict = get_demand_info(model_f)
    num_demand = len(demand_dict.keys())
    matrix_str = '\t\t\t'.join([str(1), str(demand_dict[1]['vn_id']), 
                               str(demand_dict[1]['fnode_id']),
                               str(demand_dict[1]['svr']),
                               str(demand_dict[1]['nbr_id']),
                               str(demand_dict[1]['capacity']), str(3)]) + '\n'
                               
    for index in range(2, num_demand + 1):
        temp_str = '\t' + '\t\t\t'.join([str(index), str(demand_dict[index]['vn_id']), 
                               str(demand_dict[index]['fnode_id']),
                               str(demand_dict[index]['svr']),
                               str(demand_dict[index]['nbr_id']),
                               str(demand_dict[index]['capacity']), str(3)]) + '\n'
        matrix_str += temp_str
    
    demand_param = """
    ## -- Define Substrate Link information --
    param D := {0};
    param: demand_vn    demand_fnode   demand_src   demand_dst  demand_c    Pd:=
    {1} \t;
    """.format(num_demand, matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(demand_param)
    fopen.close()
    return demand_dict
    
    
def find_slink_id(slink_dict, src, dst):
    """
    Given the src and dst substrate node id, find the substrate link id, 
    the input src and dst are source node Id and destination node id. 
    
    given: src < dst
    """    
    # in slink_dict, the node index starts from 0
    for slink_id in slink_dict:
        if slink_dict[slink_id]['src'] == src and slink_dict[slink_id]['dst'] == dst:
            return slink_id    
    
def paths_per_demand(paths_read, svr, nbr, slink_dict):
    """
    get the paths for a particular capacity demand between two substrate nodes
    paths_read is the array of lines read from a path file
    """
    path_dict = {}
    for line in paths_read:
        p_strs = line.strip().split()
        d_pair = int(p_strs[3]), int(p_strs[4])
        if d_pair == (svr, nbr) or d_pair == (nbr, svr):
            path_id = int(p_strs[2].rstrip(':'))
            path_dict[path_id] = []
            path_track = p_strs[6].split('_')
            for index in range(0, len(path_track)-1):
                node_pair = (int(path_track[index]), int(path_track[index + 1]))
                src = min(node_pair)
                dst = max(node_pair)
                link_id = find_slink_id(slink_dict, src, dst)
                path_dict[path_id].append(link_id)
                #print "check", path_dict[path_id]
    if len(path_dict) == 1:
        path_dict[2] = path_dict[1]
        path_dict[3] = path_dict[1]
    #print "check 3", path_dict
    return path_dict
             

def get_path_info(path_file, demand_dict, slink_dict):
    """
    Get path information from csv file
    """
    fopen = open(path_file, 'r')
    lines = fopen.readlines()[2:]
    demand_path = {}
    for demand_id in demand_dict:
        svr = demand_dict[demand_id]['svr']
        nbr = demand_dict[demand_id]['nbr_id']
        #print svr, nbr
        path_dict = paths_per_demand(lines, svr, nbr, slink_dict)
        #print path_dict
        demand_path[demand_id] = path_dict
    return demand_path
        
def print_path(demand_path, ampl_data_file):
    """
    print the path information to ample data file, for example:
    set paths[1, 1] = 1,2,3;  # d_pair 1-4
    set paths[1, 2] = 4,5,6,7;  # d_pair 1-4
    set paths[2, 1] = 6,7;  # d_pair 1-6
    set paths[2, 2] = 1,2,9; # d_pair 1-6
    set paths[3, 1] = 3;  # d_pair 3-4
    ....
    """
    matrix_str = ' '.join(['set paths[1,1] = ', str(demand_path[1][1])[1:-1]]) + ';\n'
    
    for demand_id in demand_path:
        for path_id in demand_path[demand_id]:
            if demand_id == 1 and path_id == 1:
                pass
            else:
                temp_str = '\t' + ''.join(['set paths[', str(demand_id), ', ', 
                                           str(path_id), '] := ', 
                                           str(demand_path[demand_id][path_id])[1:-1]]) + ';\n'
                matrix_str += temp_str
    
    path_param = """
    ## -- Define path set --
    {0}
    """.format(matrix_str)
    
    fopen = open(ampl_data_file, 'a')
    fopen.write(path_param)
    fopen.close()
    
def print_link_path_param(model_f, ampl_data_file):
    """
    Print link, demand, and path parameters in the ampl data file
    """
    path_file = 'topo_info/path/%s-3path.txt' % model_f.snet_type
    
    slink_dict = print_slink_info(model_f, ampl_data_file)
    demand_dict = print_demand_c_info(model_f, ampl_data_file)
    demand_path = get_path_info(path_file, demand_dict, slink_dict)
    print_path(demand_path, ampl_data_file)
    return demand_path, slink_dict, demand_dict
    
    