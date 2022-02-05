#!/usr/bin/env python3
# -*- coding: utf-8 

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
                st = os.stat(pp)
                if pp.endswith('.xml.zip'):
                    parse(gzip.open(pp).read(), path, f, st.st_mtime)
                    db.execute("INSERT INTO files (filepath,filename,date) VALUES('"+path+"','"+f+"','"+str(st.st_mtime)+"')")
                    #break #test stop:)
                    #if f[:2] == 'PA':
                    #    break;
                else:
                    zf = zipfile.ZipFile(pp)
                    for e in zf.namelist():
                        t = zf.getinfo(e).date_time
                        mt = datetime.datetime( t[0],t[1],t[2],t[3],t[4],t[5] )
                        parse( zf.read(e), f, e, mt.timestamp())
                        #break
                    db.execute("INSERT INTO files (filename,date) VALUES('"+f+"','"+str(st.st_mtime)+"')")
    db.commit()

def parse(s, filepath=None, filename=None, mtime=None):
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
    ldate = datetime.datetime.now().isoformat('T', 'seconds')
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
    
    if msg == True:
        val =  [PAID, PAv, TRID, TRv, RPAID, RPAv,year,company,cdate,sdate,edate,filepath,filename,ldate,mtime,hexmap] 
        tid = dbi('trips', 'PAID,PAv,TRID,TRv,RPAID,RPAv,year,company,cdate,sdate,edate,filepath,filename,ldate,mtime,hexmap', val).lastrowid
        db.execute("INSERT OR IGNORE INTO agency (agency_id) VALUES('"+company+"')")
        print(tid, filepath, filename)
        negoff = None
        otns = []
        otnsx = set()
        tr = []
        ss = rsc = 0
        for e in root.iter('CZPTTLocation'):
            ss += 1
            loc = e.find('Location')
            #iso = loc.find('CountryCodeISO').text.replace('CZ','54').replace('SK','56')
            iso = loc.find('CountryCodeISO').text
            iso = diso[iso]
            stop_id = loc.find('LocationPrimaryCode').text
            stop_name = loc.find('PrimaryLocationName').text
            atime = dtime = None
            for t in e.iter('Timing'):
                tqc = t.get('TimingQualifierCode')
                if tqc == 'ALA':
                    atime = ofs(t, negoff)
                elif tqc == 'ALD':
                    if negoff == None:
                        negoff = int( (t.find('Offset').text) )
                    dtime = ofs(t, negoff)  
            tat = set()
            pt = dot = 1
            tt = ctt = ptt = psn = nd = None
            for t in e.iter('TrainActivityType'):
                tat.add( t.text )
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
                ptt = tt
                tt = gctt(x.text)
            x = e.find('CommercialTrafficType')
            if x != None:
                ctt = gctt(x.text)            
            x = e.find('OperationalTrainNumber')
            if x != None:
                otn = x.text
                otnsx.add(otn)
            if tt != 'C4' or ptt != 'C4':
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
                if pt != 1 and dot != 1:
                    rsc += 1
                    if otn not in otns and tt != 'C4':
                        otns.append(otn)
                        tr.append((ctt if ctt else tt)+' '+otn)
            for p in e.findall('NetworkSpecificParameter'):
                n = p.find('Name').text
                v = p.find('Value').text
                if n == 'CZPassengerServiceNumber':
                    psn = v
                elif n == 'CZAlternativeTransport':
                    nd = v
            val = [tid,atime,dtime,iso+stop_id,pt,dot,ss,tt,ctt,otn,psn,'-'.join(tat),nd]
            dbi('stop_times','trip_id,arrival_time,departure_time,stop_id,pickup_type,drop_off_type,stop_sequence,tt,ctt,otn,psn,tat,nd',val)
            db.execute("INSERT OR IGNORE INTO stops(stop_id,stop_name) VALUES("+iso+stop_id+",'"+stop_name+"')")
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
        if len(tr) > 0 and tname != None:
            tr[0] = tr[0] + ' ' + tname
        if len(otns) == 0:
            otns.append(otn)
        tln = ' /'.join(tr)
        rid = grid(company,min(otns), tln )

        us = set()
        if len(otns) > 0:
            us.add("tsn='"+min(otns)+"'")
        us.add( "tln='"+tln+"'" )
        us.add( "rsc='"+str(rsc)+"'" )
        if reroute != None:
            us.add( "reroute='"+reroute+"'" )
        us.add("negoff='"+str(negoff)+"'")
        us.add("route_id='"+str(rid)+"'")
        v = ', '.join( us )
        sql = "UPDATE trips SET "+v+" WHERE trip_id='"+str(tid)+"'"
        #print(sql)
        db.execute(sql)

    elif can == True:
        val = [PAID,PAv,TRID,TRv,year,company,cdate,sdate,edate,hexmap,bitmap,filepath,filename,ldate]
        dbi('cancel', 'PAID,PAv,TRID,TRv,year,company,cdate,sdate,edate,hexmap,bitmap,filepath,filename,ldate', val)
        db.execute("UPDATE trips SET service_id = -abs(service_id) WHERE PAID = '"+PAID+"' ")

def ofs(tm, negoff):
    #print(tm, negoff)
    t = tm.find('Time').text[:8]
    o = tm.find('Offset').text
    if negoff == 0 and o == '0':
        return t
    return str(int(t[:2])+( (abs(negoff)+int(o))*24))+t[2:]   

def grid(company,rsn,rln):
    db.execute("INSERT OR IGNORE INTO routes (agency_id,route_short_name,route_long_name) VALUES('"+company+"','"+rsn+"','"+rln+"')")
    return db.execute("SELECT route_id FROM routes WHERE agency_id='"+company+"' AND route_short_name='"+rsn+"' AND route_long_name='"+rln+"' ").fetchone()[0]
  
def dbi(table, name, val, oi=''):
    #print(val)
    v = "'"+("','".join( map(str, val) ))+"'"
    v = v.replace("'None'","NULL")
    sql = "INSERT "+ oi +" INTO "+table+" ("+name+") VALUES("+v+")"
    #print(sql)
    return db.execute(sql)

diso = {'CZ': '54', 'SK': '56', 'PL': '51', 'DE': '80', 'AT': '81'}
    
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
    ldate = datetime.datetime.now().isoformat('T', 'seconds')
    sql = "SELECT trip_id,PAID,service_id,hexmap,sdate,edate,cdate,negoff FROM trips WHERE service_id < 0 OR service_id IS NULL"
    #print(sql)
    cur = db.execute(sql)
    for row in cur:
        print('cc', row[1])
        sid = row[2]
        if sid == None:
            sid = getcal( int( row[3], 0 ) )
            dbi('jr_zmeny','trip_id,typ,calid,sdate,edate,ldate,cisdate',[ row[0], 'a', sid, row[4], row[5], ldate, row[6] ], oi='OR IGNORE')
        sql2 = "SELECT trip_id,PAID,'e',sdate,edate,cdate,hexmap FROM trips WHERE RPAID = '"+row[1]+"' UNION ALL SELECT trip_id,PAID,'c',sdate,edate,cdate,hexmap FROM cancel WHERE PAID = '"+row[1]+"' ORDER BY cdate ASC"
        c2 = db.execute(sql2)
        bm = int(row[3], 0)
        for r2 in c2:
            print('cc\t',r2[0], r2[2])
            a = int( r2[6], 0)
            bm = ( bm ^ a ) & bm
            nsid = getcal(bm)
            if sid != nsid:
                print('cc\t', sid, ' > ', nsid)
                dbi('jr_zmeny','trip_id, from_id, typ, ocalid, calid, sdate, edate, ldate, cisdate',[ row[1], r2[0], r2[2],sid, nsid, r2[3], r2[4],ldate, r2[5] ], oi='OR IGNORE')
                sid = nsid
        if row[2] == None or abs(row[2]) != sid:
            gsid = sid
            if row[7] != 0:
                gsid = getcal( bm << abs(row[7]) )
            sql = "UPDATE trips SET service_id = '"+str(gsid)+"', gvdcal = '"+str(sid)+"' WHERE trip_id = '"+str(row[0])+"'"
            #print(sql)
            db.execute(sql)
    db.commit()
    
def hex2gtfs():
    print('hex2gtfs')
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

def dup():
    tt = time.time()
    print('dup')
    sql = "SELECT PAID FROM trips WHERE service_id != 0 OR service_id IS NULL GROUP BY PAID,PAv HAVING count(*) > 1"
    sql = "SELECT trip_id,PAID,PAv,mtime FROM trips WHERE PAID IN("+sql+") ORDER BY PAID, mtime DESC"
    #print(sql)
    s = set()
    cur = db.execute(sql)
    for row in cur:
        print(row)
        k = row[1]+'_'+row[2]
        if k not in s:
            s.add(k)
        else:
            db.execute("UPDATE trips SET service_id='0' WHERE trip_id = '"+str(row[0])+"'")
    print('s:::',s)
    db.commit()
    print("cas", (time.time()-tt))

def pp():
    print('pp')
    db.execute("CREATE INDEX IF NOT EXISTS stop_times_tid_ind ON stop_times(trip_id)")
    db.execute("CREATE INDEX IF NOT EXISTS stop_times_sid_ind ON stop_times(stop_id)")

    db.execute("CREATE INDEX IF NOT EXISTS trips_tid_ind ON trips(trip_id)")

    db.execute("CREATE INDEX IF NOT EXISTS nspec_tid_ind ON nspec(trip_id)")

    dup()

    calcal()
    hex2gtfs()

if __name__ == '__main__':
    t1 = time.time()
    setup.init()
    update()
    pp()
    print("cas:", time.time() - t1)
