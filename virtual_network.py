# -*- coding: utf-8 -*-
"""
Created on Fri Aug 23 18:04:49 2013
This scripts is to create virtual router class
@author: xuanliu
"""

from substrate import PhyInface, Node
import networkx as nx
import random 


class virtual_iface(PhyInface):
    ''' virtual interface class that inherits from PhyInface class '''
    def __init__(self, viface_id, default_bw=0.1, status=0):
        ''' initialize virtual interface'''
        self.viface_id = viface_id
        self.default_bw = default_bw
        self.avail_bw = 0
        self.status = status
        self.utilize = 0
        self.used_bw = 0

    def get_avail_bw(self):
        ''' Get the available bandwidth '''
        self.avail_bw = (1 - self.utilize) * self.default_bw
    
    def set_utilize(self):
        ''' set the bw that in use '''
        self.utilize = random.uniform(0,1)
        #return self.utilize * self.avail_bw
    def get_used_bw(self):
        ''' get the bw that has been taken '''
        self.used_bw = self.utilize * self.default_bw
    

class virtual_node(Node):
    ''' virtual node class that inherits from Node class'''
    def __init__(self, vnode_id, status=0, num_viface=10):
        """
        Initialize virtual node object
        There are three status:
        0: offline
        1: online
        2: standby
        """
        self.vnode_id = vnode_id
        self.status = status
        self.num_viface = num_viface
        self.viface_list = []
        self.cpu = 0
        self.ram = 0
        self.iface_bw = 0.0
        self.vneighbors = []
        self.total_traffic = 0
        self.neighbor_traffic = {}
    
    def update_total_traffic(self, dst, volume):
        """
        set the total traffic 
        """
        self.total_traffic += volume
        self.neighbor_traffic[dst] = volume
        
        
    def set_cpu(self, cpu = 2):
        ''' set cpu capacity for the vnode '''
        self.cpu = cpu
        
    def set_ram(self, ram = 2):
        ''' set ram capacity for the vnode '''
        self.ram = ram
    
    def set_iface_bw(self, iface_bw):
        ''' set a default capacity for each interface '''
        self.iface_bw = iface_bw
    
    def set_status(self, status):
        """
        set the status of a virtual node: 
        1: up
        """
        self.status = status
        
    def conf_viface(self):
        """
        Configure the virtual interfaces, populate virtual interface list
        Each virtual router has the same number of virtual interfaces, which 
        equals to the total number of substrate nodes. 
        """
        # num_viface is the total number of substrate nodes. 
        for index in range(self.num_viface):
            self.viface_list.append(virtual_iface(index, self.iface_bw))

    def enable_iface(self, iface_list, num):
        ''' Enable the virtual interface based on the virtual topology '''
        if num > len(self.viface_list):
            return "The router does not have enough interfaces."
        else:
            up_ifaces = self.get_upIface()
            down_ifaces = self.get_downIface(up_ifaces)
            if num > len(down_ifaces):
                return "The router does not have enough interfaces."
            else:
                pick_ifaces = random.sample(set(down_ifaces), num)
                for item in pick_ifaces:
                    item.status = 1
                self.update_iface_list(pick_ifaces)
    
    def get_upIface(self):
        ''' Count the number of interfaces that are up '''
        up_ifaces = []
        for item in self.viface_list:
            if item.status == 1:
                up_ifaces.append(item)
        return up_ifaces
    
    def get_downIface(self, up_ifaces):
        ''' return the number'''
        down_ifaces = set(self.viface_list) - set(up_ifaces) 
        return list(down_ifaces)
        
    def update_iface_list(self, new_iface_list):
        ''' udpate iface stats '''
        for item in self.viface_list:
            if item in new_iface_list:
                temp = self.find_iface(new_iface_list, item.viface_id)
                item.update(temp.status)
    
    def find_iface(self, iface_list, target_id):
        ''' find the target in the list '''
        for item in iface_list:
            if item.viface_id == target_id:
                return item

    
    def get_used_bw_list(self):
        """ 
        get the used bw on each interfaces
        For homogeneous case, the interface id does not matter
        only return a list of non-zero bw
        """
        used_bw_list = []
        for viface in self.viface_list:
            if viface.used_bw != 0:
                used_bw_list.append(viface.used_bw)
        return used_bw_list
        
  
        
class vnet(object):
    ''' virtual network class '''
    def __init__(self, vnodes = [], vn_id = 0):
        """ 
        initalize a virtual network 
        both vnodes and standby_vnodes are a list of virtual_node objects 
        vtopo: a graph object
        """
        self.vnodes = vnodes
        self.standby_vnodes = []   
        self.vtopo = nx.Graph()
        self.vnet_id = vn_id
        self.nonactive_vnodes = []
  

    def set_traffic(self, node_id, dst_id, volume):
        """
        Set the traffic volume in the virtual network
        """
        vnodes = self.vnodes
        target_node = vnodes[node_id]
        target_node.update_total_traffic(dst_id, round(volume, 5))
        
        
    def get_standby_ids(self):
        ''' get standby router ids '''
        standby_ids = []
        for node in self.standby_vnodes:
            standby_ids.append(node.vnode_id)
        return standby_ids
        
    def get_connected_ids(self):
        ''' get connected router ids '''
        return self.vtopo.nodes()
        
    def random_fail(self, num_failure):
        """
        generate ramdom failures in virtual network
        num_failure == 0: no failure, return -1
        num_failrue == 1: single virtual router failure, return failed vr id
        num_failure >1: multiple virtual router failure, return a list of ids
        num_failure < 0: error! num_failure has to be non-negative integer
                        return -2
        """
        connected_ids = self.get_connected_ids()
        if num_failure == 0:
            return -1
        elif num_failure == 1:
            failed_id = random.choice(connected_ids)
            return failed_id
        elif num_failure > 1:
            failed_list = random.sample(connected_ids, num_failure)
            return failed_list
        else:
            print "Error: Number of Failures has to be non-negative!"
            return -2
            
            
  
        
            
    def get_vnode_status(self):
        """
        return a list of status 
        """
        vnodes = self.vnodes
        vnode_status = []
        for vnode in vnodes:
            vnode_status.append(vnode.status)
        return vnode_status
        
    def get_vnode_traffic(self):
        """
        Generate a list of node_traffic pair, each pair is in form of
        (node_id, node_traffic)
        """
        vnodes = self.vnodes
        vnode_traffic = []
        for vnode in vnodes:
            vnode_traffic.append((vnode.vnode_id, vnode.total_traffic))
        return vnode_traffic
        
    def get_vnet_info(self):
        ''' get virtual network information '''
        vnet_dict = {}
        vnet_dict['topo'] = self.vtopo.edges()
        vnet_dict['up_nodes'] = self.get_connected_ids()
        vnet_dict['standby'] = self.get_standby_ids()
        vnet_dict['vnode_status'] = self.get_vnode_status()
        vnet_dict['traffic'] = self.get_vnode_traffic()
        return vnet_dict        
    
    
                                        
            
        

        
