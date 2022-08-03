## Components
This an experimentation into an automated way to measure wait times at the Canada-USA border. Various functions are being developped in a modular fashion.
## Methodology
The proposed methodology for this experiment is to use the Google Maps API to estimate the wait times.

This is achieved by requesting directions from the Google Maps API service for a trip that starts approximately 1km from the border, on the USA side, with the destination being the CBSA port of entry.

The response provided includes both a "time in traffic" and "time without traffic", for our purposes, the difference between these two is assumed to be the wait time.