#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import argparse
try:
    from mh.spectra import spec_from_txt, model_from_txt
    from mh.spectra.spec_functions import sky_line_fwhm
except ImportError:
    try:
        from spectra import spec_from_txt, model_from_txt
        from spectra.spec_functions import sky_line_fwhm
    except ImportError:
        print("You do not have mh.spectra/spectra installed")

FLINES = "skyline_table.dat"

def read_spectrum(fname):
    try:
        try:
            S = spec_from_txt(fname, y_unit='')
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
    while True:
        print("load spectrum:")
        print("1) load sky spectrum")
        print("2) exit")
        opt = input(">>>")

        if opt == "1":
            print("filename:")
            fname = input(">>>")
            S = read_spectrum(fname)
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
    plt.tight_layout()
    plt.show()

    if len(on_key.coords) > 0:
        lnew = np.array(on_key.coords)
        L = lnew if lines is None else np.hstack((lines, lnew))
        idx = np.argsort(L)
        items['lines'] = L[idx].copy()

def fit_lines(items):
    if items['spec'] is None:
        print("No spectrum yet")
        input()
        return
    if items['lines'] is None:
        print("No lines yet")
        input()
        return

    S, lines, dx = [items[i] for i in "spec lines dX".split()]
    results = [sky_line_fwhm(S, x, dx, return_model=True) for x in lines]

    S.plot(c='grey', drawstyle='steps-mid')
    for _, M in results:
        if M is not None:
            M.plot(c='C3')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Arbitrary flux")
    plt.tight_layout()
    plt.show()

    x, y, ye = np.array([(x, *res['fwhm']) for x, (res, M) in zip(lines, results) \
                         if res is not None]).T

    poly = np.polyfit(x, y, w=1/ye, deg=items['deg'])
    yfit = np.polyval(poly, S.x)

    plt.errorbar(x, y, ye,  fmt='k.')
    plt.plot(S.x, yfit, 'C3-')
    plt.xlabel("Wavelength [\AA]")
    plt.ylabel("Gaussian FWHM [\AA]")
    plt.tight_layout()
    plt.show()

def import_lines():
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
    items['lines'] = import_lines()

def write_lines(items):
    if items['lines'] is None:
        print("No lines yet")
        input()
        return

    with open(FLINES, 'w') as F:
        for x in items['lines']:
            F.write(f"{x:9.3f}\n")

    print(f"{len(items['lines'])} lines written to disk")
    input()

def edit_lines(items):
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

        if opt == "1":
            while True:
                for j, line in enumerate(items['lines'], 1):
                    end = '\n' if j % 5 == 0 or j == len(items['lines']) else ''
                    print(f"({j:2d}): {line:8.2f}, ", end=end)
                print("Line index to remove (0 to return):")
                opt2 = input(">>>")
                if opt2 == "0":
                    print()
                    break
                else:
                    try:
                        lines = items['lines']
                        idx = int(opt2)-1
                        line = lines[idx]
                        lines = np.delete(lines, idx)
                        items['lines'] = lines
                        print(f"Removed {line} from pos {opt2}")
                        input()
                    except IndexError:
                        print(f"No line at position {opt}")
                    except ValueError:
                        print("Could not parse input")
        elif opt == "2":
                print("CONFIRM to confirm:")
                opt = input(">>>")
                if opt == "CONFIRM":
                    items['lines'] = None
                    print("All lines cleared")
                    input()
                    return
                else:
                    print()
        elif opt == "3":
            print()
            return
        else:
            print(f"Cannot understand option '{opt}'")
            input()
            

def quit(items):
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
    parser = argparse.ArgumentParser()
    parser.add_argument("sky", nargs='?', type=str, default="",
                        help="File with sky spectrum")
    parser.add_argument("--readlines", dest='readlines', action='store_const',
                        const=True, default=False, help="read line list data")
    parser.add_argument("-dX", type=float, default=5., help="half width of fit region")
    parser.add_argument("-deg", type=int, default=1, help="polynomial deg")
    args = parser.parse_args()

    spec = None if args.sky == "" else read_spectrum(args.sky) 
    lines = import_lines() if args.readlines else None

    items = {
        "spec" : spec,
        "lines": lines,
        "deg" : args.deg,
        "dX" : args.dX,
    }
    return items

if __name__ == "__main__":
    items = get_items()
    menu(items)
