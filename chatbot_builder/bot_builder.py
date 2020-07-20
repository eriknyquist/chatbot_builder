import random

from chatbot_utils.redict import ReDict

CONTEXT_NAME_SEP = '::'

NAME_KEY = "name"
ENTRY_KEY = "entry"
RESP_KEY = "responses"
VARS_KEY = "variables"
DEFAULT_RESP_KEY = "default_responses"
CTX_KEY = "contexts"

def _check_get_response(responsedict, text):
    try:
        response = responsedict[text]
    except KeyError:
        return None, None

    return response, responsedict.groups()

def _attempt_context_entry(contexts, text):
    for name in contexts:
        context = contexts[name]
        response, groups = _check_get_response(context.entry, text)
        if response is not None:
            return context, response, groups

    return None, None, None

class BotContext(object):
    def __init__(self, name):
        self.entry = ReDict()
        self.responses = ReDict()
        self.contexts = {}
        self.variables = {}
        self.name = name

    def add_entry_phrase(self, pattern, response):
        self.entry[pattern] = response

    def add_context(self, context_name, context, overwrite=False):
        if (not overwrite) and (context_name in self.contexts):
            return None

        self.contexts[context_name] = context
        return context

    def add_variable(self, name, value):
        self.variables[name] = value

    def add_response(self, pattern, response):
        self.responses[pattern] = response

    def delete_response(self, pattern):
        del self.responses[pattern]

    def get_response(self, text):
        return _check_get_response(self.responses, text)

    def __str__(self):
        ret = ""

        e = self.entry.dump_to_dict()
        if e:
            ret += "\nEntry phrases:\n\n"
            for n in e:
                ret += '  pattern  : "%s"\n' % n
                ret += '  response : "%s"\n\n' % e[n]

        d = self.responses.dump_to_dict()
        if d:
            ret += "Pattern/response pairs:\n\n"
            for n in d:
                ret += '  pattern  : "%s"\n' % n
                ret += '  response : "%s"\n\n' % d[n]

        if self.contexts:
            ret += "\nSubcontexts:\n\n"
            for n in self.contexts:
                ret += "%s\n" % self.contexts[n].name

        if self.variables:
            ret += "\nVariables:\n\n"
            for n in self.variables:
                ret += "%s=\"%s\"\n" % (n, self.variables[n])

        return ret

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        ret = {}
        ret[NAME_KEY] = self.name
        ret[ENTRY_KEY] = self.entry.dump_to_dict()
        ret[RESP_KEY] = self.responses.dump_to_dict()
        ret[CTX_KEY] = {n: self.contexts[n].to_json() for n in self.contexts}

        if self.variables:
            ret[VARS_KEY] = {n: self.variables[n] for n in self.variables}

        return ret

    def from_json(self, attrs):
        self.name = attrs[NAME_KEY]
        self.entry.load_from_dict(attrs[ENTRY_KEY])
        self.responses.load_from_dict(attrs[RESP_KEY])

        if VARS_KEY in attrs:
            self.variables = {n: attrs[VARS_KEY][n] for n in attrs[VARS_KEY]}

        self.contexts.clear()
        for n in attrs[CTX_KEY]:
            c = BotContext(n)
            c.from_json(attrs[CTX_KEY][n])
            self.add_context(n, c)

        return self

class BotBuilder(object):
    def __init__(self):
        self.responses = ReDict()
        self.contexts = {}
        self.default_responses = ["I don't know what that means"]
        self.editing_context = None
        self.responding_context = None
        self.variables = {}

    def to_json(self):
        ret = {}
        ret[DEFAULT_RESP_KEY] = self.default_responses
        ret[RESP_KEY] = self.responses.dump_to_dict()
        ret[CTX_KEY] = {n: self.contexts[n].to_json() for n in self.contexts}

        if self.variables:
            ret[VARS_KEY] = {n: self.variables[n] for n in self.variables}

        return ret

    def from_json(self, attrs):
        self.default_responses = []
        self.responses = ReDict()
        self.contexts = {}

        if attrs:
            self.default_responses = attrs[DEFAULT_RESP_KEY]
            self.responses.load_from_dict(attrs[RESP_KEY])

            for name in attrs[CTX_KEY]:
                c = BotContext("").from_json(attrs[CTX_KEY][name])
                self.contexts[name] = c

        if VARS_KEY in attrs:
            self.variables = {n: attrs[VARS_KEY][n] for n in attrs[VARS_KEY]}

        if self.editing_context:
            self.editing_context = self._context_by_name(self.editing_context.name)

        if self.responding_context:
            self.responding_context = self._context_by_name(self.responding_context.name)

        return self

    def _context_desc(self, context_msg, main_msg, ctx):
        if ctx is not None:
            ret = ("%s '%s'\n%s"
                   % (context_msg, ctx.name, str(ctx)))
        else:
            ret = "%s\n\n" % main_msg
            d = self.responses.dump_to_dict()
            if d:
                ret += "pattern/response pairs:\n\n"
                for n in d:
                    ret += 'pattern  : "%s"\n' % n
                    ret += 'response : "%s"\n\n' % d[n]

            if self.contexts:
                ret += "contexts:\n\n"
                for n in self.contexts:
                    ret += "%s\n" % n

            if self.variables:
                ret += "\nVariables:\n\n"
                for n in self.variables:
                    ret += "%s=\"%s\"\n" % (n, self.variables[n])

        return ret

    def editing_desc(self):
        return self._context_desc("Editing context",
                                  "No context loaded for editing. Editing main context",
                                  self.editing_context)

    def responding_desc(self):
        return self._context_desc("Responding with context",
                                  "No context loaded for responses. Using main context",
                                  self.responding_context)

    def add_default_response(self, text):
        self.default_responses.append(text)

    def add_variable(self, name, value):
        if self.editing_context is None:
            self.variables[name] = value
        else:
            self.editing_context.add_variable(name, value)

    def add_context(self, context_name, overwrite=False):

        if self.editing_context is None:
            full_name = context_name
        else:
            full_name = CONTEXT_NAME_SEP.join([self.editing_context.name, context_name])

        c = BotContext(full_name)

        if self.editing_context is None:
            if (not overwrite) and (context_name in self.contexts):
                return None

            self.contexts[context_name] = c
            self.editing_context = c
            return c

        ret = self.editing_context.add_context(context_name, c, overwrite)
        if ret is None:
            return None

        self.editing_context = c
        return c

    def add_entry(self, pattern, response):
        if self.editing_context is None:
            return None

        self.editing_context.add_entry_phrase(pattern, response)
        return self.editing_context

    def add_response(self, pattern, response):
        if self.editing_context is None:
            self.responses[pattern] = response
        else:
            self.editing_context.add_response(pattern, response)

    def delete_response(self, pattern):
        try:
            if self.editing_context is None:
                del self.responses[pattern]
            else:
                self.editing_context.delete_response(pattern)
        except KeyError:
            return None

        return self

    def _context_by_name(self, context_name):
        fields = context_name.split(CONTEXT_NAME_SEP)
        curr = self

        if context_name.strip() == '':
            return None

        for field in fields:
            name = field.strip()
            if name == '':
                return None

            try:
                curr = curr.contexts[name]
            except KeyError:
                return None

        return curr

    def context_tree(self, context_name):
        ctx = self._context_by_name(context_name)
        if ctx is None:
            return None

        ret = ""
        stack = [("", ctx)]

        while stack:
            header, ctx, = stack.pop(0)

            ret += "%s%s\n" % (header, ctx.name)

            if ctx.contexts:
                header = "  " + header
                names = list(ctx.contexts.keys())
                for i in range(len(names)):
                    stack.insert(0, (header, ctx.contexts[names[i]]))

        return ret

    def load_context(self, context_name):
        self.editing_context = self._context_by_name(context_name)
        return self.editing_context

    def delete_context(self, context_name):
        fields = context_name.split(CONTEXT_NAME_SEP)
        curr = self
        name = ""

        if context_name.strip() == '':
            return None

        for field in fields[:-1]:
            name = field.strip()
            if name == '':
                return None

            try:
                curr = curr.contexts[name]
            except KeyError:
                return False

        ctxname = fields[-1].strip()

        if self.editing_context is curr.contexts[ctxname]:
            self.editing_context = None

        if self.responding_context is curr.contexts[ctxname]:
            self.repsonding_context = None

        try:
            del curr.contexts[ctxname]
        except KeyError:
            return False

        return True

    def unload_context(self):
        self.editing_context = None

    def get_response(self, text):
        response = None
        groups = None

        # If currently in a context, try to get a response from the context
        if self.responding_context:
            response, groups = self.responding_context.get_response(text)
            if response is None:
                # Try entering subcontexts contained in current context, if any
                context, response, groups = _attempt_context_entry(
                    self.responding_context.contexts, text)

                if context is not None:
                    self.responding_context = context

        # If no contextual response is available, try to get a response from
        # the dict of contextless responses
        if response is None:
            response, groups = _check_get_response(self.responses, text)
            if response is not None:
                # If we are currently in a context but only able to get a
                # matching response from the contextless dict, set the current
                # context to None
                if self.responding_context:
                    self.responding_context = None
            else:
                # No contextless responses available, attempt context entry
                context, response, groups = _attempt_context_entry(
                    self.contexts, text)

                if context is not None:
                    self.responding_context = context
                else:
                    #response = random.choice(self.default_responses)
                    response = None
                    groups = None

        return response, groups
