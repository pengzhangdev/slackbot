import os
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.utils import download_file, create_tmp_file


# @respond_to(r'upload \<?(.*)\>?')
# def upload(message, url):
#     url = url.lstrip('<').rstrip('>')
#     fname = os.path.basename(url)
#     message.reply('uploading {}'.format(fname))
#     if url.startswith('http'):
#         with create_tmp_file() as tmpf:
#             download_file(url, tmpf)
#             message.channel.upload_file(fname, tmpf, 'downloaded from {}'.format(url))
#     elif url.startswith('/'):
#         message.channel.upload_file(fname, url)

FILEHUB_ROOT = "/home/werther/Game/"

def fm_upload(message, args):
    url = args
    fname = os.path.basename(url)
    message.reply('uploading {}'.format(fname))
    if url.startswith('http'):
        with create_tmp_file() as tmpf:
            download_file(url, tmpf)
            message.channel.upload_file(fname, tmpf, 'download from {}'.format(url))
    else:
        #print("{} == {}".format(fname, os.path.join(FILEHUB_ROOT, url)))
        message.channel.upload_file(fname, os.path.join(FILEHUB_ROOT, url))

def fm_ls(message, args):
    argv = args.split()
    result = []
    if len(argv) == 0:
        argv.append(FILEHUB_ROOT);
    for arg in argv:
        files = os.listdir(arg)
        message.reply('{}'.format('\t'.join(files[:])))

def fm_download(message, args):
    url = args
    fname = os.path.basename(url)
    if url.startswith('http'):
        message.reply('downloading {}'.format(fname))
        with open('{}/{}'.format(FILEHUB_ROOT, fname)) as tmpf:
            download_file(url, tmpf)
            message.reply('download {} to {} success'.format(url, fname));


def parse_argument(contents):
    # fm [command] xxx
    argv = contents.split()
    if len(argv) > 3:
        argv = argv[:2] + [' '.join(argv[2:])]
    if len(argv) < 3:
        argv = argv + [' ']
    return argv

@respond_to(r'fm [\s]*[a-zA-Z0-9]+ (.*)')
@listen_to(r'fm [\s]*[a-zA-Z0-9]+ (.*)')
def filemanager(message, rest):
    contents = message.body.get('text', "")
    _, command, args = parse_argument(contents)
    if command == "upload":
        fm_upload(message, args)
    if command == "ls":
        fm_ls(message, args)
    if command == "download":
        fm_download(message, args)
