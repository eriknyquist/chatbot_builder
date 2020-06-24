from discord_bot import DiscordBot, MessageResponse

SERVER = 'lawds'
TOKEN = 'NzI0ODI0ODQ1MTI0MzcwNDYy.XvF0DQ.dTT3ny0LVlgA-8BwYYqG2xIfMmI'

class MyBot(DiscordBot):
    def __init__(self, *args, **kwargs):
        super(MyBot, self).__init__(*args, **kwargs)

    def on_member_join(self, member):
        return MessageResponse('Welcome, %s!' % member.name, member=member)

    def on_connect(self):
        print('%s has connected to Discord!' % self.client.user)

    def on_message(self, message):
        if message.author == self.client.user:
            return

        if hasattr(message.channel, 'name'):
            channelid = message.channel.name
        else:
            channelid = message.channel.recipient.name

        print(channelid, message.author, message.content)
        return MessageResponse('YES', channel=message.channel)

b = MyBot(TOKEN, SERVER)
b.run()
