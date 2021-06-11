import sublime
import sublime_plugin
import re

VIEW_TOO_BIG = 1000000
WORD_PATTERN = re.compile(r'(\w{2,})', re.S)  # Start from words of length 2

words_by_view = {}
words_global = set()
matching = []
lookup_index = 0
last_choice = ''


class HippieWordCompletionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global last_choice, lookup_index, matching

        primer_region = self.view.word(self.view.sel()[0])
        primer = self.view.substr(primer_region)

        def _matching(*sets):
            for s in sets:
                yield from fuzzyfind(primer, s)
            yield primer  # Always be able to cycle back

        if primer != last_choice:
            lookup_index = 0
            matching = ldistinct(_matching(words_by_view[self.view], words_global))

        if matching[lookup_index] == primer:
            lookup_index += 1
        if lookup_index >= len(matching):
            lookup_index = 0
        last_choice = matching[lookup_index]

        self.view.replace(edit, primer_region, last_choice)


class HippieListener(sublime_plugin.EventListener):
    def on_init(self, views):
        for view in views:
            index_view(view)

    def on_modified_async(self, view):
        index_view(view)


def index_view(view):
    if view.size() > VIEW_TOO_BIG:
        return
    contents = view.substr(sublime.Region(0, view.size()))
    words_by_view[view] = words = set(WORD_PATTERN.findall(contents))
    words_global.update(words)


def fuzzyfind(primer, collection, sort_results=True):
    """
    Args:
        primer (str): A partial string which is typically entered by a user.
        collection (iterable): A collection of strings which will be filtered
                               based on the `primer`.
        sort_results(bool): The suggestions are sorted by considering the
                            smallest contiguous match, followed by where the
                            match is found in the full string. If two suggestions
                            have the same rank, they are then sorted
                            alpha-numerically. This parameter controls the
                            *last tie-breaker-alpha-numeric sorting*. The sorting
                            based on match length and position will be intact.
    Returns:
        suggestions (generator): A generator object that produces a list of
            suggestions narrowed down from `collection` using the `primer`.
    """
    suggestions = []
    pat = '.*?'.join(map(re.escape, primer))
    pat = '(?=({0}))'.format(pat)   # lookahead regex to manage overlapping matches
    regex = re.compile(pat, re.IGNORECASE)
    for item in collection:
        if item == primer:
            continue
        r = list(regex.finditer(item))
        if r:
            best = min(r, key=lambda x: len(x.group(1)))   # find shortest match
            suggestions.append((len(best.group(1)), best.start(), item, item))

    if sort_results:
        return [z[-1] for z in sorted(suggestions)]
    else:
        return [z[-1] for z in sorted(suggestions, key=lambda x: x[:2])]


def ldistinct(seq):
    """Iterates over sequence skipping duplicates"""
    seen = set()
    res = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            res.append(item)
    return res
