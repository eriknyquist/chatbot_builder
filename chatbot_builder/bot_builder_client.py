import os
from chatbot_builder.bot_builder_cli import BotBuilderCLI
from chatbot_builder.discord_bot import DiscordBot, MessageResponse

SERVER_ENV_VAR = "DISCORD_BOTBUILDER_SERVER"
TOKEN_ENV_VAR = "DISCORD_BOTBUILDER_TOKEN"

class DiscordBotBuilderClient(DiscordBot):
    def __init__(self, *args, **kwargs):
        super(DiscordBotBuilderClient, self).__init__(*args, **kwargs)
        self.cli = BotBuilderCLI()

    def on_member_join(self, member):
        return MessageResponse('Welcome, %s!' % member.name, member=member)

    def on_connect(self):
        print('%s has connected to Discord!' % self.client.user)

    def on_message(self, message):
        if message.author == self.client.user:
            return

        resp = self.cli.process_message(message.content)
        if resp is None:
            return None

        return MessageResponse(resp, channel=message.channel)

def main():
    if SERVER_ENV_VAR not in os.environ:
        raise RuntimeError("Environment variable '{0}' Is not set. Set '{0}' to the "
                           "name of the guild/server you want the bot to connect "
                           "with.".format(SERVER_ENV_VAR))

    if TOKEN_ENV_VAR not in os.environ:
        raise RuntimeError("Environment variable '{0}' Is not set. Set '{0}' to your "
                           "bot API token.".format(TOKEN_ENV_VAR))

    server = os.environ[SERVER_ENV_VAR]
    token = os.environ[TOKEN_ENV_VAR]

    b = DiscordBotBuilderClient(token, server)
    b.run()

if __name__ == "__main__":
    main()
