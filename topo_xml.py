# -*- coding: utf-8 -*-
"""
This module is to retreive information from a topology xml file
It returns a dictionary of node and links. It includes the nodes' geographical 
information and node ID. The link information is a list of tuples. 

The input is an xml file.

Created on Tue Apr  8 16:02:44 2014

@author: xuanliu
"""
  

import xml.etree.ElementTree as ET


def get_node_link(topo_xml):
    """
    read the topology xml file, and get the 
    node, link structure
    """
    topo_tree = ET.parse(topo_xml)
    root = topo_tree.getroot()
    #print root.getchildren()
    #children = root.getchildren()[1]
    children = find_netstruct(root)
    node_tree = children.getchildren()[0]
    link_tree = children.getchildren()[1]
    #print node_tree, link_tree
    return node_tree, link_tree

def find_netstruct(root):
    """
    Find the netwrok structrue block in the xml file
    """
    children = root.getchildren()
    for child in children:
        if 'networkStructure' in child.tag:
            return child
        if 'topology' in child.tag:
            return child

def get_node_dict(node_tree):
    """
    Create a dictionary about the ndoes
    The node dictionary has keys: id, name, lat, long
        
    <node id="at1.at">
    <coordinates>
     <x>16.3729</x> (longitude)
     <y>48.2091</y> (latitude)
    </coordinates>
   </node>
   
    """
    node_dict = {}
    node_id = 0
    for node in node_tree:
        node_name = node.attrib['id']
        node_dict[node_name] = {}
        node_dict[node_name]['id'] = node_id
        # coordinates y
        lat = node.getchildren()[0].getchildren()[1].text
        # coordinates x
        lon = node.getchildren()[0].getchildren()[0].text
        node_dict[node_name]['lat'] = lat
        node_dict[node_name]['lon'] = lon
        node_id += 1
    
    return node_dict
        
def get_link_info(link_tree, node_dict):
    """
    get the link information, as a list of tuples
    for example:
    links = [(1,2),(2,3),(1,3)]
    """          
    link_dict = {}
    link_id = 0
    for link in link_tree:
        link_info = link.getchildren()
        src = link_info[0].text
        dst = link_info[1].text
        #print src, dst
        
        src_id = node_dict[src]['id']
        dst_id = node_dict[dst]['id']
        #print src_id, dst_id
        link_dict[link_id] = (src_id, dst_id)
        link_id += 1
    return link_dict
        
def simplify_node_dict(node_dict):
    """
    simplify the node dictionary into:
    node_geoinfo = {0: (47.611877,-122.333561),
                   1: (34.169772,-118.126588),
                   2: (40.759481,-111.829689),
                   3: (39.11621,-94.57602),
                   4: (29.814434,-95.364504),
                   5: (41.893077,-87.634034),
                   6: (33.764878,-84.3909),
                   7: (38.918284,-77.03418),
                   8: (40.741014,-74.002748)}
    """
    new_dict = {}
    for node in node_dict:
        key = node_dict[node]['id']
        new_dict[key] = (float(node_dict[node]['lat']), 
                        float(node_dict[node]['lon']))
    return new_dict

def dryrun():
    """
    debug
    """
    topo_xml = "topology/att.xml"
    node_tree, link_tree = get_node_link(topo_xml)
    node_dict = get_node_dict(node_tree)
    link_dict = get_link_info(link_tree, node_dict)
    node_dict_new = simplify_node_dict(node_dict)
    return node_dict, link_dict, node_dict_new
    
def run(xml_file):
    """
    program wrapper
    """
    node_tree, link_tree = get_node_link(xml_file)
    node_dict = get_node_dict(node_tree)
    link_dict = get_link_info(link_tree, node_dict)
    node_dict_new = simplify_node_dict(node_dict)
    return node_dict, link_dict, node_dict_new
    
    