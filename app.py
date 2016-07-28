# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

import flask
from flask import Flask
from werkzeug.contrib.fixers import HeaderRewriterFix
from werkzeug.wrappers import Response

from mohg.hg_mozilla_org import HgMozillaOrg
from pyLibrary import convert
from pyLibrary.debugs import constants, startup
from pyLibrary.debugs.exceptions import Except
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import Dict
from pyLibrary.meta import cache
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import HOUR
from pyLibrary.times.timer import Timer

app = Flask(__name__)


class TreeherderRequestLoggingService(object):
    """
    Used by other processes to determine if they should make a call to Treeherder
    """

    @cache(duration=HOUR)
    def log_first_request(self, branch, revision):
        return Date.now().unix

    def get_treeherder_job(self):
        try:
            with Timer("Process Request"):
                args = Dict(**flask.request.args)
                timestamp = self.log_first_request(self, args.get("branch"), args.get("revision"))
                response_data = str(timestamp)
                return Response(
                    response_data,
                    status=200,
                    headers={
                        "access-control-allow-origin": "*",
                        "content-type": "text/plain"
                    }
                )
        except Exception, e:
            e = Except.wrap(e)
            Log.warning("Could not process", cause=e)
            e = e.as_dict()

            return Response(
                convert.unicode2utf8(convert.value2json(e)),
                status=400,
                headers={
                    "access-control-allow-origin": "*",
                    "content-type": "application/json"
                }
            )


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    return Response(
        b"",
        status=400,
        headers={
            "access-control-allow-origin": "*",
            "content-type": "text/html"
        }
    )

if __name__ == "__main__":
    try:
        config = startup.read_settings()
        constants.set(config.constants)
        Log.start(config.debug)

        # SETUP TREEHERDER ENDPOINT
        hg = HgMozillaOrg(use_cache=True, settings=config.hg)
        th = TreeherderRequestLoggingService(hg, settings=config.treeherder)
        app.add_url_rule('/treeherder', None, th.get_treeherder_job, methods=['GET'])

        HeaderRewriterFix(app, remove_headers=['Date', 'Server'])

        app.run(**config.flask)
    except Exception, e:
        Log.error("Serious problem with service construction!  Shutdown!", cause=e)
    finally:
        Log.stop()

    sys.exit(0)





