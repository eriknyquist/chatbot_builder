from responder import BotBuilder

COMMAND_TOKEN = '%'

# command words
CMD_NEW = "new"
CMD_ON = "on"
CMD_LOAD = "load"
CMD_UNLOAD = "unload"
CMD_EDITING = "editing"
CMD_RESPONDING = "responding"

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

def _on_new(builder, args):
    if len(args) < 3:
        return "Please provide required arguments"

    ctx = builder.add_context(args[0], args[1], args[2])
    if ctx is None:
        return "Failed to add new context '%s'" % args[0]

    return "created new context %s" % ctx.name

def _on_on(builder, args):
    if len(args) < 2:
        return "Please provide required arguments"

    builder.add_response(args[0], args[1])
    return "Added new pattern/response"

def _on_load(builder, args):
    if len(args) < 1:
        return "Please provide required arguments"

    ret = builder.load_context(args[0])
    if ret is None:
        return "No context by the name of '%s'" % args[0]

    return "Context '%s' is loaded" % args[0]

def _on_unload(builder, args):
    if builder.editing_context is None:
        return "No context is loaded for editing"

    name = builder.editing_context.name
    builder.unload_context()
    return "Unloaded context '%s'" % name

def _on_editing(builder, args):
    return builder.editing_desc()

def _on_responding(builder, args):
    return builder.responding_desc()

command_table = {
    CMD_NEW: _on_new,
    CMD_ON: _on_on,
    CMD_LOAD: _on_load,
    CMD_UNLOAD: _on_unload,
    CMD_EDITING: _on_editing,
    CMD_RESPONDING: _on_responding
}

class BotBuilderCLI(object):
    def __init__(self):
        self.builder = BotBuilder()

    def process_command(self, text):
        fields = text.split()
        cmd = fields[0].lstrip(COMMAND_TOKEN).strip()
        args = ' '.join(fields[1:])

        if cmd not in command_table:
            return 'Unrecognised command "%s"' % cmd

        handler = command_table[cmd]
        return handler(self.builder, _split_args(args))

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
