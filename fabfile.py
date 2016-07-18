import os.path

from fabric import api

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
api.env.repo = 'gogs@127.0.0.1:websites/myles.photo-www.git'
api.env.remote = 'origin'
api.env.branch = 'master'


@api.task
def setup():
    """
    setup the deploy server.
    """
    # make a bunch of the directories.
    api.sudo('mkdir -p {0}'.format(' '.join([api.env.proj_dir,
                                             api.env.logs_dir,
                                             api.env.html_dir,
                                             api.env.venv_dir])))

    if not exists(os.path.join(api.env.proj_dir, '.git')):
        # clone the git repo
        with api.cd(api.env.proj_dir):
            api.run('git clone {0} .'.format(api.env.repo))

    # make sure the directories are writeable by me.
    api.sudo('chown myles:myles {0}'.format(' '.join([api.env.proj_dir,
                                                      api.env.html_dir,
                                                      api.env.venv_dir])))

    # createh virtual environment.
    if not exists(api.env.venv_dir):
        api.run('virtualenv {0}'.format(api.env.venv_dir))

    # install the dependencies.
    pip_upgrade()


@api.task
def python_version():
    """
    return the python version on the server for testing.
    """
    with api.cd(api.env.proj_dir):
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
    with api.cd(api.env.proj_dir):
        api.run('{0} install --upgrade -r '
                'requirements.txt'.format(api.env.venv_pip))


@api.task
def build_theme():
    scss_file = './theme/static/scss/style.scss'
    css_file = './theme/static/css/style.css'
    include_path = './bower_components/'

    api.local('sassc.py --include-path={0} {1} {2}'.format(include_path,
                                                           scss_file,
                                                           css_file))


@api.task
def ship_it():
    # Check to make sure that there isn't any unchecked files
    git_status = api.local('git status --porcelain', capture=True)

    if git_status:
        abort('There are unchecked files.')

    # Push the repo to the remote
    api.local('git push {0} {1}'.format(api.env.remote, api.env.branch))

    # The deploy tasks
    update_code()
    pip_upgrade()

    # Draw a ship
    puts("                           |    |    |                           ")
    puts("                          )_)  )_)  )_)                          ")
    puts("                         )___))___))___)\                        ")
    puts("                        )____)____)_____)\\                      ")
    puts("                      _____|____|____|____\\\__                  ")
    puts("             ---------\                   /---------             ")
    puts("               ^^^^^ ^^^^^^^^^^^^^^^^^^^^^                       ")
    puts("                 ^^^^      ^^^^     ^^^    ^^                    ")
    puts("                      ^^^^      ^^^                              ")