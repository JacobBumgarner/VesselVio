# -----------------------------------------------------------------------------
# Copyright (c) 2013, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------


from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files('pyexcelerate')
# import os
# from PyInstaller.utils.hooks import exec_statement

# template_path = exec_statement(
#     "from pyexcelerate.Writer import _TEMPLATE_PATH as tp; print tp"
# )

# datas = [(os.path.join(template_path, "*"), os.path.join("pyexcelerate", "templates"))];