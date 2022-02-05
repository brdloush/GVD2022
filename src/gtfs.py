#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setup
from setup import db
import os
import pathlib
import zipfile
import csv

serid = set()
stopid = set()
routeid = set()

dir = pathlib.Path(setup.gtfspath).parent

if os.path.exists(dir) == False:
    os.makedirs(dir, exist_ok=True)

sthdr = 'trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type'    
fpt = open( os.path.join(dir, 'trips.txt'), 'w', encoding='utf-8', newline='' ) 
fptr = csv.writer( fpt )
fptr.writerow(['route_id','service_id','trip_id'])
fps = open( os.path.join(dir, 'stop_times.txt'), 'w', encoding='utf-8', newline=''  )
fpst = csv.writer( fps )
fpst.writerow(sthdr.split(','))

sql = "SELECT route_id,service_id,trip_id FROM trips WHERE service_id > 0 AND rsc > 1 ORDER BY cdate"
cur = db.execute(sql)

for row in cur:
    sql2 = "SELECT "+sthdr+" FROM stop_times WHERE trip_id = '"+str(row[2])+"' AND (pickup_type != '1' AND drop_off_type != '1') ORDER BY stop_sequence ASC"
    c2 = db.execute(sql2)
    for r2 in c2:
        fpst.writerow( r2 )
        stopid.add(r2[3])
    print(row)
    serid.add(row[1])
    routeid.add(int(row[0]))
    fptr.writerow( row )
fpt.close()
fps.close()

def cp(tbl,hdr,sid,sind,rtrn=0,end=''):
    r = set()
    fp = open( os.path.join(dir, tbl+'.txt'), 'w', encoding='utf-8', newline=''  )
    cfp = csv.writer(fp)
    cfp.writerow( hdr.split(',') )
    sql = "SELECT "+hdr+" FROM "+tbl+' '+end;
    cur = db.execute(sql)
    for row in cur:
        if row[sind] in sid:
            r.add(row[rtrn])
            #val = ('"'+('","'.join( map(str,row) )) +'"').replace('"None"', '""')
            print(row)
            #fp.write(''+val+'\r\n')
            cfp.writerow( s.replace('None','') for s in map(str, row) )
    fp.close()
    return r

cp('stops','stop_id,stop_name,stop_lat,stop_lon',stopid,0,end='ORDER BY stop_name ASC')  
agid = cp('routes','route_id,agency_id,route_short_name,route_long_name,route_type',routeid,0,1)
cp('agency','agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone',agid,0)

cp('calendar','service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date',serid,0)
cp('calendar_dates','service_id,date,exception_type',serid,0)

zf = zipfile.ZipFile(setup.gtfspath, 'w', compression=zipfile.ZIP_DEFLATED)
for f in os.listdir(dir):
    if f.endswith('.txt'):
        zf.write( os.path.join(dir, f), f)
zf.close()
    
