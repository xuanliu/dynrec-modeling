# -*- coding: utf-8 -*-

"""
Created on Fri Aug 23 14:56:18 2013
This scripts is to generate topology
@author: xuanliu
"""

import networkx as nx
import random
import topo_type
import topo_xml
import copy



TOPO_PATH = "/Users/xuanliu/Documents/projects/dynrec/modeling/formulation/dynrec-modeling/topology/"
def substrate_gen(snet_type='random', rand_topo_info = (10, 16)):
    ''' generate substrate network '''
    # create 10 nodes, with 14 edges, a fixed topology
    if snet_type == 'random':
        num_nodes, num_edges = rand_topo_info
        G = nx.dense_gnm_random_graph(num_nodes, num_edges, 3)
        G.remove_edge(0,7)
        G.remove_edge(6,9)
#    if snet_type == 'I2':
#        G = nx.Graph()
#        G.add_edges_from(topo_type.I2_topo.keys())
#    if snet_type == 'GEANT':
#        geant_ip = topo_type.geant_ip
#        geant_mapping, geant_geo = \
#            topo_type.relabel_nodeinfo(topo_type.geant_node_mapping, 
#                                       topo_type.geant_node_geoinfo, 
#                                       geant_ip)                                       
#        geant_link = topo_type.relabel_linkinfo(geant_ip, geant_mapping)
#        G = nx.Graph()
#        G.add_edges_from(geant_link.keys())
    if snet_type != 'random':
        
        xml_file = TOPO_PATH + snet_type + ".xml"
        print xml_file
        node_dict, link_dict, node_dict_new = topo_xml.run(xml_file)
        G = nx.Graph()
        G.add_edges_from(link_dict.values())
        
    return G
    
def vnet_gen(snet, num_standby, fixed_node):
    """
    Generate virtual topology
    Parameters: 
    snet: the substrate network topology
    num_standby: the number of standby routers requested by a customer
    """
    node_list = snet.nodes()

    
    # minimum number of vnodes in a virtual network has to be three, but do 
    # not need to use all of the virtual nodes excluding the reserved standby 
    # virtual routers.     
    # In order to make sure every VN has a VR from a common substrate node, first remove the fixed node from the list
    rest_list = copy.deepcopy(node_list)
    rest_list.remove(fixed_node)
    vnode_in_topo = random.randint(3, len(rest_list) - num_standby)

    #vnode_in_topo = random.randint(5, len(rest_list) - num_standby)
    #vnode_in_topo = 100
    vnet_nodes = random.sample(set(rest_list), vnode_in_topo)
    vnet_nodes.append(fixed_node)
    rand_vnet = nx.gnp_random_graph(len(vnet_nodes), 0.3)
    # Avoid to create VNs with isolatd VRs
    check = check_degree(rand_vnet)
    while(check != 1):
        rand_vnet = nx.gnp_random_graph(len(vnet_nodes), 0.3)
        check = check_degree(rand_vnet)
    # relabel the nodes in the VN
    vnet = conf_vnet(rand_vnet, vnet_nodes)
    # remove selfloop edges
    vnet.remove_edges_from(vnet.selfloop_edges())
    return vnet
    
    
    

def check_degree(rand_vnet):
    """
    check whether a created network has zero degree node
    """
    check = 1
    degree_dict = rand_vnet.degree()
    if 0 in degree_dict.values():
        check = 0
    return check

def conf_vnet(vnet, vnet_nodes):
    """ 
    Match the node label in the random generated virtual network
    """ 
    mapping = {}
    for index in range(len(vnet_nodes)):
        mapping[vnet.nodes()[index]] = vnet_nodes[index]
    vnet_relabeled = nx.relabel_nodes(vnet, mapping)
    #print mapping
    return vnet_relabeled
    
    

    