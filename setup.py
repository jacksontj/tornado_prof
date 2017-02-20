try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Tornado Profiling Library',
    'author': 'Thomas Jackson',
    'url': 'https://github.com/jacksontj/tornado-prof',
    'author_email': 'jacksontj.89@gmail.com',
    'version': '0.1',
    'packages': ['tornado_prof'],
    'scripts': [],
    'name': 'tornado-prof'
}

setup(**config)
