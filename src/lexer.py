from collections import namedtuple
import datetime

import ply.lex as lex
import re


HostnamePort = namedtuple("HostnamePort", ["hostname", "port"])
HostnameIpPort = namedtuple("HostnamePort", ["hostname", "ip", "port"])


class PrettyDatetime(object):
    __slots__ = ('datetime_obj', )

    def __init__(self, datetime_obj):
        self.datetime_obj = datetime_obj

    def __unicode__(self):
        return self.datetime_obj.isoformat(" ")

    def __repr__(self):
        return unicode(self)


class CurlOutputLexer(object):

    tokens = (
        'TIMESTAMP',
        'CONNECTING',
        'CONNECTING_IP',
        'CONNECTED_HOSTNAME_IP_PORT',
        'SEND_HEADER',
        'SEND_DATA',
        'RECV_HEADER',
        'RECV_DATA',
        'REDIRECT',
        'DATA',
        'SSL_CLIENT_HELLO',
        'SSL_SERVER_HELLO',
        'SSL_FINISHED',
        'CLOSING_CONNECTION',
    )

    t_ignore = ''

    @classmethod
    def t_TIMESTAMP(cls, token):
        r'\d{2}:\d{2}:\d{2}\.\d{6}'
        today = datetime.date.today()
        datetime_obj = datetime.datetime.strptime(token.value, "%H:%M:%S.%f")
        token.value = datetime_obj.replace(year=today.year,
                                           month=today.month,
                                           day=today.day)
        token.value = PrettyDatetime(token.value)
        return token

    @classmethod
    def t_CONNECTING(cls, token):
        r'==\sInfo\:\sAbout\sto\sconnect\(\)\sto.*\n'
        elems = re.findall("About to connect\(\) to (.*) port (\d+)", token.value)[0]
        token.value = HostnamePort(hostname=elems[0], port=elems[1])
        return token

    @classmethod
    def t_CONNECTING_IP(cls, token):
        r'==\sInfo:\s{3}Trying.*\n'
        token.value = re.findall("== Info:   Trying (.*)\.\.\.\n", token.value)[0]
        return token

    @classmethod
    def t_CONNECTED_HOSTNAME_IP_PORT(cls, token):
        r'==\sInfo\:\sConnected\sto\s.*\s\(.*\)\sport\s\d+'
        elems = re.findall(r'==\sInfo\:\sConnected\sto\s(.*)\s\((.*)\)\sport\s(\d+)',
                           token.value)[0]
        token.value = HostnameIpPort(hostname=elems[0], ip=elems[1], port=elems[2])
        return token

    @classmethod
    def t_SEND_HEADER(cls, token):
        r'=>\sSend\sheader'
        token.value = None
        return token

    @classmethod
    def t_SEND_DATA(cls, token):
        r'=>\sSend\sdata.*\n'
        token.value = None
        return token

    @classmethod
    def t_RECV_HEADER(cls, token):
        r'<=\sRecv\sheader'
        token.value = None
        return token

    @classmethod
    def t_RECV_DATA(cls, token):
        r'<=\sRecv\sdata.*\n'
        token.value = None
        return token

    @classmethod
    def t_DATA(cls, token):
        r'[0-9a-f]{4}\:\s.*\n'
        token.value = re.findall(r'[0-9a-f]{4}\:\s(.*)\n', token.value)[0]
        return token

    @classmethod
    def t_REDIRECT(cls, token):
        r'==\sInfo\:\sIssue\sanother\srequest\sto\sthis\sURL\:\s.*\n'
        token.value = \
            re.findall(r'==\sInfo\:\sIssue\sanother\srequest\sto\sthis\sURL\:\s\'(.*)\'\n',
                       token.value)[0]
        return token

    @classmethod
    def t_SSL_CLIENT_HELLO(cls, token):
        r'==\sInfo\:\sSSL.*Client\shello'
        token.value = None
        return token

    @classmethod
    def t_SSL_SERVER_HELLO(cls, token):
        r'==\sInfo\:\sSSL.*Server\shello'
        token.value = None
        return token

    @classmethod
    def t_SSL_FINISHED(cls, token):
        r'==\sInfo\:\sSSL\sconnection\susing.*\n'
        token.value = None
        return token

    @classmethod
    def t_CLOSING_CONNECTION(cls, token):
        r'==\sInfo\:\sClosing\sconnection.*\n'
        token.value = None
        return token

    @classmethod
    def t_error(cls, token):
        token.lexer.skip(1)

    @classmethod
    def build(cls, **kwargs):
        lexer = lex.lex(module=cls, **kwargs)
        return lexer
