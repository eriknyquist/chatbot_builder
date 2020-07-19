import os

from chatbot_builder.bot_builder_cli import BotBuilderCLI
from chatbot_builder.clients.discord_bot import DiscordBot, MessageResponse
from chatbot_builder import constants as const

MSG_AUTHOR_MENTION_FMT_TOKEN = "author_mention"
MSG_AUTHOR_FMT_TOKEN = "author"


class DiscordBotBuilderCLI(BotBuilderCLI):
    def format_command_response(self, msg, resp):
        return "```\n%s```" % resp

    def message_response_extra_format_tokens(self, msg, resp):
        return {
            MSG_AUTHOR_MENTION_FMT_TOKEN: msg.author.mention,
            MSG_AUTHOR_FMT_TOKEN: msg.author.name
        }

    def get_message_content(self, msg):
        return msg.content

class DiscordBotBuilderClient(DiscordBot):
    def __init__(self, *args, **kwargs):
        super(DiscordBotBuilderClient, self).__init__(*args, **kwargs)
        self.clis = {}

        self.json_dir = os.path.join(os.path.expanduser(const.JSON_DIR))
        if not os.path.isdir(self.json_dir):
            os.mkdir(self.json_dir)

    def _get_message_guild_id(self, message):
        name = "default"
        ident = 0

        if message.guild is None:
            # Message is a DM
            if hasattr(message.author, 'guild'):
                # DM from a user within a guild
                name = message.author.guild.name
                ident = message.author.build.id
            else:
                # DM from a user outside of a guild
                name = message.author.name
                ident = message.author.id
        else:
            # Message is in a group channel in some guild
            name = message.guild.name
            ident = message.guild.id

        return "%s_%s" % (name, ident)

    def on_member_join(self, member):
        return MessageResponse('Welcome, %s!' % member.name, member=member)

    def on_connect(self):
        print('%s has connected to Discord!' % self.client.user)

    def on_message(self, message):
        if message.author == self.client.user:
            return

        guild_id = self._get_message_guild_id(message)
        if guild_id not in self.clis:
            filename = os.path.join(self.json_dir, "%s.json" % guild_id)
            self.clis[guild_id] = DiscordBotBuilderCLI(json_filename=filename)

        resp = self.clis[guild_id].process_message(message)
        if resp is None:
            return None

        return MessageResponse(resp, channel=message.channel)

def main():
    if const.DISCORD_SERVER_ENV_VAR not in os.environ:
        raise RuntimeError("Environment variable '{0}' Is not set. Set '{0}' to the "
                           "name of the guild/server you want the bot to connect "
                           "with.".format(const.DISCORD_SERVER_ENV_VAR))

    if const.DISCORD_TOKEN_ENV_VAR not in os.environ:
        raise RuntimeError("Environment variable '{0}' Is not set. Set '{0}' to your "
                           "bot API token.".format(const.DISCORD_TOKEN_ENV_VAR))

    server = os.environ[const.DISCORD_SERVER_ENV_VAR]
    token = os.environ[const.DISCORD_TOKEN_ENV_VAR]

    b = DiscordBotBuilderClient(token, server)
    b.run()

if __name__ == "__main__":
    main()
