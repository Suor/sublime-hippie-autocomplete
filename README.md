# Hippie Autocompletion

Sublime Text 2/3 style auto completion for ST4: cycle through words, do not show popup. Simply hit `Tab` to insert completion, hit `Tab` again if you don't like it.

Features:

- fuzzy search
- current view words go first

TODO:

- prefer matching first letters in combined_words
- prioritize previously chosen completions
- support multiple cursors
- prefer words closer to cursor?
- take into account scope/language word defined vs we are editing
- obey `word_separators` setting to parse words
- `shift+tab` to cycle back? `backspace` to cancel?


Started from discussion [here](https://forum.sublimetext.com/t/st3-style-autocomplete-in-st4/57774) and based on sketch by **LightsOut8008**.
