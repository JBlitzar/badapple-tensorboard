# badapple-tensorboard

Bad apple video played in Tensorboard scalar plots. Awful code hacked together, but pretty fun.

Is the main demo a video? Yes. Can users also play around by making their own video or looking at in the tensorboard gui? Also yes.

## Video (Flashing warning)

https://github.com/user-attachments/assets/a93e870e-036a-481c-bcf5-1068eb4c8b73

## Installation (to produce the demo video)

- Clone, cd in
- `uv sync`
- Install tensorboard
- `tar -xJf runs.tar.xz`
- `tensorboard --logdir runs`
- Run `screenshotter.py`

## To play around in tensorboard

- Clone, cd in
- Install tensorboard
- `tar -xJf runs.tar.xz`
- `tensorboard --logdir runs`
- Search for numbers and you'll see that number frame.

## I want to make this for my own video!

- Clone, cd in
- `uv sync`
- Get a video that's only black and white silhouettes. Set it as video.mp4 in `frames/`
- `cd frames; rm *.png; ffmpeg -i video.mp4 -r 30 output_%04d.jpg`
- `uv run oneframe_plt.py`
- `uv run tensorboard --logdir runs &`
- `uv run screenshotter.py`

Enjoy your tensorboard video!

Credit to https://github.com/Felixoofed/badapple-frames

<!--Listen so I did this before I started tracking stuff with Hackatime, but I still think it's a fun thing to upload and share with the world. So they require five minutes. I'll write this and perhaps spend some time tiding up the scripts. Although the main deliverable is a non-interactive video anyways, so maybe this doesn't qualify for SOM. We'll see.-->
