#! /usr/bin/env python3
import anatomy
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="mprage_recon-all: runs modified FreeSurfer recon-all pipeline on MPRAGE data "
    )
    parser.add_argument(
        "--mprage", type=str, help="path to nifti file containing MPRAGE data"
    )
    parser.add_argument(
            "--skull-strip", type=str, choices=['synthstrip', 'cat12'], required=True,
            help="choose the skull stripping method: 'synthstrip' or 'cat12'"
        )

    args = parser.parse_args()

    anatomy.mprage_recon_all(
        mprage_file = args.mprage, 
        skull_strip_method = args.skull_strip
    )
