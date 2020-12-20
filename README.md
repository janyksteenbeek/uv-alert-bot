A Telegram bot to bridge UniFi Video e-mail alerts with Telegram messages in a single group.
When motion is detected, you will receive a message in the configured group with the snapshot and snapshot timestamp. It will also send the subject of non-motion alert emails, e.g: camera disconnect/reconnect

 
## Setting up as Docker container 

1) Build the container by running `docker build .` 

2) docker run -v /path/to/config_dir/:/config --net=host

## Setting up the bot

 1) Create a bot via [BotFather](https://core.telegram.org/bots#6-botfather) and grab the token 
 2) Create a group and add your newly created bot to it
 3) Create a config based on the [config.yaml.example](config/config.yaml.example) using the token and adjust for your system/users
 4) Run `/start` and `/enable` in the group  

## Setting up UniFi Video

Visit your UniFi Video settings and follow the following steps:
  1) Enable e-mail alerts in your UniFi Video environment
  2) Use the following settings:
     - SMTP server: `127.0.0.1` (or the port you specified in the config.yaml) 
     - Port: `8025` (or the port you specified in the config.yaml)
  3) Save changes
  
## Commands
The bot supports 3 commands:

 * /start: tell the bot to send messages to the group where the command is issued, ATM only a single group is supported.
 * /status: show status (active/inactive)
 * /e, /enable: enable notifications
 * /de, /disable: disable notifications, the will receive the email alerts but not forward them to telegram

 in/active state is persistent, and will be maintained across restarts
