import os
import yaml

from boto3.session import Session


def config():
    return load_config()


def load_config(env=None):
    if not env:
        env = os.environ.get('ENV', 'development')

    with open(os.path.join(os.getcwd(), '%s.yaml' % env)) as f:
        return yaml.safe_load(f.read())


def get_session(cfg=None):
    if not cfg:
        cfg = load_config()

    return Session(cfg['aws-access-key'], cfg['aws-secret-access-key'])


def get_client(service, region=None, cfg=None):
    s = get_session(cfg)
    return s.client(service, region_name=region)


def get_resource(service, region=None, cfg=None):
    s = get_session(cfg)
    return s.resource(service, region_name=region)
