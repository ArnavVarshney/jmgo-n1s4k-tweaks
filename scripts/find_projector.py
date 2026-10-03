#!/usr/bin/env python3
"""Find the JMGO projector on the LAN by sweeping port 5555.

Usage:
    python find_projector.py
    python find_projector.py --subnet 192.168.51.0/24
    python find_projector.py --subnet 192.168.1.0/24 --timeout 0.6

DHCP moves the projector IP, so run this whenever adb refuses to connect.
"""
import argparse
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor


def probe(ip, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((str(ip), 5555))
        s.close()
        return str(ip)
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subnet", default=None,
                    help="e.g. 192.168.51.0/24. Default: guess from local IP /24s")
    ap.add_argument("--timeout", type=float, default=0.5)
    ap.add_argument("--workers", type=int, default=64)
    args = ap.parse_args()

    nets = []
    if args.subnet:
        nets = [ipaddress.ip_network(args.subnet, strict=False)]
    else:
        # guess: hostname resolves to local IP, sweep its /24
        try:
            local = socket.gethostbyname(socket.gethostname())
            nets = [ipaddress.ip_network(local.rsplit(".", 1)[0] + ".0/24",
                                         strict=False)]
        except OSError:
            nets = [ipaddress.ip_network("192.168.1.0/24", strict=False)]
    print("sweeping:", ", ".join(str(n) for n in nets))
    found = []
    for net in nets:
        hosts = list(net.hosts())
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            for ip in ex.map(lambda h: probe(h, args.timeout), hosts):
                if ip:
                    found.append(ip)
                    print("FOUND:", ip + ":5555")
    if not found:
        print("nothing found on :5555. Check Wi-Fi / same subnet.")
    else:
        for ip in found:
            print("adb connect %s:5555" % ip)


if __name__ == "__main__":
    main()
