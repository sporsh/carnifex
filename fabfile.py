from fabric.api import local

TESTS_PATH = 'test'

def test(path=TESTS_PATH, coverage=False, nosetup=False, *args, **kwargs):
    nosetests(path, coverage, *args, **kwargs)
    if not nosetup:
        local("python setup.py check")

def nosetests(path=TESTS_PATH, coverage=False):
    """Run tests using nosetests with or without coverage
    """
    args = ["nosetests"]
    if coverage:
        args.extend(["--with-coverage",
                     "--cover-erase",
                     "--cover-package=carnifex",
                     "--cover-html"])
    args.append(path)
    local(' '.join(args))

def trial(path=TESTS_PATH, coverage=False):
    """Run tests using trial
    """
    args = ['trial']
    if coverage:
        args.append('--coverage')
    args.append(path)
    print args
    local(' '.join(args))

def unittest(path=TESTS_PATH):
    """Run tests using the unittest module
    """
    local("python -m unittest discover -s %s" % path)

def release():
    test()
    local("python setup.py sdist upload")

def clean(verified=False):
    local("python setup.py clean")
    args = ["git clean",
            "-dx",
            "-e '.pydevproject'",
            "-e '.project'"]
    if not verified:
        args.append("-n")
    else:
        args.append("-f")
    local(' '.join(args))

def whatsnew():
    local("git fetch")

    locallog = local("git log --abbrev-commit "
                     "--format='%Cgreen* %C(yellow)%h %Cblue%aN %Cgreen%ar "
                     "%Creset%s' FETCH_HEAD..", capture=True)
    remotelog = local("git log --abbrev-commit "
                      "--format='%Cred* %C(yellow)%h %Cblue%aN %Cgreen%ar "
                      "%Creset%s' ..FETCH_HEAD", capture=True)

    if locallog:
        print
        print "YOUR CHANGES:"
        print "-------------"
        print locallog
    if remotelog:
        print
        print "REMOTE CHANGES:"
        print "---------------"
        print remotelog
