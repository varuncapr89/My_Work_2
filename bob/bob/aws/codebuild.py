import boto3
import json
import re
import subprocess as sp
from termcolor import colored
import datetime
import time
import random
from bob.git_helper import git
from bob.aws import registry
import requests as r

def build_container_image(client, project, ecr_path, repo_location):
    '''
    This function starts the build on govcloud/gc-rhel-base codebuild project and waits for it to finish
    and creates a PR(TF CICD) with the latest container base image to all the code build projects which are using govcloud base image 
    '''

    # Initiate a build on all of the projects in the to_build list
    print(f"Started the build for {project}", "yellow" )
    
    
    response = client.start_build(projectName=project)
    
    # Saving build ID 
    buildId = response["build"]["id"]
    
    #Instatiate build_latest_version variable
    build_latest_version = ''
    
    
    #Instantiate the boto3 client
    client_ecr = boto3.client('ecr')

    # Regex for container image
    regex = re.compile(':[0-9].+')
    
    
    #Creating a new branch name
    unique_number = random.randint(0,100)
    current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
    new_branch_name = "{cur_date}_TF_CICD_base_image_upgrade_{u_n}".format(cur_date=current_date, u_n = unique_number)

    # Waiting for build to complete and getting the latest image for the project

    while True:
        theBuild = client.batch_get_builds(ids=[buildId])
        buildStatus = theBuild['builds'][0]['buildStatus']
        print(colored(f"Still waiting for build to complete, Current Status:{buildStatus}", "yellow"))
        time.sleep(30)
        if buildStatus == 'SUCCEEDED':
        ## waiting for codebuild to completely push the latest image to ECR ##
            time.sleep(30)
            build_latest_version = registry.get_latest_image(client_ecr, ecr_path)
            break
        elif buildStatus == 'FAILED':
            print(colored("Build failed/stopped, check codebuild logs and try again", "yellow"))
            quit()

    build_version = f':{build_latest_version}\"'
    cicd_file = f"{repo_location}/cicd/fede1-us-gov-east-1.tfvars.json"

    
    #Creating a new branch name
    unique_number = random.randint(0,100)
    current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
    new_branch_name = "{cur_date}_TF_CICD_base_image_upgrade_{u_n}".format(cur_date=current_date, u_n = unique_number)
    
    # Checkout to a new branch
    git.checkout(repo_location, 'master', new_branch_name)

    with open (cicd_file, "r") as f:
        cicd_tf_text = f.read()
        cicd_tf_new_text = re.sub(regex, build_version, cicd_tf_text)
    with open(cicd_file, "w") as f:
        f.write(cicd_tf_new_text)
    
    # Add fies and make the PR
    reviewer = "govcloud/govcloud-sre"
    commit_message = "\"{c_d} Auto Commit from bob build base tf\"".format(c_d=current_date)
    pr = git.push(repo_location, 'master', new_branch_name, commit_message, reviewer)
    
    #Printing some information about the next step
    print(colored("Hooray!! Updated base image for all codeBuild projects with latest govcloud base image:\n{p}\nLatest_gc_rhel_base_version:{v}".format(p = pr, v = build_latest_version), "yellow", attrs=['bold']))
    print("------------------------------------------------------------------------------------------------")
    print(colored("So once you merge and apply this TF CICD codebuild change\nWe can go ahead and run the below command to kick off builds for codebuild govcloud base image projects\naws-vault exec fede1 -- bob build gbase -i {v}".format(v = build_latest_version), "yellow", attrs=['bold']))


def build_projects(client, projects_to_build):
    # Initiate a build on all of the projects in the to_build list
    for project in projects_to_build:
        print("Building " + project)
        response = client.start_build(projectName=project)
        print("\tStatus: " + response["build"]["buildStatus"] + "\n")
        

def list_projects_detailed(client):
    '''
    The boto3 list_projects() function just gives you project names.
    batch_get_projects() gives you the project details, but you need the list of names.
    This function combines the two so you can get a list of the projects
    and all of the details about them in one shot.
    '''
    # Retrieve the list of all codebuild projects
    response = client.list_projects()
    all_projects = response["projects"]

    # If response is longer than 100 projects, get all of the pages
    while "NextToken" in response:
        response = client.list_projects(NextToken=response["NextToken"])
        all_projects.extend(response["projects"])

    # Get details on all projects
    response = client.batch_get_projects(names=all_projects)
    detailed_projects = response["projects"]

    return detailed_projects

def medallia_base_image_projects(smtp, s3):

    '''
    Medallia_base_image_projects() gets the latest medallia base image for smtp and s3 proxy
    and creates PRs for respective repositories.
    '''

    print(colored("Updating the Medallia Base Images for S3 & SMTP and Creating PRs!!", "yellow"))

    smtp_repo_location = smtp
    s3_repo_location = s3
    
    manifests = "https://manifests.medallia.com/api/v1/apps/com.medallia.docker.base-images/versions"
    
    manifests_json = r.get(manifests).json()

    medallia_base = manifests_json["items"][0]["version"]
    
    base_versions_json = r.get("{m}/{base}".format(m=manifests, base=medallia_base)).json()
    
    artifacts_list = base_versions_json["artifacts"]

    repos = ["smtp", "s3-reverse-proxy"]
    mbase_prs = []
    
    #Initializing variables to store latest base versions for smtp and s3_reverse_proxy
    smtp_ubi8_base = ''
    s3_base = ''

    #Regex s3_base & smtp_ubi8
    smtp_base_regex = re.compile('v[0-9.]+')
    s3_base_regex = re.compile('v[0-9.]+')

    
    # Looping through list of artifacts to find ubi8 and nodejs
    for i in range(len(artifacts_list)):
        if artifacts_list[i]["docker"]["path"] == "medallia/base/ubi8-base":
            smtp_ubi8_base = artifacts_list[i]["docker"]["version"]
        elif artifacts_list[i]["docker"]["path"] == "medallia/base/nodejs16-base-jdk11-ubi8":
            s3_base = artifacts_list[i]["docker"]["version"]
    
    # Looping through each repo to update the Docker file
    for repo in repos:
        #Creating a new branch
        unique_number = random.randint(0,100)
        current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
        new_branch_name = "{cur_date}_{r}_Base_Upgrade_{u_n}".format(cur_date=current_date, r=repo, u_n = unique_number)                
        if repo == "smtp":
            # Checkout to master of repo
            git.checkout(smtp_repo_location, 'master', new_branch_name)
            with open(f'{smtp_repo_location}/Dockerfile', "r") as f:
                dfile = f.read()
                dfile_newtext = re.sub(smtp_base_regex, smtp_ubi8_base, dfile)
                # Writing the changes back to file 
            with open(f'{smtp_repo_location}/Dockerfile', "w") as d:
                d.write(dfile_newtext)
            
            # Add file and make a commit 
            reviewer = "govcloud/govcloud-sre"
            commit_message = "\"{c_d} Auto Commit from bob build mbase smtp\"".format(c_d=current_date)
            pr = git.push(smtp_repo_location, 'master', new_branch_name, commit_message, reviewer)
            mbase_prs.append(pr)
        elif repo == "s3-reverse-proxy":
            
            git.checkout(s3_repo_location, 'master', new_branch_name)

            with open(f'{s3_repo_location}/Dockerfile', "r") as f:
                dfile = f.read()
                dfile_newtext = re.sub(s3_base_regex, s3_base, dfile)
                # Writing the changes back to file 
            with open(f'{s3_repo_location}/Dockerfile', "w") as d:
                d.write(dfile_newtext)
            
            # Add file and make a commit 
            reviewer = "medallia/govcloud-sre"
            commit_message = "\"{c_d} Auto Commit from bob build mbase s3-reverse-proxy\"".format(c_d=current_date)
            pr = git.push(s3_repo_location, 'master', new_branch_name, commit_message, reviewer)
            mbase_prs.append(pr)
    mbase_string_prs = "\n".join(mbase_prs)
    print(colored("Hooray!! Here the Prs for both, approve & merge and come back and hit enter \n{prs}".format(prs=mbase_string_prs), "green", attrs=['bold']))
    return mbase_prs