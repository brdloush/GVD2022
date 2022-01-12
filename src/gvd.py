#!/usr/bin/env python3
# -*- coding: utf-8 -*

import setup
from setup import db
import os,zipfile,gzip,datetime
import xml.etree.ElementTree as ET
import time

cal = None
dtt = None

def update(path=None):
    print('update', path)
    fl = set() # na dict a kontrola
    cur = db.execute('SELECT filename FROM files')
    for row in cur:
        fl.add(row[0])
    p = setup.gvdpath
    if path != None:
        p = os.path.join(p, path)
    for f in os.listdir(p):
        pp = os.path.join(p, f)
        if os.path.isdir(pp):
            update(f)
        else:
            if f not in fl:
                if pp.endswith('.xml.zip'):
                    parse(gzip.open(pp).read(), path, f)
                    db.execute("INSERT INTO files (filename) VALUES('"+f+"')")
                    #break #test stop:)
                    #if f[:2] == 'PA':
                    #    break;
                else:
                    zf = zipfile.ZipFile(pp)
                    for e in zf.namelist():
                        parse( zf.read(e), f, e)
                        #break
                    db.execute("INSERT INTO files (filename) VALUES('"+f+"')")
    db.commit()

def parse(s, filepath=None, filename=None):
    root = ET.fromstring(s)
    msg = can = False
    if root.tag == 'CZPTTCISMessage':
        msg = True
    elif root.tag == 'CZCanceledPTTMessage':
        can = True
    for e in root.iter('PlannedTransportIdentifiers'):
        ot = e.find('ObjectType').text
        if ot == 'PA':
            PAID = e.find('Core').text
            PAv = e.find('Variant').text
            year = e.find('TimetableYear').text
        elif ot == 'TR':
            TRID = e.find('Core').text
            TRv = e.find('Variant').text
            company = e.find('Company').text
    tid = '_'.join( [PAID, PAv, year] )
    ldate = datetime.datetime.now().isoformat()
    RPAID = RPAv = None
    if msg == True:
        for e in root.iter('RelatedPlannedTransportIdentifiers'):
            if e.find('ObjectType').text == 'PA':
                RPAID = e.find('Core').text
                RPAv = e.find('Variant').text
        cdate = root.find('CZPTTCreation').text
    elif can == True:
        cdate = root.find('CZPTTCancelation').text
        
    if RPAID != None:
        db.execute("UPDATE trips SET service_id = -abs(service_id) WHERE PAID = '"+RPAID+"' ")
        
    r2 = root
    if can == False:
        r2 = root.find('CZPTTInformation')
    cal = r2.find('PlannedCalendar')
    bitmap = cal.find('BitmapDays').text
    vp = cal.find('ValidityPeriod')
    sdate = vp.find('StartDateTime').text[:10]
    edate = vp.find('EndDateTime').text[:10]
    hexmap = hex(int(bitmap, 2) << ( setup.yend.toordinal() - datetime.datetime.fromisoformat(edate).toordinal() ) )
    
    print(tid, filename)
    
    if msg == True:
        tr = []
        ss = 0
        negoff = None
        for e in root.iter('CZPTTLocation'):
            ss += 1
            loc = e.find('Location')
            iso = loc.find('CountryCodeISO').text.replace('CZ','54').replace('SK','56')
            #if iso != 'CZ':
            #    continue
            stop_id = loc.find('LocationPrimaryCode').text
            stop_name = loc.find('PrimaryLocationName').text
            ALA = ppa = ALD = ppd = None
            atime = dtime = None
            for t in e.iter('Timing'):
                tqc = t.get('TimingQualifierCode')
                if tqc == 'ALA':
                    ALA = atime = t.find('Time').text[:8]
                    ppa = t.find('Offset').text
                    atime = ofs(atime, ppa, negoff)
                elif tqc == 'ALD':
                    ALD = dtime = t.find('Time').text[:8]
                    ppd = t.find('Offset').text
                    if negoff == None:
                        negoff = int(ppd)
                    dtime = ofs(dtime, ppd, negoff)
                        
                        
            otn = tt = ctt = psn = None
            tat = set()
            lin = set()
            pt = dot = 1    
            for t in e.iter('TrainActivityType'):
                tat.add( t.text )
            if '0001' in tat:
                pt = 0; dot = 0
            if '0030' in tat:
                pt = 3
                dot = 3
            if '0028' in tat:
                dot = 1
            if '0029' in tat:
                pt = 1
            if 'CZ01' in tat: # at si zavolaji :)
                pt = 2
                dot = 2
                if stop_id == '34273': # Ostrava-Zábřeh, v provozu od 05/2023
                    pt = 1; dot = 1
            if atime == None:
                atime = dtime
            if dtime == None:
                dtime = atime
            if '0031' in tat or '0032' in tat:
                dtime = atime
            if atime != None and atime > dtime:
                atime = dtime
            x = e.find('TrafficType')
            if x != None:
                tt = x.text
            x = e.find('CommercialTrafficType')
            if x != None:
                ctt = x.text            
            x = e.find('OperationalTrainNumber')
            if x != None:
                otn = x.text
            ttt = gctt(tt)
            cttt = gctt(ctt)
            if pt != 1 and dot != 1:
                tr.append( [otn, ttt, cttt] )
            nd = obj = ''  
            for p in e.findall('NetworkSpecificParameter'):
                n = p.find('Name').text
                v = p.find('Value').text
                if n == 'CZAlternativeTransport':
                    nd = v
                elif n == 'CZPassengerPublicTransportOrderingCoName':
                    obj = v
                elif n == 'CZPassengerServiceNumber':
                    psn = v
                    lin.add(v)
                
            dbi( 'stop_times', 'trip_id,arrival_time,departure_time,stop_id,stop_name,ALA,ppa,ALD,ppd,pickup_type,drop_off_type,otn,tat,tt,ctt,psn,stop_sequence,obj,nd', [ tid, atime, dtime, iso+stop_id, stop_name, ALA, ppa, ALD, ppd, pt, dot, otn, '-'.join(tat), ttt, cttt,psn,ss,obj,nd ] )
            
        tname = reroute = None
        for e in root.findall('NetworkSpecificParameter'):
            name = e.find('Name').text
            value = e.find('Value').text
            kod = None
            if name =='CZCentralPTTNote':
                kod = value.split('|')[0]
            dbi("nspec","trip_id,name,value,kod", [tid, name, value, kod])
            if name == 'CZTrainName':
                tname = value
            elif name == 'CZReroute':
                reroute = value
        rsc = len(tr)
        tsn = ''
        tln = ''
        otns = []
        if rsc > 1:
            tr.pop(rsc-1)
            s = set()
            l = []
            if tname == None:
                tname2 = ''
            else:
                tname2 = ' '+tname
            for r in tr:
                if r[0] not in s:
                    s.add(r[0])
                    if r[2] == None:
                        r[2] = r[1]
                    l.append( r[2]+' '+r[0] + tname2 )
                    otns.append(r[0])
                    tname2 = ''
            tln = ' /'.join(l)
            tsn = min( map(int, s) )
        val = [tid, PAID, PAv, TRID, TRv, RPAID, RPAv, year, company,cdate,sdate,edate,reroute, hexmap,filepath,filename,tname,tsn,tln,'-'.join(lin),'_'.join(otns),rsc,ldate,negoff,bitmap]
        dbi("trips","trip_id,PAID,PAv,TRID,TRv,RPAID,RPAv,year,company,cdate,sdate,edate,reroute,hexmap,filepath,filename,tname,tsn,tln,psn,otns,rsc,ldate,negoff,bitmap", val)
    elif can == True:
        val = [tid,PAID,PAv,TRID,TRv,year,company,cdate,sdate,edate,hexmap,bitmap,filepath,filename,ldate]
        dbi('cancel', 'trip_id,PAID,PAv,TRID,TRv,year,company,cdate,sdate,edate,hexmap,bitmap,filepath,filename,ldate', val)
        db.execute("UPDATE trips SET service_id = -abs(service_id) WHERE PAID = '"+PAID+"' ")

def getcal(m):
    global cal
    if cal == None:
        cal = {}
        sql = "SELECT id,mask FROM gvdcal"
        cur = db.execute(sql)
        for row in cur:
            cal[ int( row[1], 0)] = row[0]
    if m in cal:
        return cal[m]
    else:
        sql = "INSERT INTO gvdcal(mask) VALUES( '"+ hex(m)  +"' )"
        db.execute(sql)
        #db.commit()
        r = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        print('service_id', r)
        cal[m] = r
        return r

def calcal():
    sql = "SELECT id,trip_id,PAID,service_id,hexmap,sdate,edate,cdate,negoff FROM trips WHERE service_id < 0 OR service_id IS NULL ORDER BY cdate ASC"
    #print(sql)
    cur = db.execute(sql)
    for row in cur:
        print('cc', row[1])
        sid = row[3]
        if sid == None:
            sid = getcal( int( row[4], 0 ) )
            dbi('jr_zmeny','trip_id,typ,calid,sdate,edate,ldate,cisdate',[ row[1], 'a', sid, row[5], row[6], datetime.datetime.now().isoformat(), row[7] ], oi='OR IGNORE')
        sql2 = "SELECT trip_id,PAID,'e',sdate,edate,cdate,hexmap FROM trips WHERE RPAID = '"+row[2]+"' UNION ALL SELECT trip_id,PAID,'c',sdate,edate,cdate,hexmap FROM cancel WHERE PAID = '"+row[2]+"' ORDER BY cdate ASC"
        c2 = db.execute(sql2)
        bm = int(row[4], 0)
        for r2 in c2:
            print('cc\t',r2[0], r2[2])
            a = int( r2[6], 0)
            bm = ( bm ^ a ) & bm
            nsid = getcal(bm)
            if sid != nsid:
                print('cc\t', sid, ' > ', nsid)
                dbi('jr_zmeny','trip_id, from_id, typ, ocalid, calid, sdate, edate, ldate, cisdate',[ row[1], r2[0], r2[2],sid, nsid, r2[3], r2[4],datetime.datetime.now().isoformat(), r2[5] ], oi='OR IGNORE')
                sid = nsid
        if row[3] == None or abs(row[3]) != sid:
            gsid = sid
            if row[8] != 0:
                gsid = getcal( bm << abs(row[8]) )
            sql = "UPDATE trips SET service_id = '"+str(gsid)+"', gvdcal = '"+str(sid)+"' WHERE id = '"+str(row[0])+"'"
            #print(sql)
            db.execute(sql)
    db.commit()
    
def hex2gtfs():
    print('hex2gtfs')
    sql = "CREATE TABLE IF NOT EXISTS calendar (service_id INTEGER,monday INTEGER,tuesday INTEGER,wednesday INTEGER,thursday INTEGER,friday INTEGER,saturday INTEGER,sunday INTEGER,start_date INTEGER,end_date INTEGER)"
    db.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS calendar_dates(service_id INTEGER,date INTEGER,exception_type INTEGER)"
    db.execute(sql)
    sql = "SELECT * FROM gvdcal WHERE id NOT IN(SELECT service_id FROM calendar)"
    cur = setup.db.execute(sql)
    for row in cur:
        m = int(row[1], 0)
        ed = setup.yend.toordinal()
        while m & 1 == 0 and m > 0:
            m = m >> 1
            ed -= 1
        edd = datetime.datetime.fromordinal( ed).date()
        sd = ed - m.bit_length() + 1
        sdd = datetime.datetime.fromordinal( sd ).date()
        e = datetime.datetime.fromordinal(ed)
        wd = e.isoweekday() - 1
        week = [0,0,0,0,0,0,0]
        m2 = m
        cd = 0
        while m2 > 0:
            cd += 1
            if m2 & 1 == 1:
                week[wd] += 1
            else:
                week[wd] -= 1
            wd -= 1
            if wd < 0:
                wd = 6
            m2 = m2 >> 1
        week2 = []
        for w in week:
            if w <= 0:
                week2.append(0)
            else:
                week2.append(1)
        m2 = m
        wd = edd.isoweekday() - 1
        xd = ed
        while m2 > 0: 
            if week2[wd] != m2 & 1:
                v = m2 & 1
                if v == 0:
                    v = 2
                exdate = datetime.datetime.fromordinal(xd).strftime('%Y%m%d')
                sql = "INSERT INTO calendar_dates(service_id,date,exception_type) VALUES('"+str(row[0])+"','"+exdate+"','"+str(v)+"')"
                db.execute(sql)
            m2 = m2 >> 1
            wd -= 1
            xd -= 1
            if wd < 0:
                wd = 6
        val = ",".join(map(str, week2))
        val2 = ",".join( [str(row[0]), val,sdd.strftime('%Y%m%d'), edd.strftime('%Y%m%d') ] )
        #print(val)
        sql = "INSERT INTO calendar(service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date) VALUES( "+val2+" ) "
        db.execute(sql)
        #print( bin(m) )
    db.commit()

def pp_route():    
    db.execute("CREATE TABLE IF NOT EXISTS routes(route_id,agency_id,route_short_name,route_long_name,route_type DEFAULT '2')")
    routes = None
    ids = set()
    sql = "SELECT company,tsn,tln,psn,otns,trip_id FROM trips WHERE route_id IS NULL"
    cur = db.execute(sql)
    for row in cur:
        if routes == None:
            routes = {} # maska, id
            c2 = db.execute("SELECT route_id,agency_id,route_short_name,route_long_name FROM routes")
            for r2 in c2:
                #print(r2)
                routes[ '#'.join(r2[1:]) ] = r2[0]
                ids.add(r2[0])

        m2 = '#'.join(row[:3])
        print(m2)
        if m2 not in routes:
            ks = row[4]
            id = ord('A')
            while ks in ids:
                ks = row[4]+'-'+chr(id)
                print(ks)
                id += 1
            dbi('routes',"route_id,agency_id,route_short_name,route_long_name",[ks,row[0], row[1], row[2] ])
            routes[m2] = ks
            ids.add(ks)
        db.execute("UPDATE trips SET route_id = '"+routes[m2]+"' WHERE trip_id = '"+row[5]+"'")
    
def pp():
    print('pp')
    sql = "INSERT INTO agency (agency_id) SELECT DISTINCT company FROM trips WHERE company NOT IN(SELECT agency_id FROM agency)"
    print(sql)
    db.execute(sql)
    
    #sql = "INSERT OR IGNORE INTO stops (stop_id,stop_name) SELECT DISTINCT stop_id,stop_name FROM stop_times WHERE pickup_type != '1' AND drop_off_type != '1'"
    #print(sql)
    #db.execute(sql)
    
    sql = "SELECT stop_id,stop_name FROM stop_times WHERE stop_id NOT IN(SELECT stop_id FROM stops WHERE stop_name IS NOT NULL) AND pickup_type != 1 GROUP BY stop_id"
    print(sql)
    cur = setup.db.execute(sql)
    for row in cur:
        print(row)
        sql = "INSERT INTO stops (stop_id, stop_name) VALUES('"+row[0]+"','"+row[1]+"') ON CONFLICT (stop_id) DO UPDATE SET stop_name = '"+row[1]+"' WHERE stop_id = '"+row[0]+"'"
        setup.db.execute(sql)
        
    pp_route()
    setup.db.commit()

def ofs(t, o, negoff):
    #print(t, o)
    if negoff == 0 and o == '0':
        return t
    return str(int(t[:2])+( (abs(negoff)+int(o))*24))+t[2:]

def dbi(table, name, val, oi=''):
    #print(val)
    v = "','".join( map(str, val) ).replace("'None'","NULL")
    sql = "INSERT "+ oi +" INTO "+table+" ("+name+") VALUES('"+v+"')"
    #print(sql)
    db.execute(sql)
    
def gctt(s):
    global dtt
    if dtt == None:
        dtt = {'11':'Os', 'C1':'Ex', 'C2':'R', 'C3':'Sp'}
        fp = '../res/SeznamKomercniDruhVlaku.xml'
        if os.path.exists(fp):
            for e in ET.parse(fp).getroot().findall('.//{http://provoz.szdc.cz/kadr}KomercniDruhVlaku'):
                #print(e.attrib)
                dtt[ e.attrib['KodTAF'] ] = e.attrib['Kod']
    if s in dtt:
        return dtt[s]
    else:
        return s

if __name__ == '__main__':
    
    t1 = time.time()
    
    setup.init()
    update()
    calcal()
    hex2gtfs()
    pp()
    
    print('cas', time.time() - t1)



