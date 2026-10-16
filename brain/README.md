# brain/

The Python brain. It drives a **Heirloom body**, never a specific robot.

- `heirloom/body/base.py`: the body interface and the Heirloom channels.
- `heirloom/body/null_body.py`: no robot, prints commands.
- `heirloom/body/reachy_body.py`: Reachy Mini test body. The only file allowed to import `reachy_mini`.
- `scripts/hello_body.py`: a short greeting through any body.
- `cartridges/`: memory cartridges (see `docs/cartridge-format.md`).
- `expressions/`: Heirloom expression clips.
