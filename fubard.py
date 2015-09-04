"""Fractionally Useful Boilerplate Application for Rapid Development.

This package provides boilerplate for a Python command line application with
flexible configuration capabilities, action dispatching, error reporting, and
packaging support.

This package requires Python >= 2.7.

This package provides a small number of classes:

- :class:`fubard.Error` class responsible for reporting application errors
- :class:`fubard.Options` class responsible for managing application options

This package also provides a small number of functions:

- :func:`fubard.main` function used as an application entrypoint by setup.py
- :func:`fubard.message` function used by application to message user
- :func:`fubard.get_parser` function used by application to parse command line for action and options
- :func:`fubard.get_action_and_options` function used to get application action and options
- :func:`fubard.do` function used to dispatch application action with options

Search for 'STEP-*' for customization steps.

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

# STEP-1: update application metadata

APP_NAME = __name__
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Fractionally Useful Boilerplate Application for Rapid Development.'
APP_AUTHOR = 'Allen Gooch'
APP_AUTHOR_EMAIL = 'allen.gooch@gmail.com'
APP_MAINTAINER = APP_AUTHOR
APP_MAINTAINER_EMAIL = APP_AUTHOR_EMAIL

#: Module user messaging may be expanded to include verbose output when configured with the 'verbose' boolean option
VERBOSE = False


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


def get_parser():
    """Returns application command line parser.

    :returns: application command line parser
    :rtype: :class:`argparse.ArgumentParser` object

    """
    # Create parser and add all common arguments.
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-c', '--configuration', help="configuration file to use for options", metavar='FILE')

    # Add actions sub-parser.
    subparsers = parser.add_subparsers(title='available actions')

    # STEP-2: add your own actions before returning the parser

    # Add 'foo' action.
    foo_parser = subparsers.add_parser('foo', help="demo 'foo' action")
    foo_parser.set_defaults(action='foo')

    # Add 'bar' action.
    archived_parser = subparsers.add_parser('bar', help="demo 'bar' action")
    archived_parser.set_defaults(action='bar')
    archived_parser.add_argument('-b', '--with_baz', help="demo 'baz' option")

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


def _do_configure(options):
    """Configure action handler.

    Edits a persistent configuration, creating it on demand.

    :param options: action options
    :type options: {str:str}

    """
    editor = options.values['editor'] if 'editor' in options.values else None
    edit_global = 'global' in options.values and options.values['global']
    Options.edit_options_file(editor=editor, edit_global=edit_global)


def _do_options(options):
    """Options action handler.

    Displays app options.

    :param options: action options
    :type options: {str:str}

    """
    table = sorted(options.items())
    headers = ['option', 'value']
    message(tabulate.tabulate(table, headers, tablefmt='psql'))


def _do_version(_):
    """Version action handler.

    Displays app version information.

    """
    message('{}-{}'.format(APP_NAME, APP_VERSION))


# STEP-3: replace example action handler functions with your own


def _do_foo(_):
    """Performs 'foo' action."""
    message('performing foo')


def _do_bar(options):
    """Performs 'bar' action with *options.

    :param options: action options
    :type options: {str:str}

    """
    message('performing bar with baz {}'.format(options.values['baz']))

#: Valid app actions and their handlers.
_ACTIONS = {
    'configure': _do_configure,
    'options': _do_options,
    'version': _do_version,

    # STEP-4: replace example action handlers in actions registry with your own

    'foo': _do_foo,
    'bar': _do_bar
}


class Error(Exception):
    """Application error class."""

    def __init__(self, category, brief, details=None):
        """Initializes new Error object.

        :param category: error category
        :type category: str

        :param brief: brief error message
        :type brief: str

        :param details: detailed error messages
        :type details: [str]

        """
        self.category = category
        self.brief = brief
        self.details = [] if details is None else details

    @property
    def text(self):
        """Error text property.

        :returns: error text
        :rtype: str

        """
        result = '{} error: {}\n'.format(self.category, self.brief)
        for detail in self.details:
            result += '\n'
            result += '\n'.join(textwrap.wrap(detail, initial_indent=' '*2))
        result += '\n'
        return result


class Options(object):
    """Application options class.

    Applications utilize flexible configuration options.  The first option is to
    load all options from a single, specific options file.  The second option
    is to load and update options from multiple sources:

    - default options
    - found persistent options
    - global persistent options
    - options parsed from command line arguments

    In the second case, options from later sources update previous options.

    """

    #: Options may be persisted in options files.
    OPTIONS_FILE_NAME = '.{}.json'.format(APP_NAME)

    # STEP-5: update options file text

    #: Options file text for new options files.
    OPTIONS_FILE_TEXT = """// fubard configuration. Uncomment and edit as desired.
    {
    //"verbose": false
    }
    """

    # STEP-6: update default options

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


if __name__ == '__main__':
    import sys
    sys.exit(main())
