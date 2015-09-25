import click
import humanize

from . import cloud
from . import helpers
from . import errors


config = helpers.config()

@click.group()
def main():
    pass


@main.group()
def instance():
    pass


@instance.command('list')
@click.option('--regions', '-r', default=None)
def instance_list(regions):
    all_instances = cloud.instances()
    out = "{0:28s} {1:11s} {2:15s} {3:10s} {4:10s} {5:14s} {6:8s} {8:1s} {7}"
    click.secho(out.format('NAME', 'ID', 'REGION', 'STATE', 'TYPE', 'AGE',
                           'ENV', 'UNITS', ''),
                bold=True)
    for r, instances in all_instances.items():
        for i in instances:
            age = humanize.naturaltime(i.launch_time.replace(tzinfo=None))
            click.echo(out.format(i.name or '', i.id, r, i.state['Name'],
                                  i.instance_type, age, i.juju_env,
                                  i.units, '*' if i.bootstrap else ''))

@instance.command('reap')
@click.option('--regions', '-r', default=None)
@click.option('--timelimit', '-t', default='24h')
def instance_reap():
    pass


@instance.command('kill')
@click.argument('instance_ids', required=True, nargs=-1)
@click.option('--yes', '-y', default=False, is_flag=True)
def instance_kill(instance_ids, yes):
    if not yes:
        click.echo('Continue? [y|N] ', nl=False)
        c = click.getchar()
        click.echo()
        if c.lower() != 'y':
            return

    instances = cloud.instances()
    for r, inst in instances.items():
        for i in inst:
            if i.id in instance_ids:
                i.terminate()
                click.echo('{1:28s} {0:11s} terminated from {2}'.format(i.id,
                                                                        i.name,
                                                                        r))


@main.group()
def user():
    pass


@user.command('list')
@click.argument('path', required=False,
                default=config.get('default-path', '/'))
def user_list(path):
    """List all users created by CDP"""

    users = cloud.users(path)
    out = "{0:22s} {1:20s} {2:50s}"
    click.secho(out.format("User ID", "Name", "ARN"), bold=True)
    for u in users:
        click.echo(out.format(u.user_id, u.name, u.arn))


@user.command('add')
@click.argument('name')
@click.option('--prefix', '-p', default=config.get('default-path', '/'))
@click.option('--policy', '-P', default=config.get('policy-arn', None))
def user_add(name, prefix, policy):
    """Create new IAM user with prefix (path) and policy"""

    user, key = cloud.create_account(name, prefix, policy)
    click.echo("{0}: {1} {2}".format(name, key.id, key.secret))


@user.command('create')
@click.argument('name')
@click.option('--prefix', '-p', default=config.get('default-path', '/'))
@click.option('--policy', '-P', default=config.get('policy-arn', None))
@click.pass_context
def user_create(ctx, name, prefix, policy):
    """Alias of add"""
    ctx.forward(user_add)


@user.command('delete')
@click.argument('name')
@click.option('--yes', '-y', is_flag=True)
def user_del(name, yes):
    if yes or click.confirm("Delete {0}?".format(name)):
        cloud.delete_user(name)


@user.group('keys', invoke_without_command=True)
@click.argument('name', required=False, default=None)
@click.option('--prefix', '-p', default=config.get('default-path', '/'))
@click.option('--quiet', '-q', is_flag=True)
@click.pass_context
def user_keys(ctx, name, prefix, quiet):
    """Show or refrhesh a users keys"""
    # Not sure if we even need this.
    if ctx.invoked_subcommand is None:
        if name:
            users = [cloud.get_user(name)]
        else:
            users = cloud.users(prefix)
        out = "{0:22s} {1:20s} {2:20s} {3:50s}"

        if not quiet:
            click.echo(out.format('User ID', 'Name', 'Access Key', 'Secret'))
        for u in users:
            keys = [k for k in u.access_keys.all()]
            if len(keys) < 1:
                click.echo(out.format(u.user_id, u.name, '', ''))
            for k in keys:
                click.echo(out.format(u.user_id, u.name, k.id, 'REDACTED'))


@user_keys.command('refresh')
@click.argument('name')
def user_keys_refresh(name):
    pass


@user_keys.command('delete')
@click.argument('name')
@click.argument('key', required=False, default=None)
@click.option('--quiet', '-q', is_flag=True)
def user_keys_delete(name, key, quiet):
    try:
        user = cloud.get_user(name)
    except errors.exceptions.NoSuchEntity:
        click.secho('User %s does not exist' % name, err=True, fg='red')
