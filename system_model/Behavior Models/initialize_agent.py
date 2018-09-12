# -*- coding: utf-8 -*-
"""
Created on Sun Nov 26 22:39:48 2017

@author: cxiong
"""

import pandas as pd
import pickle
import time
import random
start_time = time.time()
agent=pd.read_csv('output_agent_day0.csv')
with open('taz_dic.pickle') as f:  # Python 3: open(..., 'rb')
    taz_dic = pickle.load(f)
del taz_dic[98]
del taz_dic[934]
agent.assign(emp=0, inc=0, sex=0, rac=0)
start_time = time.time()
for index, row in agent.iterrows():
    if int(index)%1000 == 0:
        print str(int(index/1000))+'000 records completed'
    rd_num1 = random.random()
    rd_num2 = random.random()
    rd_num3 = random.random()
    rd_num4 = random.random()
    taz = int(row['from_zone_id'])
    try: dem_data = taz_dic[taz]
    except: 
        taz = random.choice(taz_dic.keys())
        dem_data = taz_dic[taz]
    if rd_num1 > dem_data['sex'][0]:
        agent.set_value(index, 'sex', 1)
    if rd_num2 > dem_data['esr'][0]:
        agent.set_value(index, 'emp', 1)
    if rd_num3 > dem_data['rac'][0]:
        agent.set_value(index, 'rac', 1)
    tmp = len(dem_data['inc'])
    if tmp == 2:
        if rd_num4 > dem_data['inc'][0]:
            agent.set_value(index, 'inc', 1)
    elif tmp == 3:
        if rd_num4 > dem_data['inc'][0] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]:
            agent.set_value(index, 'inc', 1)
        elif rd_num4 > dem_data['inc'][0]+dem_data['inc'][1] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]+dem_data['inc'][2]:
            agent.set_value(index, 'inc', 2)
    elif tmp == 4:
        if rd_num4 > dem_data['inc'][0] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]:
            agent.set_value(index, 'inc', 1)
        elif rd_num4 > dem_data['inc'][0]+dem_data['inc'][1] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]+dem_data['inc'][2]:
            agent.set_value(index, 'inc', 2)
        elif rd_num4 > 1- dem_data['inc'][3]:
            agent.set_value(index, 'inc', 3)
    elif tmp == 5:
        if rd_num4 > dem_data['inc'][0] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]:
            agent.set_value(index, 'inc', 1)
        elif rd_num4 > dem_data['inc'][0]+dem_data['inc'][1] and rd_num3 <= dem_data['inc'][0]+dem_data['inc'][1]+dem_data['inc'][2]:
            agent.set_value(index, 'inc', 2)
        elif rd_num4 <= 1- dem_data['inc'][4] and rd_num3 > 1- dem_data['inc'][4]- dem_data['inc'][3]:
            agent.set_value(index, 'inc', 3)  
        elif rd_num4 > 1- dem_data['inc'][4]:
            agent.set_value(index, 'inc', 4)
print("--- %s seconds ---" % (time.time() - start_time)) 
with open('synthetic_pop.pickle', 'wb') as handle:
    pickle.dump(agent, handle)
    
#check if the dictionary keys are empty
#for item in taz_dic: 
#    if len(taz_dic[item]['sex'])==0:
#        del taz_dic[item]