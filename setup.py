from setuptools import setup

install_requires = [
    'boto3',
    'charmworldlib',
    'PyYAML',
    'click',
]

tests_require = [
    'coverage',
    'nose',
    'pep8',
]


setup(
    name='cdp',
    version='0.0.0',
    description='Charm developer portal',
    install_requires=install_requires,
    author='Marco Ceppi',
    author_email='marco@ceppi.net',
    url="https://github.com/juju-solutions/cdp",
    packages=['cdp'],
    entry_points={
        'console_scripts': [
            'cdp=cdp.cli:main'
        ]
    }
)
