#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from __future__ import ( division, absolute_import, print_function, unicode_literals )

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder

if sys.version_info >= (3,):
    import urllib.request as urllib2
    import urllib.parse as urlparse
else:
    import urllib2
    import urlparse

global gSettings


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string

    url = "ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/318/18d/CORD00ARG_R_20183180000_01D_30S_MO.crx.gz"

    """
    # print('argv (treat daily-duty) = %s' % argv)
    global cBaseName  # colored version
    baseName = os.path.basename(__file__)
    cBaseName = colored(baseName, 'yellow')

    helpTxt = baseName + ' downloads files according to specified protocol to location. Example: url = ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/318/18d/CORD00ARG_R_20183180000_01D_30S_MO.crx.gz'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-p', '--protocol', help='Download protocol', required=True, type=str)
    parser.add_argument('-s', '--server', help='IGS', required=True, type=str)
    parser.add_argument('-r', '--dir_remote', help='Remote directory', required=True, type=str)
    parser.add_argument('-f', '--file_remote', help='Remote file', required=True, type=str)
    parser.add_argument('-l', '--dir_local', help='Local directory', required=True, type=str)

    parser.add_argument('-v', '--verbose', help='increase output verbosity (default False)',
                        action='store_true', required=False, default=False)

    # drop argv[0]
    args = parser.parse_args(argv)

    # return arguments
    return args.protocol, args.server, args.dir_remote, args.file_remote, args.dir_local, args.verbose


def download_file(url, proxy, dest=None, verbose=False):
    """
    Download and save a file specified by url to dest directory,
    """
    proxies = {"http":"http://%s" % proxy}
    proxy_support = urllib2.ProxyHandler(proxies)
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler(debuglevel=1))
    urllib2.install_opener(opener)

    req = urllib2.Request(url)
    req.add_unredirected_header('User-Agent', 'Mozilla/5.0')
    u = urllib2.urlopen(req)

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    filename = os.path.basename(path)
    if not filename:
        filename = 'downloaded.file'
    if dest:
        filename = os.path.join(dest, filename)

    with open(filename, 'wb') as f:
        meta = u.info()
        meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
        meta_length = meta_func("Content-Length")
        file_size = None
        if meta_length:
            file_size = int(meta_length[0])

        if verbose:
            print("... Downloading: {0} (Bytes: {1})".format(url, file_size))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)

            status = "{0:16}".format(file_size_dl)
            if file_size:
                status += "   [{0:6.2f}%]".format(file_size_dl * 100 / file_size)
            status += chr(13)
            if verbose:
                print(status, end="")

        if verbose:
            print()

    return filename


def main(argv):
    """
    ``download_file`` downloads a file from a server according to an Internet Protocol
    """

    # limit float precision
    encoder.FLOAT_REPR = lambda o: format(o, '.3f')
    cFuncName = colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    protocol, server, dir_remote, filename, dir_local, verbose = treatCmdOpts(argv)

    # store in dictionary
    gSettings = {}
    # settings of remote file
    gSettings['remote'] = {}
    gSettings['remote']['protocol'] = protocol
    gSettings['remote']['IGS'] = server
    gSettings['remote']['dir_remote'] = dir_remote
    gSettings['remote']['file_remote'] = filename
    # settings of local file
    gSettings['local'] = {}
    gSettings['local']['dir_local'] = dir_local

    gSettings['proxy'] = {}
    gSettings['proxy']['http'] = os.environ.get("http_proxy")
    gSettings['proxy']['https'] = os.environ.get("https_proxy")

    # create download url
    gSettings['remote']['url'] = gSettings['remote']['protocol'] + '://' + gSettings['remote']['IGS'] + os .path.join(gSettings['remote']['dir_remote'], gSettings['remote']['file_remote'])

    if verbose:
        print('%s:\n... %s:' % (cBaseName, colored('global Settings', 'green')))
        print(json.dumps(gSettings, sort_keys=True, indent=4))

    # download the url
    gSettings['local']['filename'] = download_file(url=gSettings['remote']['url'], dest=gSettings['local']['dir_local'], proxy=gSettings['proxy']['http'], verbose=verbose)

    # inform the user and save the json file'
    if verbose:
        print('%s: %s\n... %s:' % (cBaseName, cFuncName, colored('global Settings', 'green')))
        print(json.dumps(gSettings, sort_keys=True, indent=4))

    # # url = "http://download.thinkbroadband.com/10MB.zip"
    # url = "ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/318/18d/CORD00ARG_R_20183180000_01D_30S_MO.crx.gz"
    # filename = download_file(url)
    # print(filename)

    # url = "ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/200/18d/cord2000.18d.Z"
    # filename = download_file(url)
    # print(filename)

    # url = "ftp://cddis.gsfc.nasa.gov/pub/gps/products/2027/igr20270.sp3.Z"
    # filename = download_file(url)
    # print(filename)

    # url = "ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/318/18n/brdc3180.18n.Z"
    # filename = download_file(url)
    # print(filename)

    # url = "ftp://cddis.gsfc.nasa.gov/pub/glonass/data/daily/2018/318/18g/brdc3180.18g.Z"
    # filename = download_file(url)
    # print(filename)

    # gunzip -c CORD00ARG_R_20183190000_01D_30S_MO.crx.gz | CRX2RNX - | gfzrnx_lx -kv -fout CORD00ARG_R_20183190000_01D_30S_MO.rnx -f


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv[1:])
