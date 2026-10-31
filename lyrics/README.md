# Your lyrics

Put your own lyric files here as plain text (UTF-8), one file per song, for example
`lyrics/my_song.txt`. See `example_song.txt` for the format.

Use them with:

    python run_all.py song --request "A romantic Bollywood song with strings, flute and choir" --lyrics lyrics/my_song.txt

Or let the free open model write lyrics (saved in `lyrics/generated/`):

    python run_all.py song --request "..." --write-lyrics --language Hindi --theme "first rain"

Only Suno (optional, paid) sings the words. With the open models, the lyrics are saved with
the song and voices sing wordless lines.
