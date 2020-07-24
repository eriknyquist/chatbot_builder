DISCORD_SERVER_ENV_VAR = "DISCORD_BOTBUILDER_SERVER"
DISCORD_TOKEN_ENV_VAR = "DISCORD_BOTBUILDER_TOKEN"

JSON_DIR = "~/.chatbot_builder"

# Input text starting with this will be considered a command
COMMAND_TOKEN = '%'

# Marks the start of variable assignments within a repsonse
VAR_ASSIGNMENT_SEP = ';;'

# Bot commands that access the .JSON file will not be allowed within
# this many seconds of each other, to help prevent the disk getting spammed
FILE_ACCESS_DELAY_SECS = 5.0
