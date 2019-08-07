#!/usr/bin/python
# -*- coding: utf-8
import pymongo, mysql.connector, urllib2, sys, datetime
from pymongo import errors as Mongo
from mysql.connector import errors
 
class masscanCheck():
	found = int(0)
	iteration = int(0)
	startdate = datetime.datetime.now()
	errorlogfilepath = "./mongo-check-sql-errors.log"
	link = mysql.connector.connect( user='SQL_USERNAME', password='SQL_PASSWORD',
						host='localhost', database='masscan' )
	sqlGet = link.cursor( buffered=True )
	sqlPut = link.cursor( buffered=False )
			
	def ipConvert(self, ipAddress ):
		oc1 = int(ipAddress / 16777216) % 256
		oc2 = int(ipAddress / 65536) % 256
		oc3 = int(ipAddress / 256) % 256
		oc4 = int(ipAddress) % 256
		return str(oc1) +"."+ str(oc2) +"."+ str(oc3) +"."+ str(oc4)
					
	def mongo( self, big ):
		result = { 
			"usedSpace": 0.00, "query": "", "bases": 0, "good": False,
		}
		conn = pymongo.MongoClient( self.ipConvert( big ), serverSelectionTimeoutMS=100 )
		try:
			result['usedSpace'] = conn.admin.command("listDatabases")['totalSize']
			result['bases'] = len(conn.admin.command("listDatabases")['databases'])
		except (Mongo.ServerSelectionTimeoutError, Mongo.NetworkTimeout, 
				pymongo.errors.ServerSelectionTimeoutError, Mongo.ConfigurationError, Mongo.OperationFailure):
			pass
		finally:
			if result['usedSpace'] > 0:
				result['query'] = "UPDATE `data` \
				SET `banner` = 'Mongo checked', \
					`service` = 'mongo', \
					`title` = 'not secured: "+ str(result['usedSpace'] / 1024 / 1024) +"mb used space by "+ str(result['bases']) +" databases' \
				WHERE `ip` = '"+ str(big) +"';"
				result['good'] == True
			else:
				result['query'] = "UPDATE `data` \
					SET `banner`= 'Mongo checked', \
						`service` = 'mongo', \
						`title` = 'secured' WHERE `ip` = '"+ str(big) +"';"
			conn.close
			return result
	
	def elastick( self, big ):
		try:
			print "elk begin"
		finally:
			print "elk def"
			print self.ipConvert( big )

masscan = masscanCheck()
if( len(sys.argv) < 2 ):
	sys.exit(
	"\t\033[93mWARNING: Designed to demonstrate the power of the Python interpreter.\
	\n\tCOPYRIGHT: Designed by molemime (c) at 2019 For education use only. \033[0m\
	\n\n\tEXAMPLES:\
	\n\tFor update masscan DB strcture first: \t\033[1m python "+ sys.argv[0] +" init \033[0m\
	\n\tFor ckeking mongo service: \t\t\033[1m python "+ sys.argv[0] +" (mongo|mongo-full) \033[0m\n")
	
if( len(sys.argv) > 1 and sys.argv[1] == "init" ):
	try:
		masscan.sqlPut.execute("ALTER TABLE `data` CHANGE `banner` `banner` TEXT CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL;")
		masscan.sqlPut.execute("ALTER TABLE `data` CHANGE `title` `title` TEXT CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL;")
		masscan.sqlPut.execute("UPDATE `data` SET `banner`= NULL,`title`= NULL;")
		masscan.link.commit()
		masscan.link.close()
	finally:
		sys.exit( "masscan DB init complete" ) 
		
if( len(sys.argv) > 1 and sys.argv[1] == "mongo"):
	masscan.sqlGet.execute( "SELECT * FROM `data` WHERE \
			`title` IS NULL AND ( \
				`port_id` = '27018' OR \
				`port_id` = '27017' OR \
				`port_id` = '27019');" )
	sys.stdout.write( "Mongo available service search started at "+ str(masscan.startdate) +"\n" )
	for line in masscan.sqlGet.fetchall():
		data = masscan.mongo( line[1] )
		masscan.sqlPut.execute( data['query'] )
		sys.stdout.write( "[ -"+ str( int(round(masscan.iteration) / round(masscan.sqlGet.rowcount) * 100.00) ) +
		"%- ] \t -> GOOD: "+ str( int(masscan.found)) +"\r" )
		sys.stdout.flush()
		if( data['good'] == True ):
			masscan.found += 1
		masscan.iteration += 1

if( len(sys.argv) > 1 and sys.argv[1] == "mongo-full"):
	masscan.sqlGet.execute( "SELECT * FROM `data` WHERE \
			`port_id` = '27018' OR \
			`port_id` = '27017' OR \
			`port_id` = '27019';" )
	sys.stdout.write( "Mongo available service research started at "+ str(masscan.startdate) +"\n" )
	for line in masscan.sqlGet.fetchall():
		data = masscan.mongo( line[1] )
		masscan.sqlPut.execute( data['query'] )
		sys.stdout.write( "[ -"+ str( int(round(masscan.iteration) / round(masscan.sqlGet.rowcount) * 100.00) ) +
		"%- ] \t -> GOOD: "+ str( int(masscan.found)) +"\r" )
		sys.stdout.flush()
		if( data['good'] == True ):
			masscan.found += 1
		masscan.iteration += 1

sys.stdout.write( "Ckecing done at "+ str(datetime.datetime.now()) +"\n" )
sys.stdout.write( "\033[1mFounded "+ str(masscan.found) +" available service.\033[0m\n\n" )
