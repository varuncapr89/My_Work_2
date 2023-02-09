# Bob
## About Bob

Bob is a cli to help automate kicking off AWS CodeBuild pipelines and creating PRs to deploy the resulting artifacts. Right now only the build part has been implemented.
## Building Bob

**Step 1**: Use pip to install bob

```sh
$ pip3 install --editable .
```

**Step 2**: Run bob
```sh
$ bob --help
Usage: bob [OPTIONS] COMMAND [ARGS]...

Options:
  -r, --region TEXT  AWS region  [default: us-gov-east-1]
  --help             Show this message and exit.

Commands:
  build
  deploy
  full

bob build Sub_Commands:
  cbase - "Triggers build on gc-rhel-base CodeBuild project and creates TF CICD pr"
  gbase - "Triggers build on whichever CodeBuild projects are using gov base image"
  mbase - "Updates smtp and s3 with latest medallia base image"
  projects - "Triggers build on whichever CodeBuild projects are passed as arguments"

bob deploy Sub_Commands:
  ami - "Updates the containers running in AMI with latest base image and creates a PR" 
  aurora - "Updates the containers running aurora/mesos with latest base image and creates a PR"
  k8s - "Updates the containers running in k8s with latest base image and creates a PR"

```


## Creating a Release

Add later

## Common Errors

- `package not found`
-- make sure the pip or pip3 used to install is python3.6 or newer

- `AccessDeniedException` when calling the ListProjects operation
-- make sure the user has `codebuild:ListProjects` action allowed in their user/role/etc. Or just add `AWSCodeBuildDeveloperAccess` policy directly to your IAM user permissions

## working example, for `gc-rhel-base` version 8.6-20:

```sh
{fede1}➜  bob git:(main) bob build all --base-image="8.6-20"
Building aws-encryption-provider
	Status: IN_PROGRESS

Building filebeat
	Status: IN_PROGRESS

Building kube2iam
	Status: IN_PROGRESS
(truncated, but more of the above)
  ```
