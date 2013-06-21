#!/usr/bin/env python

import datetime
import json
import pprint
import sys
import subprocess

import dateutil.relativedelta

from parser import CurlOutputParser as CurlOutputParser


class CurlExecutor(object):

    def __init__(self, uri, output, parser_cls=CurlOutputParser):
        self.uri = uri
        self.output = output
        self.initialise(output, parser_cls)

    @classmethod
    def get_parsed_output_for_uri(cls, uri):
        cmd = ["/usr/local/bin/curl", "--trace-ascii", "-", "--trace-time", "--location",
               "--url", uri, "--output", "/dev/null", "--silent", "--show-error"]
        output = subprocess.check_output(cmd)
        return CurlExecutor(uri, output)

    def initialise(self, output, parser_cls):
        parse = [elem for elem in parser_cls.parse(output)]
        print "parse: "
        pprint.pprint(parse)
        import ipdb; ipdb.set_trace()

        #tokens = [token for token in lexer.input(output)]
        #pprint.pprint(tokens)
        #self.setup_timestamps(tokens)

    def setup_timestamps(self, tokens):
        timestamp_tokens = (token for token in tokens if token.type == "TIMESTAMP")
        first_token = timestamp_tokens.next()
        for last_token in timestamp_tokens:
            pass
        self.start_time = first_token.value
        self.end_time = last_token.value
        if self.end_time < self.start_time:
            self.end_time += datetime.timedelta(days=1)
        self.duration = dateutil.relativedelta.relativedelta(self.end_time, self.start_time)

    @property
    def duration_string(self):
        elems = []
        if self.duration.minutes > 0:
            if self.duration.minutes == 1:
                elems.append("%s minute" % self.duration.minutes)
            else:
                elems.append("%s minutes" % self.duration.minutes)
        if len(elems) > 0 or self.duration.seconds > 0:
            if self.duration.seconds == 1:
                elems.append("%s second" % self.duration.seconds)
            else:
                elems.append("%s seconds" % self.duration.seconds)
        if len(elems) > 0 or self.duration.microseconds > 0:
            elems.append("%s milliseconds" % (self.duration.microseconds // 1000, ))
        return ", ".join(elems)

    @property
    def dict(self):
        return {"start_time": self.start_time.isoformat(" "),
                "end_time": self.end_time.isoformat(" "),
                "duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "duration_string": self.duration_string,
                "uri": self.uri,
                "output": self.output}

    def __str__(self):
        return json.dumps({k: v for (k, v) in self.dict.items() if k != "output"})


def main():
    uri = "http://jira.youview.co.uk"
    #uri = "http://www.github.com"
    ce = CurlExecutor.get_parsed_output_for_uri(uri)
    print ce
    import ipdb; ipdb.set_trace()


if __name__ == "__main__":
    sys.exit(main())
