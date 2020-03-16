#!/usr/bin/env python
"""
Program to measure sky-line widths from sky-spectra.
"""
import numpy as np
import matplotlib.pyplot as plt
import argparse
import readline
import glob
try:
    from mh.spectra import Spectrum, spec_from_txt, model_from_txt
    from mh.spectra.spec_functions import sky_line_fwhm
except ImportError:
    try:
        from spectra import Spectrum, spec_from_txt, model_from_txt
        from spectra.spec_functions import sky_line_fwhm
    except ImportError:
        print("You do not have mh.spectra/spectra installed")

FLINES = "skyline_table.dat"
readline.parse_and_bind("tab: complete")

def _read_spectrum(fname, usevar):
    """
    Reads file into a spectrum given a file name"
    """
    try:
        try:
            S = spec_from_txt(fname, y_unit='')
            if usevar:
                S = Spectrum(S.x, S.var, 0.1*np.min(S.var))
            if np.allclose(S.e, 0, atol=1e-30):
                raise ValueError("File flux errors all zero")
        except IndexError:
            S = model_from_txt(fname)
            S.e = np.abs(0.1*np.min(S.y))
        return S
    except ValueError:  
        print(f"Could not parse file '{fname}'\n")
        input()
    except IOError:
        print(f"Could not find file '{fname}'\n")
        input()
    return None

def load_spectrum(items):
    """
    Menu for loading sky spectrum. Supports tab-completion for 
    inputting file names.
    """
    while True:
        print("load spectrum:")
        print("1) load sky spectrum")
        print("2) exit")
        opt = input(">>>")

        if opt == "":
            continue
        elif opt == "1":
            readline.set_completer(lambda txt, st: glob.glob(txt+'*')[st])
            print("filename:")
            fname = input(">>>")
            readline.set_completer(lambda : None)
            S = _read_spectrum(fname, items['usevar'])
            if S is not None:
                items['spec'] = S
                print()
                return
        elif opt == "2":
            print()
            return
        else:
            print(f"Cannot understand option '{opt}'")
            input()

def ID_lines(items):
    """
    Opens a plot to mark sky-emission lines for fitting.
    """
    if items['spec'] is None:
        print("No spectrum yet")
        input()
        return

    S = items['spec']
    lines = items['lines']

    def on_key(event):
        if event.key == 'w':
            xd = event.xdata
            on_key.coords.append(xd)
            print(f"{xd:9.3f}")
    on_key.coords = []

    print("Press 'w' to store line locations")
    fig = plt.figure(figsize=(8, 4.5))
    S.plot(c='grey', drawstyle='steps-mid')
    cid = fig.canvas.mpl_connect('key_press_event', on_key)
    if lines is not None:
        for x in lines:
            plt.axvline(x, c='r', ls=':')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Arbitrary flux")
    plt.ylim(0.5*np.abs(S.y.min()), 2*np.abs(S.y.max()))
    plt.semilogy()
    plt.tight_layout()
    plt.show()

    if len(on_key.coords) > 0:
        lnew = np.array(on_key.coords)
        L = lnew if lines is None else np.hstack((lines, lnew))
        idx = np.argsort(L)
        items['lines'] = L[idx].copy()

def run_fit(items):
    """
    Run the fit to the measured sky emission lines
    """
    S, lines, dX = items['spec'], items['lines'], items['dX']
    
    results = [sky_line_fwhm(S, x, dX, return_model=True) for x in lines]
    items['results'] = results
    x, y, ye = np.array([(x, *res['fwhm']) for x, (res, M) in \
                         zip(lines, results) if res is not None]).T
    poly = np.polyfit(x, y, w=1/ye, deg=items['deg'])
    items['polyfit'] = poly
    print(f"Fit to {len(items['lines'])} lines stored")
    input()

def plot_fit(items):
    """
    Show diagnostic plots from a completed fit
    """
    if items['polyfit'] is None:
        print("Need to run fit first")
        input()
        return
    S, lines, poly, results = [items[x] for x in "spec lines polyfit results".split()]
    S.plot(c='grey', drawstyle='steps-mid')
    for _, M in results:
        if M is not None:
            M.plot(c='C3')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Arbitrary flux")
    plt.ylim(0.5*np.abs(S.y.min()), 2*np.abs(S.y.max()))
    plt.semilogy()
    plt.tight_layout()
    plt.show()

    x, y, ye = np.array([(x, *res['fwhm']) for x, (res, M) in \
                         zip(lines, results) if res is not None]).T
    yfit = np.polyval(poly, S.x)

    plt.errorbar(x, y, ye,  fmt='k.')
    plt.plot(S.x, yfit, 'C3-')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Gaussian FWHM [\AA]")
    plt.tight_layout()
    plt.show()

    plt.errorbar(x, x/y, x/y**2*ye,  fmt='k.')
    plt.plot(S.x, S.x/yfit, 'C3-')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Resolving power")
    plt.tight_layout()
    plt.show()

def interpolate_fit(items):
    """
    Prompt user for a wavelength to interpolate the fit
    """
    if items['polyfit'] is None:
        print("Need to run fit first")
        input()
        return

    while True:
        print("Wavelength to interpolate:")
        try:
            usr = input(">>>")
            x = float(usr)
        except ValueError:
            print(f"Could not parse '{usr}'")
            input()
            continue

        if x in items['spec']:
            res = np.polyval(items['polyfit'], x)
            R = x/res
            print(f"resolution = {res:.3f} AA")
            print(f"resolving power = {R:.1f}")
            input()
            return 
        else:
            print(f"{x} out of bounds of spectrum wavelengths")
            input()
            
def update_dX(items):
    """
    Ask user to update the dX parameter
    """
    while True:
        print(f"New dX (currently: {items['dX']})")
        usr = input(">>>")
        if usr == "":
            continue
        try:
            newdX = float(usr)
        except ValueError:
            print(f"Could not parse '{usr}'")
            input()
            continue
        if newdX <= 0:
            print("New value must be positive")
            input()
            continue
        if newdX > 100:
            print(f"Max allowed value is 100 AA")
            input()
            continue
        items['dX'] = newdX
        print("Wavelength interval updated")
        input()
        return

def update_deg(items):
    """
    Ask user to update the deg parameter
    """
    while True:
        print(f"New polynomial order (currently: {items['deg']})")
        usr = input(">>>")
        if usr == "":
            continue
        try:
            newD = int(usr)
        except ValueError:
            print(f"Could not parse '{usr}'")
            input()
            continue
        if newD < 0:
            print("New value must be positive")
            input()
            continue
        if newD > 6:
            print(f"Max allowed value is 6")
            input()
            continue
        items['deg'] = newD
        print("polynomial order updated")
        input()
        return

def fit_lines(items):
    """
    Fits marked sky emission lines with Gaussian profile. The first
    plot shows these fits, with the second showing the fwhm as a
    function of wavelength, fitted with a polynomial.
    """
    if items['spec'] is None:
        print("No spectrum yet")
        input()
        return
    if items['lines'] is None:
        print("No lines yet")
        input()
        return

    if items['dX'] < 0:
        S = items['spec']
        items['dX'] = 6*np.mean(S.dx)

    while True:
        print("load spectrum:")
        print("1) run fit")
        print("2) plot fit")
        print("3) interpolate fit")
        print("4) change dX")
        print("5) change poly deg")
        print("6) exit")
        opt = input(">>>")

        if opt == '':
            continue
        elif opt == "1":
            run_fit(items)
        elif opt == "2":
            plot_fit(items)
        elif opt == "3":
            interpolate_fit(items)
        elif opt == "4":
            update_dX(items)
        elif opt == "5":
            update_deg(items)
        elif opt == "6":
            print()
            return
        else:
            print(f"Cannot understand option '{opt}'")
            input()

def _import_lines():
    """
    Internal function to read in file containing sky line wavelengths.
    """
    try:
        x = np.loadtxt(FLINES, dtype='float64')
        print(f"{len(x)} lines read from disk")
        input()
        return x
    except IOError:
        print(f"{FLINES} does not exist")
        input()
        return None
    except ValueError:
        print(f"Trouble reading {FLINES}")
        input()
        return None

def read_lines(items):
    """
    Read in previously saved lines from disk
    """
    items['lines'] = _import_lines()

def write_lines(items):
    """
    Write identified sky line wavelengths to disk
    """
    if items['lines'] is None:
        print("No lines yet")
        input()
        return

    with open(FLINES, 'w') as F:
        for x in items['lines']:
            F.write(f"{x:9.3f}\n")

    print(f"{len(items['lines'])} lines written to disk")
    input()

def remove_line(items):
    """
    Remove lines from line list one at a time
    """
    while True:
        for j, line in enumerate(items['lines'], 1):
            end = '\n' if j % 5 == 0 or j == len(items['lines']) else ''
            print(f"({j:2d}): {line:8.2f}, ", end=end)
        print("Line index to remove (0 to return):")
        opt = input(">>>")
        if opt == "0":
            print()
            return
        else:
            try:
                lines = items['lines']
                idx = int(opt)-1
                line = lines[idx]
                lines = np.delete(lines, idx)
                items['lines'] = lines
                print(f"Removed {line} from pos {opt}")
                input()
            except IndexError:
                print(f"No line at position {opt}")
            except ValueError:
                print("Could not parse input")

def clear_lines(items):
    """
    Remove all lines from linelist
    """
    print("CONFIRM to confirm:")
    opt = input(">>>")
    if opt == "CONFIRM":
        items['lines'] = None
        print("All lines cleared")
        input()
    else:
        print()

def edit_lines(items):
    """
    Submenu to remove problematic lines or completely clear the line list.
    """
    if items['lines'] is None:
        print("No lines yet")
        input()
        return

    while True:
        print("edit lines:")
        print("1) remove line")
        print("2) clear all lines")
        print("3) exit")
        opt = input(">>>")

        if opt == "":
            continue
        elif opt == "1":
            remove_line(items)
        elif opt == "2":
            clear_lines(items)
            if items['lines'] is None:
                return
        elif opt == "3":
            print()
            return
        else:
            print(f"Cannot understand option '{opt}'")
            input()

def quit(items):
    """
    Shuts down the program with confirmation prompt.
    """
    while True:
        print("Quit (y/n):")
        opt = input(">>>")
        if opt in ("y","Y"):
            exit()
        elif opt in ("n","N"):
            print()
            return
        else:
            print(f"Could not understand '{opt}'")
            input()

def menu(items):
    """
    Main program menu.
    """
    menu_options = {
        ""  : lambda x : None,
        "1" : load_spectrum,
        "2" : ID_lines,
        "3" : fit_lines,
        "4" : read_lines,
        "5" : write_lines,
        "6" : edit_lines,
        "7" : quit,
    }
        
    while True:
        print("FIT-SKYLINES")
        print("options:")
        print("1) load sky spectrum")
        print("2) ID lines")
        print("3) fit lines")
        print("4) read lines")
        print("5) write lines")
        print("6) edit lines")
        print("7) quit")

        opt = input(">>>")
        print()
        try:
            menu_options[opt](items)
        except KeyError:
            print(f"Cannot understand option '{opt}'")
            input()

def get_items():
    """
    Initial program set up. Parses command line arguments and 
    sets up 'items' dictionary.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("sky", nargs='?', type=str, default="",
                        help="File with sky spectrum")
    parser.add_argument("--readlines", dest='readlines', action='store_const',
                        const=True, default=False, help="read line list data")
    parser.add_argument("--usevar", dest='usevar', action='store_const', const=True,
                         default=False, help="Measure sky lines from flux variance")
    parser.add_argument("-dX", type=float, default=-1, help="half width of fit region")
    parser.add_argument("-deg", type=int, default=1, help="polynomial deg")
    args = parser.parse_args()

    spec = None if args.sky == "" else _read_spectrum(args.sky, args.usevar) 
    lines = _import_lines() if args.readlines else None

    items = {
        "spec" : spec,
        "lines": lines,
        "usevar" : args.usevar,
        "deg" : args.deg,
        "dX" : args.dX,
        "polyfit" : None,
        "results" : None,
    }
    return items

if __name__ == "__main__":
    items = get_items()
    menu(items)
