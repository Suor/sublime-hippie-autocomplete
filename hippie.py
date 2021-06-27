import sublime
import sublime_plugin
from collections import defaultdict
import re

VIEW_TOO_BIG = 1000000
WORD_PATTERN = re.compile(r'(\w{2,})', re.S)  # Start from words of length 2

words_by_view = {}
words_global = set()
last_view = None
initial_primer = ""
matching = []
last_index = 0
history = defaultdict(dict)  # type: Dict[sublime.Window, Dict[str, str]]


class HippieWordCompletionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global last_view, matching, last_index, initial_primer
        window = self.view.window()
        assert window

        def word_start(region):
            word_region = self.view.word(region)
            return sublime.Region(word_region.a, region.end())

        first_sel = self.view.sel()[0]
        primer = self.view.substr(word_start(first_sel))

        def _matching():
            yield primer  # Always be able to cycle back
            if primer in history[window]:
                yield history[window][primer]
            yield from fuzzyfind(primer, words_by_view[self.view])
            yield from fuzzyfind(primer, words_global)

        if last_view is not self.view or not matching or primer != matching[last_index]:
            if words_by_view[self.view] is None:
                index_view(self.view, exclude_sel=True)
            last_view = self.view
            initial_primer = primer
            matching = ldistinct(_matching())
            last_index = 0

        if matching[last_index] == primer:
            last_index += 1
        if last_index >= len(matching):
            last_index = 0

        for region in self.view.sel():
            self.view.replace(edit, word_start(region), matching[last_index])

        history[window][initial_primer] = matching[last_index]


class HippieListener(sublime_plugin.EventListener):
    def on_init(self, views):
        for view in views:
            index_view(view)

    def on_modified(self, view):
        words_by_view[view] = None  # Drop cached word set

    def on_deactivated_async(self, view):
        index_view(view)


def index_view(view, exclude_sel=False):
    if view.size() > VIEW_TOO_BIG:
        return

    if exclude_sel:
        regions = invert_regions(view, map(view.word, view.sel()))
    else:
        regions = [sublime.Region(0, view.size())]

    words = set().union(*[WORD_PATTERN.findall(view.substr(region)) for region in regions])
    words_by_view[view] = words
    words_global.update(words)


def invert_regions(view, regions):
    # NOTE: regions should be non-overlapping and ordered,
    #       no check here for performance reasons
    start = 0
    end = view.size()
    result = []

    for r in regions:
        if r.a > start:
            result.append(sublime.Region(start, r.a))
        start = r.b

    if start < end:
        result.append(sublime.Region(start, end))

    return result


def fuzzyfind(primer, coll):
    """
    Args:
        primer: A partial string which is typically entered by a user.
        coll: A collection of strings which will be filtered based on the `primer`.
    """
    primer_lower = primer.lower()
    suggestions = [(score, item) for item in coll if (score := fuzzy_score(primer_lower, item))]
    return [z[-1] for z in sorted(suggestions, key=lambda x: x[0])]


def fuzzy_score(primer, item, _abbr={}):
    if item not in _abbr:
        _abbr[item] = make_abbr(item)
    if _abbr[item] and (abbr_score := _fuzzy_score(primer, _abbr[item])):
        return abbr_score
    return _fuzzy_score(primer, item)

def _fuzzy_score(primer, item):
    start, pos, prev, score = -1, -1, 0, 1
    item_l = item.lower()
    for c in primer:
        pos = item_l.find(c, pos + 1)
        if pos == -1:
            return
        if start == -1:
            start = pos

        score += pos - prev
        prev = pos

    return (score, len(item))

def make_abbr(item):
    abbr = item[0]
    for c, nc in zip(item, item[1:]):
        if c in "_-" or c.isupper() < nc.isupper():
            abbr += nc
    if len(abbr) > 1:
        return abbr


def ldistinct(seq):
    """Iterates over sequence skipping duplicates"""
    seen = set()
    res = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            res.append(item)
    return res
