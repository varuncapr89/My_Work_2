import boto3
import json
import re

def get_latest_image(client, repo_name):
    '''
    The boto3 list_projects() function just gives you project names.
    batch_get_projects() gives you the project details, but you need the list of names.
    This function combines the two so you can get a list of the projects
    and all of the details about them in one shot.
    '''

    registry_name = repo_name
    # This query sorts all the images by ImagePushedAt (normally prints reverse, so it's reversed which
    # seems like it takes awhile to do)
    jmespath_query = 'reverse(sort_by(imageDetails, &to_string(imagePushedAt))[*].imageTags)'

    client = boto3.client('ecr')

    paginator = client.get_paginator('describe_images')

    iterator = paginator.paginate(repositoryName=registry_name)
    sorted_images = iterator.search(jmespath_query)
    
    #Regex for RHEL latest 
    latest_regex = re.compile('[0-9].+')
    #Regex for reverse proxy
    s3_reverse_proxy_regex = re.compile('v([0-9.]+)')
    # Regex for RHEL base images
    rhel_regex = re.compile('v([0-9.-]+)-base-8.[0-9]-[0-9]+')
    # Regex for Scratch base images
    scratch_regex = re.compile('([0-9.-]+)-base-scratch')

    for tag in sorted_images:
        if rhel_regex.search(tag[0]):
            return tag[0]
        elif scratch_regex.search(tag[0]):
            return tag[0]
        elif s3_reverse_proxy_regex.search(tag[0]):
            return tag[0]
        elif latest_regex.search(tag[0]):
            return tag[0]

    # If regex is not matched, let user now, and return foobar so user can manually replace
    print("Tag not found for {}".format(repo_name))
    return None