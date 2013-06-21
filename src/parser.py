import types

import ply.yacc as yacc

from lexer import CurlOutputLexer


class Event(object):
    __slots__ = ('datetime', 'event', 'data')

    def __init__(self, datetime_obj, event, data=None):
        self.datetime = datetime_obj
        self.event = event
        self.data = data

    def __unicode__(self):
        if self.data is not None:
            if isinstance(self.data, types.ListType):
                if len(self.data) > 3:
                    data_repr = self.data[:3] + ['...']
                else:
                    data_repr = self.data
            else:
                data_repr = self.data
            return "Event {datetime=%s, event=%s, data=%s}" % \
                (self.datetime, self.event, data_repr)
        else:
            return "Event {datetime=%s, event=%s}" % (self.datetime, self.event)

    def __repr__(self):
        return unicode(self)


class CurlOutputParser(object):
    tokens = CurlOutputLexer.tokens

    @classmethod
    def p_log_data_more(cls, p):
        'log_data : log_datum log_data'
        p[0] = [p[1]] + p[2]

    @classmethod
    def p_log_data_finished(cls, p):
        'log_data : '
        p[0] = []

    @classmethod
    def p_log_datum_connecting(cls, p):
        'log_datum : TIMESTAMP CONNECTING'
        p[0] = Event(datetime_obj=p[1], event="connecting", data=p[2])

    @classmethod
    def p_log_datum_connecting_ip(cls, p):
        'log_datum : TIMESTAMP CONNECTING_IP'
        p[0] = Event(datetime_obj=p[1], event="connecting_ip", data=p[2])

    @classmethod
    def p_log_datum_connected_hostname_ip_port(cls, p):
        'log_datum : TIMESTAMP CONNECTED_HOSTNAME_IP_PORT'
        p[0] = Event(datetime_obj=p[1], event="connected_hostname_ip_port", data=p[2])

    @classmethod
    def p_log_datum_closing_connection(cls, p):
        'log_datum : TIMESTAMP CLOSING_CONNECTION'
        p[0] = Event(datetime_obj=p[1], event="closing_connection")

    @classmethod
    def p_log_datum_send_header(cls, p):
        'log_datum : TIMESTAMP SEND_HEADER data'
        p[0] = Event(datetime_obj=p[1], event='send_header', data=p[3])

    @classmethod
    def p_log_datum_recv_header(cls, p):
        'log_datum : TIMESTAMP RECV_HEADER data'
        p[0] = Event(datetime_obj=p[1], event='recv_header', data=p[3])

    @classmethod
    def p_log_datum_redirect(cls, p):
        'log_datum : TIMESTAMP REDIRECT'
        p[0] = Event(datetime_obj=p[1], event='redirect', data=p[2])

    @classmethod
    def p_log_datum_ssl_client_hello(cls, p):
        'log_datum : TIMESTAMP SSL_CLIENT_HELLO'
        p[0] = Event(datetime_obj=p[1], event="ssl_client_hello")

    @classmethod
    def p_log_datum_ssl_server_hello(cls, p):
        'log_datum : TIMESTAMP SSL_SERVER_HELLO'
        p[0] = Event(datetime_obj=p[1], event="ssl_server_hello")

    @classmethod
    def p_log_datum_ssl_finished(cls, p):
        'log_datum : TIMESTAMP SSL_FINISHED'
        p[0] = Event(datetime_obj=p[1], event="ssl_finished")

    @classmethod
    def p_log_datum(cls, p):
        'log_datum : TIMESTAMP'

        # Return None; this will still be present in the parse output but
        # we exclude it when returning to the caller.
        pass

    @classmethod
    def p_data_more(cls, p):
        'data : data DATA'
        p[0] = p[1] + [p[2]]

    @classmethod
    def p_data_finished(cls, p):
        'data : '
        p[0] = []

    @classmethod
    def p_error(cls, p):
        """On an error restart the parser at the next timestamp.

        We can't predict everything that curl may print out, but at least
        with trace mode we know that lines will be prepended by timestamps."""
        while True:
            token = yacc.token()
            if not token or token.type == "TIMESTAMP":
                break
        yacc.errok()
        return token

    @classmethod
    def build(cls):
        parser = yacc.yacc(module=cls)
        return parser

    @classmethod
    def parse(parser_cls, text, lexer_cls=CurlOutputLexer):
        lexer = lexer_cls.build()
        parser = parser_cls.build()
        parse = [elem for elem in parser.parse(text, lexer) if elem is not None]
        parse = parser_cls.collapse_recv_headers(parse)
        return parse

    @classmethod
    def collapse_recv_headers(cls, parse):
        """Collapse multiple RECV_HEADER events into one event, with the datetime
        set to when the first header was received.datetime

        I couldn't figure out how to come up with a grammar without shift/reduce
        conflicts to do this, so we do it here."""
        
        output = []
        in_block = False
        current_block = []
        for elem in parse:
            if elem.event != 'recv_header':
                if in_block:
                    all_data = [block_elem.data[0] for block_elem in current_block]
                    new_event = Event(datetime_obj=current_block[0].datetime,
                                      event="recv_header",
                                      data=all_data)
                    output.append(new_event)
                    current_block = []
                    in_block = False
                output.append(elem)
                continue
            in_block = True
            current_block.append(elem)
        return output
