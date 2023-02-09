import click

from bob.commands.build import build
from bob.commands.deploy import deploy
from bob.commands.full import full

class Builder(object):

    def __init__(self, region_name):
        self.region_name = region_name
        
@click.group()
@click.option(
    '--region', '-r',
    type=str, default='us-gov-east-1', show_default=True,
    help="AWS region")
@click.pass_context
def cli(ctx, region):
    ctx.obj = Builder(region_name=region)

cli.add_command(build)
cli.add_command(deploy)
cli.add_command(full)