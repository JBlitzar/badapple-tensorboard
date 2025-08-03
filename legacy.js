const input = document.querySelector(
  'input[placeholder="Filter tags (regex)"]'
);

let i = 43;
const max = 6571;
const delayMs = 200;

const typeNext = () => {
  if (i > max) return;

  const padded = String(i).padStart(4, "0");
  const value = `frame_${padded}`;

  input.value = value;

  // Fire input and change events
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));

  i++;
  setTimeout(typeNext, delayMs);
};

typeNext();
