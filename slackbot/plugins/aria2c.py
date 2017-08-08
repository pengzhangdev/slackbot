#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# aria2c.py ---
#
# Filename: aria2c.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Sat Aug  5 10:22:20 2017 (+0800)
#

# Change Log:
#
#

from __future__ import division
from __future__ import absolute_import

import os
import sys
import re
import json
import base64
import urllib2, urllib
from urllib2 import URLError, HTTPError
from subprocess import check_call
from getopt import getopt
from io import open

MAX_NAME_LEN = 50
ELLIPSIS = '...'
HOST = 'localhost'
PORT = 6800
PREVIEW_COMMAND = 'open'
INFO_COMMAND = 'file'
JSON_RPC_URI = 'http://%s:%s/jsonrpc' % (HOST, PORT)

def abbrev(value):
    n = value / 1024.0
    if n < 1:
        return '%dB' % value
    value = n
    n = value / 1024.0
    if n < 1 :
        return '%.1fK' % value
    else:
        value = n
        n = value / 1024.0
        if n < 1 :
            return '%.1fM' % value
        else:
            return '%.1fG' % n

def arrival(download_speed, remaining_length):
    if (download_speed == 0):
        return 'n/a'

    s = remaining_length / download_speed
    h = s / 3600
    s = s % 3600
    m = s / 60
    s = s % 60
    result = ""
    if (h >= 1):
        result += '%dh' % h
    if (m >= 1):
        result += '%dm' % m
    result += "%ds" % s
    return result

def call_func(func, params=[]):
    jsonreq = json.dumps({'jsonrpc':'2.0', 'id':'foo',
                          'method':'aria2.%s' % func,
                          'params': params})
    try:
        c = urllib2.urlopen(JSON_RPC_URI, jsonreq)
    except IOError, err:
        code = -1
        if type(err) is URLError:
            code = err.reason.errno
        elif type(err) is HTTPError:
            code = err.code
        if code == 111:
            return {'result': 'The daemon is not running'}
        elif code == -1:
            return {'result': 'Encountered an error of type: %s.' % type(err)}
        else:
            return {'result': 'The server replied: %s.' % code}

    data = c.read()
    response = json.loads(data)
    return response

def get_active():
    return call_func('tellActive')

def get_waiting():
    return call_func('tellWaiting', [0, 666])

def get_stopped():
    return call_func('tellStopped', [0, 666])

def get_files(gids):
    output = ''
    for g in gids:
        response = call_func('getFiles', [g])
        if not response:
            print 'Failed on %s.' % g
        else:
            if len(gids) > 1:
                output += '%s: \n' % (g)
            files = response['result']
            for f in files:
                total_lenght = float(f['lenght'])
                completed_length = float(f['completedLength'])
                percent = 100

                if (total_length > 0):
                    percent = 100 * completed_length / total_length

                percent = '%.1f' % percent
                selected = f['selected']
                mark = '[ ]'

                if selected == 'true':
                    mark = 'X'

                output_line = '%s %2s %5s%% %s' % (mark, f['index'],
                                                   percent, f['path'])

                output += output_line + '\n'

    return output


def apply_func_on_gids(fn, gids):
    ouput = ''
    for g in gids:
        response = call_func(fn, [g])
        if not response:
            print 'Failed on %s.' % g
            ouput += response + '\0'

    return response

def pattern_match(index, pattern):
    for p in pattern:
        if len(p) > 1:
            first = int(p[0])
            second = int(p[1])
            if index >= first and index <= second:
                return True
        else:
            first = int(p[0])
            if index == first:
                return True
    return False


def command_by_gid(command, gids, options):
    select_file = []
    if 'select-file' in options:
        select_file = [re.split('-', x) for x in
                       re.split(',', options['select-file'])]

    output = ''
    for g in gids:
        response = call_func('getFiles', [g])
        if not response:
            print 'Failed on %s.\n' % g
        else:
            if len(gids) > 1:
                output += '%s: \n' % g
            files = response['result']
            for f in files:
                if len(select_file) > 0:
                    index = int(f['index'])
                    if not pattern_match(index, select_file):
                        continue
                completed_length = float(f['completedLength'])
                if completed_length > 0:
                    check_call([command, f['path']])

def info_by_gid(gids, options):
    return command_by_gid(INFO_COMMAND, gids, options)


def preview_by_gid(gids, options):
    return command_by_gid(PREVIEW_COMMAND, gids, options)


def pause_by_gid(gids):
    return apply_func_on_gids('pause', gids)


def resume_by_gid(gids):
    return apply_func_on_gids('unpause', gids)


def remove_by_gid(gids):
    return apply_func_on_gids('remove', gids)


def forcerm_by_gid(gids):
    return apply_func_on_gids('forceRemove', gids)


def clean():
    downloads = []
    active = get_active()
    if active:
        downloads.extend(active['result'])
    for d in downloads:
        if 'infoHash' in d:
            completed_length = int(d['completedLength'])
            total_length = int(d['totalLength'])
            if completed_length >= total_length:
                remove_by_gid([d['gid']])

def add_items(items, options={}):
    output = ''
    for item in items:
        response = None

        if item.find('://') != -1 or item.startswith('magnet:'):
            response = call_func('addUri', [[item], options])
        else:
            item_content = base64.b64encode(open(item, 'rb').read())
            item_content = item_content.decode('utf-8')
            if item.endswith('.torrent'):
                response = call_func('addTorrent', [item_content, [], options])
            elif item.endswith('.meta4') or item.endswith('.metalink'):
                response = call_func('addMetalink', [item_content, options])

        if not response:
            output += 'Failed on %s.\n' % item
        else:
            print response
            output += response['result'] + '\n'
    return output


def pause_all():
    return call_func('pauseAll')


def resume_all():
    return call_func('unpauseAll')


def list_downloads(kind):
    downloads = None
    output = ''

    if kind == 'active':
        downloads = get_active()
    elif kind == 'waiting':
        downloads = get_waiting()
    elif kind == 'stopped':
        downloads = get_stopped()

    if downloads:
        for r in downloads['result']:
            completed_length = float(r['completedLength'])
            total_length = float(r['totalLength'])
            remaining_length = total_length - completed_length
            download_speed = float(r['downloadSpeed'])
            eta = arrival(download_speed, remaining_length)
            percent = 100

            if (total_length > 0):
                percent = 100 * completed_length / total_length

            percent = '%.1f' % percent
            byte_download_speed = '%.1f' % (download_speed / 1024)
            byte_upload_speed = '%.1f' % (float(r['uploadSpeed']) / 1024)
            name = 'n/a'
            number_of_seeders = 'n/a'

            if 'numSeeders' in r:
                number_of_seeders = r['numSeeders']

            if 'bittorrent' in r:
                bt = r['bittorrent']
                if 'info' in bt:
                    name = bt['info']['name']
            else:
                if 'files' in r:
                    files = r['files']
                    for f in files:
                        if 'uris' in f:
                            uris = f['uris']
                            if len(uris) > 0:
                                name = uris[0]['uri']
                                break
                            else:
                                if 'path' in f:
                                    name = f['path']
                                    break

            if len(name) > MAX_NAME_LEN:
                name = name[:MAX_NAME_LEN - len(ELLIPSIS)] + ELLIPSIS

            strformat = '%3s %-50s %6s%% %6s %6s %5s %5s %s/%s %s'
            output_line = strformat % (r['gid'],
                                       name,
                                       percent,
                                       abbrev(completed_length),
                                       abbrev(total_length),
                                       byte_download_speed,
                                       byte_upload_speed,
                                       number_of_seeders,
                                       r['connections'],
                                       eta)

            output += output_line + '\n'

    return output

def show_errors():
    stopped = get_stopped()
    output = ''
    if stopped:
        for r in stopped['result']:
            if 'status' in r:
                status = r['status']
                if status == 'error':
                    gid = r['gid']
                    errorCode = r['errorCode']
                    error = EXIT_CODES[errorCode]
                    output +=  '%3s %s (error %s)\n' % (gid, error, errorCode)
    return output


def show_stats():
    gs = call_func('getGlobalStat')
    stats = gs['result']
    output = ''
    for key in sorted(stats.keys()):
        value = stats[key]
        output += '{}: '.format(key)
        if 'Speed' in key:
            output += '%s/s\n' % abbrev(float(value))
        else:
            output += value + '\n'

    return output


def usage():
    print '''
SYNOPSIS
    %s ACTION [ARGUMENTS]

ACTIONS
    list
        Output the list of active downloads.

    paused
        Output the list of paused downloads.

    stopped
        Output the list of stopped downloads.

    info [--select-file=...] GID ...
        Output informations regarding the given GIDs.

    files GID ...
        Output the files owned by the downloads corresponding to the given GIDs.

    errors
        Output the list of errors.

    stats
        Output download bandwidth statistics.

    add [--select-file=...] ITEM ...
        Download the given items (local or remote URLs to torrents, etc.).

    remove GID ...
        Remove the downloads corresponding to the given GIDs.

    forcerm GID ...
        Forcibly remove the downloads corresponding to the given GIDs.

    pause GID ...
        Pause the downloads corresponding to the given GIDs.

    resume GID ...
        Resume the downloads corresponding to the given GIDs.

    preview [--select-file=...] GID ...
        Preview all the files from all the downloads corresponding to the given GIDs.

    sleep
        Pause all the active downloads.

    wake
        Resume all the paused downloads.

    purge
        Clear the list of stopped downloads and errors.

    clean
        Stop seeding completed downloads.
    ''' % os.path.basename(sys.argv[0])
    sys.exit()


def main():
    optlist = ['help', 'pause', 'out=', 'header=', 'referer=',
               'user-agent=', 'dir=', 'select-file=', 'http-user=',
               'http-passwd=', 'username=', 'password=']
    opts, args = getopt(sys.argv[1:], 'hu:p:', optlist)

    options = {}
    username = None
    password = None

    for key, value in opts:
        if key in ('-h', '--help'):
            usage()
        elif key in ('-', '--username'):
            username = value
        elif key in ('-p', '--password'):
            password = value
        else:
            options.update({key.replace('--', ''): value})

    if username is not None and password is not None:
        pass_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pass_mgr.add_password(None, JSON_RPC_URI, username, password)
        auth_handler = urllib2.HTTPBasicAuthHandler(pass_mgr)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)

    if len(args) > 0:
        action = args[0]
        arguments = args[1:]

        if action in NO_ARGS_ACTIONS and len(arguments) > 0:
            print 'Action \'%s\' takes no arguments' % action
            sys.exit(1)
        elif action in ARGS_ACTIONS and len(arguments) < 1:
            print 'No arguments given for action \'%s\'' % action
            sys.exit(1)

        if action == 'add':
            print add_items(arguments, options)
        elif action == 'remove':
            print remove_by_gid(arguments)
        elif action == 'forcerm':
            print forcerm_by_gid(arguments)
        elif action == 'info':
            print info_by_gid(arguments, options)
        elif action == 'preview':
            print preview_by_gid(arguments, options)
        elif action == 'pause':
            print pause_by_gid(arguments)
        elif action == 'resume':
            print resume_by_gid(arguments)
        elif action == 'files':
            print get_files(arguments)
        elif action == 'list':
            print list_downloads('active')
        elif action == 'errors':
            print show_errors()
        elif action == 'stats':
            print show_stats()
        elif action == 'paused':
            print list_downloads('waiting')
        elif action == 'stopped':
            print list_downloads('stopped')
        elif action == 'sleep':
            print call_func('pauseAll')
        elif action == 'wake':
            print call_func('unpauseAll')
        elif action == 'purge':
            print call_func('purgeDownloadResult')
        elif action == 'clean':
            print clean()
        else:
            print 'Unknown action: %s' % action
            exit(1)
    else:
        usage()

NO_ARGS_ACTIONS = ('list', 'paused', 'stopped', 'errors', 'stats', 'sleep',
                   'wake', 'purge', 'clean')
ARGS_ACTIONS = ('add', 'remove', 'forcerm', 'preview', 'pause', 'resume',
                'files')

EXIT_CODES = {'1': 'unknown',
              '2': 'timeout',
              '3': 'resource not found',
              '4': 'resources not found',
              '5': 'download speed too slow',
              '6': 'network problem',
              '7': 'unfinished downloads',
              '8': 'resume not supported',
              '9': 'not enough disk space',
              '10': 'piece length differ',
              '11': 'was downloading the same file',
              '12': 'was downloading the same info hash',
              '13': 'file already existed',
              '14': 'renaming failed',
              '15': 'could not open existing file',
              '16': 'could not create new or truncate existing',
              '17': 'file I/O',
              '18': 'could not create directory',
              '19': 'name resolution failed',
              '20': 'could not parse metalink',
              '21': 'FTP command failed',
              '22': 'HTTP response header was bad or unexpected',
              '23': 'too many redirections',
              '24': 'HTTP authorization failed',
              '25': 'could not parse bencoded file',
              '26': 'torrent was corrupted or missing informations',
              '27': 'bad magnet URI',
              '28': 'bad/unrecognized option or unexpected option argument',
              '29': 'the remote server was unable to handle the request',
              '30': 'could not parse JSON-RPC request'}

if __name__ == '__main__':
    main()

