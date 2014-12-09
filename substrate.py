# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 14:56:18 2013
This scripts is to create substrate router class
@author: xuanliu
"""
from __future__ import division
import random
import topo_type
import numpy
# class decraration
class PhyInface(object):
    ''' Physical inteface object '''
    def __init__(self, iface_id=0, link_bw=1, status=1):
    #def __init__(self, iface_id=0, link_bw=topo_type.geant_bw, status=0):
        ''' Initialize an interface: '''
        self.iface_id = iface_id
        # by default, the bandwidth unit is 'Gbps'， this is the given capacity
        self.link_bw = link_bw 
        self.status = status
        # the utilization of the bandwidth, initial value is 0%
        self.utilize = 0
        # this keeps changing
        self.avail_bw = link_bw
    
    def get_iface_info(self):
        ''' get iface information as a dictionary '''
        iface_info = {}
        iface_info['iface_id'] = self.iface_id
        iface_info['bb_bw'] = self.link_bw
        iface_info['status'] = self.status
        iface_info['avail_bw'] = self.avail_bw
        return iface_info
    
    def enable_iface(self):
        ''' Bring up the interface '''
        self.status = 1

    def disable_iface(self):
        ''' Turn off the interface '''
        self.status = 0
    
    def set_utilize(self, util):
        ''' set the bw that in use '''
        self.utilize = util
        #self.utilize = random.uniform(0,0.2)
        #print "set_utilize", self.utilize
    
    def update_avail_bw(self):
        ''' get available bandwidth '''
        #self.avail_bw = self.link_bw * (1 - self.utilize)
        self.avail_bw = self.avail_bw * (1 - self.utilize)
        #print "update_avail_bw", self.link_bw, self.avail_bw
        
    def get_status(self):
        ''' get interface information '''
        return self.status
        
    def get_bw(self):
        ''' get interface bw capacity '''
        return self.link_bw
    
    def update(self, status):
        ''' update iface status '''
        self.status = status
        
class Node(object):
    ''' Physical(substrate) Node object '''
    def __init__(self, node_id, status=0, num_iface=10):
        ''' Initialize a substrate node'''
        self.node_id = node_id
        # maximum of VMs is self.cpu-1
        self.cpu = 16
        # self.ram = 64
        # the utilization of the cpu, value is between 0 ~ 1
        self.cpu_usage = 0
        # the utilization of the memory, value is between 0 ~ 1
        #self.ram_usage = 0
        self.num_iface = num_iface
        self.iface_list = []
        # neighbor list is a list of tuple (neighbor_id, iface_id)
        self.neighbors = []
        self.geoinfo = (0.0, 0.0)
        self.total_avail_bw = 0

    def find_iface2neighbor(self, neighbor_id):
        """
        find the interface id that connects to the node's neighbor
        """
        for pair in self.neighbors:
            if neighbor_id in pair:
                return pair[1]
                
        
    def set_neighbors(self, neighbor_list):
        """
        Set a list of neighbors in terms of tuples (neighborID, ifaceId)
        """
        self.neighbors = neighbor_list
    
    def set_res_utilize(self):
        """
        set resource utilization (cpu & memory)
        """
        # at least run 1 physical CPU core in the substrate node
        self.cpu_usage = round(random.uniform(0, 1/self.cpu),5)
        #self.ram_usage = round(random.uniform(0.2, 0.5),4)
        return self.cpu_usage
    
    def set_total_avail_bw(self):
        """
        set the total avaialabe bandwidth at the node, only consider
        the connected interfaces. self.num_iface, this is applied for the 
        first time of adding a node to a topology
        """
        self.total_avail_bw = 1 * self.num_iface
        
        

    def get_node_info(self):
        ''' Get node information in the form of dictionary '''
        node_info = {}
        node_info['id'] = self.node_id
        node_info['cpu'] = self.cpu_usage
        #node_info['ram'] = self.ram_usage
        node_info['num_iface'] = self.num_iface
        node_info['neighbor'] = self.neighbors
        node_info['geoinfo'] = self.geoinfo
        node_info['sum_avail_bw'] = self.total_avail_bw
        node_info['ifaces'] = {}
        for iface in self.iface_list:
            node_info['ifaces'][iface.iface_id] = iface.get_iface_info()
        return node_info
        
    def set_geoinfo(self, lat, lon):
        """
        set geographical information: latitude, longitude
        """
        self.geoinfo = (lat, lon)

#    def set_total_avail_bw(self):
#        """
#        set the total available bw at the node,
#        according to the number of up interfaces
#        """
#        up_iface = self.get_upIface()
#        self.total_avail_bw = topo_type.I2_bw * len(up_iface)
        

        
    def add_phy_iface(self):
        ''' Configure the physical interfaces '''
        for index in range(self.num_iface):
            iface = PhyInface(index)
            iface.enable_iface
            # first add an interface, no utilization, so avail_bw = link_bw
            iface.update_avail_bw()
            self.iface_list.append(iface)
    

#    def get_upIface(self):
#        ''' Count the number of interfaces that are up '''
#        up_ifaces = []
#        for item in self.iface_list:
#            if item.status == 1:
#                up_ifaces.append(item)
#        return up_ifaces
#    
#    def get_downIface(self, up_ifaces):
#        ''' return the number'''
#        down_ifaces = set(self.iface_list) - set(up_ifaces) 
#        return list(down_ifaces)
#    
#    def find_iface(self, iface_list, target_id):
#        ''' find the target in the list '''
#        for item in iface_list:
#            if item.iface_id == target_id:
#                return item
#        
#    def update_iface_list(self, new_iface_list):
#        ''' udpate iface stats '''
#        for item in self.iface_list:
#            if item in new_iface_list:
#                temp = self.find_iface(new_iface_list, item.iface_id)
#                item.update(temp.status)
#                                
#    def enable_iface(self, iface_list, num):
#        ''' Enable the physical interface based on the physical topology '''
#        if num > len(self.iface_list):
#            return "The router does not have enough interfaces."
#        else:
#            up_ifaces = self.get_upIface()
#            down_ifaces = self.get_downIface(up_ifaces)
#            if num > len(down_ifaces):
#                return "The router does not have enough interfaces."
#            else:
#                pick_ifaces = random.sample(set(down_ifaces), num)
#                for item in pick_ifaces:
#                    item.status = 1
#                self.update_iface_list(pick_ifaces)
                
        
#    def update_total_avail_bw(self):
#        """
#        Get the total available bw at the physical node
#        """
#        up_iface = self.get_upIface()
#        self.total_avail_bw = 0
#        for iface in up_iface:
#            self.total_avail_bw = self.total_avail_bw + iface.avail_bw
        #print "total", self.total_avail_bw
        
                
# debug
                
def print_node_info(node_list):
    for node in node_list:
        print node.node_id, node.num_iface

# Topo: Create functions to generate csv file
def add_weights(graph, weights='equal'):
    """
    add weight to the graph edges
    """
    edges = graph.edges()
    if weights == 'equal':
        ''' Equal weights on the links '''
        for link in edges:
            nodeA, nodeB = link
            graph.add_edge(nodeA, nodeB, weight=1)
    elif weights == 'random':
        ''' Random assigning weights between 1 and 4 '''
        for link in edges:
            nodeA, nodeB = link
            link_weight = random.choice(range(1,5))
            graph.add_edge(nodeA, nodeB, weight=link_weight)
    #return graph

def topo_csv_gen(csv_filename, graph):
    """
    Create an csv file that presents the connectivity information in n-by-n
    matrix format, where n is the number of nodes in the network. If there
    is no link between node i and j, then the value is set as inf
    
    for example: a four node ring topology can be presented as
    inf 1   inf 1                   1 ----- 2
    1   inf 1   inf                 .       .
    inf 1   inf 1                   .       .
    1   inf 1   inf                 4 ----- 3
    """        
    # link weight information is in dict format
    link_weight = graph.edge
    num_nodes = len(graph.nodes())
    weight_matrix = []
    for index_i in range(0,num_nodes):
        sub_dict = link_weight[index_i]
        sub_matrix = []
        for index_j in range(0,num_nodes):
            if index_j in sub_dict.keys():
                sub_matrix.append(int(sub_dict[index_j]['weight']))
            else:
                sub_matrix.append(float("inf"))
            #print "sub", sub_matrix
        weight_matrix.append(sub_matrix)
        #print "total", weight_matrix
    numpy.savetxt(csv_filename, weight_matrix, delimiter=',')
    return weight_matrix      

def run():
    num_nodes = 3
    num_iface = 5
    
    node_list = []
    for index in range(num_nodes):
        node = Node(index, num_iface)
        node.conf_phy_iface()
        node.enable_iface(node.iface_list, 5)
        node_list.append(node)
        
    print_node_info(node_list)   
    return node_list
    
    
                
                
                
            
            
        