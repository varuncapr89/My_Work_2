#Modules
import click
import datetime
import boto3
import os
import re
import random

from asyncore import file_dispatcher
from os import environ
from termcolor import colored
from ruamel.yaml import YAML
from git import Repo

#Local libraries
from bob.aws import registry
from bob.git_helper import git

@click.group()
@click.pass_obj
def deploy(builder):
    """
    Deploys updated images into envs, try --help to know more 
    """
    pass

@deploy.command()
@click.option(
    "--environment", "-e",
    type=click.Choice(['prod', 'staging'], case_sensitive=False), required=True,
    help="Specify a relative path to the prod-deployer-config repo")
@click.option(
    "--filepath", "-f", required=False,
    help="Specify a relative path to the prod-deployer config repo")
@click.pass_obj
def aurora(builder, environment, filepath):
    """
    Creates PR for aurora containers with latest base image depending on the env
    """
    # Define path to prod-deployer-config repository
    # You may have to modify these based upon your setup
    if filepath:
        prod_deployer_config_location = filepath
    else:
        prod_deployer_config_location = '../prod-deployer-config'
    
    # Instantiate the boto3 client 
    client = boto3.client('ecr')

    # Dictionary Definition:
    # Key = Prod-deployer-config file name pattern
    # Value = ECR repo Name

    projects = {
        "db-monitor": "govcloud/pogmon",
        "snapshot-service": "govcloud/snapshot-service",
        "uptime-monitor": "govcloud/go-uptime",
        "static-assets": "medallia/s3-reverse-proxy"
    }

    #Initializing lists for specific images
    db_monitor_files = []
    snapshot_files = []
    up_time_monitor_files = []
    static_assets_files = []

    # Git new branch name variable with current date and unique number
    unique_number = random.randint(0,100)
    current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
    new_branch_name = "{cur_date}_Aurora_Containers_Base_Upgrade_{env}_{u_n}".format(cur_date=current_date, u_n = unique_number, env = environment)
    
    # Depending on the env, checkout to specific master branch of the repository
    env_master_branch = ""
    if 'staging' in environment:
        env_master_branch = "fedw1-staging"

    elif 'prod' in environment:
        env_master_branch = "fedw1"

    
    #Checkout to a new branch
    git.checkout(prod_deployer_config_location, env_master_branch, new_branch_name)

    #Creating a list of files that needs to be updated for specific images
    for file in os.listdir(prod_deployer_config_location):
        if 'db-monitor' in file:
            db_monitor_files.append(file)
        elif 'snapshot-service' in file:
            snapshot_files.append(file)
        elif 'uptime-monitor' in file:
            up_time_monitor_files.append(file)             
        elif 'static-assets' in file:
            static_assets_files.append(file)

    # Looping through images in projects
    base_regex = re.compile('v([0-9.-]+)-base-8.[0-9]-[0-9]+')
    s3_reverse_regex = re.compile('v([0-9.]+)')
    for image in projects:
        if 'db-monitor' in image:
            version = registry.get_latest_image(client, projects[image])
            update_aurora_yamls(db_monitor_files, version, prod_deployer_config_location, base_regex)
        elif 'snapshot' in image:
            version = registry.get_latest_image(client, projects[image])
            update_aurora_yamls(snapshot_files, version, prod_deployer_config_location, base_regex)
        elif 'uptime' in image:
            version = registry.get_latest_image(client, projects[image])
            update_aurora_yamls(up_time_monitor_files, version, prod_deployer_config_location, base_regex)
        elif 'static-assets' in image:
            version = registry.get_latest_image(client, projects[image])
            update_aurora_yamls(static_assets_files, version, prod_deployer_config_location, s3_reverse_regex)

    # Add files and make the commit
    reviewer = "medallia/govcloud-sre"
    commit_message = "\"{date} Auto commit from bob deploy aurora {env}\"".format(date = current_date, env = environment)
    pr = git.push(prod_deployer_config_location, env_master_branch, new_branch_name, commit_message, reviewer)
    
    #Printing some information about the outcome
    print(colored("Hooray!! Updated base image for {e} prod_deployer_config containers:\n{p}".format(e = environment, p = pr), "yellow", attrs=['bold']))


# Inputs:
# - file_list: The list of files needs to be updated with latest tag
# - version: The new tag for the specified image
# - repo_location: The location of repo we are updating. In this case, prod-deployer-config 

def update_aurora_yamls(file_list, version, repo_location, regex):
    # Storging bob path
    origin_path = os.getcwd()

    # Changing the directory to repo location
    os.chdir(repo_location)

    # Looping through list of files to update with latest tag 
    for file in file_list:
        # Reading the specified file
        with open(file, "r") as f:
            prod_deployer_yaml = f.read()
            # Updating the tag with latest tag
            prod_deployer_yaml_new_text = re.sub(regex, version, prod_deployer_yaml)
        # Writing the changes back to file  
        with open(file, "w") as f:
            f.write(prod_deployer_yaml_new_text)
    # Changing the path back to origin
    os.chdir(origin_path)
    

@deploy.command()
@click.option(
    "--filepath", "-f", required=False, 
    help="Specify a relative path to the tf-ami repo")
@click.pass_obj
def ami(builder, filepath):
    """
    Creates PR for AMI based containers with latest base image 
    """
    # Define path to tf-ami repositories
    # You may have to modify these based upon setup
    if filepath:
        tf_ami_repo_location = filepath
    else:
        tf_ami_repo_location = '../tf-ami'
    
    #Instantiate the boto3 client
    client = boto3.client('ecr')
    
    # Dictionary Definition:
    #   Key = Tf-Ami Path
    #   Value = ECR Repo Name
    projects = {
        "aurora": "govcloud/docker-aurora-cli",
        "keycloak": "govcloud/keycloak-fips",
        "kube-controller": "govcloud/aws-encryption-provider",
        "mgk-access-sync": "govcloud/mgk-access-sync"
    }
    
    # Create New Branch Name
    unique_number = random.randint(0,100)
    current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
    new_branch_name = "{cur_date}_Ami_Containers_Base_Upgrade_{u_n}".format(cur_date=current_date, u_n = unique_number)
    
    # Checkout a new branch  
    git.checkout(tf_ami_repo_location, 'master', new_branch_name)
    # Looping through images in projects and updating the specific files with regards to project with new tag 
    for image in projects:
        base_regex = re.compile('v([0-9.-]+)-base-8.[0-9]-[0-9]+')
        folder = "image/modules/{service}".format(service = image)
        version = registry.get_latest_image(client, projects[image])
        if 'aurora' in image:
            file = "{file_path}/files/aurora_alias.sh".format(file_path = folder)
            update_ami_file(file,base_regex,version, tf_ami_repo_location)
        elif 'keycloak' in image:
            file = "{file_path}/personalize.sh".format(file_path = folder)
            update_ami_file(file, base_regex, version, tf_ami_repo_location)
        elif 'kube-controller' in image:
            file = "{file_path}/files/aws-encryption-provider.yaml".format(file_path = folder)
            update_ami_file(file, base_regex, version, tf_ami_repo_location)
        else:
            file = "{file_path}/personalize.sh".format(file_path = folder)
            update_ami_file(file, base_regex, version, tf_ami_repo_location)
    
    # Git reviewer variable 
    reviewer = 'govcloud/govcloud-sre'
    
    # Git commit message
    commit_message = "\"{date} Automatic update from bob deploy ami\"".format(date=current_date)

    #Generating Git PR 
    pr = git.push(tf_ami_repo_location, 'master', new_branch_name, commit_message, reviewer)

    #Final print with PR 
    print(colored("Hooray!! Updated base image for tf_ami containers:\n{p}".format(p = pr), "yellow", attrs=['bold']))

# Inputs:
# - file: tf-ami file which needs to be updated 
# - version: the new tag for the specified image
# - pattern: regex you wanted to find       

def update_ami_file(file, pattern, version, location):
    origin = os.getcwd()
    os.chdir(location)
    # Open file, read the text, find the pattern and replace it with new tag
    with open(file) as f:
        file_text = f.read()
        new_file_text = re.sub(pattern, version, file_text)
    # Open the file and write back the text with new tag 
    with open(file, 'w') as f:
        f.write(new_file_text)
    os.chdir(origin)
        
@deploy.command()
@click.option(
    "--environment", "-e", 
    type=click.Choice(['prod', 'staging'], case_sensitive=False), required=True,
    help="Create PR for Prod or Staging Environment")
@click.option(
    "--filepath", "-f", required=False, 
    help="Specify a relative path to the deployment-infra repo")
@click.pass_obj
def k8s(builder, environment, filepath):
    """
    Creates PR for K8S containers with latest base image depending on the env
    """
    # Define paths to deployment and deployment-infra repositores
    # You may have to modify these based upon your setup
    if filepath:
        deployment_infra_repo_location = filepath
    else: 
        deployment_infra_repo_location = '../deployment-infra'

    # Instantiate the boto3 client
    client = boto3.client('ecr')

    # Dictionary Definition:
    #   Key = Deployment-Infra Path
    #   Value = ECR Repo Name
    projects = {
        "aws-audit": "govcloud/aws-audit",
        "csi-ebs": "govcloud/aws-ebs-csi-driver",
        "aws-cloud-controller-manager": "govcloud/cloud-controller-manager",
        "kube2iam": "govcloud/kube2iam",
        "logstash": "govcloud/logstash",
        "filebeat": "govcloud/filebeat",
        "smtp": "govcloud/postfix-exporter",
        "smtp1": "govcloud/smtp"
    }

    # Create new branch name
    unique_number = random.randint(0,100)
    current_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()
    new_branch_name = "{cur_date}_K8S_Containers_Base_Upgrade_{env}_{u_n}".format(cur_date=current_date, u_n = unique_number, env = environment)

    # Checkout a new branch to create the PR
    git.checkout(deployment_infra_repo_location, 'master', new_branch_name)

    # Looping through images in projects and updating files
    for image in projects:
        overlay_folder = ''
        if image == 'smtp1':
            overlay_folder = "{root}/apps/{file_path}/overlays".format(root = deployment_infra_repo_location, file_path = 'smtp')
        else:
            overlay_folder = "{root}/apps/{file_path}/overlays".format(root = deployment_infra_repo_location, file_path = image)
        image_tag = registry.get_latest_image(client, projects[image])
        update_kustomization_yaml(projects[image], overlay_folder, image_tag, environment, deployment_infra_repo_location)

    # Add files and make the commit
    reveiwer = "govcloud/govcloud-sre"
    commit_message = "\"{date} Auto commit from bob deploy k8s {env}\"".format(env=environment, date=current_date)
    pr = git.push(deployment_infra_repo_location, 'master', new_branch_name, commit_message, reveiwer)
    print(colored("Hooray!! Updated base image for {e} deployment_infra containers:\n{p}".format(p=pr, e=environment), "yellow", attrs=['bold']))

# Inputs:
#   - ecr_path: The project/repo name, used to verify the correct image is being updated
#   - overlay_folder: the folder where the overlays are located for a particular app
#   - image_tag: the new tag for the specified image
#   - environment: the environment to be updated (staging or prod)
#   - deployment_infra_repo_location: used for apps that don't have an overlay (aws-audit)
def update_kustomization_yaml(ecr_path, overlay_folder, image_tag, environment, deployment_infra_repo_location):

    # Initialize the yaml object and modify the indentation settings to match ours
    yaml = YAML()
    yaml.indent(sequence=2, mapping=2)
   
    if "staging" in environment:
        root_path = "{}/fedw1-staging/".format(overlay_folder)
        try: 
            for root, dirs, files in os.walk(root_path, onerror=False):
                if "kustomization.yaml"in files:
                    kustomization_file = "{root}/kustomization.yaml".format(root=root)
                    #print("Updating {} to tag {}".format(kustomization_file, image_tag))
                    # Read the file, and modify the tag with the new image
                    with open(kustomization_file, "r") as file:
                        kustomization = yaml.load(file)
                        for image in kustomization["images"]:
                            # Some overlays do not have the newName attribute, so this verifies it exists
                            # newName is preferred because it will always point to the ECR path
                            if "newName" in image:
                                if ecr_path in image["newName"]:
                                    if "newTag" in image:
                                        image["newTag"] = image_tag
                            else:
                                if ecr_path in image["name"]:
                                    if "newTag" in image:
                                        image["newTag"] = image_tag
                    # This writes back the file, adding newlines
                    with open(kustomization_file, "w") as file:
                        yaml.dump(kustomization, file)
        except:
            print("No staging overlay exists for {}".format(ecr_path))

    elif "prod" in environment:
        for root, dirs, files in os.walk(overlay_folder, onerror=False):
            # Update every VPC overlay that's not staging (fedw1, fede1, apps, etc)
            if "staging" not in root:
                if "kustomization.yaml"in files:
                    kustomization_file = "{root}/kustomization.yaml".format(root=root)
                    # Read the file, and modify the tag with the new image
                    #print("Updating {} to {}".format(kustomization_file, image_tag))
                    with open(kustomization_file, "r") as file:
                        kustomization = yaml.load(file)
                        for image in kustomization["images"]:
                            # Some overlays do not have the newName attribute, so this verifies it exists
                            # newName is preferred because it will always point to the ECR path
                            if "newName" in image:
                                if ecr_path in image["newName"]:
                                    if "newTag" in image:
                                        image["newTag"] = image_tag
                            else:
                                if ecr_path in image["name"]:
                                    if "newTag" in image:
                                        image["newTag"] = image_tag
                    # This writes back the file, adding newlines
                    with open(kustomization_file, "w") as file:
                        yaml.dump(kustomization, file)
    else:
        print("Something went wrong. Tried to update {} in {}".format(ecr_path, environment))