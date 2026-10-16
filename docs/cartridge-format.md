# Cartridge format (v0)

A cartridge is a folder (later, a USB drive in a cassette shell). Any computer can read it.

```
cartridge/
  personality.json   what it has learned, one layer per owner
  journal/           photos (JPEG), named by date and time
  journal.json       entry list: file, date, owner, caption (optional)
```

- Personality and journal are separate so transfer can be tested with or without photos.
- Open formats only. No robot-specific data.
- `format_version` increases when the format changes. Old versions must stay readable.
