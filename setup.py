from setuptools import setup
from fubard import APP_NAME, APP_VERSION, APP_DESCRIPTION, APP_AUTHOR, \
    APP_AUTHOR_EMAIL, APP_MAINTAINER, APP_MAINTAINER_EMAIL

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_AUTHOR,
    author_email=APP_AUTHOR_EMAIL,
    maintainer=APP_MAINTAINER,
    maintainer_email=APP_MAINTAINER_EMAIL,
    py_modules=['fubard'],
    install_requires=[
        'commentjson',     # for JSON processing
        'tabulate'         # for table printing
    ],
    entry_points={
        'console_scripts': [
            'fubard=fubard:main'
        ]
    }
)
