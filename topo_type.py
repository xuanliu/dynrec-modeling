# -*- coding: utf-8 -*-

"""
Created on Fri Aug 23 14:56:18 2013
This scripts contains several classical topology information
@author: xuanliu
"""
from math import radians, sqrt, sin, cos, atan2
import topo_parser
# Internet 2 Network IP router topology
TOPO_GML = "Geant2012.json"
I2_node_mapping = {0: 'SEAT',
                    1: 'LOSA',
                    2: 'SALT',
                    3: 'KANS',
                    4: 'HOUS',
                    5: 'CHIC',
                    6: 'ATLA',
                    7: 'WASH',
                    8: 'NEWY'}
I2_topo = {(0,1): 1342,
           (0,2): 913,
           (1,2): 1303,
           (1,4): 1750,
           (2,3): 1330,
           (3,5): 690,
           (3,4): 818,
           (4,6): 1385,
           (6,7): 700,
           (5,7): 905,
           (5,8): 1000,
           (7,8): 277,
           (5,6): 1045}
           
I2_node_geoinfo = {0: (47.611877,-122.333561),
                   1: (34.169772,-118.126588),
                   2: (40.759481,-111.829689),
                   3: (39.11621,-94.57602),
                   4: (29.814434,-95.364504),
                   5: (41.893077,-87.634034),
                   6: (33.764878,-84.3909),
                   7: (38.918284,-77.03418),
                   8: (40.741014,-74.002748)}
I2_bw = 1                   


"""
GEANT Topoloty information
"""
geant_dict = topo_parser.load_topo(TOPO_GML)
geant_fiber, geant_ip = topo_parser.get_link_info(geant_dict)
    
geant_node_mapping = \
{0: 'NL',
 1: 'BE',
 2: 'DK',
 3: 'PL',
 4: 'DE',
 5: 'CZ',
 6: 'LU',
 7: 'FR',
 8: 'CH',
 9: 'IT',
 10: 'UA',
 11: 'MD',
 12: 'BG',
 13: 'RO',
 14: 'TR',
 15: 'GR',
 16: 'CY',
 17: 'IL',
 18: 'MT',
 19: 'BY',
 20: 'MK',
 21: 'ME',
 22: 'HU',
 23: 'SK',
 24: 'PT',
 25: 'ES',
 26: 'RS',
 27: 'HR',
 28: 'SL',
 29: 'AT',
 30: 'LT',
 31: 'RU',
 32: 'IS',
 33: 'IE',
 34: 'UK',
 35: 'NO',
 36: 'SE',
 37: 'FI',
 38: 'EE',
 39: 'LV'}

geant_node_geoinfo = \
{0: (52.37403, 4.88969),
 1: (50.85045, 4.34878),
 2: (55.67594, 12.56553),
 3: (52.41667, 16.96667),
 4: (50.11667, 8.68333),
 5: (50.08804, 14.42076),
 6: (49.61167, 6.13),
 7: (48.85341, 2.3488),
 8: (46.94809, 7.44744),
 9: (45.46427, 9.18951),
 10: (48.922499,31.106415),
 11: (47.576526,28.408928),
 12: (42.69751, 23.32415),
 13: (44.43225, 26.10626),
 14: (39.05901, 34.91155),
 15: (37.97945, 23.71622),
 16: (35.16667, 33.36667),
 17: (31.5, 34.75),
 18: (35.90917, 14.42556),
 19: (53.225768,27.879868),
 20: (42.0, 21.43333),
 21: (42.44111, 19.26361),
 22: (47.49801, 19.03991),
 23: (48.14816, 17.10674),
 24: (38.71667, -9.13333),
 25: (40.4165, -3.70256),
 26: (44.80401, 20.46513),
 27: (45.81444, 15.97798),
 28: (46.05108, 14.50513),
 29: (48.20849, 16.37208),
 30: (54.9, 23.9),
 31: (55.75222, 37.61556),
 32: (64.13548, -21.89541),
 33: (53.34399, -6.26719),
 34: (51.50853, -0.12574),
 35: (62.0, 10.0),
 36: (59.33258, 18.0649),
 37: (60.45148, 22.26869),
 38: (59.43696, 24.75353),
 39: (56.946, 24.10589)}

geant_bw = 25    



def relabel_nodeinfo(topo_node_mapping, topo_node_geoinfo, topo_link_info):
    """
    This function is used to filter out the nodes appeared in the topology 
    from the original node set, and reble them sequencially from 0.
    """
    new_mapping = {}
    new_geoinfo = {}
    index = 0
    for nodeA, nodeB in topo_link_info.keys():
        #print nodeA, nodeB
        if not nodeA in new_mapping.values():
            #print "local", index
            new_mapping[index] = nodeA
            new_geoinfo[index] = topo_node_geoinfo[nodeA]
            #print topo_node_mapping[nodeA], new_mapping[index]
            index = index + 1            
        if not nodeB in new_mapping.values():
            #print "remote", index
            new_mapping[index] = nodeB
            new_geoinfo[index] = topo_node_geoinfo[nodeB]
            #print topo_node_mapping[nodeA], new_mapping[index]
            index = index + 1
    return new_mapping, new_geoinfo

def relabel_linkinfo(topo_link_info, new_mapping):
    """
    This function is used to re-label the link with the relabed node id
    """
    new_link_info = {}
    for nodeA, nodeB in topo_link_info.keys():
        new_nodeA = [key for key, value in new_mapping.iteritems() \
                        if value == nodeA]
        new_nodeB = [key for key, value in new_mapping.iteritems() \
                        if value == nodeB]
        new_link_info[(new_nodeA[0], new_nodeB[0])] = topo_link_info[(nodeA, nodeB)]
        print new_nodeA, new_nodeB, topo_link_info[(nodeA, nodeB)]
    return new_link_info

def geocalc(lat1, lon1, lat2, lon2):
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon1 - lon2

    EARTH_R = 6372.8

    y = sqrt(
        (cos(lat2) * sin(dlon)) ** 2
        + (cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)) ** 2
        )
    x = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(dlon)
    c = atan2(y, x)
    return EARTH_R * c