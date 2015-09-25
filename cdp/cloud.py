import boto3

from . import errors
from .helpers import (
    get_client,
    get_resource,
    config,
)


def create_account(name, path='/', policy=None):
    iam = get_resource('iam')
    try:
        user = iam.create_user(UserName=name, Path=path)
    except Exception as e:
        raise errors.uhoh(e)

    if not policy:
        cfg = config()
        policy = cfg['policy-arn']
    try:
        user.attach_policy(UserName=name, PolicyArn=policy)
    except Exception as e:
        raise errors.uhoh(e)

    key = create_key_pair(user)
    return user, key


def create_key_pair(name):
    user = get_user(name)

    try:
        return user.create_access_key_pair()
    except Exception as e:
        raise errors.uhoh(e)


def get_user(name):
    # Ask tim about this
    if name.__class__.__name__ == 'iam.User':
        return name

    iam = get_resource('iam')
    try:
        # Simple invoking this won't guarentee we have a record
        # Load will fail if the record does not exist
        u = iam.User(name=name)
        u.load()
    except Exception as e:
        raise errors.uhoh(e)

    return u


def list_keys(user):
    pass


def delete_keys(user):
    user = get_user(user)

    for k in user.access_keys.all():
        k.delete()


def delete_user(user):
    try:
        user = get_user(user)
    except errors.exceptions.NoSuchEntity:
        return
    except:
        raise

    for p in user.attached_policies.all():
        user.detach_policy(PolicyArn=p.arn)

    delete_keys(user)
    user.delete()


def users(path='/'):
    # list_users doesn't exist in resource, but we need it and resource
    iam = get_resource('iam')
    iam_client = iam.meta.client

    try:
        users_resp = iam_client.list_users(PathPrefix=path, MaxItems=999)
    except Exception as e:
        raise errors.uhoh(e)

    users = users_resp['Users']
    return [iam.User(name=n['UserName']) for n in users]


def get_instance(name):
    pass


def instances(regions=None):
    if type(regions) == str:
        regions = [regions]

    if not regions:
        cfg = config()
        regions = cfg['regions']

    instances = {}
    for r in regions:
        instances[r] = []
        ec2 = get_resource('ec2', r)
        for i in ec2.instances.all():
            i.name = None
            i.units = ""
            i.juju_env = ""
            i.bootstrap = False
            if i.tags:
                for t in i.tags:
                    if t['Key'] == 'Name':
                        i.name = t['Value']
                    if t['Key'] == 'juju-env-uuid':
                        i.juju_env = t['Value'].split('-')[0]
                    if t['Key'] == 'juju-units-deployed':
                        i.units = t['Value']
                    if t['Key'] == 'juju-is-state':
                        i.bootstrap = True

            instances[r].append(i)

    return instances
