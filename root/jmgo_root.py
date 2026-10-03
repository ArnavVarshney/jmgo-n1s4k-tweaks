#!/usr/bin/env python3
"""
JMGO N1S 4K — One-Click Root
Run this script on your computer while the projector is connected via ADB.
It handles everything automatically: installs the exploit app, applies
the patches, reboots, and sets up root.

Requirements: Python 3.6+, ADB installed and in PATH.
Usage: python3 jmgo_root.py <PROJECTOR_IP>
"""
import subprocess, struct, sys, time, tempfile, base64, os

# ─── Embedded ExecCmd APK (base64) ───────────────────────────────
# This tiny app exploits JMGO's unprotected SettingService.execCommand()
# to run commands as the system user (uid 1000).
APK_B64 = (
"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"
)

# ─── Patch definitions ────────────────────────────────────────────
# Offsets within each FILE (same across firmware 1.1.31.x)
PATCHES = [
    {
        "name": "Security check #1 (jmgo_check_security)",
        "file": "/system/lib/libjmgosecury.so",
        "file_offset": 0xC5C,
        "expect": bytes([0x70, 0xB5, 0xAD, 0xF5]),
        "patch":  bytes([0x00, 0x20, 0x70, 0x47]),
    },
    {
        "name": "Security check #2 (encrypt_code)",
        "file": "/system/lib/libjmgosecury.so",
        "file_offset": 0xBEC,
        "expect": bytes([0xB0, 0xB5, 0x86, 0xB0]),
        "patch":  bytes([0x00, 0x20, 0x70, 0x47]),
    },
    {
        "name": "Boot flag bypass (jsu BNE→NOP)",
        "file": "/system/xbin/jsu",
        "file_offset": 0xE88,
        "expect": bytes([0x15, 0xD1]),
        "patch":  bytes([0x00, 0xBF]),
    },
]


def run(cmd, check=False):
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    return r

def adb(*args, device=None):
    cmd = ["adb"]
    if device:
        cmd += ["-s", device]
    cmd += list(args)
    r = run(cmd)
    return r.stdout

def sh(command, device=None):
    return adb("shell", command, device=device).decode("utf-8", errors="replace").strip()

def sh_bytes(command, device=None):
    return adb("shell", command, device=device)

def die(msg):
    print(f"\n  ERROR: {msg}")
    sys.exit(1)

def ok(msg):
    print(f"  OK — {msg}")

def step(n, msg):
    print(f"\n{'='*50}")
    print(f"  STEP {n}: {msg}")
    print(f"{'='*50}")


def connect(ip):
    """Connect to the projector and return the device string."""
    device = f"{ip}:5555"
    print(f"\n  Connecting to {device}...")
    adb("connect", device)
    time.sleep(2)

    uid = sh("id", device=device)
    if "uid=2000" not in uid:
        die(f"Connection failed. Got: {uid}")

    model = sh("getprop ro.product.model", device=device)
    fw = sh("getprop ro.build.version.incremental", device=device)
    ok(f"Connected to {model} (firmware {fw})")
    return device


def install_apk(device):
    """Install the ExecCmd exploit APK."""
    # Check if already installed
    check = sh("pm list packages com.exec.cmd", device=device)
    if "com.exec.cmd" in check:
        ok("ExecCmd already installed")
        return

    print("  Installing ExecCmd app...")
    # Use the pre-built APK (the embedded base64 was corrupted)
    apk_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apk-build", "execmd.apk")
    if not os.path.exists(apk_path):
        die(f"APK not found: {apk_path}\n"
            "Rebuild it from apk-source/ using the build instructions.")

    result = adb("install", apk_path, device=device).decode()
    if "Success" in result:
        ok("ExecCmd installed")
    else:
        die(f"APK install failed: {result}")


def execmd(command, device):
    """Run a command as system user (uid 1000) via ExecCmd."""
    sh(f"am start -n com.exec.cmd/.MainActivity -e cmd '{command}'", device=device)
    time.sleep(2)


def chmod_device(path, device):
    """Use JMGO's property trigger to chmod+chown a path as root."""
    sh(f"setprop vendor.jmgo.hal.change.permission {path}", device=device)
    time.sleep(0.5)


def read_raw(dev, offset, count, device):
    """Read bytes from a block device on the projector."""
    # NOTE: must use `exec-out` (not `shell`): `adb shell` mangles binary
    # output (0x0A -> 0x0D 0x0A), corrupting struct parsing. exec-out is raw.
    # Use 4K blocks for speed (bs=1 byte-at-a-time is far too slow).
    BS = 4096
    skip_blocks = offset // BS
    skip_within = offset % BS
    nblocks = (skip_within + count + BS - 1) // BS
    out = adb("exec-out",
              f"dd if={dev} bs={BS} skip={skip_blocks} count={nblocks} 2>/dev/null",
              device=device)
    return out[skip_within:skip_within + count]


def find_block(device, filepath, sb):
    """Find the first physical ext4 block of a file on dm-0."""
    inode_num = int(sh(f"stat -c %i {filepath}", device=device))
    bpg = sb["inodes_per_group"]
    bsz = sb["block_size"]
    isz = sb["inode_size"]

    bg = (inode_num - 1) // bpg
    local_idx = (inode_num - 1) % bpg

    # Group descriptor table at block 1
    gd = read_raw("/dev/block/dm-0", bsz + bg * 32, 32, device)
    inode_table_block = struct.unpack_from("<I", gd, 8)[0]

    # Read inode
    inode = read_raw("/dev/block/dm-0", inode_table_block * bsz + local_idx * isz, isz, device)

    # Parse extent header
    magic = struct.unpack_from("<H", inode, 40)[0]
    if magic != 0xF30A:
        die(f"Bad extent magic for {filepath}: {magic:#x}")

    depth = struct.unpack_from("<H", inode, 46)[0]
    if depth != 0:
        die(f"Multi-level extent tree in {filepath} — not supported")

    # First extent → physical block
    ee_hi = struct.unpack_from("<H", inode, 58)[0]
    ee_lo = struct.unpack_from("<I", inode, 60)[0]
    return (ee_hi << 32) | ee_lo


def find_system_offset(device):
    """Parse LP metadata to find the system partition's byte offset in mmcblk0p22."""
    geo = read_raw("/dev/block/mmcblk0p22", 4096, 128, device)
    magic = struct.unpack_from("<I", geo, 0)[0]
    if magic != 0x616c4467:
        die(f"Bad LP geometry magic: {magic:#x}")

    # LP layout: reserved (4096) + primary geometry (4096) + backup geometry (4096) = 12288
    meta_offset = 12288
    hdr = read_raw("/dev/block/mmcblk0p22", meta_offset, 256, device)

    hdr_magic = struct.unpack_from("<I", hdr, 0)[0]
    if hdr_magic != 0x414c5030:
        die(f"Bad LP metadata magic: {hdr_magic:#x}")

    hdr_size = struct.unpack_from("<I", hdr, 8)[0]

    # Partition table descriptor at header offset 0x50
    p_off  = struct.unpack_from("<I", hdr, 0x50)[0]
    p_cnt  = struct.unpack_from("<I", hdr, 0x54)[0]
    p_size = struct.unpack_from("<I", hdr, 0x58)[0]

    # Extent table descriptor at header offset 0x5C
    e_off  = struct.unpack_from("<I", hdr, 0x5C)[0]
    e_cnt  = struct.unpack_from("<I", hdr, 0x60)[0]
    e_size = struct.unpack_from("<I", hdr, 0x64)[0]

    tables_base = meta_offset + hdr_size
    parts = read_raw("/dev/block/mmcblk0p22", tables_base + p_off, p_cnt * p_size, device)
    exts  = read_raw("/dev/block/mmcblk0p22", tables_base + e_off, e_cnt * e_size, device)

    for i in range(p_cnt):
        ent = parts[i * p_size:(i+1) * p_size]
        name = ent[0:36].split(b'\x00')[0].decode()
        if name == "system":
            ext_idx = struct.unpack_from("<I", ent, 40)[0]
            ext = exts[ext_idx * e_size:(ext_idx+1) * e_size]
            sector = struct.unpack_from("<I", ext, 12)[0]
            return sector * 512

    die("'system' partition not found in LP metadata")


def apply_patches(device):
    """Find offsets and apply all three patches."""
    # Open block devices
    print("  Opening block devices...")
    chmod_device("/dev/block/dm-0", device)
    chmod_device("/dev/block/mmcblk0p22", device)

    # Read ext4 superblock
    print("  Reading filesystem layout...")
    sb_raw = read_raw("/dev/block/dm-0", 1024, 256, device)
    sb = {
        "block_size": 1024 << struct.unpack_from("<I", sb_raw, 24)[0],
        "blocks_per_group": struct.unpack_from("<I", sb_raw, 32)[0],
        "inodes_per_group": struct.unpack_from("<I", sb_raw, 40)[0],
        "inode_size": struct.unpack_from("<H", sb_raw, 88)[0],
    }

    # Find system partition offset
    sys_offset = find_system_offset(device)
    print(f"  System partition at byte {sys_offset} in super partition")

    # Find file blocks
    blocks = {}
    for p in PATCHES:
        f = p["file"]
        if f not in blocks:
            blocks[f] = find_block(device, f, sb)
            print(f"  {os.path.basename(f)} at ext4 block {blocks[f]}")

    # Calculate and verify each patch
    bsz = sb["block_size"]
    need_patch = []

    for p in PATCHES:
        absolute = sys_offset + blocks[p["file"]] * bsz + p["file_offset"]
        p["absolute"] = absolute
        current = read_raw("/dev/block/mmcblk0p22", absolute, len(p["expect"]), device)
        cur_hex = " ".join(f"{b:02x}" for b in current)

        if current == p["patch"]:
            print(f"  {p['name']}: already patched")
        elif current == p["expect"]:
            print(f"  {p['name']}: ready ({cur_hex})")
            need_patch.append(p)
        else:
            exp_hex = " ".join(f"{b:02x}" for b in p["expect"])
            die(f"{p['name']}: unexpected bytes!\n"
                f"    Expected: {exp_hex}\n"
                f"    Found:    {cur_hex}\n"
                f"    Your firmware may be a different version.")

    if not need_patch:
        ok("All patches already applied!")
        return True

    # Apply patches via ExecCmd (system user)
    print(f"\n  Applying {len(need_patch)} patch(es)...")
    for p in need_patch:
        hex_str = "".join(f"\\x{b:02x}" for b in p["patch"])
        bin_file = f"/sdcard/_patch_{id(p)}.bin"
        log_file = f"/sdcard/_patch_{id(p)}.log"

        sh(f"printf '{hex_str}' > {bin_file}", device=device)

        script = (
            f"#!/system/bin/sh\n"
            f"exec > {log_file} 2>&1\n"
            f"dd if={bin_file} of=/dev/block/mmcblk0p22 "
            f"bs=1 seek={p['absolute']} count={len(p['patch'])} conv=notrunc\n"
            f"echo EXIT:$?\nsync\n"
        )
        script_file = f"/sdcard/_dopatch_{id(p)}.sh"
        sh(f"printf '%s' '{script}' > {script_file}", device=device)

        execmd(f"sh {script_file}", device)

        log = sh(f"cat {log_file}", device=device)
        if "EXIT:0" not in log:
            die(f"Patch failed for {p['name']}: {log}")

        # Verify
        verify = read_raw("/dev/block/mmcblk0p22", p["absolute"], len(p["patch"]), device)
        if verify != p["patch"]:
            die(f"Verify failed for {p['name']}")

        ok(p["name"])

        # Cleanup temp files
        sh(f"rm {bin_file} {log_file} {script_file}", device=device)

    return True


def install_su(device):
    """Create a convenience su wrapper on the system partition."""
    sh("/system/xbin/jsu --key x root blockdev --setrw /dev/block/dm-0", device=device)
    sh("/system/xbin/jsu --key x root mount -o rw,remount /", device=device)
    sh('/system/xbin/jsu --key x root sh -c \''
       'printf "#!/system/bin/sh\\nexec /system/xbin/jsu --key x root \\"\\$@\\"\\n"'
       ' > /system/xbin/su && chmod 755 /system/xbin/su\'', device=device)

    result = sh("su id", device=device)
    if "uid=0" in result:
        ok("su wrapper installed — use 'su <command>' for root")
    else:
        print("  su wrapper may not have installed correctly.")
        print("  You can still use: jsu --key x root <command>")


def main():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║   JMGO N1S 4K — One-Click Root       ║")
    print("  ╚══════════════════════════════════════╝")

    if len(sys.argv) < 2:
        print("\n  Usage: python3 jmgo_root.py <PROJECTOR_IP>")
        print("  Example: python3 jmgo_root.py 192.168.1.50")
        print("\n  Find your projector's IP: open File Manager on the projector,")
        print("  go to lan share — the IP is shown in the top-right corner.")
        sys.exit(1)

    ip = sys.argv[1]

    # ── Step 1: Connect ──
    step(1, "CONNECT")
    device = connect(ip)

    # ── Step 2: Install exploit app ──
    step(2, "INSTALL EXPLOIT APP")
    install_apk(device)

    # ── Step 3: Back up ──
    step(3, "BACK UP")
    print("  Backing up critical partitions...")
    chmod_device("/dev/block/mmcblk0p23", device)
    sh("dd if=/dev/block/mmcblk0p23 of=/sdcard/jmgoenv_backup.img 2>/dev/null", device=device)
    adb("pull", "/sdcard/jmgoenv_backup.img", ".", device=device)
    ok("jmgoenv_backup.img saved to current directory")

    # ── Step 4: Patch ──
    step(4, "PATCH")
    apply_patches(device)

    # ── Step 5: Reboot & verify ──
    step(5, "REBOOT & VERIFY")
    print("  Rebooting projector...")
    sh("reboot", device=device)
    time.sleep(15)

    print("  Waiting for projector to come back...")
    for attempt in range(40):
        try:
            adb("connect", device)
            time.sleep(2)
            result = sh("/system/xbin/jsu --key x root id", device=device)
            if "uid=0(root)" in result:
                print()
                print("  ╔══════════════════════════════════════╗")
                print("  ║         ROOT ACCESS ACHIEVED!        ║")
                print("  ╚══════════════════════════════════════╝")
                print(f"\n  {result}")
                break
        except Exception:
            pass
        time.sleep(5)
    else:
        die("Projector didn't come back after reboot. "
            "Try reconnecting manually: adb connect " + device)

    # ── Step 6: Install su shortcut ──
    step(6, "INSTALL SU SHORTCUT")
    install_su(device)

    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║              ALL DONE!               ║")
    print("  ╠══════════════════════════════════════╣")
    print("  ║  Root persists across reboots.       ║")
    print("  ║  Use: adb shell su <command>         ║")
    print("  ║  Or:  adb shell su   (root shell)    ║")
    print("  ╚══════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
