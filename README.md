# badapple-tensorboard

```
const i=document.querySelector('input[placeholder="Filter tags (regex)"]');let t=43;const e=()=>{if(t>6571)return;let n=`frame_${String(t).padStart(4,"0")}`;i.value=n,i.dispatchEvent(new Event("input",{bubbles:!0})),i.dispatchEvent(new Event("change",{bubbles:!0})),t++,setTimeout(e,200)};e();
```
