import pathlib
import os
import subprocess
import json
import urllib.request
import wget
import zipfile
import tarfile
import shutil
import argparse
import sys

GITHUB_REPO = "m2aia/m2aia"


def get_release_assets(version: str = "latest") -> tuple[str, list]:
    """Return (tag_name, assets) for a GitHub release.

    Pass version='latest' to resolve the most recent release automatically,
    or a specific tag such as 'v2025.07' to pin a version.
    """
    if version == "latest":
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    else:
        tag = version if version.startswith("v") else f"v{version}"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["tag_name"], data["assets"]


def find_asset_url(assets: list, keyword: str, ext: str) -> str:
    for asset in assets:
        name = asset["name"].lower()
        if keyword in name and name.endswith(ext):
            return asset["browser_download_url"]
    raise RuntimeError(f"No release asset matching '{keyword}' + '{ext}' found in: {[a['name'] for a in assets]}")

def prepare():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--target", default="install_binaries")
    parser.add_argument("-l","--linux-archive", default="linux.tar.gz")
    parser.add_argument("-w","--windows-archive", default="windows.zip")
    parser.add_argument("-v","--version",default="latest",
                        help="GitHub release tag (e.g. 'v2025.07') or 'latest'")
    parser.add_argument("-d","--download", action="store_true")
    parser.add_argument("--linux", action="store_true")
    parser.add_argument("--windows", action="store_true")
    args = parser.parse_args()

    binaries_root=pathlib.Path("src/m2aia/bin/")
    # clean binaries
    shutil.rmtree(binaries_root, ignore_errors=True)
    binaries_root.mkdir(exist_ok=True)
    
    # ---------------------------------------------------------------
    if args.linux:
        linux_archive = pathlib.Path(args.linux_archive)
        if args.download:
            tag, assets = get_release_assets(args.version)
            url = find_asset_url(assets, "ubuntu", ".tar.gz")
            print(f"Downloading {tag}: {url}")
            if linux_archive.exists():
                os.remove(linux_archive)
            wget.download(url, str(linux_archive))

        if linux_archive.exists():
            linux_extracted = pathlib.Path(args.target) / pathlib.Path("linux")
            shutil.rmtree(linux_extracted, ignore_errors=True)
            with tarfile.open(str(linux_archive)) as f:
                f.extractall(str(linux_extracted))
            linux_root = list(linux_extracted.glob("M2aia*"))[0]
            m2aia_bin = linux_root.joinpath("bin")

            # Collect libM2aiaCore.so and all M2aia-bundled transitive deps via ldd.
            # auditwheel will later rewrite RPATHs and pull in any remaining non-system libs.
            env = os.environ.copy()
            env["LD_LIBRARY_PATH"] = str(m2aia_bin)
            ldd_out = subprocess.check_output(
                ["ldd", str(m2aia_bin / "libM2aiaCore.so")],
                env=env, universal_newlines=True
            )
            deps_to_copy = {str(m2aia_bin / "libM2aiaCore.so")}
            for line in ldd_out.splitlines():
                if "=>" in line:
                    resolved = line.split("=>")[1].strip().split()[0]
                    if resolved.startswith(str(m2aia_bin)):
                        deps_to_copy.add(resolved)

            for dep in sorted(deps_to_copy):
                dest = binaries_root / pathlib.Path(dep).name
                print(dep, "->", dest)
                shutil.copy(dep, str(dest))

            # Set RPATH to $ORIGIN on every bundled .so so they find siblings
            # in the same directory without needing LD_LIBRARY_PATH at runtime.
            for so in binaries_root.glob("*.so*"):
                subprocess.run(
                    ["patchelf", "--set-rpath", "$ORIGIN", str(so)],
                    check=True
                )
        else:
            print("Linux Archive not found!")
            
    # ---------------------------------------------------------------
    if args.windows:
        windows_archive = pathlib.Path(args.windows_archive)
        if args.download:
            tag, assets = get_release_assets(args.version)
            url = find_asset_url(assets, "windows", ".zip")
            print(f"Downloading {tag}: {url}")
            if windows_archive.exists():
                os.remove(windows_archive)
            wget.download(url, str(windows_archive))

        if windows_archive.exists():
            windows_extracted = pathlib.Path(args.target) / pathlib.Path("windows")
            shutil.rmtree(windows_extracted, ignore_errors=True)
            with zipfile.ZipFile(str(windows_archive)) as f:
                f.extractall(str(windows_extracted))
            windows_root=list(windows_extracted.glob("M2aia*"))[0]
            os.environ["M2AIA_PATH"] = str(windows_root.joinpath("bin").absolute())
            
            globs = [f for f in windows_root.joinpath('bin').glob("*.dll")]
            for lib in globs:
                if "Qt5" in str(lib):
                    print("FOUND => ", lib)
                    continue
                print(str(lib), "->", str(binaries_root.joinpath(lib.name)))
                shutil.copy(str(lib),str(binaries_root.joinpath(lib.name)))
        else:
            print("Windows Archive not found!")
            


if __name__ == '__main__':
    prepare()