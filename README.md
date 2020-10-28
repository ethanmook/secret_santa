# Automated Secret Santa

This is a simple utility to assign secret santa pairings to a group of people
and send out emails to everyone so that they know their giftee but nothing else.

## Usage

In order to run the program with default settings and have it send emails you
will need:

- A csv file `players.csv` containing a list of players and their email addresses (and
  potentially other information)
- A text file `message.txt` containing the message that will form the body of the email
- A file `creds.txt` containing the credentials for the email account that will send out the
  emails in the form
  ```
  example@email.com
  password
  ```

Then simply run 
```
./secret_santa.py players.csv message.txt -c creds.txt
```

For more usage info simply run

```
./secret_santa.py -h
```

See the example files for more info.

## Features

### Automated emails with templated messages

The script will automatically send out emails to all players in the game
(presumably including yourself). It is recommended that you use a specialized
email account to send the emails so that you, as the game administrator, are not
tempted to look at who everyone buys for. However, you'll always be able to log
in to the account and see the log all the pairings in sent mail.

The message contained in the emails can be modified and can include templated
information about each recipient.

### Constrained derangement generation

Every player is guaranteed to not get their own name. Additionally, you can
categorize your players into groups and have a guarantee that no player will get
another person in the same group. This allows pairs of significant others or
families to play without having to buy gifts within the group.

The generation of the constrained derangements is currently done by brute force:
generating a derangement and then checking if it satisfies the group
conditions. If you happen to know a better way of doing this, I'd love to hear
about it.

## Limitations

You are currently required to store your email credentials in plain text (at
least for the duration of your use of the program). If I care enough I'll add
the capability to read credentials from stdin. The program only supports SMTP
and uses gmail by default. I added the ability to change the server, but I've
never tested it with other servers (I also don't really know much about how SMTP
works).
