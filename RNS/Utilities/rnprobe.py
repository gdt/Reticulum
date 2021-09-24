#!/usr/bin/env python3

import RNS
import os
import sys
import time
import argparse

from RNS._version import __version__

DEFAULT_PROBE_SIZE = 16

def program_setup(configdir, destination_hexhash, size=DEFAULT_PROBE_SIZE, full_name = None):
    if full_name == None:
        print("The full destination name including application name aspects must be specified for the destination")
        exit()
    
    try:
        app_name, aspects = RNS.Destination.app_and_aspects_from_name(full_name)

    except Exception as e:
        print(str(e))
        exit()

    try:
        dest_len = (RNS.Reticulum.TRUNCATED_HASHLENGTH//8)*2
        if len(destination_hexhash) != dest_len:
            raise ValueError("Destination length is invalid, must be {hex} hexadecimal characters ({byte} bytes).".format(hex=dest_len, byte=dest_len//2))
        try:
            destination_hash = bytes.fromhex(destination_hexhash)
        except Exception as e:
            raise ValueError("Invalid destination entered. Check your input.")
    except Exception as e:
        print(str(e))
        exit()


    reticulum = RNS.Reticulum(configdir = configdir)

    if not RNS.Transport.has_path(destination_hash):
        RNS.Transport.request_path(destination_hash)
        print("Path to "+RNS.prettyhexrep(destination_hash)+" requested  ", end=" ")
        sys.stdout.flush()

    i = 0
    syms = "⢄⢂⢁⡁⡈⡐⡠"
    while not RNS.Transport.has_path(destination_hash):
        time.sleep(0.1)
        print(("\b\b"+syms[i]+" "), end="")
        sys.stdout.flush()
        i = (i+1)%len(syms)

    server_identity = RNS.Identity.recall(destination_hash)

    request_destination = RNS.Destination(
        server_identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        app_name,
        *aspects
    )

    probe = RNS.Packet(request_destination, os.urandom(size))
    receipt = probe.send()

    print("\rSent "+str(size)+" byte probe to "+RNS.prettyhexrep(destination_hash)+" via "+RNS.prettyhexrep(RNS.Transport.next_hop(destination_hash))+" on "+str(RNS.Transport.next_hop_interface(destination_hash))+"  ", end=" ")

    i = 0
    while not receipt.status == RNS.PacketReceipt.DELIVERED:
        time.sleep(0.1)
        print(("\b\b"+syms[i]+" "), end="")
        sys.stdout.flush()
        i = (i+1)%len(syms)

    print("\b\b ")
    sys.stdout.flush()

    hops = str(RNS.Transport.hops_to(destination_hash))
    rtt = receipt.get_rtt()
    if (rtt >= 1):
        rtt = round(rtt, 3)
        rttstring = str(rtt)+" seconds"
    else:
        rtt = round(rtt*1000, 3)
        rttstring = str(rtt)+" milliseconds"

    print(
        "Valid reply received from "+
        RNS.prettyhexrep(receipt.destination.hash)+
        ", round-trip time is "+rttstring+
        " over "+hops+" hops"
    )

    

def main():
    try:
        parser = argparse.ArgumentParser(description="Reticulum Probe Utility")

        parser.add_argument("--config",
            action="store",
            default=None,
            help="path to alternative Reticulum config directory",
            type=str
        )

        parser.add_argument(
            "--version",
            action="version",
            version="rnpath {version}".format(version=__version__)
        )

        parser.add_argument(
            "full_name",
            nargs="?",
            default=None,
            help="full destination name in dotted notation",
            type=str
        )

        parser.add_argument(
            "destination_hash",
            nargs="?",
            default=None,
            help="hexadecimal hash of the destination",
            type=str
        )

        args = parser.parse_args()

        if args.config:
            configarg = args.config
        else:
            configarg = None

        if not args.destination_hash:
            print("")
            parser.print_help()
            print("")
        else:
            program_setup(
                configdir = configarg,
                destination_hexhash = args.destination_hash,
                full_name = args.full_name
            )

    except KeyboardInterrupt:
        print("")
        exit()

if __name__ == "__main__":
    main()