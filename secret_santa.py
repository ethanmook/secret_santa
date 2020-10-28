#!/usr/bin/python

import random
import sys
import argparse
import pandas

import smtplib
from email.message import EmailMessage


def gen_derangement(n):
    '''The code for generating a derangement 
    (a permutation such that der[i] != i)'''
    perm = list(range(n))
    random.shuffle(perm)
    der = [-1] * n
    for i in range(n):
        der[perm[i]] = perm[(i + 1) % n]
    return der


def gen_constrained_derangement(df, group):
    '''Generates a derangement with the additional constraint that no one gets a
    person in their group (someone with the same value in column
    group). Currently just tries by brute force.'''
    der = []
    fail = True
    while fail:
        fail = False
        der = gen_derangement(len(df))
        for i, j in enumerate(der):
            player = df.iloc[i]
            recipient = df.iloc[j]
            if player['group'] == recipient['group']:
                fail = True
                continue
    return der


def build_msg(uname, player, recipient, subject, body):
    '''Construct the message to be sent to a given person. recipient is a row of the
    dataframe containing contact info for the recipient'''
    msg = EmailMessage()
    recipient = recipient.map(lambda x: x.replace('||', '\n')
                              if isinstance(x, str) else x)
    msg.set_content(body.format(**recipient))
    msg['Subject'] = subject
    msg['From'] = uname
    msg['To'] = player['email']
    return msg


def print_emails(uname, df, subject, body):
    '''Print emails without sending'''
    for _, player in df.iterrows():
        recipient = df.iloc[player['recipient']]
        msg = build_msg(uname, player, recipient, subject, body)
        print(msg)
        print('-----------------------')


def send_emails(uname, pwd, server, df, subject, body):
    '''Send emails by logging in with uname and pwd'''
    conf = input('Confirm sending emails [y/n]: ')
    if conf[0].lower() != 'y':
        print('Aborting')
        return
    s = smtplib.SMTP(server, 587)
    s.starttls()
    s.login(uname, pwd)
    for _, player in df.iterrows():
        recipient = df.iloc[player['recipient']]
        msg = build_msg(uname, player, recipient, subject, body)
        s.send_message(msg)
    s.quit()


def first_line_rest(path):
    f = open(path)
    first_line = f.readline().strip()
    rest = f.read().strip()
    f.close()
    return first_line, rest


def print_constrained_derangement(df, group, name, der):
    '''Print the constrained derangement. For debugging purposes only'''
    for index, player in df.iterrows():
        recipient = df.iloc[der[index]]
        print('({:2d}, {:>10.10}) in group {} got ({:2d}, {:>10.10}) in group {}'.format(
            index, player[name], player[group],
            der[index], recipient[name], recipient[group]
        ))
        assert(player[group] != recipient[group])


def main():
    parser = argparse.ArgumentParser(description='Secret Santa Helper')
    parser.add_argument('players',
                        help='CSV file with player names and emails')
    parser.add_argument('message',
                        help='Text file with message to send: subject<\\n>message')
    parser.add_argument('-c', '--credfile',
                        dest='credfile',
                        help='File with gmail creds email pwd on separate lines. If not present no emails are sent')
    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_true',
                        help='Print emails to stdout')
    parser.add_argument('-s', '--server',
                        dest='server',
                        default='smtp.gmail.com',
                        help='SMTP server domain. Default: smtp.gmail.com *not been tested with other servers*')
    parser.add_argument('-g', '--group',
                        dest='group',
                        help='Generate the derangement with constraint that no one gets a person with the same value in column "GROUP""')
    parser.add_argument('-t', '--no-derangement',
                        dest='test',
                        action='store_true',
                        help='Test mode: skip derangement (i.e. everyone gets themselves)')
    args = parser.parse_args()
    subject, body = first_line_rest(args.message)
    df = pandas.read_csv(args.players)
    der = df.index.tolist()
    if not args.test:
        if args.group is not None:
            der = gen_constrained_derangement(df, args.group)
            print_constrained_derangement(df, args.group, 'name', der)
        else:
            der = gen_derangement(len(df))
    df['recipient'] = der
    
    uname, pwd = '', ''
    if args.credfile is not None:
        uname, pwd = first_line_rest(args.credfile)
        send_emails(uname, pwd, args.server, df, subject, body)

    if args.verbose:
        print_emails(uname, df, subject, body)


if __name__ == '__main__':
    main()
