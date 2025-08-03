# badapple-tensorboard

Bad apple played in Tensorboard scalars. Awful code hacked together, but pretty fun.

## Video (Flashing warning)

<video src="recording.mp4" controls width="600"></video>

## Installation

- Clone, cd in
- Install tensorboard
- `tar -xJf runs.tar.xz`
- `tensorboard --logdir runs`
- Paste the following in console

```
const i=document.querySelector('input[placeholder="Filter tags (regex)"]');let t=43;const e=()=>{if(t>6571)return;let n=`frame_${String(t).padStart(4,"0")}`;i.value=n,i.dispatchEvent(new Event("input",{bubbles:!0})),i.dispatchEvent(new Event("change",{bubbles:!0})),t+=10,setTimeout(e,200)};e();
```

Credit to https://github.com/Felixoofed/badapple-frames
