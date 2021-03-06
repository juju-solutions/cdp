import click
import humanize

from dateutil import tz

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


@main.command('instances')
@click.option('--regions', '-r', default=None)
def instance_list(regions):
    all_instances = cloud.instances()
    out = "{9:8s} {8:1s} {0:30s} {1:21s} {2:15s} {3:10s} {4:10s} {5:14s} {6:8s} {7}"
    click.secho(out.format('NAME', 'ID', 'REGION', 'STATE',
                           'TYPE', 'AGE', 'MODEL', 'UNITS', '', 'CNTRLR'),
                bold=True)
    for r, instances in all_instances.items():
        for i in instances:
            # This entire tz thing is a bunch of shit
            local_tz = tz.tzlocal()
            launch_time = i.launch_time.astimezone(local_tz)
            age = humanize.naturaltime(launch_time.replace(tzinfo=None))
            i.name = i.name or ''
            click.echo(out.format(i.name[:27] or '', i.id, r, i.state['Name'],
                                  i.instance_type, age,
                                  i.model, i.units,
                                  '*' if i.is_controller else '', i.controller))


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
                msg = '{1:28s} {0:11s} terminated from {2}'
                click.echo(msg.format(i.id, i.name, r))


@main.command('kill-model')
@click.argument('model_ids', required=True, nargs=-1)
@click.option('--yes', '-y', default=False, is_flag=True)
def model_kill(model_ids, yes):
    if not yes:
        click.echo('Continue? [y|N] ', nl=False)
        c = click.getchar()
        click.echo()
        if c.lower() != 'y':
            return

    instances = cloud.instances()
    for region, inst in instances.items():
        for i in inst:
            if i.model in model_ids:
                i.terminate()
                msg = '{1:28s} {0:21s} {3} terminated from {2}'
                click.echo(msg.format(i.id, i.name, region, i.model))


@main.command('kill-controller')
@click.argument('controller_ids', required=True, nargs=-1)
@click.option('--yes', '-y', default=False, is_flag=True)
def model_kill(controller_ids, yes):
    if not yes:
        click.echo('Continue? [y|N] ', nl=False)
        c = click.getchar()
        click.echo()
        if c.lower() != 'y':
            return

    instances = cloud.instances()
    for region, inst in instances.items():
        for i in inst:
            if i.controller in controller_ids:
                i.terminate()
                msg = '{1:28s} {0:21s} {3} terminated from {2}'
                click.echo(msg.format(i.id, i.name, region, i.model))


@main.command('clean-groups')
@click.option('--yes', '-y', default=False, is_flag=True)
def group_clean(yes):
    if not yes:
        click.echo('Continue? [y|N] ', nl=False)
        c = click.getchar()
        click.echo()
        if c.lower() != 'y':
            return

    instances = cloud.groups()
    for region, inst in instances.items():
        for i in inst:
            click.echo('{0}: {1} '.format(i.id, i.description), nl=False)
            msg = cloud.delete_group(i)
            click.echo('({0})'.format(msg))


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
    click.echo("user: {0}\naccess: {1}\nsecret: {2}".format(name, key.id, key.secret))


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
@click.argument('names', required=False, default=None, nargs=-1)
@click.option('--prefix', '-p', default=config.get('default-path', '/'))
@click.option('--quiet', '-q', is_flag=True)
@click.pass_context
def user_keys(ctx, names, prefix, quiet):
    """Show or refrhesh a users keys"""
    # Not sure if we even need this.
    if not names:
        names = ['list']

    if names[0] == 'refresh':
        return ctx.invoke(user_keys_refresh, names=names[1:])
    else:
        if names[0] == 'list':
            names = names[1:]

        return ctx.invoke(user_keys_list, names=names, prefix=prefix,
                          quiet=quiet)


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


@user_keys.command('list')
@click.argument('names', required=False, default=None, nargs=-1)
@click.option('--prefix', '-p', default=config.get('default-path', '/'))
@click.option('--quiet', '-q', is_flag=True)
def user_keys_list(names, prefix, quiet):
    if names:
        users = []
        for name in names:
            users.append(cloud.get_user(name))
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
@click.argument('names', required=False, nargs=-1)
def user_keys_refresh(names):
    if not names:
        click.secho('Need a User ID or Name to generate new keys', err=True,
                    fg='red')
        return

    for name in names:
        try:
            cloud.delete_keys(name)
            key = cloud.create_key_pair(name)
        except errors.exceptions.NoSuchEntity:
            click.secho('User %s does not exist' % name, err=True, fg='red')
        else:
            click.echo('user: {0}\naccess: {1}\nsecret: {2}'.format(name, key.id, key.secret))


@user_keys.command('delete')
@click.argument('name')
@click.argument('key', required=False, default=None)
@click.option('--quiet', '-q', is_flag=True)
def user_keys_delete(name, key, quiet):
    try:
        user = cloud.get_user(name)
    except errors.exceptions.NoSuchEntity:
        click.secho('User %s does not exist' % name, err=True, fg='red')
