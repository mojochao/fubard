"""Fractionally Useful Boilerplate Application for Rapid Development.

This package requires Python 2.7 or higher.

This package provides boilerplate for a Python command line application with
flexible configuration capabilities, action dispatching, error reporting, and
packaging support.

This package provides a small number of classes:

- :class:`fubard.App` class responsible for defining and running application
- :class:`fubard.Error` class responsible for reporting application errors
- :class:`fubard.Options` class responsible for managing application options

Modules using this package are expected to provide:

- a METADATA dictionary containing module information used by setup.py
- a subclass of the :class:`fubard.App` class providing your own application actions and options
- a main() function creating and running an instance of your application class
- a test for the module being invoked as main that calls your main()

A minimal, yet complete, example of this might look like the following:

::

    from fubard import App, Error, message

    METADATA = {
        'name': __name__,
        'version': '1.0.0',
        'description': 'Demonstration Foo Bar Application',
        'author': 'John Doe',
        'author_email': 'john.doe@nonesuch.com',
        'maintainer': 'Jane Doe',
        'maintainer_email': 'jane.doe@nonesuch.com'
    }

    class FooBarApp(App):

        def init_actions(self):
            super(FooBarApp, self).init_actions()  # let the base application add its own actions
            self.register_action('foo', self._do_foo, "demonstrate a 'foo' action")
            self.register_action('bar', self._do_bar, "demonstrate a 'bar' action", [
                ('baz', ['-z', '--baz'], {
                    'help': "demonstrate a 'bar' action 'baz' option"
                })])
            self.register_action('hello', self._do_hello, "demonstrate a 'hello' action", [
                ('who', ['-w', '--who'], {
                    'help': "who to greet"
                })])

        def _do_foo(self, options, others):
            message("doing foo action")

        def _do_bar(self, options, others):
            message("doing bar action with baz option '{}'".format(options['baz']))

        def _do_hello(self, options, others):
            if len(others) < 1:
                raise Error('usage', "missing 'who' option")
            message('Hello, {}'.format(others[0]))

    def main():
        return FooBarApp(METADATA).run()

    if __name__ == '__main__':
        sys.exit(main())

And that's all it that's required.  Go forth and create command line apps!

"""

# standard modules
from __future__ import print_function
import argparse
import textwrap
import sys


# Package metadata
METADATA = {
    'name': __name__,
    'version': '1.0.0',
    'description': 'Fractionally Useful Basis for Application Rapid Development',
    'author': 'Allen Gooch',
    'author_email': 'allen.gooch@gmail.com',
    'maintainer': 'Allen Gooch',
    'maintainer_email': 'allen.gooch@gmail.com'
}

# TODO(AG): add logging capability

if sys.version_info < (2, 7):
    print('error: Python 2.7 or higher required')

#: Application user messaging verbosity enabled.
VERBOSE = False


def message(messages, verbose=False):
    """Writes *message* to console stdout.

    :param messages: messages to write
    :type messages: str

    :param verbose: only write if verbose option is enabled
    :type verbose: bool

    """
    if verbose and not App.VERBOSE:
        return
    if not isinstance(messages, list):
        messages = [messages]
    [print(m) for m in messages]


class App(object):
    """Application class."""

    def __init__(self, metadata):
        """Initializes new App object.

        The initializer is where additions of actions and options should take place.

        Make sure to call super() first in your subclass's __init__ method.

        """
        self._metadata = metadata
        self._actions_registry = []
        self._options_registry = []
        self.init_actions()
        self.init_options()

    @property
    def metadata(self):
        """Application metadata property.

        :returns: application name
        :rtype: str

        """
        return self._metadata

    def init_actions(self):
        """Initializes all application actions.

        All applications must have actions registered to perform any meaningful work.
        Register them here.

        """
        self.register_action('version', self._do_version, 'view version information')

    def is_action(self, name):
        """Tests if *name* is name of registered action.

        :param name: name of action to test
        :type name: str

        :returns: True if registered action, False otherwise
        :rtype: bool

        """
        exists = [action for action in self._actions_registry if action[0] == name]
        return len(exists) == 1

    def get_action(self, name):
        """Gets action descriptor registered with *name*.

        An action descriptor is a tuple of the form (name, function, description, [options])
        where [options] is a list of option descriptors.

        :param name: name of action to get
        :type name: str

        :returns: registered action descriptor
        :rtype: (str, func, help, [(str, [str], {str:str}]

        :raises: KeyError if no action found registered as *name*

        """
        exists = [action for action in self._actions_registry if action[0] == name]
        if len(exists) != 1:
            raise KeyError(name)
        return exists[0]

    def register_action(self, name, func, desc, option_descriptors=None):
        """Adds action descriptor to actions registry.

        An action descriptor is a tuple of the form (name, function, description, [options])
        where [options] is a list of option descriptors.

        :param name: action name
        :type name: str

        :param func: action handler function or function name
        :type func: func

        :param desc: action description
        :type desc: str

        :param option_descriptors: action option descriptors
        :type option_descriptors: [{str:str}]

        """
        exists = [action for action in self._actions_registry if action[0] == name]
        if exists:
            return ValueError("action '{}' already added".format(name))
        if option_descriptors is None:
            option_descriptors = []
        action_descriptor = (name, func, desc, option_descriptors)
        self._actions_registry.append(action_descriptor)

    def init_options(self):
        """Initializes all application options.

        Many applications require global options when performing any work.
        Register them here.

        """
        self.register_option('verbose', ['-v', '--verbose'], {
            'help': 'enable verbose output',
            'action': 'store_true',
            'default': False,
        })

    def is_option(self, name):
        """Tests if *name* is name of registered option.

        :param name: name of option to test
        :type name: str

        :returns: True if registered option, False otherwise
        :rtype: bool

        """
        exists = [option for option in self._options_registry if option[0] == name]
        return len(exists) == 1

    def get_option(self, name):
        """Gets option descriptor registered with *name*.

        An option descriptor is a tuple of the form (name, [argparse-args], {argparse-kwargs})

        :param name: name of option to get
        :type name: str

        :returns: registered option descriptor
        :rtype: (str, func, help, [(str, [str], {str:str}]

        :raises: KeyError if no option found registered as *name*

        """
        exists = [option for option in self._options_registry if option[0] == name]
        if len(exists) != 1:
            raise KeyError(name)
        return exists[0]

    def register_option(self, name, args, kwargs):
        """Adds option descriptor to options registry.

        An option descriptor is a tuple of the form (name, [argparse-args], {argparse-kwargs})

        :param name: option name
        :type name: str

        :param args: positional args passed to argparse
        :type args: [str]

        :param kwargs: keyword args passed to argparse
        :type kwargs: {str:str}

        """
        exists = [option for option in self._options_registry if option[0] == name]
        if exists:
            return ValueError("option '{}' already added".format(name))
        self._options_registry.append((name, args, kwargs))

    def run(self, cmdline=None):
        """Runs application.

        Runs application and returns exit code, where success is indicated by 0 and
        failure is indicated by 1, suitable for return to shell to indicate process
        success status.

        :param cmdline: command line arguments, or something acting as such
        :type cmdline: [str]|str

        :returns: exit code
        :rtype: int

        """
        if cmdline is None:
            cmdline = sys.argv[1:]
        elif isinstance(cmdline, basestring):
            cmdline = cmdline.split()
        try:
            action, options, others = self._parse(cmdline)
            self._dispatch(action, options, others)
            exit_code = 0
        except Error as error:
            message(error.text)
            exit_code = 1
        return exit_code

    @property
    def _parser(self):
        """Application command line parser property.

        :returns: application command line parser
        :rtype: :class:`argparse.ArgumentParser` object

        """
        parser = argparse.ArgumentParser(description=self.metadata['description'])

        # First, add all global options,
        for name, args, kwargs in self._options_registry:
            kwargs = {k: v for k, v in kwargs.items() if k != 'default'}   # defaults not handled by parser
            parser.add_argument(*args, **kwargs)

        # Next, add an actions subparser and add all action parsers to it.
        actions_subparser = parser.add_subparsers(title='available actions')
        for name, func, desc, option_descriptors in self._actions_registry:
            action_parser = actions_subparser.add_parser(name, help=desc)
            action_parser.set_defaults(action=name)
            for _, args, kwargs in option_descriptors:
                kwargs = {k: v for k, v in kwargs.items() if k != 'default'}   # defaults not handled by parser
                action_parser.add_argument(*args, **kwargs)

        return parser

    def _parse(self, cmdline):
        """Returns application action, options, and other tokens in *args*.

        Parses *args* for action and options.  If a configuration file was
        specified, use its data exclusively.

        :param cmdline: command line arguments, or something acting as such
        :type cmdline: [str]

        :returns: application action, options, and others
        :rtype: (str, {str:str}, [str])

        """
        args, others = self._parser.parse_known_args()
        options = vars(args)
        action = options['action']
        del options['action']
        return action, options, others

    def _dispatch(self, action, options, others):
        """Dispatches *action* with *options*.

        :param action: action name
        :type action: str

        :param options: action options
        :type options: {str:str}

        :param others: action other tokens
        :type others: [str]

        """
        # set the verbosity
        if 'verbose' in options:
            global VERBOSE
            VERBOSE = options['verbose']
        try:
            action_descriptor = self.get_action(action)
            func = action_descriptor[1]
            func(options, others)
        except ValueError:
            raise Error('usage', 'unknown action: {}'.format(action))

    def _do_version(self, options, others):
        """Version action handler.

        Displays app version information.

        :param options: action options
        :type options: {str:str}

        :param others: action other tokens
        :type others: [str]

        """
        message('{}-{}'.format(self.metadata['name'], self.metadata['version']))


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


class _FooBarApp(App):

    def __init__(self):
        super(_FooBarApp, self).__init__(METADATA)

    def init_actions(self):
        super(_FooBarApp, self).init_actions()  # let the base application add its own actions
        self.register_action('foo', self._do_foo, "demonstrate a 'foo' action")
        self.register_action('bar', self._do_bar, "demonstrate a 'bar' action", [
            ('baz', ['-z', '--baz'], {
                'help': "demonstrate a 'bar' action 'baz' option"
            })])
        self.register_action('hello', self._do_hello, "demonstrate a 'hello' action", [
            ('who', ['-w', '--who'], {
                'help': "who to greet"
            })])

    def _do_foo(self, options, others):
        message("doing foo action")

    def _do_bar(self, options, others):
        try:
            message("doing bar action with baz option '{}'".format(options['baz']))
        except KeyError:
            raise Error('usage', "missing 'baz' option")

    def _do_hello(self, options, others):
        if len(others) < 1:
            raise Error('usage', "missing name argument")
        message('Hello, {}!'.format(others[0]))


def main():
    return _FooBarApp().run()


if __name__ == '__main__':
    sys.exit(main())
