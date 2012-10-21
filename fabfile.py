from fabric.api import local

def unittest():
    local("python -m unittest discover -s test/unit")

def integrationtest():
    local("python -m unittest discover -s test/integration")

def test():
    local("python -m unittest discover")
    local("python setup.py check")

def release():
    test()
    local("python setup.py sdist upload")

def clean():
    local("python setup.py clean")

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
