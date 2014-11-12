wiftgish
========

wiftgish - wish list sharing

About
-----

wiftgish is a wish list sharing application. My (extended) family uses it to share gift suggestions for winter-time holidays.

Supported Platforms
-------------------

wiftgish is implemented in Python for Google App Engine. Reference:

* https://developers.google.com/appengine/?csw=1

License
-------

wiftgish is licensed under the GNU AGPLv3.

Notes
-----

wiftgish was originally developed during the early(ish) days of App Engine -- long before the NDB Datastore API was introduced; consequently, the current code goes through fairly elaborate lengths to aggressively cache data to avoid unnecessary datastore access and deal with eventual consistency. This level of micro-management is no longer needed and could be removed in a refactor.

To Do
-----

* Rewrite in Go.
