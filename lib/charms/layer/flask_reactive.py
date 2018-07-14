import os

import toml

from jinja2 import (
    Environment,
    FileSystemLoader,
)

from charmhelpers.core import unitdata, hookenv, host

from charmhelpers.core.hookenv import charm_dir, status_set, log

from charmhelpers.contrib.python.packages import pip_install_requirements

from charmhelpers.core.templating import render



FLASK_HOME = "/home/ubuntu/flask"
FLASK_SECRETS = os.path.join(FLASK_HOME, 'flask_secrets.py')

kv = unitdata.kv()


def load_template(name, path=None):
    """Load template file for rendering config."""

    if path is None:
        path = os.path.join(charm_dir(), 'templates')
    env = Environment(
        loader=FileSystemLoader(path))

    return env.get_template(name)


def render_flask_secrets(secrets=None):
    """Renders flask secrets from template."""

    if secrets:
        secrets = secrets
    else:
        secrets = {}

    if os.path.exists(FLASK_SECRETS):
        os.remove(FLASK_SECRETS)

    app_yml = load_template('flask_secrets.py.j2')
    app_yml = app_yml.render(secrets=return_secrets(secrets))

    spew(FLASK_SECRETS, app_yml)
    os.chmod(os.path.dirname(FLASK_SECRETS), 0o755)


def spew(path, data):
    """Writes data to path."""

    with open(path, 'w+') as f:
        f.write(data)


def return_secrets(secrets=None):
    """Return sercrets dictionar."""

    if secrets:
        secrets_mod = secrets
    else:
        secrets_mod = {}

    return secrets_mod


def load_site():
    if not os.path.isfile('site.toml'):
        return {}

    with open('site.toml') as fp:
        conf = toml.loads(fp.read())

    return conf


def configure_site(site, template, **kwargs):

    status_set('maintenance', 'Configuring site {}'.format(site))

    status_set('active', '')
    config = hookenv.config()
    context = load_site()
    context['host'] = config['host']
    context['port'] = config['port']
    context.update(**kwargs)
    conf_path = '/etc/nginx/sites-available/{}'.format(site)
    if os.path.exists(conf_path):
        os.remove(conf_path)
    render(source=template,
           target=conf_path,
           context=context)

    symlink_path = '/etc/nginx/sites-enabled/{}'.format(site)
    if os.path.exists(symlink_path):
        os.unlink(symlink_path)

    if os.path.exists('/etc/nginx/sites-enabled/default'):
        os.remove('/etc/nginx/sites-enabled/default')

    os.symlink(conf_path, symlink_path)
    log(context)
