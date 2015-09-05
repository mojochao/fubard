from setuptools import setup
from fubard import METADATA

setup(
    name=METADATA['name'],
    version=METADATA['version'],
    description=METADATA['description'],
    author=METADATA['author'],
    author_email=METADATA['author_email'],
    maintainer=METADATA['maintainer'],
    maintainer_email=METADATA['maintainer_email'],
    py_modules=['fubard'],
    install_requires=[
        'commentjson',
        'tabulate'
    ],
    entry_points={
        'console_scripts': [
            'fubard=fubard:main'
        ]
    }
)
