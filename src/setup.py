#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import datetime

gtfspath = '../gtfs/vlakyCR.zip'
dbpath = '../GVD2022.sqlite'
gvdpath = '../szdc/2022'

yend = datetime.datetime(2022, 12, 10).date()

db = sqlite3.connect(dbpath)

def init():
    print('init')    

    db.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,filepath,filename,size INTEGER,date REAL)")
    
    db.execute("CREATE TABLE IF NOT EXISTS trips (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,trip_id,service_id INTEGER,gvdcal INTEGER,PAID,PAv,TRID,TRv,RPAID,RPAv,year,company,cdate DATETIME,sdate DATE,edate DATE,reroute,filepath,filename,route_id,tname,tsn,tln,psn,otns,rsc INTEGER,ldate DATETIME,negoff INTEGER,hexmap,bitmap)")
    db.execute("CREATE INDEX IF NOT EXISTS trips_tid_ind ON trips(trip_id)")
    db.execute("CREATE INDEX IF NOT EXISTS trips_paid_ind ON trips(PAID)")
    db.execute('CREATE INDEX IF NOT EXISTS trips_rpaid_ind ON "trips" ("RPAID")')
    
    db.execute("CREATE TABLE IF NOT EXISTS cancel (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,trip_id,PAID,PAv,TRID,TRv,year,company,cdate DATETIME,sdate DATE,edate DATE,filepath,filename,ldate DATETIME,hexmap,bitmap)")
    
    db.execute("CREATE TABLE IF NOT EXISTS nspec (trip_id, stop_id, name, value, Kod)")
    db.execute("CREATE INDEX IF NOT EXISTS nspec_tid_ind ON nspec(trip_id)")
    
    
    db.execute("CREATE TABLE IF NOT EXISTS stop_times (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,trip_id,arrival_time TIME,departure_time TIME,stop_id,cis_id,stop_name,ALA TIME,ppa INTEGER,ALD TIME,ppd INTEGER,pickup_type INTEGER,drop_off_type INTEGER,otn,tat,tt,ctt,psn,stop_sequence INTEGER,obj,nd)")
    db.execute("CREATE INDEX IF NOT EXISTS stop_times_tid_ind ON stop_times(trip_id)")
    db.execute("CREATE INDEX IF NOT EXISTS stop_times_sid_ind ON stop_times(stop_id)")
    
    db.execute("CREATE TABLE IF NOT EXISTS 'gvdcal' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'mask')")
    db.execute("INSERT OR IGNORE INTO gvdcal (id,mask) VALUES ('0','0x0')")
    
    sql = "CREATE TABLE IF NOT EXISTS jr_zmeny (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, trip_id,from_id,typ,ocalid,calid,g_stops,g_times,nd,sdate DATE,edate DATE,ldate DATE,cisdate DATETIME, CONSTRAINT jr_zmenty_ui UNIQUE(trip_id,from_id) )"
    db.execute(sql)
    
    db.execute('CREATE TABLE IF NOT EXISTS stops (stop_id UNIQUE, stop_cis, sr70, stop_name, tar_nazev, typ, typname,stop_lat,stop_lon,vla,prov,g)')
    db.execute('CREATE INDEX IF NOT EXISTS stops_sid ON stops(stop_id)')
    
    db.execute("CREATE TABLE IF NOT EXISTS agency (agency_id UNIQUE,agency_name,agency_short_name,agency_url,agency_timezone DEFAULT 'Europe/Prague',agency_lang DEFAULT 'cs',agency_phone)")

    db.execute('CREATE TABLE IF NOT EXISTS IDS (Kod UNIQUE, Zkratka, Nazev, Poznamka) ')
    db.execute('CREATE TABLE IF NOT EXISTS PoznamkyKJR (Kod UNIQUE, Nazev)')
    db.execute('CREATE TABLE IF NOT EXISTS Linky (Kod UNIQUE, Zkratka, Znacka, Nazev)')
    
if __name__ == '__main__':
    init()
