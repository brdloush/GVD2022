#!/usr/bin/env python3
# -*- coding: utf-8 -*

from setup import db
import setup
import os
import csv
import re
import xml.etree.ElementTree as ET 

setup.init()

def wgs(s):
    #print(s)
    deg, minutes, seconds, direction =  re.split('[°\'"]', s)
    seconds = seconds.replace(',','.')
    print(deg, minutes, seconds, direction)
    return str(round((float(deg) + float(minutes)/60 + float(seconds)/(60*60)) ,5))

fp = '../res/sr70.csv'
if os.path.exists(fp):
    fi = os.lstat(fp)
    sql = "SELECT date,size FROM 'files' WHERE filename = 'sr70.csv' ORDER BY rowid DESC LIMIT 1"
    row = db.execute(sql).fetchone()
    if row == None or fi.st_ctime > row[0] or fi.st_size != row[1]:
        c = csv.DictReader(open(fp))
        for row in c:
            #print(row)
            sid = 'CZ'+(row['SR70'][:-1].zfill(5))
            tn = row['Tarifní název']
            x = y = ''
            try:
                x = wgs(row['GPS X'][1:].replace("°'","°0'"))
                y = wgs(row['GPS Y'][1:].replace("°'","°0'"))
                print(x, y)
            except:
                print('err')
            val = [ sid, tn, y, x ]
            val2 = "','".join(val)
            sql = "INSERT INTO stops (stop_id,tar_nazev,stop_lat,stop_lon) VALUES('"+val2+"') ON CONFLICT (stop_id) DO UPDATE SET tar_nazev = '"+tn+"', stop_lat='"+y+"', stop_lon = '"+x+"'"
            db.execute(sql)
            #print(sql)
        db.execute("INSERT INTO files (filename,size,date) VALUES('sr70.csv','"+str(fi.st_size)+"','"+str(fi.st_ctime)+"')")
        db.commit()
    
def ag():
    fp = '../res/SeznamSpolecnosti.xml'
    if os.path.exists(fp) == False:
        return
    sql = "SELECT agency_id FROM agency WHERE agency_name IS NULL"
    cur = db.execute(sql)
    ags = set()
    for row in cur:
        print(row)
        ags.add( row[0] )
        
    if len(ags) != 0:
        print(ags)
        sp = ET.parse(fp).getroot()
        for aa in sp.findall('.//{http://provoz.szdc.cz/kadr}Spolecnost'):
            if 'EvCisloEU' in aa.attrib:
                agid = aa.attrib['EvCisloEU']
                if agid in ags:
                    www = 'http://'
                    if 'WWW' in aa.attrib:
                        www += aa.attrib['WWW']
                    print(www)
                    name = aa.attrib['ObchodNazev']
                    shname = aa.attrib['ZkrObchodNazev']
                    val = "','".join([ agid, name, shname, www ])
                    sql = "INSERT INTO agency (agency_id,agency_name,agency_short_name,agency_url) VALUES('"+val+"') ON CONFLICT (agency_id) DO UPDATE SET agency_name = '"+name+"', agency_short_name='"+shname+"', agency_url='"+www+"'"
                    
                    print(sql)
                    db.execute(sql)

ag()
db.commit()
