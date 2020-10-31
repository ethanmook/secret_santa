#!/usr/bin/python

import random
import sys
import argparse
import pandas
import re

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


def satisfies_rule(df, der, col1, val1, col2, val2, gets):
    '''The rule constructed from reading the line'''
    for idx, row in df.loc[df[col1] == val1].iterrows():
        recipient = df.iloc[der[idx]]
        if (df.iloc[der[idx]][col2] == val2) != gets:
            return False
    return True


def is_valid_constrained_derangement(df, der, group, rules):
    '''Checks if a given derangement satisfies the constraints'''
    if group is not None:
        for i, j in enumerate(der):
            player = df.iloc[i]
            recipient = df.iloc[j]
            if player[group] == recipient[group]:
                return False

    for rule in rules:
        if not satisfies_rule(df, der, *rule):
            return False

    return True


def gen_constrained_derangement(df, group, rules):
    '''Generates a derangement with the additional constraints that no one gets a
    person in their group (someone with the same value in column group) and the
    rules are satisfied. Currently just tries by brute force.'''
    der = gen_derangement(len(df))
    while not is_valid_constrained_derangement(df, der, group, rules):
        der = gen_derangement(len(df))

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


def parse_first_rest(path):
    '''Reads a file and returns the first line and rest of file as separate strings'''
    with open(path, 'r') as f:
        first_line = f.readline().strip()
        rest = f.read().strip()
        return first_line, rest


def parse_rules_file(path):
    '''Parse path as a rulesfile to build a list of tokens to be checked by check_rule'''
    with open(path, 'r') as f:
        rules = []
        for line in f:
           line = line.strip()
           if not line or line[0] == '#':
               continue
           tokens = re.split(r'(?:\s|:)(?=(?:[^"]*"[^"]*")*[^"]*$)', line)
           col1, val1, mode, col2, val2 = tokens
           val1 = val1.replace('"', '')
           val2 = val2.replace('"', '')
           gets = mode == 'gets'

           rules.append((col1, val1, col2, val2, gets))
        return rules
           

def print_derangement(df, printcol, der):
    '''Print the derangement, printing the value of printcol for each player.'''
    for index, player in df.iterrows():
        recipient = df.iloc[der[index]]
        print('({:2d}, {:>10.10}) -> ({:2d}, {:>10.10})'.format(
            index, player[printcol], 
            der[index], recipient[printcol],
        ))


def main():
    parser = argparse.ArgumentParser(description='Secret Santa Helper')
    parser.add_argument('players',
                        help='CSV file with player names and emails')
    parser.add_argument('message',
                        help='Text file with message to send: subject<\\n>message')
    parser.add_argument('-c', '--credfile',
                        dest='credfile',
                        help='File with gmail creds email pwd on separate lines. '\
                        'If not present no emails are sent')
    parser.add_argument('-v', '--verbose',
                        dest='verbose',
                        action='store_true',
                        help='Print emails to stdout')
    parser.add_argument('-s', '--server',
                        dest='server',
                        default='smtp.gmail.com',
                        help='SMTP server domain. Default: smtp.gmail.com '\
                        '*not been tested with other servers*')
    parser.add_argument('-g', '--group',
                        dest='group',
                        help='Generate the derangement with constraint that '\
                        'no one gets a person with the same value in column "GROUP""')
    parser.add_argument('-t', '--no-derangement',
                        dest='test',
                        action='store_true',
                        help='Test mode: skip derangement (i.e. everyone gets themselves)')
    parser.add_argument('-r', '--rulesfile',
                        dest='rulesfile',
                        help='File with additional rules (see example for details)')
    parser.add_argument('-p', '--print',
                        dest='printcol',
                        help='Print the resulting derangement, printing PRINTCOL'\
                        ' as an identifier for each player')
    args = parser.parse_args()
    subject, body = parse_first_rest(args.message)
    df = pandas.read_csv(args.players, dtype=object)
    der = df.index.tolist()

    rules = parse_rules_file(args.rulesfile) if args.rulesfile is not None else []
    if not args.test:
        if args.group is not None or args.rulesfile is not None:
            der = gen_constrained_derangement(df, args.group, rules)
        else:
            der = gen_derangement(len(df))
    if args.printcol is not None:
        print_derangement(df, args.printcol, der)

    df['recipient'] = der
    
    uname, pwd = '', ''
    if args.credfile is not None:
        uname, pwd = parse_first_rest(args.credfile)
        send_emails(uname, pwd, args.server, df, subject, body)

    if args.verbose:
        print_emails(uname, df, subject, body)


if __name__ == '__main__':
    main()
