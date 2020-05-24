# phelng

> Batch-download music with metadata from Spotify &amp; audio from YouTube, using a .tsv file

Streaming services allow easy discovery of new music, but lock you, and prevents you from listening offline, DRM-free. Get the best of both worlds — online music services and offline music files — by downloading them using _phelng_.

## Features

This project is a work-in-progress, and is close to releasing a first working version.

- Your music library is contained in a single file using a [plain text, human-readable, intuitive, and universal file format](#library-file-format)
- YouTube videos' volume varies greatly, so audio files are normalized
- phelng has no config files, all configuration is done via CLI arguments, [just like nnn](https://github.com/jarun/nnn)
- If you use spotify, don't worry, you can [import your tracks](#import-your-tracks) from your playlists or your library (liked tracks)
- Each audio file is tagged with IDv3 metadata from Spotify, including but not limited to:
  - cover art
  - artist
  - album
  - track title
  - year of release
- The YouTube video is carefully selected by…
  - comparing the track duration from Spotify against the YouTube videos'
  - comparing release dates from Spotify and YouTube upload dates (TODO)
  - prefering official artist channels
- Multiple files can be downloaded in parallel (TODO)
- Provides options to throttle the network usage so you can use it in the background (TODO)

## Your music `library.tsv`

At first, I had the idea of using the simplest, most intuitive file format possible: a text file, each track a line, using the format `{artist} - {title}`.

But this has some caveats:

- **Artist names can't contain " - "**

  …which you think would never occur anyway, but with [the track titles that _Four Tet_ comes up with](https://open.spotify.com/album/6iFZ3Kcx8CDmcMNyKRqUwc?highlight=spotify:track:3bCs4oOGpM0KkVB78Laiqp), we should never underestimate the creativty sometimes displayed in titles.)
- **Additional information can't be added without restraining track titles**

  Some artists like to add "Intro" and/or "Outro" tracks to their albums, for example
  Imagine that an artist has two albums _A_ and _B_, each having an intro track named exactly _Intro_.
  If you want to download **_B_**'s _Intro_, you can't specify that.
  A new syntax could be introduced, something like `artist - track [album]` but, again, what if the track title contains an opening square bracket "["?

The solution: using a literal _tab character_ as an information separator.

And some people have already thought about that, so we have the bonus of using an already-existing language: the _tsv file format_, or tab-separated values. This also means that you can easily edit and view your library in any spreadsheet software.

The only caveat for this use case with tsv files is that there is no standard for comments. Comments could be useful in your library file to temporarily "deactivate" tracks and prevent them from being downloaded, or to serve as a header at the beginning of the file to help you remember the format.

Since we don't want to limit what characters artist names can contain, we can't use something like `# a comment` or `// another one`. As the two first field are _required_, Simply having a line that starts with a tab character gets ignored by _phelng_, and would otherwise mean that the column "artist" is undefined for this row.

<a id="library-file-format"></a>

Thus, the format (so far*) is (with `⭾` representing a tab character)

    ⭾A comment (ignored by phelng)
    Artist⭾Track title⭾Album (optional)⭾Duration (in seconds, optional)

*Additional fields could be added in the future, _without breaking backwards compatibility_, since the field's order will _always be preserved_.

## Why this name?

I was searching for a cool name by fooling around Google Translate, and stumbled upon "phelng", which is the Latin-transliterated version of "เพลง" – "music" in Thai.

On GitHub, I'm the only repository with this name for now, but on Google obviously searching for "phelng" pulls a lot of Thai websites. So tell your friends to search on GitHub! :)
