import os
import json

from responder import BotBuilder

COMMAND_TOKEN = '%'

# command words
CMD_NEW = "new"
CMD_ON = "on"
CMD_LOAD = "load"
CMD_UNLOAD = "unload"
CMD_LOADED = "loaded"
CMD_RESPONDING = "responding"
CMD_SAVE = "save"
CMD_DROP = "drop"

DEFAULT_JSON = os.path.join(os.path.expanduser('~'), 'bot-builder-database.json')

def _split_args(text):
    ret = []
    arg = ""
    escape = False
    space = False
    in_paren = False

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

        elif c in ['"', "'"]:
            in_paren = not in_paren
            space = False
            if arg != "":
                ret.append(arg)
                arg = ""

            continue

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

def _on_new(cli, args):
    if len(args) < 3:
        return "Please provide required arguments"

    ctx = cli.builder.add_context(args[0], args[1], args[2])
    if ctx is None:
        return "Failed to add new context '%s'" % args[0]

    return "Created new context %s" % ctx.name

def _on_on(cli, args):
    if len(args) < 2:
        return "Please provide required arguments"

    cli.builder.add_response(args[0], args[1])
    return "Added new pattern/response"

def _on_load(cli, args):
    if len(args) < 1:
        return "Please provide required arguments"

    ret = cli.builder.load_context(args[0])
    if ret is None:
        return "No context by the name of '%s'" % args[0]

    return "Context '%s' is loaded for editing" % args[0]

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
    cli.save()
    return "All changes saved"

def _on_drop(cli, args):
    cli.load()
    return "All unsaved changes dropped"

command_table = {
    CMD_NEW: _on_new,
    CMD_ON: _on_on,
    CMD_LOAD: _on_load,
    CMD_UNLOAD: _on_unload,
    CMD_LOADED: _on_loaded,
    CMD_RESPONDING: _on_responding,
    CMD_SAVE: _on_save,
    CMD_DROP: _on_drop
}

class BotBuilderCLI(object):
    def __init__(self, json_filename=DEFAULT_JSON):
        self.json_filename = json_filename
        self.builder = BotBuilder()

        if os.path.isfile(json_filename):
            self.load(json_filename)

    def load(self, filename=None):
        if filename is None:
            filename = self.json_filename

        if filename is None:
            attrs = {}
        else:
            with open(filename, 'r') as fh:
                 attrs = json.load(fh)

        self.builder.from_json(attrs)

    def save(self, filename=None):
        if filename is None:
            filename = self.json_filename

        with open(filename, 'w') as fh:
            json.dump(self.builder.to_json(), fh, indent=4)

    def process_command(self, text):
        fields = text.split()
        cmd = fields[0].lstrip(COMMAND_TOKEN).strip()
        args = ' '.join(fields[1:])

        if cmd not in command_table:
            return 'Unrecognised command "%s"' % cmd

        handler = command_table[cmd]
        return handler(self, _split_args(args))

    def process_message(self, text):
        message = text.strip()

        if message == '':
            return None

        if message.startswith(COMMAND_TOKEN):
            return self.process_command(message)
        else:
            return self.builder.get_response(text)

def main():
    builder_cli = BotBuilderCLI()

    while True:
        text = input(" > ")
        resp = builder_cli.process_message(text)

        if resp is not None:
            print("\n%s\n" % resp.strip())

if __name__ == "__main__":
    main()
