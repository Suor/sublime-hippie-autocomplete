from collections import defaultdict
from itertools import chain
import re

import sublime
import sublime_plugin

flatten = chain.from_iterable

VIEW_TOO_BIG = 1000000
WORD_PATTERN = re.compile(r'(\w{2,})', re.S)  # Start from words of length 2

words_by_view = defaultdict(dict)  # type: Dict[sublime.Window, Dict[sublime.View, Set(str)]]
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

        primer_region = self.view.word(self.view.sel()[0])
        primer = self.view.substr(primer_region)

        def _matching(*sets):
            for s in sets:
                yield from fuzzyfind(primer, s)
            yield primer  # Always be able to cycle back

        if last_view is not self.view or not matching or primer != matching[last_index]:
            if self.view not in words_by_view[window]:
                index_view(self.view)
            last_view = self.view
            initial_primer = primer
            matching = ldistinct(_matching(
                (
                    {history[window][initial_primer]}
                    if initial_primer in history[window]
                    else set()
                ),
                words_by_view[window][self.view] - {initial_primer},
                (
                    set(flatten(words_by_view[window].values()))
                    - words_by_view[window][self.view]
                    - {initial_primer}
                )
            ))

            last_index = 0
        else:
            last_index += 1
            if last_index >= len(matching):
                last_index = 0

        for region in self.view.sel():
            self.view.replace(edit, self.view.word(region), matching[last_index])

        history[window][initial_primer] = matching[last_index]


class HippieListener(sublime_plugin.EventListener):
    def on_init(self, views):
        for view in views:
            index_view(view)

    def on_modified_async(self, view):
        window = view.window()
        if not window:
            ...
        else:
            words_by_view[window].pop(view, None)  # Drop cached word set


def index_view(view):
    window = view.window()
    assert window
    if view.size() > VIEW_TOO_BIG:
        return
    contents = view.substr(sublime.Region(0, view.size()))
    words_by_view[window][view] = set(WORD_PATTERN.findall(contents))


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
    for item in collection:
        if score := fuzzy_score(primer.lower(), item):
            suggestions.append((score, item))

    if sort_results:
        return [z[-1] for z in sorted(suggestions)]
    else:
        return [z[-1] for z in sorted(suggestions, key=lambda x: x[0])]


def fuzzy_score(primer, item):
    start, pos, prev, score = -1, -1, -1, 1
    item_l = item.lower()
    for c in primer:
        pos = item_l.find(c)
        if pos == -1:
            return
        if start == -1:
            start = pos
            if pos == 0:
                score = -1  # match at the start of the word gets extra points

        if (
            pos > 0
            and (pc := item[pos - 1])
            and (
                pc in "_-"
                or pc.isupper() < item[pos].isupper()
            )
        ):
            # no penalty if we matched exactly the next char of a sub-word
            pass
        else:
            score += 2 * abs(pos - prev - 1)

        if score > 5:
            return
        prev = pos

    return (score, len(item))


def ldistinct(seq):
    """Iterates over sequence skipping duplicates"""
    seen = set()
    res = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            res.append(item)
    return res
