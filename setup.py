from distutils.core import setup

readme = open('README.rst', 'r').read()

setup(
      name='carnifex',
      version='0.1.0',
      packages=['carnifex'],
      provides=['carnifex'],
      requires=['Twisted'],

      author='Geir Sporsheim',
      author_email='gksporsh@gmail.com',
      url='http://github.com/sporsh/carnifex',

      description="Provides a uniform way of running processes remotely and locally.",
      classifiers=[
                   'Programming Language :: Python',
                   'Development Status :: 3 - Alpha',
                   'Framework :: Twisted',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Information Technology',
                   'Intended Audience :: System Administrators',
                   'Operating System :: OS Independent',
                   'Topic :: Internet',
                   'Topic :: Security',
                   'Topic :: System',
                   'Topic :: System :: Networking',
                   'Topic :: System :: Operating System',
                   'Topic :: System :: Systems Administration',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Terminals'
                   ],
      long_description=readme
      )
