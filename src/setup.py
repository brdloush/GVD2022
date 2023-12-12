#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import datetime

gtfspath = '../gtfs/vlakyCR.zip'
dbpath = '../GVD2024.sqlite'
gvdpath = '../szdc/2024'

yend = datetime.datetime(2024, 12, 14).date()

db = sqlite3.connect(dbpath)

def init():
    print('init')    

    db.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,filepath,filename,size INTEGER,date INTEGER)")

    db.execute("CREATE TABLE IF NOT EXISTS trips (trip_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,service_id INTEGER,gvdcal INTEGER,PAID,PAv,TRID,TRv,RPAID,RPAv,year,company,cdate DATETIME,sdate DATE,edate DATE,reroute,filepath,filename,route_id,tsn,tln,rsc INTEGER,ldate DATETIME,mtime INTEGER,negoff INTEGER(1),hexmap)")
    
    db.execute("CREATE INDEX IF NOT EXISTS trips_paid_ind ON trips(PAID)")
    db.execute('CREATE INDEX IF NOT EXISTS trips_rpaid_ind ON "trips" ("RPAID")')

    db.execute("CREATE TABLE IF NOT EXISTS cancel (trip_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,PAID,PAv,TRID,TRv,year,company,cdate DATETIME,sdate DATE,edate DATE,filepath,filename,ldate DATETIME,hexmap,bitmap)")

    db.execute("CREATE TABLE IF NOT EXISTS nspec (trip_id INTEGER(6), stop_id, name TEXT, value TEXT, Kod TEXT(3))")

    #db.execute("CREATE TABLE IF NOT EXISTS stop_times (trip_id INTEGER,arrival_time TIME,departure_time TIME,stop_id,stop_name,pickup_type INTEGER,drop_off_type INTEGER,otn INTEGER,tat,tt,ctt,psn INTEGER,stop_sequence INTEGER,nd INTEGER,pp)")
    #db.execute("CREATE TABLE IF NOT EXISTS stop_times (trip_id INTEGER,arrival_time TIME,departure_time TIME,stop_id,stop_name,pickup_type INTEGER(1),drop_off_type INTEGER(1))")
    db.execute("CREATE TABLE IF NOT EXISTS stop_times (trip_id INTEGER(6),stop_id INTEGER(7),arrival_time TIME,departure_time TIME,pickup_type INTEGER(1),drop_off_type INTEGER(1),stop_sequence INTEGER(3),tt TEXT(2),ctt TEXT(4),otn INTEGER(7),psn INTEGER(5),tat TEXT,nd INTEGER(1))")
    #db.execute("CREATE INDEX IF NOT EXISTS stop_times_tid_ind ON stop_times(trip_id)")
    #db.execute("CREATE INDEX IF NOT EXISTS stop_times_sid_ind ON stop_times(stop_id)")
    
    db.execute('CREATE TABLE IF NOT EXISTS stops (stop_id INTEGER(7) UNIQUE, sr70, stop_name TEXT, tar_nazev, typ, typname,stop_lat,stop_lon,vla,prov,g)')
    #db.execute('CREATE INDEX IF NOT EXISTS stops_sid ON stops(stop_id)')

    db.execute("CREATE TABLE IF NOT EXISTS 'gvdcal' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'mask')")
    db.execute("INSERT OR IGNORE INTO gvdcal (id,mask) VALUES ('0','0x0')")
    
    sql = "CREATE TABLE IF NOT EXISTS jr_zmeny (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, trip_id,from_id,typ,ocalid,calid,g_stops,g_times,nd,sdate DATE,edate DATE,ldate DATE,cisdate DATETIME, CONSTRAINT jr_zmenty_ui UNIQUE(trip_id,from_id) )"
    db.execute(sql)
    
    sql = "CREATE TABLE IF NOT EXISTS calendar (service_id INTEGER,monday INTEGER,tuesday INTEGER,wednesday INTEGER,thursday INTEGER,friday INTEGER,saturday INTEGER,sunday INTEGER,start_date INTEGER,end_date INTEGER)"
    db.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS calendar_dates(service_id INTEGER,date INTEGER,exception_type INTEGER)"
    db.execute(sql)
    
    db.execute("CREATE TABLE IF NOT EXISTS routes(route_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, agency_id,route_short_name,route_long_name,route_type DEFAULT '2', CONSTRAINT routes_uid UNIQUE(agency_id,route_short_name,route_long_name))")

    db.execute("CREATE TABLE IF NOT EXISTS agency (agency_id UNIQUE,agency_name,agency_short_name,agency_url,agency_timezone DEFAULT 'Europe/Prague',agency_lang DEFAULT 'cs',agency_phone)")

    db.execute('CREATE TABLE IF NOT EXISTS IDS (Kod UNIQUE, Zkratka, Nazev, Poznamka) ')
    db.execute('CREATE TABLE IF NOT EXISTS PoznamkyKJR (Kod UNIQUE, Nazev)')
    db.execute('CREATE TABLE IF NOT EXISTS Linky (Kod UNIQUE, Zkratka, Znacka, Nazev)')
    
if __name__ == '__main__':
    init()
