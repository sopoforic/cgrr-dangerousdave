dangerousdave
=============

This module extracts the EGA tiles from the DOS game Dangerous Dave by John
Romero.

Usage
=====

Verify that you have the supported version of the game:

```python
verify("path/to/dave") # Returns True or False
```

Extract the EGA tiles:

```python
tiles = extract_tiles("path/to/dave")
```

`tiles` is now a list of PIL `Image` objects.

License
=======

This module is available under the GPL v3 or later. See the file COPYING for
details.
