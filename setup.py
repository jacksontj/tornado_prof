try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Tornado Profiling Library',

    'url': 'https://github.com/jacksontj/tornado-prof',
    'author': 'Thomas Jackson',
    'author_email': 'jacksontj.89@gmail.com',
    'license': 'MIT',
     'classifiers': [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    'version': '0.0.6',
    'packages': ['tornado_prof'],
    'scripts': [],
    'name': 'tornado-prof',
    # TODO: unify with requirements.txt
    'install_requires': ['tornado>=3.0'],
}

setup(**config)
