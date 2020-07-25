Chatbot Builder: a discord chatbot
----------------------------------

A discord bot that is programmed through commands sent in discord messages by
discord users. You can invite this bot to a server and teach it to say whatever you like!

The bot will see all messages in all channels within the server you invite it to.
Any message starting with '%' is assumed to be a command. If a message does not
start with '%', the bot will assume it is conversational text and will respond,
if has any appropriate responses programmed.

Run the '%help' command to get started with available commands to program the bot.

Install
-------

Install with pip:

::

  python3 -m pip install chatbot_builder

Usage
-----

#. Set the environment variable ``DISCORD_BOTBUILDER_TOKEN`` to the API token for your
   discord bot application.

#. Run the discord client:

   ::

     python3 -m chatbot_builder.clients.discord_client

#. The bot should now be online in any servers that you have invited it to
