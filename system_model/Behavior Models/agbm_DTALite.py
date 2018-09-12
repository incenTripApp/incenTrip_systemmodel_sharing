# -*- coding: utf-8 -*-
__author__ = 'Chenfeng'

import os
import csv
import pandas as pd
import time # this is for the agbm idling time for DTALite
import random
import numpy as np
import json
import itertools
import copy
global time_ca
global time_agbm
global time_alternative
#import matplotlib.pyplot as plt
os.chdir('D:\\Dropbox (Lei Zhang Group)\\Parallel Processing\\1_ODME_DOE_6am_4pm') 
#os.chdir('C:\\Users\\xchenfeng\\Desktop\\New_folder\\White_Flint_2010_WZ')  # define project folder
#os.chdir("C:\\Dropbox\\For_Dr_Zhou\\Interstate_270_Maryland")
random.seed(12345678)
iter = 0  # Initialize the model
converg = 0
time_scope = [360, 960]
inc = [1, 2, 3, 4]              # agent characteristics
sex = [1, 2]
flex = [1, 2]
purp = [1, 2]
veh = [1, 2]
inc_probabilities = [0.2, 0.2, 0.3, 0.3]
sex_probabilities = [0.5, 0.5]
flex_probabilities = [0.22, 0.78]
purp_probabilities = [0.8, 0.2]
veh_probabilities = [0.75, 0.25]   # 1: <= 2 veh/hh; 2: ow
MODE = ['WALK','BIKE','TRANSIT','RIDESHARE','DRIVE']
Choice_Flag = ['Original','SuggestedRoute','SuggestedDepTime','SuggestedTransit','SuggestedRideshare','SuggestedWalk','SuggestedBike']
def random_pick(some_list, probabilities):  # random assignment of agent attributes
    x = random.uniform(0, 1)
    cumulative_probability = 0
    for item, item_prob in zip(some_list, probabilities):
        cumulative_probability += item_prob
        if x < cumulative_probability: break
    return item

def route_search(routeA, routeB):
    delta_time = routeB[0] / routeA[0] - 1
    if routeA[2] == 0:
        delta_Btime = 1
    else:
        delta_Btime = routeB[2] / routeA[2] - 1
    delta_transfer = routeB[3] - routeA[3]
    if delta_time > 0.21: return routeA
    elif -0.57 > delta_time > 0.13 and delta_time <= 0.21: return routeA
    elif delta_time > 0.13 and delta_time <= 0.21 and delta_Btime >= -0.57 and\
            delta_Btime < 0.19 and (delta_transfer == 0 or 1): return routeA
    elif delta_time > 0.13 and delta_time <= 0.21 and delta_Btime >= 0.19 and\
            delta_Btime<0.19 and routeA[0]>30: return routeA
    elif delta_time > 0.13 and delta_time <= 0.21 and delta_Btime >= -0.57 and\
            delta_transfer == 1: return routeA
    else: return routeB

def route_switch(routeA, routeB, distance, income):
    #print routeA
    #print routeB
    delta_time = routeB[0] / routeA[0] - 1
    if routeA[1] < 0.0001 and routeB[1] < 0.0001:
        delta_delay = 0
    elif routeA[1] < 0.0001 and routeB[1] > 0.0001:
        routeA[1] = 0.0001
        delta_delay = routeB[1] / routeA[1] - 1
    else: delta_delay = routeB[1] / routeA[1] - 1
    delta_pleasure = -routeB[3] + routeA[3]
    if routeA[2] < 0.0001 and routeB[2] < 0.0001:
        delta_familiarity = 0
    elif routeA[2] < 0.0001 and routeB[2] > 0.0001:
        routeA[2] = 0.0001
        delta_familiarity = routeB[2] / routeA[2] - 1
    else: delta_familiarity = routeB[2] / routeA[2] - 1
    if delta_time <= -0.39: return routeB[4]
    elif delta_time <= -0.11 and delta_pleasure >= -1: return routeB[4]
    elif delta_familiarity >= 0.5 and routeA[0] <= 20: return routeB[4]
    elif delta_time <= 0.06 and delta_pleasure >= 3: return routeB[4]
    elif delta_time <= 0.15 and delta_familiarity >= 2 and delta_delay >= -0.4: return routeB[4]
    elif delta_familiarity < 0.5 and delta_time <= 0.51 and routeA[0] <= 20 and income == 1: return routeB[4]
    elif routeA[1] >= 4 and distance <= 8: return routeB[4]
    elif delta_pleasure >= 2 and delta_familiarity >= 0 and routeA[0] <= 16: return routeB[4]
    else: return routeA[4]



def deptime_search(deptime, time, delay, asde, asdl):
    x = random.uniform(0, 1) * 30
    if asdl > 70: return deptime - x - 60
    elif asdl <= 70 and asdl > 45: return deptime - x - 30
    elif asdl > 0 and delay > 0: return deptime - x
    elif asdl > 0 and asdl <=30 and delay > 0.4: return deptime + x
    elif asdl <= 10 and asde <= 40 and delay <= 0.5 and time <= 65: return deptime + x
    elif asdl == 0: return deptime + 30 + x
    elif asde > 75: return deptime + 60 + x
    elif asde > 45 and delay > 0.1: return deptime + 60 + x
    else: return deptime - x

def deptime_switch(deptime1, deptime2, time1, time2, cost1, cost2, asde1, asde2, asdl1, asdl2, highinc, purpose):
    npeak = 1
    if deptime1 >= 360 and deptime1 <= 540: npeak = 0
    elif deptime1 >= 900 and deptime1 <= 1260: npeak = 0
    delta_time = (time2 - time1) / time1
    delta_cost = (cost2 - cost1) / cost1
    d_cost = cost2 - cost1
    if asde1 < 0.0001 and asde2 > 0.0001:
        delta_asde = 1
    elif asde1 < 0.0001 and asde2 < 0.0001:
        delta_asde = 0
    else: delta_asde = (asde2 - asde1) / asde1
    if asdl1 < 0.0001 and asdl2 > 0.0001:
        delta_asdl = 1
    elif asdl1 < 0.0001 and asdl2 < 0.0001:
        delta_asdl = 0
    else:delta_asdl = (asdl2 - asdl1) / asdl1
    if delta_time <= -0.35 and delta_cost <= -0.08: return deptime2
    elif d_cost <= 2.5 and delta_asdl <= -0.48: return deptime2
    elif d_cost <=2.4 and highinc == 1 and delta_asdl <= -0.31: return deptime2
    elif npeak == 1 and purpose == 2 and delta_time <= -0.08 and delta_asdl <= 0.53: return deptime2
    elif delta_asde <= -0.2 and d_cost <= 0.7: return deptime2
    else: return deptime1






class agbm:                         # Agent-based modeling
    def __init__(self, n_agents, pre_info_ratio, en_info_ratio, n_iterations):
        self.n_agents = n_agents
        self.pre_info_ratio = pre_info_ratio
        self.en_info_ratio = en_info_ratio
        self.n_iterations = n_iterations
        self.agent_id = []
        self.agents = {}            # define a dictionary for agents
        self.agents_char = {}       # define agent characteristics
        self.agents_knowledge = {}  # define agent knowledge
        self.input_links={}
        self.dimension = {}
        self.switch = {}
        self.sp_users = {}
        self.sp_searchers = {}
        self.excessive_time = {}
        self.sp_switchers = {}
        self.early_departurers = {}
        self.late_departurers = {}
        self.linkTDdelay = {}
        self.linkTDtime = {}
        self.linkTDenergy = {}
        self.OD_paths = {}
        self.path_TDtimes = {}
        self.path_TDenergies = {}
        self.pathtimes = {}
        self.OD_SP = {}
        self.OD_ST = {}
        self.n_searchers = [[],[],[],[]]
        self.n_switchers = [[],[],[],[]]
        self.counters = [[],[],[],[],[],[]]
        self.avg_excessive_ratio = []
        self.search_count_m = {}
        self.search_count_r = {}
        self.search_count_d = {}
        self.search_outcome_m = {}
        self.search_outcome_r = {}
        self.search_outcome_d = {}
        self.agents_gain = {}
        self.agents_cost = {}
        self.agent_alternatives = {}




    def populate(self):
        agent_decisions = []
        agent_char = []
        agent_knowledge = []
        agent_dimension = []
        agent_switch = []
        agent_sp_user = []
        agent_sp_search = []
        agent_sp_switch = []
        agent_early_dep = []
        agent_late_dep = []
        agent_excessive_time =[]
        search_count = []
        search_outcome = []
        agent_gain = []
        agent_cost = []
        os.chdir('D:\\Dropbox (Lei Zhang Group)\\Parallel Processing\\1_ODME_DOE_6am_4pm') 
        # building the dictionary for link travel times
        file_d = open('input_link.csv', "rb")
        csvreader = csv.reader(file_d)
        next(csvreader)
        link_ids = []
        link_attr = []
        for row in csvreader:
            from_node = row[2]
            to_node = row[3]
            link_id = from_node +';'+ to_node
            fftt = (float(row[5])*60)/(float(row[7]))
            link_ids.append(link_id)
            link_attr.append([fftt, row[9], row[5]])    # free-flow time, roadway type, length
        self.input_links = dict(zip(link_ids, link_attr))

        file_init = open('output_agent.csv', "rb")
        csvread = csv.reader(file_init)
        next(csvread)
        for row in csvread:
            n_nodes = int(row[28])
            txt = row[29]    # the txt data recording the path_node_sequence
            a = txt.split(';')
            free_time = 0
            for i in range(n_nodes-1):
                linkid = a[i] + ';' + a[i+1]
                #print linkid
                free_time = free_time + self.input_links[linkid][0]
            self.agent_id.append(row[0])
            tmp = (row[13], row[9], row[29])              # mode, deptime, route
            agent_decisions.append(tmp)
            tmp1 = (random_pick(inc, inc_probabilities),
                    random_pick(sex, sex_probabilities),
                    random_pick(flex, flex_probabilities),
                    random_pick(veh, veh_probabilities),
                    random_pick(purp, purp_probabilities),
                    float(row[6])+free_time, free_time, float(row[19])) # Preferred Arrival Time (Departure + free-flow time); free-flow time; travel distance
            tmp2 = (row[13], row[9], row[29], float(row[12]))   # mode, departure time, route, travel time
            tmp4 = (0, 0, 0)
            inc1 = 0
            inc2 = 0
            inc3 = 0
            inc4 = 0
            if tmp1[0] == 1: inc1 = 1
            elif tmp1[0] == 2: inc2 = 1
            elif tmp1[0] == 3: inc3 = 1
            elif tmp1[0] == 4: inc4 = 1
            inc_dum = (inc1, inc2, inc3, inc4)
            cost1 = 1.341 + 0.023 * tmp2[3] + 0.014 * (tmp1[1]-1) +\
                0.118 * (tmp1[2]-1) - 0.101 * (tmp1[4] - 1) + 0.188 * inc_dum[0] +\
                0.085 * inc_dum[1] -0.007 * inc_dum[2] -0.02 * tmp1[6]
            cost2 = 0.702 + 0.008 * tmp2[3] + 0.162 * (tmp1[1]-1) +\
                0.194 * (tmp1[2]-1) - 0.091 * (tmp1[4] - 1) -0.272 * inc_dum[0] +\
                0.285 * inc_dum[1] -0.542 * inc_dum[2] -0.008 * tmp1[6]
            cost3 = 0.384 + 0.001 * tmp2[3] + 0.098 * (tmp1[1]-1) +\
                0.115 * (tmp1[2]-1) - 0.098 * (tmp1[4] - 1) -0.299 * inc_dum[0] +\
                0.207 * inc_dum[1] -0.089 * inc_dum[2] -0.006 * tmp1[6]

            agent_char.append(tmp1)
            agent_knowledge.append([tmp2])
            agent_dimension.append([0])
            agent_switch.append([0])
            agent_sp_search.append([0])
            agent_sp_user.append([0])
            agent_sp_switch.append([0])
            agent_early_dep.append([0])
            agent_late_dep.append([0])
            agent_excessive_time.append([0])
            search_count.append(0)
            search_outcome.append([])
            agent_gain.append([tmp4])
            agent_cost.append([cost1, cost2, cost3])
           # print row[0]
        self.agents = dict(zip(self.agent_id, agent_decisions))
        self.agents_char = dict(zip(self.agent_id, agent_char))
        self.agents_knowledge = dict(zip(self.agent_id, agent_knowledge))
        self.dimension = dict(zip(self.agent_id, agent_dimension))
        self.switch = dict(zip(self.agent_id, agent_switch))
        self.sp_users = dict(zip(self.agent_id, agent_sp_user))
        self.sp_searchers = dict(zip(self.agent_id, agent_sp_search))
        self.sp_switchers = dict(zip(self.agent_id, agent_sp_switch))
        self.early_departurers = dict(zip(self.agent_id, agent_early_dep))
        self.late_departurers = dict(zip(self.agent_id, agent_late_dep))
        self.excessive_time = dict(zip(self.agent_id, agent_excessive_time))
        self.search_count_d = dict(zip(self.agent_id, search_count))     # initialized # of searches
        self.search_count_m = dict(zip(self.agent_id, search_count))
        self.search_count_r = dict(zip(self.agent_id, search_count))
        self.search_outcome_d = dict(zip(self.agent_id, search_outcome))
        self.search_outcome_m = dict(zip(self.agent_id, search_outcome))
        self.search_outcome_r = dict(zip(self.agent_id, search_outcome))
        self.agents_gain = dict(zip(self.agent_id, agent_gain))
        self.agents_cost = dict(zip(self.agent_id, agent_cost))
        # initial belief: gets initial travel time and no delays
        file_init.close()
    #def is_unsatisfied(self, x):

    def learn(self, iter):  # learn the past experience into agent_knowledge on day iter
        str1 = 'output_agent_day'
        str2 = '.csv'
        str3 = 'input_agent_day'
        str4 = 'output_LinkTDMOE'
        iter1  = iter + 1
        out_str = str1 + `iter` + str2
        write_str = str3 + `iter1` + str2
        link_str = str4 + str2
        link_file = open(link_str, "rb")
        linkreader = csv.reader(link_file)
        next(linkreader)
        linkTD_ids = []
        times = []
        delays = []
        energy_uses = []
        for row in linkreader:
            from_node = row[0]
            to_node = row[1]
            timestamp_LinkTDMOE = row[4]
            linkTD_id = from_node +';'+ to_node+';'+ timestamp_LinkTDMOE
            tt = row[5]
            delay = row[6]
            energy_use = row[17]
            linkTD_ids.append(linkTD_id)
            times.append(tt)
            delays.append(delay)
            energy_uses.append(energy_use)
        self.linkTDtime = dict(zip(linkTD_ids, times))
        self.linkTDdelay = dict(zip(linkTD_ids, delays))
        self.linkTDenergy = dict(zip(linkTD_ids, energy_uses))
        #print self.linkTDenergy
        link_file.close()

        file_OD = open('Path_11.csv','rb')
        OD_reader = csv.reader(file_OD)
        line = next(OD_reader)
        OD_list = []

        for row in OD_reader:
            origin = row[1]
            destination = row[2]
            OD = origin + ';' + destination
            OD_list.append(OD)
            
            #path_list.append([])
        #print OD_list
        OD_list = list(set(OD_list))
        #print OD_list
        #print len(OD_list)
        path_list = [[] for _ in range(len(OD_list))]
        self.OD_paths = dict(zip(OD_list, path_list))
        file_OD.close()
        # generated an empty OD_paths dictionary

        file_path = open ('Path_11.csv','rb')
        path_reader = csv.reader(file_path)
        line = next(path_reader)
        all_paths1 = []
        all_paths2 = []
        veh_id = 'v0'
        for row in path_reader:
            link_nodes = row[4].split('->')
            if row[3] == '0':  # link_sequence = 0 incidate that this is the first link in the sequence
                origin = row[1]
                destination = row[2]
                veh_id = row[0]
                path_sequence = link_nodes[0] + ';' + link_nodes[1] + ';'
            elif row[0] == veh_id:
                path_sequence += link_nodes[1] + ';'
                if destination == link_nodes[1]:
                    OD = origin + ';' + destination
                    self.OD_paths[OD].append(path_sequence)
                    all_paths1.append(path_sequence)    # recording all paths being used in the system
                    all_paths2.append(path_sequence)
        all_paths1 = list(set(all_paths1))
        all_paths2 = list(set(all_paths2))
        path_TDfeatures1 = [[] for _ in range(len(all_paths1))]   
        path_TDfeatures2 = [[] for _ in range(len(all_paths2))]
        self.path_TDtimes = dict(zip(all_paths1, path_TDfeatures1))     # empty dictionary for path TD times
        self.path_TDenergies = dict(zip(all_paths2, path_TDfeatures2))  # empty dictionary for path TD energies    
        for OD in self.OD_paths:
            temp = self.OD_paths[OD]
            tmp = list(set(temp))
            self.OD_paths[OD] = tmp
        file_path.close()
        #print OD_paths[OD]
        # extract OD-Skim Data for the previous day (using RT_Output_ODMOE_09h_15m_00s.csv)
        # from 0300 to 1200 time stamp (180 min to 720 min)
        ODT_list = []
        SP_list = []
        ST_list = []   # shortest time
        for minutes in range(time_scope[0], time_scope[1]+1, 15): # from 3:00 to 12:00 time frame
            for item in OD_list:
                #print item
                ODT = item + ';' + str(minutes)
                ODT_list.append(ODT)
                traveltimes = []
                travelenergies = []
                for node_sequence in self.OD_paths[item]:
                    travel_time = 0
                    travel_energy = 0
                    path_ids = node_sequence
                    node_sequence = node_sequence.split(';')
                    #print node_sequence
                    for i in range(len(node_sequence)-2):
                                linkid = node_sequence[i] + ';' + node_sequence[i+1]
                                linkTDid = node_sequence[i] + ';' + node_sequence[i+1] + ';' + `minutes`
                                #print linkTDid
                        #print self.input_links[linkid]
                                travel_time += float(self.linkTDtime[linkTDid])
                                travel_energy += float(self.linkTDenergy[linkTDid])
                                traveltimes.append(travel_time)
                                #travelenergies.append(travel_energy)
                    self.path_TDtimes[path_ids].append(travel_time)
                    self.path_TDenergies[path_ids].append(travel_energy)
                self.pathtimes = dict(zip(self.OD_paths[item], traveltimes))

                #print self.pathtimes
                [(SP,ST) for SP,ST in self.pathtimes.items() if SP==min(self.pathtimes.values())]    # calculate the shortest path among the path_dictionary
                SP_list.append(SP)
                ST_list.append(ST)
        self.OD_SP = dict(zip(ODT_list, SP_list))
        self.OD_ST = dict(zip(ODT_list, ST_list))

        filewriteobj = file(write_str, "wb")
        writer = csv.writer(filewriteobj)
        file_d = open(out_str, "rb")
        csvreader = csv.reader(file_d)
        
        line = next(csvreader)
        #line[4] = 'from_origin_node_id'
        #line[5] = 'to_destination_node_id'
        #line[24] = 'vehicle_age'
        writer.writerow(line)
        agent_id_list = []
        agent_alternatives_list = []
        #counter = 0
        time_pathgeneration = time.clock()
        print time_pathgeneration, "path generation completed"
        print "calculating alternatives"
        #total_ = 1000000
        #count_ = 0
        for row in csvreader:
            #count_ += 1
            #print count_
            #for x in range(0,10):
            #    if 10*count_ / total_ > x and 10 * count_ / total_ <x+1:print x
            #counter += 1
            # row[0] should match self.agent_id
            agentid = 'agent' + str(row[0])
            pat = self.agents_char[row[0]][5]   # preferred arrival time
            
            #mode=random.choice(MODE)
            tmp3 = (row[9], row[5], row[6], row[12])   # DepTime, O, D, Trip_Time
            agent_O = int(row[5])
            agent_D = int(row[6])
            agent_OD = row[5] + ';' + row[6]
            agent_path = row[29]                # calculating path data
            agent_distance = float(row[19])
            deptime = round(float(row[9]))                    # actual dearture time PAY ATTENTION!!! CHANGED FROM FLOAT TO INT
            energy = float(row[20])
            fuel_cost = energy / 131760 * 2.5      # 131760 KJ/Gallon; $2.5/Gallon
            trip_time = float(row[12])
	    if trip_time <= 0.0000000001: continue
            arrtime = float(row[10])                    # actual arrival time
            delay = (trip_time - self.agents_char[row[0]][6])/self.agents_char[row[0]][6]
            delay_time = trip_time - self.agents_char[row[0]][6]
            sde = max(0, pat - arrtime)
            sdl = max(0, arrtime - pat)              
            for i in range(50):
                if int(row[0])==i*100000: print str(i*100000)+" agents completed"   
            # generate a internal list of alternatives for each agent
            if random.random()>0.79: # should be replaced by a adopter profile model
                if agent_OD in OD_list:
                    x = self.OD_paths[agent_OD]
                    agent_paths = list(set(x))
                else: agent_paths = [agent_path]
                agent_alternatives = []
                alternative_path = [agent_path]
                path_attributes = []
                deptime_1 = deptime - 20
                if deptime_1 < time_scope[0]: deptime_1 = time_scope[0]
                deptime_2 = deptime + 20
                if deptime_2 > time_scope[1]: deptime_2 = time_scope[1]
                alt_deptimes = [deptime_1, deptime, deptime_2]
                #alternativeID = 0
                #alternativeIDs = []
                #, counter
                # alternative attributes: efficiency, O, D, mode, paths, deptime, trip_time, arr_time,energy,energy savings,delay)
                                            # choice flag (original choice, suggested deptimes, suggested route, ride-sharing, transit, walk, bike) 
                
                original_attributes=[0,agent_O,agent_D,MODE[4],agent_path,agent_distance, deptime,trip_time,arrtime,energy,fuel_cost, 0,delay_time,Choice_Flag[0]]
                agent_alternatives.append(original_attributes)
                if agent_O <= 1163 and agent_D<=1163:  # transit service are available for the selected OD pair
                    if deptime >= 360 and deptime <= 540: 
                        transit_time =float(transit_skim[agent_O][agent_D-1])
                        transit_fare = float(transit_fare_pk[agent_O][agent_D-1])/100 * 1.11
                    elif deptime >= 900 and deptime <= 1140: 
                        transit_time =float(transit_skim[agent_O][agent_D-1])
                        transit_fare = float(transit_fare_pk[agent_O][agent_D-1])/100 * 1.11
                    else:
                        transit_fare = float(transit_fare_op[agent_O][agent_D-1])/100 * 1.11  
                        transit_time=float(transit_skim_op[agent_O][agent_D-1])
                    if transit_time<>0:
                        transit_energy = 0.25 * energy
                        transit_arrtime=deptime+transit_time
                        transit_asde=max(0,pat-transit_arrtime)
                        transit_asdl=max(0,transit_arrtime-pat)
                        transit_rewards = max(0.1,-1/0.115*(-1.826-0.018*(transit_time-trip_time)-0.051*(transit_fare-fuel_cost)-0.014*(transit_asde-sde)-0.001*(transit_asdl-sdl)))
                        transit_efficiency = transit_rewards/(energy - transit_energy)
                        transit_attr=[transit_efficiency,agent_O,agent_D,MODE[2],0,agent_distance,deptime,transit_time,transit_arrtime,transit_energy,transit_fare, energy-transit_energy,0,Choice_Flag[3]]
                        agent_alternatives.append(transit_attr)
                RS_energy=0.7*energy
                RS_fuelcost=RS_energy / 131760 * 2.5
                RS_time=trip_time*1.10
                RS_arrtime=deptime+RS_time
                RS_asde=max(0,pat-RS_arrtime)
                RS_asdl=max(0,RS_arrtime-pat)
                RS_rewards=max(0.1,-1/0.115*(-1.42-0.018*(RS_time-trip_time)-0.051*(RS_fuelcost-fuel_cost)-0.014*(RS_asde-sde)-0.001*(RS_asdl-sdl)))
                RS_efficiency = RS_rewards/(energy - RS_energy)
                RS_attr=[RS_efficiency,agent_O,agent_D,MODE[3],0,agent_distance,deptime,RS_time,RS_arrtime,RS_energy,RS_fuelcost,energy-RS_energy,delay_time,Choice_Flag[4]]
                agent_alternatives.append(RS_attr)
                if float(agent_distance)<5:
                    BK_time=agent_distance*10
                    BK_energy=0
                    BK_arrtime=deptime+BK_time
                    BK_asde=max(0,pat-BK_arrtime)
                    BK_asdl=max(0,BK_arrtime-pat)
                    BK_rewards=max(0.2,-3.876*(-2.02-0.1*(BK_time-trip_time)-0.02*(BK_asde-sde)-0.003*(BK_asdl-sdl)))
                    BK_efficiency = BK_rewards/(energy - BK_energy)
                    BK_attr=[BK_efficiency,agent_O,agent_D,MODE[1],0,agent_distance,deptime,BK_time,BK_arrtime,BK_energy,0,energy-BK_energy,0,Choice_Flag[6]]
                    agent_alternatives.append(BK_attr)
                    if float(agent_distance)<3:
                        WK_time=float(agent_distance)*18
                        WK_energy=0
                        WK_arrtime=deptime+WK_time
                        WK_asde=max(0,pat-WK_arrtime)
                        WK_asdl=max(0,WK_arrtime-pat)
                        WK_rewards=max(0.2,-3.876*(-2.02-0.1*(WK_time-trip_time)-0.02*(WK_asde-sde)-0.003*(WK_asdl-sdl)))
                        WK_efficiency = WK_rewards/(energy - WK_energy)
                        WK_attr=[WK_efficiency,agent_O,agent_D,MODE[0],0,agent_distance,deptime,WK_time,WK_arrtime,WK_energy,0,energy-WK_energy,0,Choice_Flag[5]]
                        agent_alternatives.append(WK_attr)
                for deptimes in alt_deptimes:
                    #timestamps = int(round(float(deptimes)/15) * 15)
                    #agent_ODT = agent_OD + ';' + `int(timestamps)`
                    if deptimes<>deptime:flag=Choice_Flag[2]
                    else: flag=Choice_Flag[1]
                    #print flag
                    deptime_int = int(deptimes)
                    timestamp = int(round(float(deptime_int)/15) * 15)
                    timesequence = int(round(float(deptime_int - time_scope[0])/15))
                    for paths in agent_paths:
                        #if paths<>agent_path:flag=Choice_Flag[1]
                        #alternativeID = alternativeID + 1
                        #alternative_ID = `agentid` + ";" + `alternativeID` 
                        #alternativeIDs.append(alternative_ID)
                        if agent_OD in OD_list:
                            alternativeTIME = self.path_TDtimes[paths][timesequence]
                            #print alternativeTIME
                            alternativeENERGY = self.path_TDenergies[paths][timesequence]
                            #print "time_sequence:",timesequence
                            #print self.path_TDenergies[paths]
                            #print alternativeENERGY
                        else:
                            alternativeTIME = 0
                            alternativeENERGY = 0
                            node_sequence = paths.split(';')
                            for i in range(len(node_sequence)-2):
                                linkTDid = node_sequence[i] + ';' + node_sequence[i+1] + ';' + `timestamp`
                            #print self.linkTDtime[linkTDid]
                                alternativeTIME = alternativeTIME + float(self.linkTDtime[linkTDid])
                                alternativeENERGY = alternativeENERGY + float(self.linkTDenergy[linkTDid])
                        alternative_delay_time = alternativeTIME - self.agents_char[row[0]][6]
                        if alternativeENERGY < 100: alternativeENERGY = alternativeTIME/float(tmp3[3]) * energy   #IMPORTANT: LINEAR INTERPOLATION ON ENERGY USAGE
                        if alternativeENERGY < energy:
                            arrTime=deptimes+alternativeTIME
                            ASDE = max(0, pat-arrTime)
                            ASDL = max(0, arrTime-pat)
                            alt_fuelcost = alternativeENERGY / 131760 * 2.5
                            rewards = max(0.1,-1/0.747*(-1.05-0.09*(alternativeTIME-trip_time)-0.1*(alt_fuelcost-fuel_cost)-0.004*(ASDE-sde)-0.012*(ASDL-sdl)))
                            efficiency = rewards/(energy - alternativeENERGY)
                            alternative_attributes = [efficiency, agent_O,agent_D, MODE[4], paths, agent_distance, deptimes, alternativeTIME, deptimes+alternativeTIME, alternativeENERGY, alt_fuelcost, energy - alternativeENERGY, alternative_delay_time,flag]
                            agent_alternatives.append(alternative_attributes)
                
                if len(agent_alternatives) > 1: 
                    #print ("unsorted", agent_alternatives)
                    agent_alternatives = sorted(agent_alternatives, key = lambda x:x[0])
                    #print ("sorted",agent_alternatives)
                
                if len(agent_alternatives) >= 1: 
                    agent_id_list.append(agentid)
                    agent_alternatives_list.append(agent_alternatives)
                    #add agent_path and the current departure time
                    #add SP, if SP is different to agent_path
                    #add another path from agent_paths, if it is different to agent_path and SP
                
                # 先循环deptime：
                #    然后：对每个deptime, 建立path set：
                #            首先加入：agent_path, 
                #            然后，如果SP于agent_path不一样， 加入SP，
                #           最后：加入 transit, ride sharing, walking (if distance < 3), biking (if distance < 5)
                

        self.agent_alternatives = dict(zip(agent_id_list, agent_alternatives_list))    
        #print self.agent_alternatives.items() 
        time_agbm = time.clock()  
        print time_agbm, "agbm simulation completed"
        out_file1 = open("sorted_agents_pm.json", "w")
        sorted_agent_alternatives = sorted(self.agent_alternatives.items(), key = lambda x:x[1][0], reverse=True)
        json_str = json.dump(sorted_agent_alternatives, out_file1, indent = 4) #save sorted agent list for CA allocation
        out_file1.close()

        #budget = 50000
        #for i in range(0, len(sorted_agent_alternatives)):
        #    for j in range(0, len(sorted_agent_alternatives[i][1])):
        #        if (budget>0):
        #            (sorted_agent_alternatives[i][1][j].append('yes'))
        #            budget=budget-sorted_agent_alternatives[i][1][0][4]
        #            if (j>0):
        #                sorted_agent_alternatives[i][1][j][4]=min(sorted_agent_alternatives[i][1][0][4],sorted_agent_alternatives[i][1][j][0]*sorted_agent_alternatives[i][1][j][5])
        #        else:
        #            (sorted_agent_alternatives[i][1][j].append('no'))
        
        
        #print ("sorted_agents",sorted_agent_alternatives)
        #out_file2 = open("allocated_agent_50k_budget.json", "w")
        # define budget.
        #budget = 10000
        #json_str = json.dump(sorted_agent_alternatives, out_file2, indent = 4)
        #out_file2.close()
        file_d.close()
        filewriteobj.close()
        time_ca = time.clock()
        print time_ca, "incentive allocation completed"
        #test = (11,1,1)
        #print self.agents_knowledge[self.agent_id[1]]
        #self.agents_knowledge[self.agent_id[1]].append([test])



    #def search(self, iter):
        #for agent in self.agents:
            #if self.dimension[agent[0]][iter] == 2:
            #    # search rules
            #    RA = [1, 2, 3, 4]
            #    RB = [2, 3, 4, 5]
             #   newroute = route_search(RA, RB)
            #elif self.dimension[agent[0]][iter] == 3:
                # search rules
             #   newdeptime = deptime_search(360, 50, 50,50,50)
#    def converge(self):
#    def update(self):
#        for i in range(self.n_iterations):
#            self.old_agents = copy.deepcopy(self.agents)
#            n_changes = 0
#            for agent in self.old_agents:
#                if self.is_unsatisfied(agent[0]):
#                    agent_race = self.agents
#                    empty_house = random.choice(self.empty_houses)
    def update(self):
        #os.chdir('C:\\Users\\xchenfeng\\Desktop\\New_folder\\White_Flint_2010_WZ')
        os.chdir('D:\\Dropbox (Lei Zhang Group)\\Parallel Processing\\1_ODME_DOE_6am_4pm') 

        # initialization: setup input_demand_meta_data
        os.rename('input_demand_file_list.csv', 'temp.csv')
        file_config = open('temp.csv', "rb")
        configreader = csv.reader(file_config)
        line = next(configreader)
        updateconfig = file('input_demand_file_list.csv', "wb")
        configwriter = csv.writer(updateconfig)
        configwriter.writerow(line)
        line = next(configreader)
        line[2] = 'input_agent.csv'
        line[3] = 'agent_csv'
        configwriter.writerow(line)
        updateconfig.close()
        file_config.close()
        os.remove('temp.csv')
        global avg_excessive_ratios, n_switchers, n_searchers, counters   # globalization of the outputs
        # initialization: remove redundant output files
        for i in range(0,51,1):
            file_name_1 = 'input_agent_day' + `i` + '.csv'
            if os.path.isfile(file_name_1):
                os.remove(file_name_1)
            file_name_2 = 'output_agent_day' + `i` + '.csv'
            if os.path.isfile(file_name_2):
                os.remove(file_name_2)
        for iter in range(self.n_iterations):
            str1 = 'output_agent_day'
            str2 = '.csv'
            str3 = 'input_agent_day'
            iter1 = iter + 1
            in_str = str1 + `iter` + str2
            out_str = str3 + `iter1` + str2
            os.rename('output_agent.csv', in_str)

            #while not os.path.isfile(in_str):
            #    print 'waiting agent file for day '+`iter`
            #    time.sleep(3)
            #print 'extracting agent file for day '+`iter`
            self.learn(iter)
            n_changes = [0, 0, 0, 0]
            n_switches = [0, 0, 0, 0]
            counter = [0, 0, 0, 0, 0]   # i.e. sp_users, sp_searchers, sp_switchers, early_deps, late_deps
            sum_excessive_ratio = 0
            for agent in self.agents:
                sum_excessive_ratio += self.excessive_time[agent][iter+1]

                #print agent
                #print self.dimension[agent]
                if self.sp_users[agent][iter+1] == 1: counter[0] += 1
                if self.sp_searchers[agent][iter+1] == 1: counter[1] += 1
                if self.sp_switchers[agent][iter+1] == 1: counter[2] += 1
                if self.early_departurers[agent][iter+1] == 1: counter[3] += 1
                if self.late_departurers[agent][iter+1] == 1: counter[4] += 1
                if self.dimension[agent][iter+1] >= 0:
                    n_changes[3] += 1
                    if self.dimension[agent][iter+1] == 1:
                        n_changes[0] += 1
                    elif self.dimension[agent][iter+1] == 2:
                        n_changes[1] += 1
                    elif self.dimension[agent][iter+1] == 3:
                        n_changes[2] += 1
                if self.switch[agent][iter+1] >= 0:
                    n_switches[3] += 1
                    if self.switch[agent][iter+1] == 1:
                        n_switches[0] += 1
                    elif self.switch[agent][iter+1] == 2:
                        n_switches[1] += 1
                    elif self.switch[agent][iter+1] == 3:
                        n_switches[2] += 1
            #print n_changes
            avg_excessive_ratio = sum_excessive_ratio / 40000
            self.avg_excessive_ratio.append(avg_excessive_ratio)
            self.n_searchers[0].append(n_changes[0])
            self.n_searchers[1].append(n_changes[1])
            self.n_searchers[2].append(n_changes[2])
            self.n_searchers[3].append(n_changes[3])
            self.n_switchers[0].append(n_switches[0])
            self.n_switchers[1].append(n_switches[1])
            self.n_switchers[2].append(n_switches[2])
            self.n_switchers[3].append(n_switches[3])
            self.counters[0].append(counter[0])
            self.counters[1].append(counter[1])
            self.counters[2].append(counter[2])
            self.counters[3].append(counter[3])
            self.counters[4].append(counter[4])

            if n_changes[3] <= 5317768 * 0:
                break
            #print self.n_searchers
            os.rename('input_demand_file_list.csv', 'temp.csv')
            file_config = open('temp.csv', "rb")
            configreader = csv.reader(file_config)
            line = next(configreader)
            updateconfig = file('input_demand_file_list.csv', "wb")
            configwriter = csv.writer(updateconfig)
            configwriter.writerow(line)
            line = next(configreader)
            line[2] = out_str
            line[3] = 'agent_csv'
            configwriter.writerow(line)
            file_config.close()
            updateconfig.close()
            os.remove('temp.csv')
            #os.system('DTALite_64.exe')     # IF YOU DO NOT WANT THE PROGRAM TO RUN, can comment it off.
        counters = self.counters
        n_searchers = self.n_searchers
        n_switchers = self.n_switchers
        avg_excessive_ratios = self.avg_excessive_ratio
            #print self.n_searchers
            #print self.n_switchers
            #print self.counters
            #print self.avg_excessive_ratio





            #iter = iter + 1 This is not necessary




time_start = time.clock()
print time_start
#os.system('C:\\Users\\CXIONG-UMD\\Desktop\\ICC_2PM_BIG\\DTALite_64.exe')
os.chdir('D:\\Dropbox (Lei Zhang Group)\\Parallel Processing\\1_ODME_DOE_6am_4pm\\skims') 
file_transit=open('Transit_skm_time_PK_new.csv','rb')
time_pk=csv.reader(file_transit)
next(time_pk)
origins=[]
transit_times=[]
for row in time_pk:
    origin=int(row[0])
    
    origins.append(origin)
    transit_time=row[1:]
    transit_times.append(transit_time)

transit_skim=dict(zip(origins,transit_times))  # fraction of the skim matrix
file_transit.close()
file_PT_optime=open('Transit_skm_time_OP_new.csv','rb')
time_op=csv.reader(file_PT_optime)
next(time_op)
origins=[]
transit_times=[]
for row in time_op:
    origin=int(row[0])
    
    origins.append(origin)
    transit_time=row[1:]
    transit_times.append(transit_time)

transit_skim_op=dict(zip(origins,transit_times))  # fraction of the skim matrix
file_PT_optime.close()

file_PT_opfare=open('Transit_skm_fare_OP_new.csv','rb')
fare_op=csv.reader(file_PT_opfare)
next(fare_op)
origins=[]
transit_fares=[]
for row in fare_op:
    origin=int(row[0])
    
    origins.append(origin)
    transit_fare=row[1:]
    transit_fares.append(transit_fare)

transit_fare_op=dict(zip(origins,transit_fares)) 
file_PT_opfare.close()

file_PT_pkfare=open('Transit_skm_fare_PK_new.csv','rb')
fare_pk=csv.reader(file_PT_pkfare)
next(fare_pk)
origins=[]
transit_fares=[]
for row in fare_pk:
    origin=int(row[0])
    
    origins.append(origin)
    transit_fare=row[1:]
    transit_fares.append(transit_fare)

transit_fare_pk=dict(zip(origins,transit_fares)) 
file_PT_pkfare.close()
agbm_1 = agbm(1000,50,50,1)  # number of agents; pre-trip info; en-route info; iterations
agbm_1.populate()
time_populate = time.clock()
print time_populate, "population completed"
agbm_1.update()
time_DTALite = time.clock()
print time_DTALite, "dtalite traffic simulation completed"






