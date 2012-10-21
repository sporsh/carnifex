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
