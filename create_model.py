# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 22:06:37 2014

This script is to create a model that provide failure cases to generate 
ampl data file

Most of the functions are the same as the DRCN paper model creation, 
the differences are the way of creating virtual interfaces and the way 
to compute residual bandwidths on each physical interface.

The CPU utilization is given by a uniform distribution between 0 ~ 1, 
The residual bw on a phsyical interface is also given a uniform distribution
between 0 ~ 1. 



@author: xuanliu
"""
from __future__ import division
import sys
import random
import networkx as nx
import topo_gen
#import topo_type
import substrate
import virtual_network as vn
import ampl_gen
import shutil
import topo_xml
import heuristic_obj

from copy import deepcopy
from optparse import OptionParser


class reconf_model(object):
    """
    A model class that gives a specific failure states of a 
    virtualized network environment. 
    """
    def __init__(self):    
        """
        Initialize a model by giving the basic components information
        1. the number of substrate nodes
        2. Create an graph object for substrate network
        3. initialize an empty list of virtual network
        4. Initialize an empty dictionary for failed nodes in multiple virtual
        networks
        5. initialize the substrate network type
        6. initialize the cost dictionay
        6. initialize the number of standby virtual router in each vnet
        """
        self.snet_nodes = []
        self.snet_topo = nx.Graph()
        self.vnets = []
        self.failed_dict = {}
        self.snet_type = ''
        self.cost_dict = {}
        self.num_standby = 0

    def set_cost_dict(self, cost_info_dict):
        """
        set the cost information to the model
        """
        self.cost_dict = cost_info_dict
        
        
    def create_snet(self, snet_type='geant'):
        ''' create substrate network topology '''
        self.snet_topo = topo_gen.substrate_gen(snet_type)
        self.snet_type = snet_type

    def create_snodes(self):
        """
        Create substrate nodes with activated physical interfaces
        The number of activated physical interfaces depends on the number
        of neighbors a substarte node has. 
        This will help to generate the parameter b[i,p] in the ampl data
        file
        """
        #snode_id_list = self.snet_topo.nodes()
        # get a list of nodes with a list of their neighbors
        node_neighbor_tuple = [(n,nbrdict) for n,nbrdict in \
                        self.snet_topo.adjacency_iter()]
        for pair in node_neighbor_tuple:
            node_id = pair[0]
            num_iface = len(pair[1])
            neighbors = pair[1].keys()
            neighbor_list = []
            index = 0
            for item in neighbors:
                neighbor_list.append((item, index))
                index = index + 1
            new_node = substrate.Node(node_id, 0, num_iface)
            new_node.set_neighbors(neighbor_list)
            new_node.add_phy_iface()
            new_node.set_total_avail_bw()
            self.snet_nodes.append(new_node)
        #self.set_snodes_curr_bw()        
        
    def find_shotestpath(self,src=None, dst=None):
        """
        find the shortest path, in order to change the residual 
        capacity on the physical interface of each substrate node 
        after creating a virtual network
        """
        path_nodes = nx.shortest_path(self.snet_topo, src, dst)
        return path_nodes
                       
    def find_remote_onpath(self, path_nodes, node):
        """
        given a node id, find its neighbors on the path
        """
        neighbor_list = []
        for index in range(len(path_nodes)):
            if path_nodes[index] == node:
                if index == 0:
                    neighbor_list.append(path_nodes[index + 1])
                elif index == len(path_nodes) - 1:
                    neighbor_list.append(path_nodes[index - 1])
                else:
                    neighbor_list.append(path_nodes[index - 1])
                    neighbor_list.append(path_nodes[index + 1])
        return neighbor_list
                
    # Internet2 Node Geolocation information
    def set_node_geoloc(self):
        ''' Set up the geolocation for the substratenodes '''
        for node in self.snet_nodes:
#            if self.snet_type == 'I2':
#                lat, lon = topo_type.I2_node_geoinfo[node.node_id]
#            elif self.snet_type == 'GEANT':
#                geant_ip = topo_type.geant_ip
#                geant_mapping, geant_geo = \
#                topo_type.relabel_nodeinfo(topo_type.geant_node_mapping, 
#                                       topo_type.geant_node_geoinfo, 
#                                       geant_ip)
#                lat, lon = geant_geo[node.node_id]
            #elif self.snet_type == 'geant':
            if self.snet_type != 'random':
                xml_file = "topology/" + self.snet_type + ".xml"
                node_dict, link_dict, node_dict_new = topo_xml.run(xml_file)
                lat, lon = node_dict_new[node.node_id]
            node.set_geoinfo(lat, lon)    
            

    def set_res_util(self):
        """
        set cpu utilization for physical router
        """
        for node in self.snet_nodes:
            node.set_res_utilize()
            
    def add_vnet(self, max_standby, min_standby, req_bw, vn_id, fixed_node):
        """
        Create a virtual network on the substrate network, by reserving 
        a maximum number of standby virtual router as a initial state. 
        Then the virtual netwok will start reserving a given minimum number
        of standby router
        """
        new_vnet = vn.vnet([],vn_id)
        new_vnet.vtopo = topo_gen.vnet_gen(self.snet_topo, max_standby, fixed_node)
        for node in self.snet_nodes:
            new_usage = round(random.uniform(0, 1/node.cpu),4)
            node.cpu_usage = node.cpu_usage + new_usage
        self.conf_vnet_node(new_vnet, req_bw)
        self.get_vnet_standbys(new_vnet, min_standby)
        self.vnets.append(new_vnet)
    
    
    def conf_vnet_node(self, new_vnet, req_bw):
       """
       configure the virtual router with specific initial configurations
       set all connected routers' status as 1, others are 0, including standby
       routers
       """
       num_viface = len(self.snet_nodes)
       for snode in self.snet_nodes:
           new_vnode = vn.virtual_node(snode.node_id, 0, num_viface)
           new_vnode.set_iface_bw(req_bw)
           new_vnode.conf_viface()
           # if a virtual node is created from a substrate ndoe (has equal id)
           if snode.node_id in new_vnet.vtopo.nodes():
               new_vnode.set_status(1)
               new_vnode.vneighbors = new_vnet.vtopo.adj[snode.node_id].keys()
               new_vnode.enable_iface(new_vnode.viface_list, 
                                      len(new_vnode.vneighbors))
           else:
               # the vnode in status 0 are not connected, it could be either 
               # non-active vnodes or standby vnodes
               new_vnode.set_status(0)  
           new_vnet.vnodes.append(new_vnode)
                   
    def get_vnet_standbys(self, vnetwork, num_standby):
        """
        return a list of standby node objets in the virtual network
        this function is called when a virtual network is first created
        Once a standby router is reserved, it is removed from the 
        nonactivated node list, and its status is set as 2
        """
        for node in vnetwork.vnodes:
            if node.status == 0:
                vnetwork.nonactive_vnodes.append(node)
        vnetwork.standby_vnodes = random.sample(vnetwork.nonactive_vnodes, 
                                                num_standby)
        for standby in vnetwork.standby_vnodes:
            standby.set_status(2)
            vnetwork.nonactive_vnodes.remove(standby)
        
    def add_standby(self, diff_standby):
        """
        This function is to add more standby virtal routers to each 
        of current virtual networks, without changing other status
        """
        new_svr_dict = {}
        for vnet in self.vnets:
            new_svr_list = []
            new_standby = random.sample(vnet.nonactive_vnodes, diff_standby)
            #print new_standby[0].vnode_id
            #print "# of new added: ", len(new_standby)
            for new in new_standby:
                new.set_status(2)
                vnet.nonactive_vnodes.remove(new)
                #print "NOW: Nonactive: ", len(vnet.nonactive_vnodes)
                vnet.standby_vnodes.append(new)
                new_svr_list.append(new.vnode_id)
            #standby_list = vnet.get_standby_ids()
            #print "new standby list: ", standby_list
            new_svr_dict[vnet.vnet_id] = new_svr_list
        #print "new added: ", new_svr_dict
        return new_svr_dict
        # check vnet status -- for debug
        #for vnet in self.vnets:
        #    for standby in vnet.standby_vnodes:
        #        print vnet.vnet_id, standby.vnode_id, standby.status, ";"

    def add_standby2(self, new_svr_dict):
        """
        This function is to add more standby virtal routers to each 
        of current virtual networks, without changing other status
        """
       
        for vnet in self.vnets:
            #print "NON active: ", len(vnet.nonactive_vnodes)
            new_standby = new_svr_dict[vnet.vnet_id]
            #standby_list = vnet.get_standby_ids()
            #print "this model standby list: ", standby_list
            #print "new model svr: ", new_standby
            #print new_standby[0].vnode_id
            #print "# of new added: ", len(new_standby)
            for new_id in new_standby:
                new = vnet.vnodes[new_id]
                new.set_status(2)
                vnet.nonactive_vnodes.remove(new)
                #print "NOW: Nonactive: ", len(vnet.nonactive_vnodes)
                vnet.standby_vnodes.append(new)
           
                   
        
    def snapshot_cpu_util(self):
        """
        Take a snapshot of physical resource utilization at the failure, 
        which the dynamic reconfiguration is based on
        Assume each VR runs 1 CPU core at maximum, so 1/self.snet_ndoes[nodeid].cpu
        """
        for vnet in self.vnets:
            vnet_info = vnet.get_vnet_info()
            vnode_up = vnet_info['up_nodes']
            for nodeid in vnode_up:
                self.snet_nodes[nodeid].cpu_usage += \
                    round(random.uniform(0, 1/self.snet_nodes[nodeid].cpu),5)
        
    def snapshot_bw_util(self):
        """
        Take a snapshot of physical link bandwith usage at the failure,
        Based on the virtual link connections and determin the traffic on 
        the physical links
        """              
        for vnet in self.vnets:
            vnet_info = vnet.get_vnet_info()
            vtopo = vnet_info['topo']
        
            for link in vtopo:
                src, dst = link
                snet_path_nodes = self.find_shotestpath(src, dst)
                
                # the traffic along the path should be the same
                link_usage = round(random.uniform(0,0.01), 5)
                vnet.set_traffic(src, dst, link_usage)
                vnet.set_traffic(dst, src, link_usage)
                for node_id in snet_path_nodes:
                    neighbor_list = self.find_remote_onpath(snet_path_nodes, 
                                                            node_id)
                    if snet_path_nodes.index(node_id) == 0:
                        neighbor_id = neighbor_list[0]
                        iface_id = self.snet_nodes[node_id].find_iface2neighbor(neighbor_id)
                        link_usage = round(random.uniform(0,0.01), 5)
                        #print "start: ", link_usage
                        self.snet_nodes[node_id].iface_list[iface_id].set_utilize(link_usage)
                        self.snet_nodes[node_id].iface_list[iface_id].update_avail_bw()
                        self.snet_nodes[node_id].total_avail_bw -= link_usage
                        #check = link_usage
                    elif snet_path_nodes.index(node_id) < len(snet_path_nodes) - 1:
                        iface_id1 = self.snet_nodes[node_id].find_iface2neighbor(neighbor_list[0])
                        self.snet_nodes[node_id].iface_list[iface_id1].set_utilize(link_usage)
                        self.snet_nodes[node_id].iface_list[iface_id1].update_avail_bw()
                        self.snet_nodes[node_id].total_avail_bw -= link_usage
                        iface_id2 = self.snet_nodes[node_id].find_iface2neighbor(neighbor_list[1])
                        #link_usage = round(random.uniform(0,0.01), 5)
                        #print "one iface:", check
                        self.snet_nodes[node_id].iface_list[iface_id2].set_utilize(link_usage)
                        self.snet_nodes[node_id].iface_list[iface_id2].update_avail_bw()
                        self.snet_nodes[node_id].total_avail_bw -= link_usage
                        #print "other iface:", check
                    else:
                        iface_id1 = self.snet_nodes[node_id].find_iface2neighbor(neighbor_list[0])
                        self.snet_nodes[node_id].iface_list[iface_id1].set_utilize(link_usage)
                        self.snet_nodes[node_id].iface_list[iface_id1].update_avail_bw()
                        self.snet_nodes[node_id].total_avail_bw -= link_usage
                        #print "last: ", check


    def get_snet_info(self):
        """ 
        Get substrate network inforamtion in the form of embedded dictionary
        First level key: node_id, value: 
        node attributes(cpu, ram, num_iface, etc.)
        a sub-library for interface information
        Second level key: iface_id, value: iface attributes (bw, status, etc.)
        """
        snet_info = {}
        for node in self.snet_nodes:
            snet_info[node.node_id] = {}
            snet_info[node.node_id] = node.get_node_info()
        return snet_info

    def get_vnet_info(self):
        """
        Get virtual network information:
            virtual router status
        """
        vnet_info = {}
        for vnet in self.vnets:
            vnet_info[vnet.vnet_id] = vnet.get_vnet_info()
        return vnet_info

    def check_no_failure(self, failed_dict):
        """
        For study purpose, we want to make sure at least one 
        virtual network has virtual router failure.
        This function is only called when random failure occurs 
        in virtual networks
        """
        failed_ids = failed_dict.values()
        if failed_ids.count(-1) == len(failed_dict):
            return 0
        else:
            return 1


    def get_common_nodes(self):
        """
        find the substrate nodes that are used in all virtual topologies as 
        active virtual routers.
        Find the intersection of multiple sets. 
        """
        vnet_info = self.get_vnet_info()
        set_list = []
        for vnet in vnet_info:
            up_nodes = vnet_info[vnet]['up_nodes']
            set_list.append(set(up_nodes))
        common_nodes = set.intersection(*set_list)
        return list(common_nodes)              

    def set_sfailure(self):
        """
        Called by adjust_failure()
        set failure type: substrate failure or virtual network failure
        input ftype = 's' or 'v'
        
        ftype = 's': substrate failure. Randomly selects a substrate node,
        and each virtual router with the same id has to be marked as 
        failed(-1). Currently, only consider single substrate router failure.
        
        ftype = 'v': virtual network failure. Randomly generate failures in
        each virtual networks, the number of failures can be any 
        non-negative integer. Only consider single virtual router failure
        """
#        if ftype == 's':
        failed_dict = {}
        #snodes = self.snet_nodes
        #fsnode = random.choice(snodes)
        common_nodes = self.get_common_nodes()
        fsnode = random.choice(common_nodes)
        for vnet in self.vnets:
            vnodes = vnet.vnodes
            vstandby_list = vnet.get_standby_ids()
            #print vstandby_list
            if fsnode not in vstandby_list:
                failed_dict[vnet.vnet_id] = fsnode
            for vnode in vnodes:
                if vnode.vnode_id == fsnode:
                    vnode.set_status(-1)
                    #print "virtual network ", vnet.vnet_id, "failed ", vnode.vnode_id
                    break
        return failed_dict
#        if ftype == 'v':
#            failed_dict = {}
#            
#            vnet_subset = random.sample(self.vnets, num_failure)
#            #print "sub-set size", len(vnet_subset)
#            for vnet in self.vnets:
#                if vnet in vnet_subset:
#                    #print vnet.vnet_id
#                    fvnode_id = vnet.random_fail(1) #single failure
#                    #print "failed vr is ", fvnode_id
#                    if fvnode_id != -2: # in current scenario, only one failure
#                        for vnode in vnet.vnodes:
#                            if vnode.vnode_id == fvnode_id:
#                                vnode.set_status(-1)
#                                #print "virtual network＃", vnet.vnet_id, "failed vr#", vnode.vnode_id
#                                failed_dict[vnet.vnet_id] = fvnode_id
#                                break 
#                else: 
#                    fvnode_id = -1  # there is no failure
#                    failed_dict[vnet.vnet_id] = fvnode_id
#                    pass
#            return failed_dict
            
    def set_vfailure(self, num_failure=1, fail_record=None):
        """
        Called by adjust_failure()
        set failure type: substrate failure or virtual network failure
        input ftype = 's' or 'v'
        
        ftype = 's': substrate failure. Randomly selects a substrate node,
        and each virtual router with the same id has to be marked as 
        failed(-1). Currently, only consider single substrate router failure.
        
        ftype = 'v': virtual network failure. Randomly generate failures in
        each virtual networks, the number of failures can be any 
        non-negative integer. Only consider single virtual router failure
        
        fail_record is in form of [(<vnet_id, fail_id>), ...]
        """
#        if ftype == 's':
#            failed_dict = {}
#            #snodes = self.snet_nodes
#            #fsnode = random.choice(snodes)
#            common_nodes = self.get_common_nodes()
#            fsnode = random.choice(common_nodes)
#            for vnet in self.vnets:
#                vnodes = vnet.vnodes
#                vstandby_list = vnet.get_standby_ids()
#                #print vstandby_list
#                if fsnode not in vstandby_list:
#                    failed_dict[vnet.vnet_id] = fsnode
#                for vnode in vnodes:
#                    if vnode.vnode_id == fsnode:
#                        vnode.set_status(-1)
#                        #print "virtual network ", vnet.vnet_id, "failed ", vnode.vnode_id
#                        break
#            return failed_dict
#        if ftype == 'v':
        failed_dict = {}
        #print "sub-set size", len(vnet_subset)
        
        
        #print "num_faliure", num_failure, "current record", len(fail_record)
        if fail_record != [] and num_failure > len(fail_record):
            for item in fail_record:
                vnet_id = item[0]
                fail_vr = item[1]
                self.vnets[vnet_id - 1].vnodes[fail_vr].set_status(-1)
                #print "virtual network＃", vnet_id, "failed vr#", fail_vr
                failed_dict[vnet_id] = fail_vr
        elif fail_record != [] and num_failure <= len(fail_record):
            #print "new round", fail_record
            for item in fail_record:
                #print item
                vnet_id = item[0]
                fail_vr = item[1]
                self.vnets[vnet_id - 1].vnodes[fail_vr].set_status(-1)
                failed_dict[vnet_id] = fail_vr
                #print "vnet_id", vnet_id, "num_failrue", num_failure
                if vnet_id > num_failure:
                    failed_dict[vnet_id] = -1
            return failed_dict, fail_record
     
        
        new_failure = num_failure - len(failed_dict)
        #print "new failure", new_failure
        if fail_record == [] or new_failure > 0:
            # new failure needs to be added
            #print "Start"
            for vnet in self.vnets:
                if vnet.vnet_id not in failed_dict and new_failure > 0:
                    fvnode_id = vnet.random_fail(1)
                    if fvnode_id != -2:
                        vnet.vnodes[fvnode_id].set_status(-1)
                        failed_dict[vnet.vnet_id] = fvnode_id
                        #print "virtual network＃", vnet.vnet_id, "failed vr#", fvnode_id
                        fail_record.append((vnet.vnet_id, fvnode_id))
                        new_failure -= 1
                    else:
                        failed_dict[vnet.vnet_id] = -1
                elif new_failure == 0 and vnet.vnet_id not in failed_dict:
                    failed_dict[vnet.vnet_id] = -1
                else:
                    pass
        
                
        return failed_dict, fail_record
                                    

#def add_standby(model, diff=1):
#    """
#    create a new model that has changed the standby
#    """

def adjust_failure_s(model, num_failure):
    """
    This function is used to adjust failure types and numbers
    ftype reprentes the failure type is a virtual failure or a physical failure
    num_failure is the total number failed virtual network
    If ftype = 's', num_failure takes default value 1
    If ftype = 'v', num_failure takes the maximum values as the number of 
    virtual networks, as we consider only single virtual router failure in each
    virtual networks.
    """
    model_f = deepcopy(model)
    #num_failure = 1
#    if ftype == 'v':
#        failed_dict = model_f.set_failure2(ftype, num_failure)
#        check = model_f.check_no_failure(failed_dict)
#        while not check:
#            failed_dict = model_f.set_failure2(ftype)
#            check = model_f.check_no_failure(failed_dict)
#        model_f.failed_dict = failed_dict
#    if ftype == 's':
    failed_dict = model_f.set_sfailure()
    model_f.failed_dict = failed_dict   
    #snet_info = model.get_snet_info()
    #vnet_info = model.get_vnet_info()
    return model_f
 

def adjust_failure_v(model, num_failure, failure_record):
    """
    The function is used to create failures to the virtual network
    The inputs are:
    model: the original model generated
    ftype: failure type
    num_failures: the total number of failures
    failure_record: the record of failed vrs in the previous scenario with
    (num_failure - 1). This is to provide a garantee that the new scenario is 
    created based on the previous scenario, that has the VNs has the same 
    failed VRs, and then generate a new failure.
    """
    model_f = deepcopy(model)
   
    failed_dict, fail_record = model_f.set_vfailure(num_failure, failure_record)
    model_f.failed_dict = failed_dict
#    if ftype == 's':
#        failed_dict = model_f.set_failure2(ftype)
#        model_f.failed_dict = failed_dict
    return model_f, fail_record

def dryrun():
    """
    For Debug
    """
    num_vnet = 2
    max_standby = 6
    min_standby = 4
    req_bw = 0.01
    fail_type = 'v'
    ampl_data = 'lp_test1.dat'
    mat_file = 'lp_test1.mat'
    standby_limit = num_vnet
    # Create a new model
    model = reconf_model()
    # Create substrate network
    model.create_snet('abilene') 
    substrate.add_weights(model.snet_topo)
    
    model.create_snodes()
    model.set_node_geoloc()
    model.set_res_util()
    #model.num_standby = 3
    heuristic_obj_file = 'abilene' + "-" + fail_type + \
                        "-" + str(num_vnet) + ".txt"
    fopen = open(heuristic_obj_file, 'w')
    fopen.write("Heuristic Obj Values \n")
    fopen.close()
    random.seed(37)
    #create virtual networks
    fixed_node = random.choice(model.snet_topo.nodes())
    vnet_id = 1
    #seed_list = [23,59,101,239,383,499,617,701,823,919]
    while vnet_id <= num_vnet:
        #req_standby = random.randint(3, max_standby)
        #print vnet_id, num_vnet
        model.add_vnet(max_standby, min_standby, req_bw, vnet_id, fixed_node)
        vnet_id = vnet_id + 1 
        
    
    model.snapshot_cpu_util()
    model.snapshot_bw_util()
    
    snet_info = model.get_snet_info()
    cost_dict = ampl_gen.run(model, snet_info, ampl_data, mat_file) 
    model.set_cost_dict(cost_dict)
    
    
    if standby_limit == 'inf' or standby_limit == 'rand':
        ampl_gen.change_limits(model, ampl_data, standby_limit)
    else:
        pass
    num_vp = len(model.snet_nodes)
   
       
    w_b_list = [(1,0)]
    theta_list = [(0,1,0)]#,(0,0,1),(0,0.02,0.98)]
    w_a_list = [(0.2, 0.8)]#[(0.8,0.2),(0.2,0.8)]
    # Change number of failures from 1 to the total number of vnet
    if fail_type == 'v':
        # change the number of standby
        fail_record = []
        for num_svr in range(min_standby, max_standby+1, 2):
            model.num_standby = num_svr
            # change the number of failures
            
            for num_failure in range(1,num_vnet + 1):
                #model_f = adjust_failure(model, fail_type, num_failure)
                model_f, fail_record = adjust_failure_v(model, num_failure, fail_record)
                              
                if standby_limit != 'inf' and standby_limit != 'rand':
                    # change the limit of standby
                    for limit in range(standby_limit, int(standby_limit) + 1, 1):
                        limit_ext = str(limit)
                        (fname, part, ext) = ampl_data.partition('.')
                        # changing weight parameters
                        for w_a in w_a_list:
                            w_a1, w_a2 = w_a
                            for w_b in w_b_list:
                                w_b1, w_b2 = w_b
                                for theta in theta_list:
                                    theta1, theta2, theta3 = theta
                                    # generate data file name            
                                    new_datafile = fname + "_" + str(num_svr) + "_" + \
                                         str(w_a1) + "_" + str(w_a2) + "_" + \
                                         str(w_b1) + "_" + str(w_b2) + "_" + \
                                         str(theta1) + "_" + str(theta2) + "_" + \
                                         str(theta3) + "_" + \
                                         limit_ext + "_" + \
                                         str(num_failure) + "_fail.dat"
                                    shutil.copyfile(ampl_data, new_datafile)
                                    #print min_standby, model_f.num_standby    
                                    ampl_gen.change_standby_num(model, new_datafile, min_standby, model_f)
                                    min_standby = num_svr
                                    
            
                                    ampl_gen.change_weight(w_a, w_b, 
                                                           theta, 
                                                           new_datafile)
                                    ampl_gen.change_limits(model_f, 
                                                           new_datafile, 
                                                           limit_ext)
                                    #print "print c"
                                    failed = ampl_gen.adjust_run(model_f, 
                                                                  snet_info, 
                                                                  num_vp, 
                                                                  new_datafile)
                                    # print link-path parameter in the ampl data file
                                    demand_path, slink_dict, demand_dict = ampl_gen.print_link_path_param(model_f, new_datafile)
                                    calc_obj, select_dict, max_r, used_time = heuristic_obj.get_obj_new(model_f, demand_path, slink_dict, demand_dict,
                                                                     w_a, 
                                                                     w_b, 
                                                                     theta, 
                                                                     limit)
#                                    calc_obj, select_dict, max_r, used_time = heuristic_obj.get_obj(model_f,
#                                                                     w_a, 
#                                                                     w_b, 
#                                                                     theta, 
#                                                                     limit)
                                    #print new_datafile, calc_obj
                                    fopen = open(heuristic_obj_file, 'a')
                                    fopen.write(new_datafile + ', ' + \
                                                str(calc_obj) + ', ' + \
                                                str(used_time) + ',' + \
                                                str(max_r) + ', ' + \
                                                str(select_dict) +'\n')
    #return model
                else:
                    (fname, part, ext) = ampl_data.partition('.')
                    new_datafile = fname + "_" + standby_limit + "_" + str(num_failure) + "fail.dat"
                    shutil.copyfile(ampl_data, new_datafile)
                    model_f = adjust_failure_s(model, num_failure)
                    failed = ampl_gen.adjust_run(model_f, 
                                          snet_info, 
                                          num_vp, 
                                          new_datafile)
                    print failed
    
    return model, model_f, demand_path, slink_dict, demand_dict
    
    




def create_option(parser):
    """
    add the options to the parser:
    takes arguments from commandline
    """
    parser.add_option("-v", action="store_true",
                      dest="verbose",
                      help="Print output to screen")
    parser.add_option("-n", dest="num_vnet",
                      type="int",
                      default=1,
                      help="The number of virtual network to be creatd")
    parser.add_option("--bw", dest="req_bw", 
                      type="float",
                      default=2,
                      help="the bandwidth requested for the virtual links")
    parser.add_option("--maxstandby", dest="max_standby",
                      type="int",
                      default=3,
                      help="the maximum number of standby router \
                      are allowed to be reserved  \
                      for each virtual network")
    parser.add_option("--minstandby", dest="min_standby",
                      type="int",
                      default=3,
                      help="the minimum number of standby router \
                      are allowed to be reserved  \
                      for each virtual network")
    parser.add_option("-f", dest="ampl_data",
                      type="str",
                      default="dyn.dat",
                      help="create the ampl data file based on the model")
    parser.add_option("-m", dest="mat_file",
                      type="str",
                      default="dyn.mat",
                      help="create .mat file for cost matrix")
    parser.add_option("--type", dest="snet_type", 
                      type="str",
                      default='geant',
                      help="substrate netwok type")
    parser.add_option("--ftype", dest="fail_type",
                      type="str",
                      default='v',
                      help="failure type: substrate router failiure (s)\
                      or virtual router failure (v)")
    parser.add_option("--limit", dest="standby_limit",
                      type="str",
                      default='inf',
                      help="The limit on the maximum number of standby virtual \
                      routers can be selected from a host")
    parser.add_option("--seed", dest="seed_value",
                      type="int",
                      default='37',
                      help="initial seed")
                   
                      
def run(argv=None):
    """
    Create a template model with fixed configuration.
    Genrate a template ampl data file for furthur changes
   
    Inputs are:
        -n number of virtual networks
        --bw the requested bw for each virtual interface (normalized): 0.01
        --standby the maximum number of standby virtual routers 
        -f ampl data file to be created
        -m the mat data file storing the resource information
        --ftype the failure type ('s' or 'v')
        --type the type of substrate network topology
    """
    if not argv:
        argv=sys.argv[1:]
    usage = ("%prog [-v verbose] \
                    [-n num_vnet] \
                    [-bw req_bw] \
                    [-maxstandby max_standby]\
                    [-minstandby min_standby] \
                    [-f ampl_data] \
                    [-m mat_file] \
                    [--type snet_type] \
                    [--ftype fail_type] \
                    [--limit standby_limit] \
                    [--seed seed_value]")
    parser = OptionParser(usage=usage)
    create_option(parser)
    (options, _) = parser.parse_args(argv)
    num_vnet = options.num_vnet
    req_bw = options.req_bw
    max_standby = options.max_standby
    min_standby = options.min_standby
    ampl_data = options.ampl_data
    mat_file = options.mat_file
    snet_type = options.snet_type
    fail_type = options.fail_type
    standby_limit = options.standby_limit
    seed_value = options.seed_value

    
    heuristic_obj_file = snet_type + "-" + fail_type + \
                        "-" + str(num_vnet) + ".txt"
    fopen = open(heuristic_obj_file, 'w')
    fopen.write("Heuristic Obj Values \n")
    fopen.close()
    random.seed(seed_value)
    
    model = reconf_model()
    # Create substrate network
    model.create_snet(snet_type)    
    model.create_snodes()
    model.set_node_geoloc()
    model.set_res_util()
    
    #create virtual networks
    # fake a fixed node to be failed 
    fixed_node = random.choice(model.snet_topo.nodes())
    vnet_id = 1
    while vnet_id <= num_vnet:
        model.add_vnet(max_standby, min_standby, req_bw, vnet_id, fixed_node)
        vnet_id = vnet_id + 1 
    
    # Take a snapshot of CPU and BW utilization
    model.snapshot_cpu_util()
    model.snapshot_bw_util()
    
    
    snet_info = model.get_snet_info()
    cost_dict = ampl_gen.run(model, snet_info, ampl_data, mat_file) 
    model.set_cost_dict(cost_dict)
    if standby_limit == 'inf' or standby_limit == 'rand':
        ampl_gen.change_limits(model, ampl_data, standby_limit)
    else:
        pass
    num_vp = len(model.snet_nodes) 
    
    #w_a_list = [(1, 0), (0.8, 0.2), (0.5, 0.5), (0.2, 0.8), (0, 1)]#[(0.5,0.5), (1, 0), (0, 1), (0.2, 0.8), (0.8, 0.2)]
    w_b_list = [(1,0)]#[(0.5,0.5), (1, 0), (0, 1), (0.2, 0.8), (0.8, 0.2)]
    #theta_list = [(0, 0, 1), (0, 0.1, 0.9), (0, 0.5, 0.5), (0,1,0)]#[(1, 0, 0), (0, 1, 0), (0, 0, 1), 
                  #(0.1, 0.2, 0.7), (0.1, 0.7, 0.2), (0.333, 0.333, 0.333)]
    theta_list = [(0,1,0),(0,0,1),(0,0.02,0.98)]
    w_a_list = [(0.2, 0.8)]#[(0.8,0.2),(0.2,0.8)]
    # Change number of failures from 1 to the total number of vnet
    if fail_type == 'v':
        # change the number of standby
        fail_record = []
        for num_svr in range(min_standby, max_standby+1, 2):
            model.num_standby = num_svr
            # change the number of failures
            
            for num_failure in range(1, num_vnet+1):
                #model_f = adjust_failure(model, fail_type, num_failure)
                model_f, fail_record = adjust_failure_v(model, num_failure, fail_record)
                              
                if standby_limit != 'inf' and standby_limit != 'rand':
                    # change the limit of standby
                    for limit in range(1, int(standby_limit) + 1, 2):
                        limit_ext = str(limit)
                        (fname, part, ext) = ampl_data.partition('.')
                        # changing weight parameters
                        for w_a in w_a_list:
                            w_a1, w_a2 = w_a
                            for w_b in w_b_list:
                                w_b1, w_b2 = w_b
                                for theta in theta_list:
                                    theta1, theta2, theta3 = theta
                                    # generate data file name            
                                    new_datafile = fname + "_" + str(num_svr) + "_" + \
                                         str(w_a1) + "_" + str(w_a2) + "_" + \
                                         str(w_b1) + "_" + str(w_b2) + "_" + \
                                         str(theta1) + "_" + str(theta2) + "_" + \
                                         str(theta3) + "_" + \
                                         limit_ext + "_" + \
                                         str(num_failure) + "_fail.dat"
                                    shutil.copyfile(ampl_data, new_datafile)
                                    #print min_standby, model_f.num_standby    
                                    ampl_gen.change_standby_num(model, new_datafile, min_standby, model_f)
                                    min_standby = num_svr
                                    
            
                                    ampl_gen.change_weight(w_a, w_b, 
                                                           theta, 
                                                           new_datafile)
                                    ampl_gen.change_limits(model_f, 
                                                           new_datafile, 
                                                           limit_ext)
                                    #print "print c"
                                    failed = ampl_gen.adjust_run(model_f, 
                                                                  snet_info, 
                                                                  num_vp, 
                                                                  new_datafile)
                                    demand_path, slink_dict, demand_dict = ampl_gen.print_link_path_param(model_f, new_datafile)
#                                    calc_obj, select_dict, max_r, used_time = heuristic_obj.get_obj(model_f,
#                                                                     w_a, 
#                                                                     w_b, 
#                                                                     theta, 
#                                                                     limit)
                                    calc_obj, select_dict, max_r, used_time = heuristic_obj.get_obj_new(model_f,
                                                                     demand_path,
                                                                     slink_dict,
                                                                     demand_dict,
                                                                     w_a, 
                                                                     w_b, 
                                                                     theta, 
                                                                     limit)                                
                            
                                    #print new_datafile, calc_obj
                                    fopen = open(heuristic_obj_file, 'a')
                                    fopen.write(new_datafile + ', ' + \
                                                str(calc_obj) + ', ' + \
                                                str(used_time) + ',' + \
                                                str(max_r) + ', ' + \
                                                str(select_dict) +'\n')
        #vnet_info = model_f.get_vnet_info()                                          
                    #print failed
                # infinite standby VRs
#                else:
#                    (fname, part, ext) = ampl_data.partition('.')
#                    new_datafile = fname + "_" + standby_limit + "_" + str(num_failure) + "fail.dat"
#                    shutil.copyfile(ampl_data, new_datafile)
#                    model_f = adjust_failure_v(model, fail_type, num_failure)
#                    failed = ampl_gen.adjust_run(model_f, 
#                                          snet_info, 
#                                          num_vp, 
#                                          new_datafile)
#                    print failed
                
              
    if fail_type == 's':
        num_failure = 1
        model_f = adjust_failure_s(model, num_failure)
        for num_svr in range(min_standby, max_standby+1, 2):
            model.num_standby = num_svr
            #for limit in range(1, int(standby_limit) + 1, 2):
            for limit in range(8, 10, 2):
                limit_ext = str(limit)
                (fname, part, ext) = ampl_data.partition('.')
                    # changing weight parameters
                for w_a in w_a_list:
                    w_a1, w_a2 = w_a
                    for w_b in w_b_list:
                        w_b1, w_b2 = w_b
                        for theta in theta_list:
                            theta1, theta2, theta3 = theta
                                # generate data file name            
                            new_datafile = fname + "_" + str(num_svr) + "_" + \
                                         str(w_a1) + "_" + str(w_a2) + "_" + \
                                         str(w_b1) + "_" + str(w_b2) + "_" + \
                                         str(theta1) + "_" + str(theta2) + "_" + \
                                         str(theta3) + "_" + \
                                         limit_ext + "_" + \
                                         str(num_failure) + "_fail.dat"
                            shutil.copyfile(ampl_data, new_datafile)
                            ampl_gen.change_standby_num(model, new_datafile, min_standby, model_f)
                            min_standby = num_svr
                            ampl_gen.change_weight(w_a, w_b, 
                                                           theta, 
                                                           new_datafile)
                            ampl_gen.change_limits(model_f, 
                                                           new_datafile, 
                                                           limit_ext)
                            failed = ampl_gen.adjust_run(model_f, 
                                                                  snet_info, 
                                                                  num_vp, 
                                                                  new_datafile)
                                               

                            demand_path, slink_dict, demand_dict = ampl_gen.print_link_path_param(model_f, new_datafile)
                            calc_obj, select_dict, max_r, used_time = heuristic_obj.get_obj_new(model_f,
                                                             demand_path,
                                                             slink_dict,
                                                             demand_dict,
                                                             w_a, 
                                                             w_b, 
                                                             theta, 
                                                             limit)                                                              
                            fopen = open(heuristic_obj_file, 'a')
                            fopen.write(new_datafile + ', ' + \
                                                str(calc_obj) + ', ' + \
                                                str(used_time) + ',' + \
                                                str(max_r) + ', ' + \
                                                str(select_dict) +'\n')
#        (fname, part, ext) = ampl_data.partition('.')
#        new_datafile = fname + "_" + str(num_failure) + "fail.dat"
#        shutil.copyfile(ampl_data, new_datafile)
#        failed = ampl_gen.adjust_run(model_f, 
#                                          snet_info, 
#                                          num_vp, 
#                                          new_datafile)
#        print failed
    fopen.close()   
        
if __name__ == '__main__':
    sys.exit(run())
