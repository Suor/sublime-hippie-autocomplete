# Hippie Autocompletion

Sublime Text 2/3 style auto completion for ST4: cycle through words, do not show popup. Simply hit `Tab` to insert completion, hit `Tab` again if you don't like it.

Features:

- fuzzy search
- supports multiple cursors
- prioritizes previously chosen completions
- current view words go before other views words

TODO:

- prefer matching first letters in combined_words
- prefer words closer to cursor?
- take into account scope/language word defined vs we are editing
- better support for multiple cursors, i.e. if primers differ
- obey `word_separators` setting to parse words
- `shift+tab` to cycle back? `backspace` to cancel?


Started from discussion [here](https://forum.sublimetext.com/t/st3-style-autocomplete-in-st4/57774) and based on sketch by **LightsOut8008**.
