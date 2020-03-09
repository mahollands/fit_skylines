# fit-skylines
A tool for quickly selecting skylines in a sky-spectrum and then performing 
a wavelength dependent fit.

### Dependencies
* Python >= 3.6
* Usual data-analysis modules (numpy, scipy, matplotlib)
* mh.spectra -- another repo of mine for working with astrophysical spectra

### Basic usage
To start without any spectrum loaded
```
fit_skylines
```
or
```
fit_skylines my_spectrum.dat
```
to read from a text file containing a spectrum.

If you have already written some lines to disk and
want to reload them
```
fit_skylines --readlines

Other options are available for the skyline box width
and polynomial order.

Description of all options
fit_skylines -h/--help
