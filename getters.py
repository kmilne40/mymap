import os
from collections import defaultdict
from termcolor import colored
import re

# In this file: functions that get stuff and return it without needing other functions

def get_target():
    #get target ip/file
    while True:
        target = input(colored("\nEnter an IP address or file:\n-> ", "yellow"))

        #if it is an IP address
        if re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', target):  
            print(colored("\nValid IP address entered.", "green"))
            break  
        else:
            #if it is not an IP check if it is a file which exists
            if os.path.isfile(target) == False:
                print((colored("\nNo valid IP address or file found.", "red")))
            else:
                print(colored("\nFile located.", "green"))
                break
    return target


def get_scripts():
    # Directory where Nmap scripts are stored
    scripts_dir = "/usr/share/nmap/scripts/"
    try:
        # Get a list of all scripts in the directory
        scripts = os.listdir(scripts_dir)
    except FileNotFoundError:
        print("The directory does not exist.")
        return defaultdict(list)
    except PermissionError:
        print("You do not have the necessary permissions to read the directory.")
        return defaultdict(list)

    # Create a dictionary to categorize scripts
    categorized_scripts = defaultdict(list)
    for script in scripts:
        # Use the prefix of the script name as the category
        category = script.split("-")[0]
        categorized_scripts[category].append(script)
    
    # Sort categories and scripts within each category
    for category in categorized_scripts:
        categorized_scripts[category] = sorted(categorized_scripts[category])
    
    # Add SSL, SMB, SSH, RDP, DATABASE, VULN, BRUTE, FTP, MAINFRAME and RPC sub-menus
    categorized_scripts["SSL"] = []
    categorized_scripts["SMB"] = []
    categorized_scripts["SSH"] = []
    categorized_scripts["RDP"] = []
    categorized_scripts["DATABASE"] = []
    categorized_scripts["VULN"] = []
    categorized_scripts["BRUTE"] = []
    categorized_scripts["FTP"] = []
    categorized_scripts["RPC"] = []
    categorized_scripts["MAINFRAME"] = []

    # Populate the sub-menus with the appropriate scripts
    for script in scripts:
        if script.startswith("ssl"):
            categorized_scripts["SSL"].append(script)
        elif script.startswith("smb"):
            categorized_scripts["SMB"].append(script)
        elif script.startswith("ssh"):
            categorized_scripts["SSH"].append(script)
        elif script.startswith("rdp"):
            categorized_scripts["RDP"].append(script)
        elif script.startswith(("tn3270","nwg-tn3270", "cics","nwg-cics","tso","nwg-tso", "vtam","nwg-vtam", "lu","nwg-lu", "db2", "nwg-db2","ims","nwg-ims")):
            categorized_scripts["MAINFRAME"].append(script)
        elif script.startswith(("oracle", "mysql", "mssql", "ms-sql", "pgsql", "db2")):    
                    categorized_scripts["DATABASE"].append(script)
        elif "vuln" in script:
            categorized_scripts["VULN"].append(script)
        elif "brute" in script:
            categorized_scripts["BRUTE"].append(script)
        elif "ftp" in script:
            categorized_scripts["FTP"].append(script)
        elif "rpc" in script:
            categorized_scripts["RPC"].append(script)

    # Return the categorized scripts as a sorted dictionary
    return dict(sorted(categorized_scripts.items()))

def get_port():
    # Ask the user for the port to scan
    while True:
        print(colored("\nEnter port option:", "yellow"))
        print(colored("- leave blank for default", "yellow"))
        print(colored("- 'all' for all ports", "yellow"))
        print(colored("- single port/list e.g. '8080' or '8080,443,25'", "yellow"))
        port = input(colored("-> ", "yellow"))

        if port.lower() == "":
            port = ""
            break
        elif port.lower() == "all":
            port = "-p-"
            break
        else:
            #input validation, only allow numbers and commas
            if not re.match(r'^[0-9,]+$', port):
                print(colored("\nInvalid port option", "red"))
            else:
                port = "-p " + port
                break
    return port
