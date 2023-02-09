import os
import subprocess as sp
from termcolor import colored
from git import Repo
import datetime

'''
Since bob works with a lot of files and repositories, this git_helper eases creating branches 
and making PR's with their respective master branch, creating tags and everything the PR needs!! 
'''

### Defining date for git utilization ###
cur_date = (datetime.datetime.now().date().strftime("%m-%d-%Y")).strip()

### Tag function creates new tags for smtp and s3 repo and pushes it to remote. ###
def tag(smtp, s3):

    ### Defining the repos ###
    repos = {
        "govcloud/smtp:": "{smtp}".format(smtp=smtp),
        "medallia/s3-reverse-proxy:": "{s3}".format(s3=s3)
    }
    ### Defining the colo docker repository for building the image url
    dockerRepository = "virtual-docker.martifactory.io/"

    ### Instantiating the imagesToPush and tags list
    imagesToPush = []
    tags = []
    release_msg_list = []

    ### Actual 'for' loop where all the tag creation magic happens!! ###
    for repo in repos:
        
        ### For the repo provided, make a git repo object and do the necessary actions ###
        ### Storing the current path ###
        origin_path = os.getcwd()
        ### Changing Directory to that repo ###
        os.chdir(repos[repo])
        r = Repo(repos[repo])
        git_command = r.git
        git_command.checkout('master')
        git_command.pull("origin", 'master')
        
        
        ### Get latest tag for that repo ####
        gh_cli_output = sp.run("git tag --sort=committerdate | tail -1", capture_output=True, shell=True)
        curr_tag = gh_cli_output.stdout.decode('utf-8').strip()
        current_tag = repo+curr_tag
        print(colored("Current tag is {c_t}".format(c_t=current_tag), "yellow"))
        
        ### Asking the user the current tag ###
        new_t = (input(colored("Enter the next tag, you would like to create {repo}".format(repo=repo), "yellow")))
        image = dockerRepository+repo+new_t
        new_tag = repo+new_t
        new_tag_git_command = "git tag {nt}".format(nt=new_t)

        ### tag creation command ###
        gh_cli_tag = sp.run(new_tag_git_command, capture_output=True, shell=True)
        if gh_cli_tag.returncode == 0:
            print(colored("Created tag {n}".format(n=new_tag), "yellow"))
        else:
            print("tag creation failed")
        
        ### tag push command 
        tag_push_command = "git push origin {t}".format(t=new_t)
        gh_cli_tag_push = sp.run(tag_push_command, capture_output=True, shell=True)
        if gh_cli_tag_push.returncode == 0:
            print(colored("Pushesd {n} to remote successfully".format(n=new_tag), "yellow"))
        else:
            print("tag push failed")
        ### Get release log 
        tag_log_command = "git log {old_v}..{new_v} --oneline --no-decorate --no-merges".format(old_v=curr_tag, new_v=new_t)
        gh_cli_log = sp.run(tag_log_command, capture_output=True, shell=True)
        release_msg = gh_cli_log.stdout.decode('utf-8').strip()
        ### Appending both release log, new tags && images to lists
        release_msg_list.append(release_msg)
        tags.append(new_t)
        image = dockerRepository+repo+new_t
        imagesToPush.append(image)
        os.chdir(origin_path)

    return imagesToPush, tags, release_msg_list

    
# This clone function, clones the repository which is passed as argument
def clone(repo_location, repo_link):
    if os.path.exists(repo_location):
        pass
    else:
        Repo.clone_from(repo_link, repo_location)

# This git checkout function pulls master branch, creates a new branch and checkout into it. ###
def checkout(git_repo_location, master_branch, new_branch_name):
    '''
    This git_checkout function pulls from master, creates a new branch and checkout into it

    '''
    repo = Repo(git_repo_location)
    git_command = repo.git
    git_command.checkout(f"{master_branch}")
    git_command.pull("origin", f"{master_branch}")
    git_command.checkout("-b", new_branch_name)


# This git push functions helps with pushing !! ###
def push(git_repo_location, env_master, new_branch_name, commit_message, r):
    '''
    This git_push function takes all arguments required for it to create a PR!!
    '''

    commit_body = "Auto_commit_from_bob_base_image_upgrade"
    repo = Repo(git_repo_location)
    git_command = repo.git
    git_command.add("-A")
    git_command.commit("-m", commit_message)
    git_command.push("-u", "origin", new_branch_name)
    origin_path = os.getcwd()
    os.chdir(git_repo_location)
    gh_command = 'gh pr create --head {head_branch} --base {base_branch} --title {title} --body {b} --reviewer {reviewer}'.format(base_branch = env_master, title = commit_message, head_branch = new_branch_name, b = commit_body, reviewer = r)
    gh_cli_output = sp.run(gh_command, capture_output=True, shell=True)
    pr = gh_cli_output.stdout.decode('utf-8').strip()
    os.chdir(origin_path)
    return pr