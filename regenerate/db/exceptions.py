#
# Manage registers in a hardware design
#
# Copyright (C) 2008  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Provides the exceptions for reporting and handling I/O.

Custom extensions for reporting error when reading/writing regenerate
files. File names are stored, so it can be determined which of the files
caused the issue.

"""


class CorruptProjectFile(Exception):
    """
    Syntax error in the project file.

    Reported when an error parsing the file occurs.

    """

    def __init__(self, filename: str, text: str):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            text (str): message

        """
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self) -> str:
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"{self.filename} is corrupt\n{self.msg}"


class CorruptBlockFile(Exception):
    """
    Syntax error in the block file.

    Reported when an error parsing the file occurs.

    """

    def __init__(self, filename: str, text: str):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            text (str): message

        """
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self):
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"{self.filename} is corrupt\n{self.msg}"


class CorruptRegsetFile(Exception):
    """
    Syntax error in the register set file.

    Reported when an error parsing the file occurs.

    """

    def __init__(self, filename: str, text: str):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            text (str): message

        """
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self):
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"{self.filename} is corrupt\n{self.msg}"


class IoErrorProjectFile(Exception):
    """
    I/O Error accessing the project file.

    Reported when an I/O error occurs while attempting to access the file.

    """

    def __init__(self, filename: str, error: OSError):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            error (OSError): exception that triggered the problem

        """
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"Error accessing {self.filename}: {self.error.strerror}"


class IoErrorBlockFile(Exception):
    """
    I/O Error accessing the block file.

    Reported when an I/O error occurs while attempting to access the file.

    """

    def __init__(self, filename: str, error: OSError):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            error (OSError): exception that triggered the problem

        """
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"Error accessing {self.filename}: {self.error.strerror}"


class IoErrorRegsetFile(Exception):
    """
    I/O Error accessing the register set file.

    Reported when an I/O error occurs while attempting to access the file.

    """

    def __init__(self, filename: str, error: OSError):
        """
        Create the exception.

        Parameters:
            filename (str): file where the error occurred
            error (OSError): exception that triggered the problem

        """
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        """
        Return a message describing the exception.

        Returns:
            str: message describing the problem

        """
        return f"Error accessing {self.filename}: {self.error.strerror}"
