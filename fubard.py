"""Fractionally Useful Boilerplate Application for Rapid Development.

This package provides boilerplate for a Python command line application with
flexible configuration capabilities, action dispatching, error reporting, and
packaging support.

To create a new application named YOURAPPNAME:
- edit README.rst to reflect your application
- edit requirements.txt to reflect your application's dependencies
- edit setup.py to reflect your application's module and dependencies
- move fubard.py to YOURAPPNAME.py and edit to reflect your application's functionality

This package requires Python >= 2.7.

This package provides a small number of classes:
- :class:`fubard.Options` class responsible for managing application options
- :class:`fubard.Error` class responsible for reporting application errors

This package also provides a small number of functions:
- :func:`fubard.main` function used as an application entrypoint
- :func:`fubard.message` function used to message the application user
- :func:`fubard.get_parser` function used to access application command line parser
- :func:`fubard.get_action_and_options` function used to access application action and options
- :func:`fubard.do` function used to dispatch application actions with options

"""

# standard modules
from __future__ import print_function
import argparse
import os
import subprocess
import textwrap

# vendor modules
import commentjson
import tabulate

# module metadata
APP_NAME = __name__
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Fractionally Useful Boilerplate Application for Rapid Development.'
APP_AUTHOR = 'Allen Gooch'
APP_AUTHOR_EMAIL = 'allen.gooch@gmail.com'
APP_MAINTAINER = APP_AUTHOR
APP_MAINTAINER_EMAIL = APP_AUTHOR_EMAIL

#: Module user messaging may be expanded to include verbose output when configured with the 'verbose' boolean option
VERBOSE = False


def message(messages, verbose=False):
    """Writes *message* to console stdout.

    :param messages: messages to write
    :type messages: str

    :param verbose: only write if verbose option is enabled
    :type verbose: bool

    """
    if verbose and not VERBOSE:
        return
    if not isinstance(messages, list):
        messages = [messages]
    [print(m) for m in messages]


def main():
    """Module main function.

    :returns: process exit code returned to shell
    :rtype: int

    """
    try:
        action, options = get_action_and_options()
        if not action:
            raise Error('usage', 'missing action')
        do(action, options)
        exit_code = 0
    except Error as error:
        message(error.text)
        exit_code = 1
    return exit_code


def get_parser():
    """Returns application command line parser.

    :returns: application command line parser
    :rtype: :class:`argparse.ArgumentParser` object

    """
    def _add_build_arguments(parser_):
        parser_.add_argument('--sku', help='build sku')
        parser_.add_argument('--platform', help='build platform')
        parser_.add_argument('--environment', help='build environment')
        parser_.add_argument('--buildnum', help='build number')

    def _add_s3_arguments(parser_):
        parser_.add_argument('--s3access', help='aws s3 access key')
        parser_.add_argument('--s3secret', help='aws s3 secret key')

    # Create parser and add all common arguments.
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-c', '--configuration', help="configuration file to use for options", metavar='FILE')

    # Add actions sub-parser.
    subparsers = parser.add_subparsers(title='available actions')

    # Add 'activate' action.
    activate_parser = subparsers.add_parser('activate', help='activate a deployed build')
    activate_parser.set_defaults(action='activate')
    _add_build_arguments(activate_parser)

    # Add 'activated' action.
    activated_parser = subparsers.add_parser('activated', help='display activated build')
    activated_parser.set_defaults(action='activated')

    # Add 'archived' action.
    archived_parser = subparsers.add_parser('archived', help='list archived builds')
    archived_parser.set_defaults(action='archived')
    archived_parser.add_argument('-a', '--archives', help='archives server url')

    # Add 'cache' action.
    cache_parser = subparsers.add_parser('cache', help='cache an archived build')
    cache_parser.set_defaults(action='cache')
    _add_build_arguments(cache_parser)

    # Add 'cached' action.
    cached_parser = subparsers.add_parser('cached', help='list cached builds')
    cached_parser.set_defaults(action='cached')

    # Add 'clean' action.
    clean_parser = subparsers.add_parser('clean', help='clean a cached build')
    clean_parser.set_defaults(action='clean')
    _add_build_arguments(clean_parser)

    # Add 'configure' action.
    configure_parser = subparsers.add_parser('configure', help='edit a persistent configuration')
    configure_parser.set_defaults(action='configure')
    configure_parser.add_argument('-e', '--editor', help='editor to use')
    configure_parser.add_argument('-g', '--global', help='edit global configuration', action='store_true')

    # Add 'deploy' action.
    deploy_parser = subparsers.add_parser('deploy', help='deploy a cached build')
    deploy_parser.set_defaults(action='deploy')
    _add_build_arguments(deploy_parser)
    _add_s3_arguments(deploy_parser)

    # Add 'deployed' action.
    deployed_parser = subparsers.add_parser('deployed', help='list deployed builds')
    deployed_parser.set_defaults(action='deployed')
    _add_s3_arguments(deployed_parser)

    # Add 'version' action.
    version_parser = subparsers.add_parser('version', help='display version information')
    version_parser.set_defaults(action='version')

    # Add 'options' action.
    options_parser = subparsers.add_parser('options', help='display options')
    options_parser.set_defaults(action='options')

    # Add 'skus' action.
    skus_parser = subparsers.add_parser('skus', help='display valid skus')
    skus_parser.set_defaults(action='skus')

    # Add 'platforms' action.
    platforms_parser = subparsers.add_parser('platforms', help='display valid platforms')
    platforms_parser.set_defaults(action='platforms')

    # Add 'environments' action.
    environments_parser = subparsers.add_parser('environments', help='display valid environments')
    environments_parser.set_defaults(action='environments')

    return parser


def get_action_and_options():
    """Returns application action and options.

    Parses command line for action and options.  If a configuration file was
    specified, use its data exclusively.

    :returns: application action and options
    :rtype: (str, {str:str})

    """
    parser = get_parser()
    args = vars(parser.parse_args())
    action = args['action']
    configuration = args['configuration']
    options = Options(args, configuration)
    return action, options


def do(action, options):
    """Performs *action* with *options*.

    :param action: action name
    :type action: str

    :param options: action options
    :type options: {str:str}

    :raises: :class:`fubard.Error`

    """
    if action not in _ACTIONS:
        raise Error('usage', 'unknown action: {}'.format(action))
    if 'verbose' in options:
        global VERBOSE
        VERBOSE = options['verbose']
    _ACTIONS[action](options)


def _do_foo(_):
    """Performs 'foo' action with *options."""
    message('performing foo')


def _do_bar(options):
    """Performs 'bar' action with *options.

    :param options: action options
    :type options: {str:str}

    """
    message('performing bar with baz {}'.format(options.values['baz']))


# Valid app actions and their handlers.
_ACTIONS = {
    'foo': _do_foo,
    'bar': _do_bar
}


class Options(object):
    """Application options class.

    Applications utilize flexible configuration options.  The first option is to
    load all options from a single, specific options file.  The second option
    is to load and update options from multiple sources.

    - default options
    - found persistent options
    - global persistent options
    - options parsed from command line arguments

    In the second case, options from later sources update previous options.

    """

    #: Options may be persisted in options files.
    OPTIONS_FILE_NAME = '.{}.json'.format(APP_NAME)

    #: Options file text for new options files.
    OPTIONS_FILE_TEXT = """// fubard configuration. Uncomment and edit as desired.
    {
    //"verbose": false
    }
    """

    #: Default options.
    DEFAULT_OPTIONS = {
        'verbose': False
    }

    #: Default text editor
    DEFAULT_EDITOR = os.environ['EDITOR'] if 'EDITOR' in os.environ else 'vi'

    def __init__(self, args=None, options_file=None, ignore_defaults=False, ignore_persistent=False):
        """Initializes new Options object.

        :param args: command line args, if any
        :type args: {str:str}

        :param options_file: path of options file to load
        :type options_file: str

        :param ignore_defaults: ignore default options
        :type ignore_defaults: bool

        :param ignore_persistent: ignore persistent options
        :type ignore_persistent: bool

        """
        self._args_options = args if args is not None else {}
        self._options_file = options_file
        self._ignore_defaults = ignore_defaults
        self._ignore_persistent = ignore_persistent

        # the following attributes are all lazy-loaded on property access
        self._persistent_options_file = None
        self._persistent_options = None
        self._user_options = None
        self._values = None
        self._sources = None

    @property
    def names(self):
        """Option names property.

        :returns: option names
        :rtype: [str]

        """
        return self.defaults.keys()

    @property
    def values(self):
        """Option values property.

        :returns: option values
        :rtype: {str:str}

        """
        if self._values is None:
            if self._options_file is not None:
                self._values = Options.load_options_file(self._options_file)
            else:
                options = self.defaults
                Options.update_options(options, self.persistent)
                Options.update_options(options, self.args)
                self._values = {k: v for k, v in options.items() if v is not None}
        return self._values

    @property
    def sources(self):
        """Option sources property.

        :returns: option sources
        :rtype: {str:str}

        """
        if self._sources is None:
            if self._options_file is not None:
                self._sources = {k: self._options_file for k in self.values.keys()}
            else:
                sources = {k: 'default' for k in self.defaults.keys()}
                sources.update({k: self.persistent_options_file for k, v in self.persistent.items() if v is not None})
                sources.update({k: 'arg' for k, v in self.args.items() if v is not None})
                self._sources = sources
        return self._sources

    @property
    def defaults(self):
        """Default options property.

        :returns: default options
        :rtype: {str:str}

        """
        return dict(Options.DEFAULT_OPTIONS)

    @property
    def args(self):
        """Args options property.

        :returns: args options
        :rtype: {str:str}

        """
        return dict(self._args_options)

    @property
    def persistent(self):
        """Persistent options property.

        :returns: persistent options
        :rtype: {str:str}

        """
        if self._persistent_options is None:
            location = self._persistent_options_file
            self._persistent_options = Options.load_options_file(location) if location else {}
        return self._persistent_options

    @property
    def persistent_options_file(self):
        """Persistent options file property.

        :returns: persistent options file path
        :rtype: str

        """
        if self._persistent_options_file is None:
            self._persistent_options_file = Options.find_options_file()
        return self._persistent_options_file

    @property
    def user(self):
        """User options property.

        :returns: args options
        :rtype: {str:str}

        """
        if self._user_options is None:
            location = os.path.expanduser('~/{}'.format(Options.OPTIONS_FILE_NAME))
            self._user_options = Options.load_options_file(location)
        return dict(self._user_options)

    @staticmethod
    def create_options_file(path):
        """Creates options file at *path*.

        :param path: options file path
        :type path: str

        """
        if not os.path.exists(path):
            with open(path, 'w') as outfile:
                outfile.write(Options.OPTIONS_FILE_TEXT)
            message('created new configuration: {}'.format(path), verbose=True)

    @staticmethod
    def edit_options_file(path=None, editor=None, edit_global=False):
        """Edit options file at *path*.

        :param path: options file path
        :type path: str

        :param editor: editor command to use
        :type editor: str

        :param edit_global: edit the global options file
        :type edit_global: bool

        """
        if editor is None:
            editor = Options.DEFAULT_EDITOR

        if edit_global:
            filename = os.path.expanduser('~/{}'.format(Options.OPTIONS_FILE_NAME))
        elif path is None:
            filename = Options.find_options_file()
        else:
            filename = path

        try:
            if not os.path.exists(filename):
                Options.create_options_file(filename)
            subprocess.call([editor, filename])
        except Exception as error:
            raise Error('exec', 'cannot launch editor: {}'.format(error))

    @staticmethod
    def load_options_file(path):
        """Loads options from file at *path*.

        :param path: options file path
        :type path: str

        :returns: loaded options
        :rtype: {str:str}

        """
        try:
            with open(path) as infile:
                text = infile.readlines()
            return commentjson.loads(text)
        except Exception as error:
            raise Error('load', 'cannot load options file {}: {}'.format(path, error))

    @staticmethod
    def find_options_file(path=None):
        """Locates options file.

        The search will start at the current working directory, and will continue to
        search up through all successive parent directories until no more parent
        directories remain.  The first options file found will be returned.

        :param path: path of directory to start search in
        :type path: str

        :returns: options file path if exists, otherwise None
        :rtype: str|None

        """
        # find all candidate directories
        if path is None:
            path = os.path.expanduser('~')
        search_dirs = [path]
        parts = os.getcwd().split('/')[1:]
        for i, part in enumerate(parts):
            search_dirs.append(os.path.join('/', *parts[:i+1]))

        # search candidate directories for options files
        for search_dir in reversed(search_dirs):
            options_file = os.path.join(search_dir, Options.OPTIONS_FILE_NAME)
            if os.path.exists(options_file):
                return options_file  # Success!
        return None  # Failure!

    @staticmethod
    def update_options(options, new):
        """Updates values in *options* with those found in *new*.

        :param options: options to be updated dictionary
        :type options: {str:str}

        :param new: new, updated options dictionary
        :type new: {str:str}

        """
        for k, v in new.items():
            if v is not None:
                options[k] = v


class Error(Exception):
    """Application error abstract base class."""

    def __init__(self, category, brief, details=None):
        self.category = category
        self.brief = brief
        self.details = [] if details is None else details

    def __str__(self):
        return '{} error: {}'.format(self.category, self.brief)

    @property
    def text(self):
        result = '{} error: {}\n'.format(self.category, self.brief)
        for detail in self.details:
            result += '\n'
            result += '\n'.join(textwrap.wrap(detail, initial_indent=' '*2))
        result += '\n'
        return result


if __name__ == '__main__':
    import sys
    sys.exit(main())
