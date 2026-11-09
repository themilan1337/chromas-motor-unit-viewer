# What the viewer shows, in plain words

By Kamilya Mukh. All numbers come from `runs/within_between.txt`, and the code facts from `SPIKE.md`.

A chromatophore is a small pigment cell in cephalopod skin. CHROMAS cuts each one into thin radial slices and watches how the slices expand and shrink in the video. Then it pulls the movement apart into independent components. Think of each component as one "pattern of movement" inside a cell.

The question is which patterns belong together. If two patterns rise and fall at the same moments, they may be driven by the same motor neuron. CHROMAS measures this with one number for every pair of components: the absolute Pearson correlation, written |r|. It is 1 when the two time courses match exactly and 0 when they have nothing to do with each other. Components that group well form a cluster, and the lab reads a cluster as a putative motor unit.

This matters because you cannot put an electrode on every cell. The video is the only evidence for most of them, so it helps to see the evidence clearly.

## How to read the page

- The big picture is a frame of the video. The colored dots mark the chromatophores of the unit you picked in the table. Switch on "show the radial slices" to see which slices belong to it.
- The table lists the units. "chroms" is how many chromatophores a unit spans, "ICs" is how many components it holds, and the last columns summarise |r|.
- The wavy lines under the picture are the time courses of the unit's components, one line each. If a unit is a good one, you would expect the lines to move together.
- The square heat map is the |r| between every pair of the unit's components. The diagonal is always 1.00, because a component matches itself. Darker blue means a higher value. What we look for is a block of dark squares away from the diagonal.

## What the tutorial video gives

In the first chunk the pairs inside a cluster average 0.122, and pairs from different clusters average 0.052. The largest pair is 0.326. In the last chunk the numbers are 0.126, 0.052 and 0.501. Inside is higher than between, but nothing is close to 1. The chunks are short and only 8 to 11 chromatophores could be analysed, so we do not call these clusters motor units. They show that the pipeline and the viewer work. The real test needs a recording like the ones in the paper.
