#! /usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import absolute_import
import os
import re
import sys
import json
import base64
import urllib2, urllib
from urllib2 import URLError, HTTPError
from subprocess import check_call
from getopt import getopt
from io import open

MAX_NAME_LEN = 50
ELLIPSIS = u'...'
HOST = os.getenv(u'DIANA_HOST', u'localhost')
PORT = os.getenv(u'DIANA_PORT', u'6800')
PREVIEW_COMMAND = os.getenv(u'DIANA_PREVIEW_COMMAND', u'open')
INFO_COMMAND = os.getenv(u'DIANA_INFO_COMMAND', u'file')
SECRET_TOKEN = os.getenv(u'DIANA_SECRET_TOKEN')
JSON_RPC_URI = u'http://%s:%s/jsonrpc' % (HOST, PORT)
TOKEN_PREFIX = u'token:'
BLACK = 30
GREEN = 32
BLUE = 34
MAGENTA = 35


def abbrev(value):
    n = value / 1024.0
    if n < 1:
        return u'%dB' % value
    value = n
    n = value / 1024.0
    if n < 1:
        return u'%.1fK' % value
    else:
        value = n
        n = value / 1024.0
        if n < 1:
            return u'%.1fM' % value
        else:
            return u'%.1fG' % n


def arrival(download_speed, remaining_length):
    if (download_speed == 0):
        return u'n/a'
    s = remaining_length / download_speed
    h = s / 3600
    s = s % 3600
    m = s / 60
    s = s % 60
    result = u""
    if (h >= 1):
        result += u'%dh' % h
    if (m >= 1):
        result += u'%dm' % m
    result += u"%ds" % s
    return result


def call_func(func, params=[]):
    if SECRET_TOKEN is not None:
        params.insert(0, u'{}{}'.format(TOKEN_PREFIX, SECRET_TOKEN))
    jsonreq = json.dumps({u'id': u'foo',
                          u'method': u'aria2.%s' % func,
                          u'params': params}).encode(u'utf-8')
    try:
        c = urllib2.urlopen(JSON_RPC_URI, jsonreq)
    except IOError, err:
        code = -1
        if type(err) is URLError:
            code = err.reason.errno
        elif type(err) is HTTPError:
            code = err.code
        if code == 111:
            print u'The daemon is not running.'
        elif code == -1:
            print u'Encountered an error of type: %s.' % type(err)
        else:
            print u'The server replied: %s.' % code
        exit(1)
    data = c.read().decode(u'utf-8')
    response = json.loads(data)
    return response


def get_active():
    return call_func(u'tellActive')


def get_waiting():
    return call_func(u'tellWaiting', [0, 666])


def get_stopped():
    return call_func(u'tellStopped', [0, 666])


def get_files(gids):
    for g in gids:
        response = call_func(u'getFiles', [g])
        if not response:
            print u'Failed on %s.' % g
        else:
            if len(gids) > 1:
                print u'%s: ' % magenta(g)
            files = response[u'result']
            for f in files:
                total_length = float(f[u'length'])
                completed_length = float(f[u'completedLength'])
                percent = 100

                if (total_length > 0):
                    percent = 100 * completed_length / total_length

                percent = u'%.1f' % percent
                selected = f[u'selected']
                mark = u'[ ]'

                if selected == u'true':
                    mark = u'[X]'

                output_line = u'%s %2s %5s%% %s' % (mark, f[u'index'],
                                                   percent, f[u'path'])

                if completed_length >= total_length:
                    output_line = green(output_line)

                print output_line


def apply_func_on_gids(fn, gids):
    for g in gids:
        response = call_func(fn, [g])
        if not response:
            print u'Failed on %s.' % g


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
    if u'select-file' in options:
        select_file = [re.split(u'-', x) for x in
                       re.split(u',', options[u'select-file'])]

    for g in gids:
        response = call_func(u'getFiles', [g])
        if not response:
            print u'Failed on %s.' % g
        else:
            if len(gids) > 1:
                print u'%s: ' % magenta(g)
            files = response[u'result']
            for f in files:
                if len(select_file) > 0:
                    index = int(f[u'index'])
                    if not pattern_match(index, select_file):
                        continue
                completed_length = float(f[u'completedLength'])
                if completed_length > 0:
                    check_call([command, f[u'path']])


def info_by_gid(gids, options):
    command_by_gid(INFO_COMMAND, gids, options)


def preview_by_gid(gids, options):
    command_by_gid(PREVIEW_COMMAND, gids, options)


def pause_by_gid(gids):
    apply_func_on_gids(u'pause', gids)


def resume_by_gid(gids):
    apply_func_on_gids(u'unpause', gids)


def remove_by_gid(gids):
    apply_func_on_gids(u'remove', gids)


def forcerm_by_gid(gids):
    apply_func_on_gids(u'forceRemove', gids)


def clean():
    downloads = []
    active = get_active()
    if active:
        downloads.extend(active[u'result'])
    for d in downloads:
        if u'infoHash' in d:
            completed_length = int(d[u'completedLength'])
            total_length = int(d[u'totalLength'])
            if completed_length >= total_length:
                remove_by_gid([d[u'gid']])


def add_items(items, options={}):
    for item in items:
        response = None

        if item.find(u'://') != -1 or item.startswith(u'magnet:'):
            response = call_func(u'addUri', [[item], options])
        else:
            item_content = base64.b64encode(open(item, u'rb').read())
            item_content = item_content.decode(u'utf-8')
            if item.endswith(u'.torrent'):
                response = call_func(u'addTorrent', [item_content, [], options])
            elif item.endswith(u'.meta4') or item.endswith(u'.metalink'):
                response = call_func(u'addMetalink', [item_content, options])

        if not response:
            print u'Failed on %s.' % item
        else:
            print response[u'result']


def pause_all():
    call_func(u'pauseAll')


def resume_all():
    call_func(u'unpauseAll')


def list_downloads(kind):
    downloads = None

    if kind == u'active':
        downloads = get_active()
    elif kind == u'waiting':
        downloads = get_waiting()
    elif kind == u'stopped':
        downloads = get_stopped()

    if downloads:
        for r in downloads[u'result']:
            completed_length = float(r[u'completedLength'])
            total_length = float(r[u'totalLength'])
            remaining_length = total_length - completed_length
            download_speed = float(r[u'downloadSpeed'])
            eta = arrival(download_speed, remaining_length)
            percent = 100

            if (total_length > 0):
                percent = 100 * completed_length / total_length

            percent = u'%.1f' % percent
            byte_download_speed = u'%.1f' % (download_speed / 1024)
            byte_upload_speed = u'%.1f' % (float(r[u'uploadSpeed']) / 1024)
            name = u'n/a'
            number_of_seeders = u'n/a'

            if u'numSeeders' in r:
                number_of_seeders = r[u'numSeeders']

            if u'bittorrent' in r:
                bt = r[u'bittorrent']
                if u'info' in bt:
                    name = bt[u'info'][u'name']
            else:
                if u'files' in r:
                    files = r[u'files']
                    for f in files:
                        if u'uris' in f:
                            uris = f[u'uris']
                            if len(uris) > 0:
                                name = uris[0][u'uri']
                                break
                            else:
                                if u'path' in f:
                                    name = f[u'path']
                                    break

            if len(name) > MAX_NAME_LEN:
                name = name[:MAX_NAME_LEN - len(ELLIPSIS)] + ELLIPSIS

            strformat = u'%3s %-50s %6s%% %6s %6s %5s %5s %s/%s %s'
            output_line = strformat % (r[u'gid'],
                                       name,
                                       percent,
                                       abbrev(completed_length),
                                       abbrev(total_length),
                                       byte_download_speed,
                                       byte_upload_speed,
                                       number_of_seeders,
                                       r[u'connections'],
                                       eta)

            if completed_length >= total_length:
                output_line = green(output_line)
            elif download_speed > 0:
                output_line = blue(output_line)

            print output_line


def show_errors():
    stopped = get_stopped()
    if stopped:
        for r in stopped[u'result']:
            if u'status' in r:
                status = r[u'status']
                if status == u'error':
                    gid = r[u'gid']
                    errorCode = r[u'errorCode']
                    error = EXIT_CODES[errorCode]
                    print u'%3s %s (error %s)' % (gid, error, errorCode)


def show_stats():
    gs = call_func(u'getGlobalStat')
    stats = gs[u'result']
    for key in sorted(stats.keys()):
        value = stats[key]
        print u'%24s: ' % grey(key)
        if u'Speed' in key:
            print u'%s/s' % abbrev(float(value))
        else:
            print value


def grey(s):
    return colored_string(BLACK, s)


def green(s):
    return colored_string(GREEN, s)


def blue(s):
    return colored_string(BLUE, s)


def magenta(s):
    return colored_string(MAGENTA, s)


def colored_string(c, s):
    if sys.stdout.isatty():
        return u'\033[1;%im%s\033[0m' % (c, s)
    else:
        return s


def usage():
    print u'''
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
    optlist = [u'help', u'pause', u'out=', u'header=', u'referer=',
               u'user-agent=', u'dir=', u'select-file=', u'http-user=',
               u'http-passwd=', u'username=', u'password=']
    opts, args = getopt(sys.argv[1:], u'hu:p:', optlist)

    options = {}
    username = None
    password = None

    for key, value in opts:
        if key in (u'-h', u'--help'):
            usage()
        elif key in (u'-u', u'--username'):
            username = value
        elif key in (u'-p', u'--password'):
            password = value
        else:
            options.update({key.replace(u'--', u''): value})

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
            print u'Action \'%s\' takes no arguments' % action
            sys.exit(1)
        elif action in ARGS_ACTIONS and len(arguments) < 1:
            print u'No arguments given for action \'%s\'' % action
            sys.exit(1)

        if action == u'add':
            add_items(arguments, options)
        elif action == u'remove':
            remove_by_gid(arguments)
        elif action == u'forcerm':
            forcerm_by_gid(arguments)
        elif action == u'info':
            info_by_gid(arguments, options)
        elif action == u'preview':
            preview_by_gid(arguments, options)
        elif action == u'pause':
            pause_by_gid(arguments)
        elif action == u'resume':
            resume_by_gid(arguments)
        elif action == u'files':
            get_files(arguments)
        elif action == u'list':
            list_downloads(u'active')
        elif action == u'errors':
            show_errors()
        elif action == u'stats':
            show_stats()
        elif action == u'paused':
            list_downloads(u'waiting')
        elif action == u'stopped':
            list_downloads(u'stopped')
        elif action == u'sleep':
            call_func(u'pauseAll')
        elif action == u'wake':
            call_func(u'unpauseAll')
        elif action == u'purge':
            call_func(u'purgeDownloadResult')
        elif action == u'clean':
            clean()
        else:
            print u'Unknown action: %s' % action
            exit(1)
    else:
        usage()

NO_ARGS_ACTIONS = (u'list', u'paused', u'stopped', u'errors', u'stats', u'sleep',
                   u'wake', u'purge', u'clean')
ARGS_ACTIONS = (u'add', u'remove', u'forcerm', u'preview', u'pause', u'resume',
                u'files')

EXIT_CODES = {u'1': u'unknown',
              u'2': u'timeout',
              u'3': u'resource not found',
              u'4': u'resources not found',
              u'5': u'download speed too slow',
              u'6': u'network problem',
              u'7': u'unfinished downloads',
              u'8': u'resume not supported',
              u'9': u'not enough disk space',
              u'10': u'piece length differ',
              u'11': u'was downloading the same file',
              u'12': u'was downloading the same info hash',
              u'13': u'file already existed',
              u'14': u'renaming failed',
              u'15': u'could not open existing file',
              u'16': u'could not create new or truncate existing',
              u'17': u'file I/O',
              u'18': u'could not create directory',
              u'19': u'name resolution failed',
              u'20': u'could not parse metalink',
              u'21': u'FTP command failed',
              u'22': u'HTTP response header was bad or unexpected',
              u'23': u'too many redirections',
              u'24': u'HTTP authorization failed',
              u'25': u'could not parse bencoded file',
              u'26': u'torrent was corrupted or missing informations',
              u'27': u'bad magnet URI',
              u'28': u'bad/unrecognized option or unexpected option argument',
              u'29': u'the remote server was unable to handle the request',
              u'30': u'could not parse JSON-RPC request'}

if __name__ == u'__main__':
    main()
