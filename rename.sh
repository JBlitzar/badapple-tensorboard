#!/bin/bash

# Find all files matching the pattern and rename them
find runs -name "events.out.tfevents.*.*.local.*.*" -type f | while read -r file; do
    # Get the directory of the file
    dir=$(dirname "$file")
    # Rename to .badapple.local in the same directory
    uuid=$(uuidgen)
    mv "$file" "$dir/events.out.tfevents.$uuid.badapple.local"
done