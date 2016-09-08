import os
from contextlib import contextmanager

from fabric import api
from fabric.contrib.files import exists

api.env.hosts = ['bear']
api.env.use_ssh_config = True

# directories
api.env.root_dir = '/srv/www/myles.photo/www'
api.env.proj_dir = os.path.join(api.env.root_dir, 'proj')
api.env.venv_dir = os.path.join(api.env.root_dir, 'venv')
api.env.logs_dir = os.path.join(api.env.root_dir, 'logs')
api.env.html_dir = os.path.join(api.env.root_dir, 'html')

# python bullshit
api.env.venv_python = os.path.join(api.env.venv_dir, 'bin/python')
api.env.venv_pip = os.path.join(api.env.venv_dir, 'bin/pip')

# git bullshit
api.env.repo = 'https://github.com/myles/myles.photo.git'
api.env.remote = 'origin'
api.env.branch = 'master'


@contextmanager
def virtualenv():
    """
    A context for enabling the virtualenv.
    """
    with api.cd(api.env.venv_dir):
        activate = os.path.join(api.env.venv_dir, 'bin/activate')
        with api.prefix('source {0}'.format(activate)):
            yield


def sigal(command, args='', **opts):
    """
    Helper function for running the sigal command.
    """
    options = ' '.join(['--{0}={1}'.format(k, v) for (k, v) in opts.items()])

    with virtualenv():
        api.run('sigal {0} {1} {2}'.format(command, options, args))


@api.task
def setup():
    """
    Setup the deploy server.
    """
    # make a bunch of the directories.
    api.sudo('mkdir -p {0}'.format(' '.join([api.env.proj_dir,
                                             api.env.logs_dir,
                                             api.env.html_dir,
                                             api.env.venv_dir])))

    # make sure the directories are writeable by me.
    api.sudo('chown myles:myles {0}'.format(' '.join([api.env.proj_dir,
                                                      api.env.html_dir,
                                                      api.env.venv_dir])))

    # clone the git repo
    if not exists(os.path.join(api.env.proj_dir, '.git')):
        with api.cd(api.env.proj_dir):
            api.run('git clone {0} .'.format(api.env.repo))

    # createh virtual environment.
    if not exists(api.env.venv_python):
        api.run('virtualenv {0}'.format(api.env.venv_dir))

    # install the dependencies.
    pip_upgrade()
    bower_upgrade()


@api.task
def python_version():
    """
    Return the python version on the server for testing.
    """
    with virtualenv():
        api.run("{0} -V".format(api.env.venv_python))


@api.task
def update_code():
    """
    Update to the latest version of the code.
    """
    with api.cd(api.env.proj_dir):
        api.run('git reset --hard HEAD')
        api.run('git checkout {0}'.format(api.env.branch))
        api.run('git pull {0} {1}'.format(api.env.remote, api.env.branch))


@api.task
def pip_upgrade():
    """
    Upgrade the third party Python libraries.
    """
    requirements_txt = os.path.join(api.env.proj_dir, 'requirements.txt')
    api.run('{0} install --upgrade -r {1}'.format(api.env.venv_pip,
                                                  requirements_txt))


@api.task
def bower_upgrade():
    """
    Upgrade the third party Bower libraries.
    """
    with api.cd(api.env.proj_dir):
        api.run('bower install --upgrade')


@api.task
def compile_scss():
    """
    Compile the SCSS files.
    """
    scss_file = os.path.join(api.env.proj_dir, 'theme/static/scss/style.scss')
    css_file = os.path.join(api.env.proj_dir, 'theme/static/css/style.css')
    include_path = os.path.join(api.env.proj_dir, 'bower_components/')

    with virtualenv():
        api.run('sassc.py --include-path={0} {1} {2}'.format(include_path,
                                                             scss_file,
                                                             css_file))


@api.task
def build():
    """
    Build the photo gallery.
    """
    config_file = os.path.join(api.env.proj_dir, 'sigal.conf.py')
    source_dir = os.path.join(api.env.proj_dir, 'source')

    sigal('build', args='{0} {1}'.format(source_dir, api.env.html_dir),
          config=config_file)


@api.task
def proselint():
    """
    Test for some basic grammer mistakes.
    """
    source_dir = os.path.join(api.env.proj_dir, 'source')
    md_files = api.run('find {0} -name "*.md"'.format(source_dir))

    with virtualenv():
        for md_file in md_files:
            api.run('proselint {0}'.format(md_file))


@api.task
def ship_it():
    """
    Ship the code to the server.
    """

    # Check to make sure that there isn't any unchecked files
    git_status = api.local('git status --porcelain', capture=True)

    if git_status:
        api.abort('There are unchecked files.')

    # Push the repo to the remote
    api.local('git push {0} {1}'.format(api.env.remote, api.env.branch))

    # The deploy tasks
    update_code()
    pip_upgrade()
    bower_upgrade()
    compile_scss()
    build()

    # Draw a ship
    api.puts("                           |    |    |                ")
    api.puts("                          )_)  )_)  )_)               ")
    api.puts("                         )___))___))___)\             ")
    api.puts("                        )____)____)_____)\\           ")
    api.puts("                      _____|____|____|____\\\__       ")
    api.puts("             ---------\                   /---------  ")
    api.puts("               ^^^^^ ^^^^^^^^^^^^^^^^^^^^^            ")
    api.puts("                 ^^^^      ^^^^     ^^^    ^^         ")
    api.puts("                      ^^^^      ^^^                   ")


@api.task
def truck_it():
    """
    Ship the code from the server.
    """

    # Get the latest version of the code.
    api.local('git pull {0} {1}'.format(api.env.remote, api.env.branch))
    build()
