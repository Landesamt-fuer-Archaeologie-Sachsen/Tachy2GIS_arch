import os, sys, glob
this_dir = os.path.dirname(os.path.realpath(__file__))
wheel_paths = [os.path.join(this_dir, wheel) for wheel in glob.glob("libs/*.whl")]
sys.path += wheel_paths

import tachyconnect

if __name__ == "__main__":
    print(sys.path)