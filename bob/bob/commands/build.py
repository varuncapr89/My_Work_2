from email.policy import default
import click
import boto3
import os
import re
from termcolor import colored
from bob.git_helper import git
from bob.pro_helper import state
from bob.pro_helper import helpers


from bob.aws import codebuild
from bob.web_helper import web


@click.group()
@click.pass_obj
def build(builder):
    """
    Builds different base images, try --help to know more
    """
    pass
'''
@build.command()
@click.argument(
    'projects', nargs=-1, type=click.STRING)
@click.option(
    '--branch', '-b', 
    type=str, default="project_default",
    help="Branch to build from. [not yet implemented]")
@click.pass_obj
def projects(builder, projects, branch):
    """Starts build on whichever CodeBuild projects are passed as arguments"""

    client = boto3.client('codebuild', region_name=builder.region_name)

    codebuild.build_projects(client, projects)
'''

@build.command()
@click.option(
    "--filepath", "-f", 
    required=True,
    help="Specify a relative path to the tf repo")
@click.pass_obj
def cbase(builder, filepath):
    """
    Container Base(cbase) - Triggers Code Build to create new container base image and creates PR to update container base image in TF CICD
    """
    # Define path to prod-deployer-config repository
    # You may have to modify these based upon your setup
    if filepath:
        tf_location = filepath
    else:
        tf_location = '../tf'

    # # Dictionary Definition:
    # Key = CodeBuild project name
    # Value = ECR repo Name

    projects = {
        "gc-rhel-base": "govcloud/gc-rhel-base"
    }

    client = boto3.client('codebuild', region_name=builder.region_name)
    for project in projects:
        codebuild.build_container_image(client, project, projects[project], tf_location)
    

@build.command()
@click.option(
    "--base-image", "-i", 
    type=str, required=True,
    help="Build any project that is using this base image tag --base-image/-i")
@click.pass_obj
def gbase(builder, base_image):

    """
    Govcloud Base(gbase) - Triggers Code Build on all projects which are using Govcloud Base Image that was passed with --base-image/-i
    """
    print(colored("Before continuing,\nMake sure that you merged and applied the TF PR to update gc-rhel-base for TF CICD Codebuild projects", "yellow", attrs=['bold']))
    full_base_image = "715289973214.dkr.ecr.us-gov-east-1.amazonaws.com/govcloud/gc-rhel-base:" + base_image
    projects_to_build = []

    client = boto3.client('codebuild', region_name=builder.region_name)

    detailed_projects = codebuild.list_projects_detailed(client)

    # If a project has an environment variable called "BASE_IMAGE"
    # whose value equals the base image provided, then add that project to
    # the list to be built.
    for project in detailed_projects:
        for env_var in project["environment"]["environmentVariables"]:
            if env_var["name"] == "BASE_IMAGE":
                if env_var["value"] == full_base_image:
                    projects_to_build.append(project["name"])
                    break
    

    codebuild.build_projects(client, projects_to_build)
    print(colored("Hooray!! You kicked off new builds for all codebuild projects which are using BASE image", "yellow", attrs=['bold']))
    print(colored("Now you can continue to kick off smtp and s3_reverse_proxy:\nbob build mbase ", "yellow", attrs=['bold']))


@build.command()
@click.option(
    "--filepath_smtp", "-sf", required=False,
    help="Specify a relative path to the smtp repo")
@click.option(
    "--filepath_reverse", "-rf", required=False,
    help="Specify a relative path to the s3-reverse-proxy repo")
@click.pass_obj
def mbase(builder, filepath_smtp, filepath_reverse):
    """
    Medallia Base(mbase) - Creates PRs, Tags, Releases, Builds, Images into ECR for S3-Reverse && SMTP
    """
    ### To maintain the state of PRs tags and release notes I have create these lists in here as well ###

    imagesToPush = []
    tags = []
    release_log_list = []

    ### regex to search the tags in dictionary ## 
    smtp_n_s3_tag_regex = re.compile('v([0-9.]+)')

    if filepath_smtp:
        smtp_repo = filepath_smtp
    else:
        if os.path.exists('../smtp'):
            print(colored("smtp repository already exists at ../smtp, so using it!!", "yellow"))
            smtp_repo = '../smtp'
        else:
            print(colored("Repo not given with option filepath(-sf) and did not find the repo, so downloading into ../smtp", "yellow"))
            smtp = 'git@github.medallia.com:govcloud/smtp.git'
            smtp_repo = '../smtp'
            git.clone(smtp_repo, smtp)
            
    if filepath_reverse:
        s3_repo = filepath_reverse
    else:
        if os.path.exists('../s3-reverse-proxy'):
            print(colored("s3-reverse-proxy repository already exists at ../s3-reveerse-proxy, so using it!!", "yellow"))
            s3_repo = '../s3-reverse-proxy'
        else:
            print(colored("Repo not given with option filepath(-rf) and did not find the repo, so downloading into ../s3-reverse-proxy", "yellow"))
            s3_repo = '../s3-reverse-proxy'
            s3 = "git@github.medallia.com:medallia/s3-reverse-proxy.git"
            git.clone(s3_repo, s3)
    
    ###Checking if the PR's and Tags already exists###
    if os.path.exists('../bob_mbase_state'):
        
        print(colored("Found the mbase state file(@ ../bob_mbase_state), so I will look if we already have PRs and Tags to retrieve!!", "yellow"))
        # Get PRs if already exist
        p = state.getStatePr()
        if bool(re.search('github', str(p['prs']))) == True:
            prs_msg = "{smtp}\n{s3}\nLooks like we already have the above PRs, did you already approve and merge? if so Type 'c' to continue or 'a' to abort and hit ENTER :".format(smtp=p['prs']['smtp'], s3=p['prs']['s3'])
            helpers.waitForUser(prs_msg)
        else:
            print(("State file don't have PRs, so creating new PR's!!"))
            prs = codebuild.medallia_base_image_projects(smtp_repo, s3_repo)
            state.saveStatePr(prs)

        ## Storing state of tags in T ## 
        
        t = state.getStateTag()
        if bool(re.search(smtp_n_s3_tag_regex, str(t['tags']))) == True:
            
            ### Retrieving tags from state and adding data to global variable
            tags.append(t['tags']['smtp'])
            tags.append(t['tags']['s3'])
            ### Retrieving images from state and adding data to global variable 
            imagesToPush.append(t['images']['smtp'])
            imagesToPush.append(t['images']['s3'])
            ### Retrieving log from state and adding data to global variable
            release_log_list.append(t['log']['smtp'])
            release_log_list.append(t['log']['s3'])
            ### Will wait for user Input before continuing ### 
            tags_msg = "govcloud/smtp:{smtp}\nmedallia/s3-reverse-proxy:{s3}\nLooks like we already have the above Tags, if so Type 'c' to continue or 'a' to abort and hit ENTER :".format(smtp=t['tags']['smtp'], s3=t['tags']['s3'])
            helpers.waitForUser(tags_msg)

        else:
            print(colored("State file don't have tags, so creating new tags", "yellow"))
            #imagelist, tags, release_log_list = git.tag(smtp_repo, s3_repo)
            state.saveStateTag(tags)
            state.saveStateImages(imagelist)
            state.saveStateReleaseLog(release_log_list)

    else:
        prs = codebuild.medallia_base_image_projects(smtp_repo, s3_repo)
        state.saveStatePr(prs)
        #imagelist, tags, release_log_list = git.tag(smtp_repo, s3_repo)
        state.saveStateTag(tags)
        state.saveStateImages(imagelist)
        state.saveStateReleaseLog(release_log_list)

    images = ("\n".join(imagesToPush)).rstrip()
    next_msg = "If everything looks good, Type 'c' to continue or 'a' to abort and hit ENTER to continue, so we will go and release, build and push images :"
    helpers.waitForUser(next_msg)
    web.build_push(images, tags, release_log_list)
    state_file_msg = "If everything went well, we can remove the state file(which contains current PR's, tags, images, relesae notes). So are we good to go ahead and remove? Type 'c' to continue or 'a' to abort and hit ENTER :"
    helpers.waitForUser(state_file_msg)
    os.system ("rm -rf ../bob_mbase_state")
    print(colored("Fantastic, we finished medallia base image creation!!", "green"))
