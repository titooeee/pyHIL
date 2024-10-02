"""
Convert a log file from one format to another.
"""

import argparse
import errno
import sys

from can import Logger, LogReader, SizedRotatingLogger


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(errno.EINVAL, f"{self.prog}: error: {message}\n")

# inputFilePath  = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\absA_808.asc"
# outputFilePath = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\absA_808.mf4"


inputFilePath = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\dutCanA_317.asc"
outputFilePath = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\dutCanA_317.mf4"
dbcFile = r"G:\Shared drives\Engineering - Dyno Engine Test Data\Software\Temp\sharedfolder\dbc\dutdbc\maint_icd_CanA.dbc"

# inputFilePath = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\dutCanC_758.asc"
# outputFilePath = r"G:\Shared drives\Engineering - Dyno Engine Test Data\DataSharing\Viper Crash Log\ASC File\dutCanC_758.mf4"
# dbcFile = r"C:\Users\Public\Documents\sharedFolder\dbc\dutdbc\b-sampleDBC_HS\icd.dbc"


def main():
    
    with LogReader(filename=inputFilePath) as reader:
        logger = Logger(filename=outputFilePath,database = dbcFile, compression_level = 0)
        with logger:
            try:
                for m in reader:
                    logger(m)
            except KeyboardInterrupt:
                sys.exit(1)


if __name__ == "__main__":
    main()
