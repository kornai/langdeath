"""This parser needs dbpedia dump to be downloaded from
http://wiki.dbpedia.org/Downloads39
Three files are needed: Raw Infobox Properties, nt
to be put into @basedir,
short abstracts dump (nt) to be put into @basedir, and
a file containing the titles (one per line) of dbpedia type Language,
(see Mapping Based Types Dump) which has to be put in
@basedir/@needed_fn (see constructor).
Since dumpis are quite big, parsing is a little slow, so there is a
parse_and_save() method, that will pickle results to two files files, and
parse() that only reads end merges results parsed from the two dump.
"""

