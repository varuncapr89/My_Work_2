from setuptools import setup, find_packages

setup(
    name='bob',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'boto3',
        'ruamel.yaml',
        'GitPython',
        'termcolor',
        'pwinput'
    ],
    entry_points={
        'console_scripts': [
            'bob = bob.scripts.entrypoint:cli',
        ],
    },
)