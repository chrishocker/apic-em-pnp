#!/usr/bin/env python3

#
# (C) Cisco Systems Inc.
# Maintened by Ivan Villalobos ivillalo@cisco.com
# Can be used and modified freely
#

#
# Revision: 1.1 9/29/16
#

# System libraries
import os, sys, os.path, json, glob, csv

from login import login
from configuration import DNS, DOMAIN, NTP, LUSER, LUPASS, VLANS, SNMP

#
## Global variables
#

initial_ip = 30

#
## Functions
#

def LoadInventory( file ):
	t_file = open( file, "r" )
	csv_f = csv.reader( t_file )
	line_num = 0
	result = []

	# Quick check to make sure all fields are present
	for row in csv_f:
		if ( row[0] == "" or row[1] == "" or row[2] == "" ):
			print( "Call error: a field is missing in line",line_num+1 )
			return "666"
		else:
			result.append( row )
			line_num += 1
				
		t_file.close()
		return result

def CreateProject(apic, project_name):
    project = apic.pnpproject.getPnpSiteByRange(siteName=project_name)

    if project.response != []:
        project_id = project.response[0].id
    else:
        # create it
        print ( "\nCreating project:{project}".format( project=project_name ) )
        pnp_task_response= apic.pnpproject.createPnpSite( project=[{'siteName' :project_name}] )
        task_response = apic.task_util.wait_for_task_complete( pnp_task_response, timeout=5 )

        # 'progress': '{"message":"Success creating new site","siteId":"6e059831-b399-4667-b96d-8b184b6bc8ae"}'
        progress = task_response.progress
        project_id = json.loads( progress )['siteId']

    return project_id

def CheckFile(apic, namespace, filename):
    filename = filename
    file_list = apic.file.getFilesByNamespace( nameSpace=namespace )
    fileid_list = [file.id for file in file_list.response if file.name == filename]
    return None if fileid_list == [] else fileid_list[0]

def UploadFile(apic, filename):
    file_id = CheckFile( apic, "config", filename )
    if file_id is not None:
        print( "File %s already uploaded: %s" %( filename, file_id ) )
        return file_id

    file_result = apic.file.uploadFile( nameSpace="config", fileUpload=filename )
    file_id = file_result.response.id
    return file_id

def CreateRule( apic,serial_number,host_name,platform,project_id,file_id ):
    rule_data = [{
        "serialNumber": serial_number,
        "platformId": platform,
        "hostName": host_name,
        "configId": file_id,
        "pkiEnabled": True
}]
    #print(json.dumps(rule_data,indent=2))
    rule_task = apic.pnpproject.createPnpSiteDevice(projectId=project_id, rule=rule_data)
    task_response = apic.task_util.wait_for_task_complete(rule_task, timeout=5)
    progress = task_response.progress
    print(progress)

#
# Main
#

# Collect information
storenum = input( "Store number: " )
inventory_file = "inventory-st00" + storenum + ".txt"

# Login to APIC-EM first
apic = login()

# Generate project
project_name = "ST-00"+storenum
project_id = CreateProject( apic, project_name )
print( "Created, ID", project_id, "\n" )

# Load inventory file
inventory = LoadInventory( inventory_file )
if inventory == "666":
	print( "Error loading file!" )
	exit
print( "\nInventory file loaded.", len( inventory ), "entries loaded." )

# Get Hostnames
hostnames = [device[1] for device in inventory]

# Main loop to generate configuration files
for host_index in hostnames:
	print( "Generating configuration for router:",host_index )
	
	working_file = open( host_index+".txt","w" )
	
	# Hostname
	working_file.write( "hostname "+host_index+"\n" )
	
	# DNS Configuration
	
	DNSlist = DNS.split( "," )
	working_file.write( "ip domain-name "+DOMAIN+"\n" )
	for DNSip in DNSlist:
		working_file.write( "ip name-server "+DNSip+"\n" )
		
	# NTP Server
	
	NTPlist = NTP.split( "," )
	for NTPip in NTPlist:
		working_file.write( "ntp server "+NTPip+"\n" )
	
	# AAA Stuff
	
	working_file.write( "aaa new-model\naaa authentication login default local\naaa authentication enable default none\naaa authorization console\n" )
		
	# Default local user
	
	working_file.write( "username "+LUSER+" privilege 15 password 7 "+LUPASS+"\n" )
	
	# Disable HTTP
	
	working_file.write( "no ip http server\nno ip http secure-server\n" )

	# SMTP String
	
	working_file.write( "snmp-server community "+SNMP+" RW\n" )
	
	#End
	initial_ip += 1
	working_file.close()

# Upload files to APIC-EM and create a configuration rule.
os.chdir(".")
files =  glob.glob("st-00"+storenum+"*.txt")

if len( files ) > 0:
	print( "Uploading configuration files to APIC-EM\nFound", len(files), "file(s) in this directory to upload:" )
	index = 0

	for working_file in files:
		print( "Uploading file: ",working_file,"...",end="")
		file_id = UploadFile( apic, working_file )
		print( "File ID: ", file_id )
		CreateRule( apic, inventory[index][0], inventory[index][1], inventory[index][2], project_id, file_id )
		index += 1

	print( "\nALL DONE!!!" )
else:
	print( "No files found to load!" )
