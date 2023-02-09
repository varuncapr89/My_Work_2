import click

@click.group()
@click.pass_obj
def full(builder):
    """
    Work in progress
    """
    pass

@full.command()
@click.argument(
    'projects', nargs=-1, type=click.STRING)
@click.option('--branch', '-b', type=str)
@click.pass_obj
def projects(builder, projects, branch):
    pass


@full.command()
@click.option(
    "--base-image", "-i", 
    type=str, required=True,
    help="Build any project that is using this base image tag")
@click.pass_obj
def all(builder, base_image):
    pass