### This file includes all the misllaneous bob program helpers ###
from termcolor import colored
import pwinput as pw
import os

#Get user credentials 
def getUserCreds():
    #Storing and retreiving user credentials to re-use
    if os.path.exists('../creds.conf'):
        okta = input((colored("Found credential file but did you change your okta creds recently? y/n", "yellow")))
        if okta.lower() in ["n", "no"]:
            print(colored("Using saved creds", "yellow"))
        elif okta.lower() in ["y", "yes"]:
            username = input(colored("Enter your okta user(ex: vvemulapalli):", "yellow"))
            password = pw.pwinput(colored("Enter your okta pass:", "yellow"))
            #Creds file creation and storing user given credentials into the conf file for reutilization.
            fp = open('../creds.conf', "w+")
            fp.write('{u}\n{p}'.format(u=username, p=password))
            fp.close()
    else:
        print(colored("Did not find credential file", "yellow"))
        username = input(colored("Enter your okta user:", "yellow"))
        password = pw.pwinput(colored("Enter your okta pass:", "yellow"))
        #Creds file creation and storing user given credentials into the conf file for reutilization.
        fp = open('../creds.conf', "w+")
        fp.write('{u}\n{p}'.format(u=username, p=password))
        fp.close()
    f = open('../creds.conf', 'r')
    cred = f.readlines()
    creds={
        "username": cred[0].strip(),
        "password": cred[1].strip()
        }
    return creds

### This function waits for user to input 'c' and hit ENTER to continue to next step ### 
def waitForUser(msg):
    userInput = input(colored(msg,"green", attrs=['bold']))
    while True:
        if userInput == "c":
            break
        elif userInput == "a":
            quit()
        else:
            userInput = input(colored("Wrong entry, type 'c to continue or a to abort' and hit ENTER :", "green", attrs=['bold']))