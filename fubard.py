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
- :func:`fubard.register_action` function used to add an action to the application actions registry
- :func:`fubard.register_option` function used to add an option to the application options registry
- :func:`fubard.get_parser` function used by application to parse command line for action and options
- :func:`fubard.get_action_and_options` function used to get application action and options
- :func:`fubard.dispatch_action_and_options` function used to dispatch application action with options

"""

# STEP-0: Update the module docstring at top of this file to reflect your application.

# standard modules
from __future__ import print_function
import argparse
import os
import subprocess
import textwrap
import sys

# vendor modules
import commentjson
import tabulate

# STEP-1: Update application metadata.

METADATA = {
    'name': __name__,
    'version': '1.0.0',
    'description': 'Fractionally Useful Boilerplate Application for Rapid Development.',
    'author': 'John Doe',
    'author_email': 'john.doe@nonesuch.com',
    'maintainer': 'Jane Doe',
    'maintainer_email': 'jane.doe@nonesuch.com'
}

# STEP-2: Append new options defaults as needed.

DEFAULT_OPTIONS = {
    'verbose': False
}

# STEP-3: Append new configuration file text as needed.

####################################################################################
# BOILERPLATE-BEGIN: Everything from here to BOILERPLATE-END should be off limits. #
####################################################################################

CONFIGURATION_JSON_TEXT = '''{
// "verbose": false
}'''

#: Application user messaging verbosity enabled.
VERBOSE = False

#: Application actions registry.  It's a list to provide ordering of additions.
ACTIONS_REGISTRY = []

# Application options registry.  It's a list to provide ordering of additions.
OPTIONS_REGISTRY = []


def main():
    """Module main function used as an application entrypoint.

    :returns: process exit code returned to shell
    :rtype: int

    """
    try:
        action, options = get_action_and_options()
        if not action:
            raise Error('usage', 'missing action')
        dispatch_action_and_options(action, options)
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


def register_action(name, func, desc, options=None):
    """Adds application action to actions registry.

    :param name: action name
    :type name: str

    :param func: action handler function or function name
    :type func: func|str

    :param desc: action description
    :type desc: str

    :param options: action options metadata
    :type options: [{str:str}]

    """
    exists = [action for action in ACTIONS_REGISTRY if action[0] == name]
    if exists:
        return ValueError("action '{}' already added".format(name))
    ACTIONS_REGISTRY.append((name, func, desc, options))


def register_option(name, *args, **kwargs):
    """Adds application action to actions registry.

    :param name: option name
    :type name: str

    :param args: positional args passed to argparse
    :type args: [str]

    :param kwargs: keyword args passed to argparse
    :type kwargs: {str:str}

    """
    exists = [option for option in OPTIONS_REGISTRY if option[0] == name]
    if exists:
        return ValueError("option '{}' already added".format(name))
    OPTIONS_REGISTRY.append((name, args, kwargs))


def get_parser():
    """Returns application command line parser.

    :returns: application command line parser
    :rtype: :class:`argparse.ArgumentParser` object

    """
    parser = argparse.ArgumentParser(description=METADATA['description'])
    for name, args, kwargs in OPTIONS_REGISTRY:
        parser.add_argument(args, kwargs)
    subparsers = parser.add_subparsers(title='available actions')
    for name, func, desc in ACTIONS_REGISTRY:
        subparsers.add_parser(name, help=desc)
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
    del args['action']

    configuration = args['configuration']
    options = Options(args, configuration)

    return action, options


def dispatch_action_and_options(action, options):
    """Dispatches *action* with *options*.

    :param action: action name
    :type action: str

    :param options: action options
    :type options: {str:str}

    """
    found = [item for item in ACTIONS_REGISTRY if item[0] == action]
    if not found:
        raise Error('usage', 'unknown action: {}'.format(action))
    if 'verbose' in options:
        global VERBOSE
        VERBOSE = options['verbose']
    action = found[1]
    if isinstance(action, basestring):
        action = globals()[action]
    action(options)


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
    message('{}-{}'.format(METADATA['name'], METADATA['version']))


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
    OPTIONS_FILE_NAME = '.{}.json'.format(__name__)

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
                Options.update_options(options, self.user)
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
                sources.update({k: 'user' for k in self.user.keys()})
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
        return dict(DEFAULT_OPTIONS)

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
                outfile.write(CONFIGURATION_JSON_TEXT)
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


# Add boilerplate application actions and options
register_action('configure', 'do_configure', 'create or edit configuration file', [
            ('user', ['-u', '--user'], {'help': 'create or edit user configuration file'}),
            ('file', ['-f', '--file'], {'help': 'create or edit specified configuration file'})])
register_action('options', 'do_options', 'view options information')
register_action('version', 'do_version', 'view version information')

register_option('verbose', ['-v', '--version'], {'help': 'enable verbose output', 'action': 'store_true'})
register_option('configuration', ['-c', '--configuration'], {'help': 'configuration file to use', 'metavar': 'FILE'})

if __name__ == '__main__':
    sys.exit(main())

################################################################################
# BOILERPLATE-END: Everything your own application needs should go below here. #
################################################################################

# STEP-4: Replace the action handler functions below with those needed by your application

def _do_foo(_):
    message("doing foo action")

def _do_bar(options):
    message("doing bar action with baz option '{}'".format(options.values['baz']))

# STEP-5: Replace the register actions and options below with those needed by your application.

register_action('foo', _do_foo, "demonstrate a 'foo' action")
register_action('bar', '_do_bar', "demonstrate a 'bar' action", [
            ('baz', ['-z', '--baz'], {'help': "demonstrate a 'bar' action 'baz' option"})])
