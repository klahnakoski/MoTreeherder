# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals

from mohg.hg_mozilla_org import HgMozillaOrg
from pyLibrary.debugs import startup, constants
from pyLibrary.debugs.logs import Log
from pyLibrary.env import http
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import DAY
from treeherder import TreeHerder


def find_some_work(th):
    # th.get_markup("fx-team", "036f62007472", "B8kS5IJ5Rom8l-kcSIRIlA")
    # th.get_markup("mozilla-inbound", "971c1ee26cad", "fNuzNmZxS6m3i_p9jDh8iA")

    # GET SOME TASKS
    result = http.post_json(url="http://activedata.allizom.org/query", data={
        "from": "task",
        "select": ["build.branch", "build.revision", "task.id"],
        "where": {"and": [
            {"gt": {"task.run.start_time": (Date.today() - DAY).unix}},
            {"exists": "build.revision"},
            {"exists": "build.branch"}
        ]},
        "format": "list"
    })


    # TRY TO GET THEM OUT OF OUR CACHE
    for r in result.data:
        Log.note("look for task {{task_id}}", task_id=r.task.id)
        th.get_markup(r.build.branch, r.build.revision, r.task.id)


def main():

    try:
        settings = startup.read_settings()
        constants.set(settings.constants)
        Log.start(settings.debug)

        hg = HgMozillaOrg(settings.hg)
        th = TreeHerder(settings=settings)
        find_some_work(th)
    except Exception, e:
        Log.error("Problem with etl", e)
    finally:
        Log.stop()


if __name__ == "__main__":
    main()


