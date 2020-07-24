import os
import re
import traceback
import json
import time

from chatbot_builder.bot_builder import BotBuilder
from chatbot_builder import constants as const

# Command word definitions
CMD_HELP = "help"
CMD_NEW = "new"
CMD_ENTRY = "entry"
CMD_ON = "on"
CMD_FORGET = "forget"
CMD_LOAD = "load"
CMD_UNLOAD = "unload"
CMD_LOADED = "loaded"
CMD_DELETE = "delete"
CMD_RESPONDING = "responding"
CMD_SAVE = "save"
CMD_DROP = "drop"
CMD_TREE = "tree"
CMD_SETVAR = "set"
CMD_GETVAR = "get"

RESPONSE_FORMAT_TEXT = """
----- FORMAT TOKENS -----

The provided response text may include format tokens that reference matching text
within parenthesis groups in the pattern. These tokens should be of the form "{{pN}}",
where "N" is an integer representing the position of the parenthesis group within
the pattern, from left-to-right.

For example, given the pattern "I like ([a-z]*) and ([a-z]*)", and the response
text "I like {{p0}} too, but not {{p1}}", an input of "I like cats and dogs" would yield
a response of "I like cats too, but not dogs".

The provided response text may also contain commands to create custom format tokens
on the fly. Custom format tokens may be mapped to arbitrary literal strings, or to
other format tokens. This is achieved by appending ";;" to the end of the response
text, to mark the beginning of the custom format tokens, followed by one or more
comma-separated assignment statements of the form "name=value" (both name and value
may be any string of characters, except for "," and "=").

For example, given the pattern "I like (.*) and (.*)", and the response text
"OK, {{p0}} and {{p0}};;like1={{p0}},like2={{p1}}", an input of "I like green and red"
would yield a response of "OK, green and red", and would create two new format
tokens. You can now use "like1" and "like2" as format tokens in further responses.
For example, the response text "you like {{like1}} and {{like2}}" would yield
"you like green and red" when triggered.
"""

# Help text definitions for command words
CMD_HELP_HELP = """
{0} [command_name]

Get information about how to use a command by name.
Usage information about [command_name] will be shown.
"""

CMD_SETVAR_HELP = """
{0} [token_name] [token_value]

Creates a new format token [token_name] with the value [token_value]. [token_value]
may be a literal string, or another format token. If [token_name] already exists
then its value will be overwritten.
"""

CMD_GETVAR_HELP = """
{0} [token_name]

Gets the value of a format token named [token_name].
"""

CMD_NEW_HELP = """
{0} [name]

Creates a new sub-context under the currently loaded context.
[name] will be the name of the new sub-context.
"""

CMD_ENTRY_HELP = """
{0} [pattern] [response]

Creates a new entry pattern/response pair under the context currently loaded for editing.
If the bot recognises an entry [pattern] for any of the sub-contexts in the current
context, entry of that sub-context will be triggered, and [response] will be returned.
If no context is currently loaded for editing, then this command will do nothing.
""" + RESPONSE_FORMAT_TEXT

CMD_ON_HELP = """
{0} [pattern] [response]

Creates a new pattern/response pair under the context currently loaded for editing.
[pattern] is a regular expression for the bot to recognise. [response] is the
string that will be sent in response to the pattern being recognised.
""" + RESPONSE_FORMAT_TEXT

CMD_FORGET_HELP = """
{0} [pattern]

Deletes the pattern/response pair associated with [pattern] under the context
currently loaded for editing. If [pattern] does not exist in the context currently
loaded for editing, then this command does nothing.
"""

CMD_LOAD_HELP = """
{0} [context_name]

Loads the context [context_name] for editing.
Further commands to create new subcontexts or pattern/response pairs will be
applied to this context until it is unloaded.
"""

CMD_UNLOAD_HELP = """
{0}

Unloads the context that is currently loaded for editing, if any.
"""

CMD_LOADED_HELP = """
{0}

Shows information about the context currently loaded for editing, if any.
"""

CMD_DELETE_HELP = """
{0} [context_name]

Deletes the context [context_name]
"""

CMD_RESPONDING_HELP = """
{0}

Shows information about the context currently loaded for responding, if any.
"""

CMD_SAVE_HELP = """
{0}

Saves all unsaved changes.
All commands to add/delete new contexts or pattern response pairs are temporary.
This command saves all changes made since the last save operation.
"""

CMD_DROP_HELP = """
{0}

Drops all changes made since the last save operation.
"""

CMD_TREE_HELP = """
{0} [context_name]

Shows a tree view of all subcontexts contained under [context_name]
"""

# Default location of .json file if none is provided
DEFAULT_JSON = os.path.join(os.path.expanduser('~'), 'bot-builder-database.json')

command_table = {}

class Command(object):
    def __init__(self, word, handler, helptext):
        self.word = word
        self.handler = handler
        self.helptext = helptext

    def format_helptext(self):
        return self.helptext.format(self.word)

def _split_args(text):
    ret = []
    arg = ""
    escape = False
    space = False
    in_paren = False
    parentype = None

    for c in text:
        if escape:
            arg += c
            escape = False

        elif c == '\\':
            escape = True
            if space:
                space = False
                ret.append(arg)
                arg = ""

        elif in_paren:
            if c == parentype:
                in_paren = False
                space = False
                if arg != "":
                    ret.append(arg)
                    arg = ""
            else:
                arg += c

        elif c in ['"', "'"]:
            in_paren = True
            space = False
            parentype = c
            if arg != "":
                ret.append(arg)
                arg = ""

        else:
            if c.isspace() and (not in_paren):
                space = True
            else:
                if space:
                    space = False
                    ret.append(arg)
                    arg = ""

                arg += c

    if arg != "":
        ret.append(arg)

    return ret

# Command handlers
def _on_new(cli, args):
    if len(args) < 1:
        return "Please provide a context name"

    ctx = cli.builder.add_context(args[0])
    if ctx is None:
        return "Failed to add new context '%s'" % args[0]

    return "Created new context %s" % ctx.name

def _on_entry(cli, args):
    if len(args) < 2:
        return "Please provide an entry pattern and repsonse"

    ret = cli.builder.add_entry(args[0], args[1])
    if ret is None:
        return "No context is loaded for editing."

    ctxname = cli.builder.editing_context.name
    return ("Added new entry pattern/response to %s:\n\npattern  : %s\n\nresponse : %s\n"
            % (ctxname, args[0], args[1]))

def _on_on(cli, args):
    if len(args) < 2:
        return "Please provide a pattern and a response"

    # Make sure a valid regex has been provided
    try:
        _ = re.compile(args[0])
    except Exception:
        return "Invalid regular expression"

    cli.builder.add_response(args[0], args[1])

    if cli.builder.editing_context is None:
        ctxname = "main context"
    else:
        ctxname = "context '%s'" % cli.builder.editing_context.name

    return ("Added new pattern/response to %s:\n\npattern  : %s\n\nresponse : %s\n"
            % (ctxname, args[0], args[1]))

def _on_forget(cli, args):
    if len(args) < 1:
        return "Please provide a pattern to delete"

    if cli.builder.editing_context:
        ctxname = cli.builder.editing_context.name
    else:
        ctxname = "(no context loaded, editing main context)"

    ret = cli.builder.delete_response(args[0])
    if ret is None:
        return "No pattern '%s' in current context %s." % (args[0], ctxname)

    return "Deleted '%s' from current context %s." % (args[0], ctxname)

def _on_load(cli, args):
    if len(args) < 1:
        return "Please provide name of context to load"

    ret = cli.builder.load_context(args[0])
    if ret is None:
        return "No context by the name of '%s'" % args[0]

    return "Context '%s' is loaded for editing" % args[0]

def _on_delete(cli, args):
    if len(args) < 1:
        return "Please provide name of context to delete"

    ret = cli.builder.delete_context(args[0])
    if ret is None:
        return "No context by the name of '%s'" % args[0]

    return "Context '%s' has been deleted" % args[0]

def _on_unload(cli, args):
    if cli.builder.editing_context is None:
        return "No context is loaded for editing"

    name = cli.builder.editing_context.name
    cli.builder.unload_context()
    return "Unloaded context '%s'" % name

def _on_loaded(cli, args):
    return cli.builder.editing_desc()

def _on_responding(cli, args):
    return cli.builder.responding_desc()

def _on_save(cli, args):
    if not cli.file_access_allowed():
        return "Too much file access, please wait a bit and try again"

    cli.save()
    return "All changes saved"

def _on_drop(cli, args):
    if not cli.file_access_allowed():
        return "Too much file access, please wait a bit and try again"

    cli.load()
    return "All unsaved changes dropped"

def _on_tree(cli, args):
    if len(args) < 1:
        return "Please provide name of context to get tree for"

    ret = cli.builder.context_tree(args[0])
    if ret is None:
        return "No context by the name of %s" % args[0]

    return ret

def _on_help(cli, args):
    if len(args) < 1:
        ret = ("Please provide the name of a command name to get help with. "
                "Here are all possible command names:\n\n")
        ret += "\n".join(["  %s" % n for n in list(command_table.keys())])
        return ret

    if args[0] not in command_table:
        return "Unrecognised command '%s'" % args[0]

    return command_table[args[0]].format_helptext()

def _on_setvar(cli, args):
    if len(args) < 2:
        return "Please provide a token name and token value"

    if cli.builder.editing_context is None:
        v = cli.builder.variables
    else:
        v = cli.builder.editing_context.variables

    v[args[0]] = args[1]
    return "value '%s' assigned to format token '%s'" % (args[1], args[0])

def _on_getvar(cli, args):
    if len(args) < 1:
        return "Please provide a token name"

    if cli.builder.editing_context is None:
        v = cli.builder.variables
    else:
        v = cli.builder.editing_context.variables

    if args[0] not in v:
        return "No format token named '%s' in context currently loaded for editing" % args[0]

    return v[args[0]]

# Dictionary mapping command words to command handlers
command_table.update({
    CMD_HELP:        Command(CMD_HELP, _on_help, CMD_HELP_HELP),
    CMD_NEW:         Command(CMD_NEW, _on_new, CMD_NEW_HELP),
    CMD_ENTRY:       Command(CMD_ENTRY, _on_entry, CMD_ENTRY_HELP),
    CMD_ON:          Command(CMD_ON, _on_on, CMD_ON_HELP),
    CMD_FORGET:      Command(CMD_FORGET, _on_forget, CMD_FORGET_HELP),
    CMD_LOAD:        Command(CMD_LOAD, _on_load, CMD_LOAD_HELP),
    CMD_UNLOAD:      Command(CMD_UNLOAD, _on_unload, CMD_UNLOAD_HELP),
    CMD_LOADED:      Command(CMD_LOADED, _on_loaded, CMD_LOADED_HELP),
    CMD_DELETE:      Command(CMD_DELETE, _on_delete, CMD_DELETE_HELP),
    CMD_RESPONDING:  Command(CMD_RESPONDING, _on_responding, CMD_RESPONDING_HELP),
    CMD_SAVE:        Command(CMD_SAVE, _on_save, CMD_SAVE_HELP),
    CMD_DROP:        Command(CMD_DROP, _on_drop, CMD_DROP_HELP),
    CMD_TREE:        Command(CMD_TREE, _on_tree, CMD_TREE_HELP),
    CMD_SETVAR:      Command(CMD_SETVAR, _on_setvar, CMD_SETVAR_HELP),
    CMD_GETVAR:      Command(CMD_GETVAR, _on_getvar, CMD_GETVAR_HELP)
})

class BotBuilderCLI(object):
    """
    Creates a BotBuilder instance, and provides an API for processing input text
    to get a response.
    """
    def __init__(self, json_filename=DEFAULT_JSON):
        self.json_filename = json_filename
        self.builder = BotBuilder()
        self.command = None
        self.last_file_access_time = 0

        if os.path.isfile(json_filename):
            self.load(json_filename)

        # Reset file access time so save/load works immediately
        self.last_file_access_time = 0

    def message_response_extra_format_tokens(self, msg, resp):
        return {}

    def format_command_response(self, msg, resp):
        return resp

    def load(self, filename=None):
        """
        Load a saved state from .json file
        """
        if filename is None:
            filename = self.json_filename

        if filename is None:
            attrs = {}
        else:
            if os.path.isfile(filename):
                with open(filename, 'r') as fh:
                    attrs = json.load(fh)
            else:
                attrs = {}

        self.last_file_access_time = time.time()
        self.builder.from_json(attrs)

    def save(self, filename=None):
        """
        Save current state to .json file
        """
        if filename is None:
            filename = self.json_filename

        with open(filename, 'w') as fh:
            json.dump(self.builder.to_json(), fh, indent=4)

        self.last_file_access_time = time.time()

    def file_access_allowed(self):
        """
        Returns true if the last file access was at least const.FILE_ACCESS_DELAY_SECS
        in the past.
        """
        delta = time.time() - self.last_file_access_time
        return delta >= const.FILE_ACCESS_DELAY_SECS

    def process_command(self, text):
        """
        Process an input string containing a command (a string that starts with
        const.COMMAND_TOKEN), and return the response
        """
        fields = text.split()
        cmd = fields[0].lstrip(const.COMMAND_TOKEN).strip().lower()
        args = ' '.join(fields[1:])

        if cmd not in command_table:
            return 'Unrecognised command "%s"' % cmd

        self.command = command_table[cmd]
        return self.command.handler(self, _split_args(args))

    def get_var_assignments_from_response(self, resp, fmtargs):
        fields = resp.split(const.VAR_ASSIGNMENT_SEP)
        if len(fields) < 2:
            return resp

        text, ass = const.VAR_ASSIGNMENT_SEP.join(fields[:-1]), fields[-1]

        try:
            ass = ass.format(**fmtargs)
        except KeyError:
            return "Invalid format token in variable assignment"

        # Do variable assignments
        assdict = {}
        fields = ass.split(',')
        for f in fields:
            names = f.split('=')
            if len(names) != 2:
                return resp

            self.builder.add_variable(names[0].strip(), names[1].strip())

        return text

    def get_response_and_format(self, msg):
        resp, groups = self.builder.get_response(self.get_message_content(msg))

        if resp is None:
            return None

        # Build format args for match groups
        if groups is None:
            fmtargs = {}
        else:
            fmtargs = {"p%d" % i: groups[i] for i in range(len(groups))}

        resp = self.get_var_assignments_from_response(resp, fmtargs)

        # Get variables for current context
        if self.builder.editing_context is None:
            variables = self.builder.variables
        else:
            variables = self.builder.editing_context.variables

        # Add variables to format args
        fmtargs.update(variables)

        # Add user defined format args
        fmtargs.update(self.message_response_extra_format_tokens(msg, resp))

        # Do the formatting
        try:
            fmtd = resp.format(**fmtargs)
        except (KeyError, IndexError):
            if self.builder.editing_context is None:
                ctxname = "main context"
            else:
                ctxname = "context %s" % self.builder.editing_context.name

            ret = "Invalid format token in response (%s):\n\n  %s" % (ctxname, resp)
            return self.format_command_response(msg, ret)

        return fmtd

    def process_message(self, message):
        """
        Process an input string (either a command or some conversational text),
        and return the response
        """
        try:
            text = self.get_message_content(message).strip()

            if text == '':
                return None

            if text.startswith(const.COMMAND_TOKEN):
                return self.format_command_response(message, self.process_command(text))
            else:
                return self.get_response_and_format(message)
        except Exception as e:
            return "Uh, Something bad happened.\n\n" + traceback.format_exc()

    def get_message_content(self, message):
        return message

def main():
    """
    Example main for testing, uses stdin for input
    """
    builder_cli = BotBuilderCLI()

    while True:
        text = input(" > ")
        resp = builder_cli.process_message(text)

        if resp is not None:
            print("\n%s\n" % resp.strip())

if __name__ == "__main__":
    main()
