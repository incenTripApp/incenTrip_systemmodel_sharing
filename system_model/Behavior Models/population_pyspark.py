# -*- coding: utf-8 -*-


import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import multiprocessing as mp
import csv
import math 
import time 
import json
import requests

import random
from pytz import timezone
import os
from datetime import datetime
from datetime import timedelta
from time import gmtime, strftime
from itertools import islice
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import cgitb
import pickle
import pandas as pd
import time

#from agbm import parallel_agent
#from agbm import parallel_CA
#from agbm import CA_alternatives_spark
import csv
import sys

cgitb.enable()
import pyspark
import os,sys
##os.environ['JAVA_HOME']
os.environ['HADOOP_HOME']
os.environ['SPARK_HOME']
#os.environ['JAVA_HOME']='C:\Java'

sys.path.append('C:\opt\spark\spark-2.2.0-bin-hadoop2.7\python')
import findspark
findspark.init("C:\opt\spark\spark-2.2.0-bin-hadoop2.7")
# Spark home
spark_home = os.environ.get("SPARK_HOME")
sys.path.insert(0, spark_home + "\python")
sys.path.insert(0, os.path.join(spark_home, "python\lib\py4j-0.10.4-src.zip"))
sys.path.insert(0, os.path.join(spark_home, "python\lib"))
#make sure u do not have multiple instances of spark running
#pyspark.SparkContext().stop()
conf = pyspark.SparkConf()
conf.set("spark.executor.memory", '6g')
conf.set('spark.executor.cores', '16')
conf.set('spark.cores.max', '20')
conf.set("spark.driver.memory",'64g')
conf.setMaster("local[16]")
sc = pyspark.SparkContext.getOrCreate(conf=conf)
#############################
#from pyspark import SparkContext
#sc = SparkContext.getOrCreate()
start_time = time.time()

import numpy as np
df1 = pd.read_csv("Population/DC/person_synthetic.csv")
df2 = pd.read_csv("Population/MD/person_synthetic.csv")
df3 = pd.read_csv("Population/VA/person_synthetic.csv")
print("data loaded")
# need these data: gender, age, employment, income, geo

hh_dc = pd.read_csv("Population/DC/housing_synthetic.csv")
df1["hincgroup"] = ""

#generate a list of dictionaries for persons
def convert_personal_data(pdata):
    key_list = []
    for item in pdata:
        key_list.append(item)
        person_data = []
    for index in pdata.index:
        value_list = []
    #for value in df1.loc[index].values:
    #    value_list.append(value)
        dictmy=dict(zip(key_list,pdata.loc[index].values))
        person_data.append(dictmy)
    return person_data
            
def make_part_filter(index):
    def part_filter(split_index, iterator):
        if split_index == index:
            for el in iterator:
                yield el
    return part_filter


def generate_hinc(agent, hh_data):
    agent["hincgroup"]=int(hh_data.value[(hh_data.value.geo == agent['geo']) & 
                (hh_data.value.unique_id_in_geo == agent['unique_id_in_geo'])].hincgroup)
    if agent["hincgroup"]!=0:
    #else: 
        new_dict = dict((key,value) for key, value in agent.iteritems() if key in ('unique_person_id', 'unique_id_in_geo', 'geo', 
                        'page_18','AGEP', 'pesr', 'pgender', 'hincgroup'))
        return agent
        
    
start_time = time.time()
person_dc = convert_personal_data(df1)
broadcastVar = sc.broadcast(hh_dc)           
dots_dc = sc.parallelize(person_dc).map(lambda j:generate_hinc(j,broadcastVar))#.collect()    
dots_dc = [x for x in dots_dc if x is not None]            
print("DC data generated..")
print("--- %s seconds ---" % (time.time() - start_time))





hh_md = pd.read_csv("Population/MD/housing_synthetic.csv")
df2["hincgroup"] = ""
person_md = convert_personal_data(df2)
broadcastVar = sc.broadcast(hh_md)           
step = 600000
md_data = []
for i in range(int(len(person_md)/step)+1):
    start_time = time.time()
    k = i*step
    l = min(len(person_md), (i+1)*step)    
    dots_md = sc.parallelize(person_md[k:l]).map(lambda j:generate_hinc(j,broadcastVar))#.collect()    
    #dots_md = [x for x in dots_md if x is not None]  
    md_data.append(dots_md)
    print("--- %s partition %s seconds ---" % (i,time.time() - start_time))
sum_data =md_data[0]+md_data[1]+md_data[2]+md_data[3]+md_data[4]+md_data[5]+md_data[6]+md_data[7]+md_data[8]
#final_data = [x for x in sum_data if x is not None] 
print("MD data generated..")
print("--- %s seconds ---" % (time.time() - start_time))

for part_id in range(sum_data.getNumPartitions()):
    start_time = time.time()
    part_rdd = sum_data.mapPartitionsWithIndex(make_part_filter(part_id), True)
    data_from_part_rdd = part_rdd.collect()
    final_data = [x for x in data_from_part_rdd if x is not None] 
    md_data = md_data + final_data
    print "partition id: %s elements: %s" % (part_id, len(final_data))
    print("--- %s partition collected in %s seconds ---" % (i,time.time() - start_time))


hh_va = pd.read_csv("Population/VA/housing_synthetic.csv")
df3["hincgroup"] = ""
person_va = convert_personal_data(df2)
broadcastVar = sc.broadcast(hh_va)           
step = 600000
va_data = []
for i in range(int(len(person_va)/step)+1):
    start_time = time.time()
    k = i*step
    l = min(len(person_va), (i+1)*step)    
    dots_va = sc.parallelize(person_va[k:l]).map(lambda j:generate_hinc(j,broadcastVar)).collect()    
    dots_va = [x for x in dots_va if x is not None]  
    va_data.append(dots_va)
    print("--- %s partition %s seconds ---" % (i,time.time() - start_time))
print("VA data generated..")






#start_time = time.time()
#hh_va = pd.read_csv("Population/VA/housing_synthetic.csv")
#df3["hincgroup"] = ""
#person_va = convert_personal_data(df3)
#broadcastVar = sc.broadcast(hh_va)           
#dots_va = sc.parallelize(person_va).map(lambda j:generate_hinc(j,broadcastVar)).collect()    
#dots_va = [x for x in dots_va if x is not None] 
#print("VA data generated..")  
#print("--- %s seconds ---" % (time.time() - start_time))

# concatenating objects
persons = dots_dc + md_data + va_data

# this is the concatenation of three pandas dataframes
#frames = [df1, df2, df3]
#result=pd.concat(frames)


# selected data: geo: TAZ id, age_18: age divided into 18 groups, 
# AGEP: actual age, pesr: employment (1: employed; 2 otherwise)
# pgender: 1-male; 2-female. hincgroup: income category 1 (15K minus),2,3,4,5 (100K plus)
import pickle
with open('synthetic_population.pickle', 'wb') as handle:
    pickle.dump(persons, handle)