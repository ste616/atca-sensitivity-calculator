# atca-sensitivity-calculator
ATCA CABB sensitivity calculator, Python version

This is the new ATCA sensitivity calculator. This new version
was made in response to the old version providing very pessimistic
results at high frequency, which did not agree with real observations.
The new version is a complete re-write, with almost no code,
assumptions or quantities carried over from the previous calculator,
save for those that could be re-verified.

The new calculator can now take into account realistic weather
models and variables, correctly determine required integration
times from required sensitivities, and is fully commented with
references for each important equation used.

There is a stand-alone command line version, along with a web
interface for easier usage.

All questions regarding this calculator should be sent to
Jamie.Stevens@csiro.au.

