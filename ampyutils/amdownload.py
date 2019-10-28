import urllib
import requests


def download_file(url, localName):
    """
    download_file downloads a requested url from a server and stores the information locally
    """
    # handle proxy if needed
    # proxyExist = ping('proxy.intra.ma.ac.be')
    # print('ping = {!s}'.format(proxyExist))
    # if proxyExist:
    proxy = urllib.request.ProxyHandler({'http': 'proxy.intra.mil.be'})
    opener = urllib.request.build_opener(proxy)
    remote = opener.open(url)
    # else:
    #     url_request = urllib.request.Request(url)
    #     remote = urllib.request.urlopen(url_request)

    # open local file
    fdLocal = open(localName, 'wb')

    chunk_size=1024

    data = remote.read(chunk_size)
    while data:
        fdLocal.write(data)
        data = remote.read(chunk_size)
    fdLocal.close()
    remote.close()

    # print('done download')

    # # download_file('ftp://gssc.esa.int/gnss/data/daily/2019/100/BRUX00BEL_R_20191000000_01D_EN.rnx.gz')

    # try:
    #     r = requests.get(url, stream=True)
    #     print('r = %s' % type(r))
    #     with open('/tmp/BRUX.nav.gz', 'wb') as f:
    #         for chunk in r.iter_content(chunk_size=1024):
    #             if chunk:  # filter out keep-alive new chunks
    #                 f.write(chunk)
    #                 f.flush()
    #                 # f.flush() commented by recommendation from J.F.Sebastian
    #                 os.fsync(f)
    # except (requests.exceptions.ConnectionError):
    #     sys.stderr.write('Connection to NORAD could not be established.\n')

    # print('done download 2')



def ping(host: str) -> bool:
    """
    Returns True if host responds to a ping request
    """
    import subprocess, platform

    # Ping parameters as function of OS
    ping_str = "-n 1" if  platform.system().lower()=="windows" else "-c 1"
    args = "ping " + " " + ping_str + " " + host
    need_sh = False if  platform.system().lower()=="windows" else True

    # Ping
    return (subprocess.call(args, shell=need_sh) == 0)

