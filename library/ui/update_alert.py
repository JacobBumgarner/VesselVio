"""
The current route to check for app updates. In the future, it may be worth looking at pyupdater
"""

__author__ = "Jacob Bumgarner <jrbumgarner@mix.wvu.edu>"
__license__ = "GPLv3 - GNU General Pulic License v3 (see LICENSE)"
__copyright__ = "Copyright 2022 by Jacob Bumgarner"
__webpage__ = "https://jacobbumgarner.github.io/VesselVio_Web/"
__download__ = "https://jacobbumgarner.github.io/VesselVio_Web/Downloads"


import http.client as httplib
import re
<<<<<<< Updated upstream
import urllib.request
=======
>>>>>>> Stashed changes

from library import helpers
from library.ui import qt_objects as QtO

from PyQt5.QtWidgets import QDialog, QLabel

#####################
### Version Check ###
#####################
# Check to see if there is an updated version of the app available. If so, point to the download site.

local_version = None


class updateAlert(QDialog):
    def __init__(self, local_version, current_version):
        super().__init__()
        layout = QtO.new_layout(self, "V")
        self.setWindowTitle("Version Update")

        URL = "https://jacobbumgarner.github.io/VesselVio/Downloads"

        message = QLabel(
            f"""<center>An updated version of VesselVio is available to download!<br><br>
                         <b>Your version:</b> {local_version}<br>
                         <b>Current version:</b> {current_version}<br><br>
                         You can download the update by clicking <u><a href={URL}>here</u></a>.<br>"""
        )
        message.setOpenExternalLinks(True)

        self.update_check = QtO.new_checkbox("Hide these updates in the future")
        okButton = QtO.new_button("Ok", self.accept)

        QtO.add_widgets(
            layout, [message, self.update_check, 5, [okButton, "Right"]], "Center"
        )

        self.window().setFixedSize(self.window().sizeHint())


# Thanks to Ivelin for the code
"""https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python"""


def internet_check():
    conn = httplib.HTTPSConnection("8.8.8.8", timeout=5)
    try:
        conn.request("HEAD", "/")
        return True
    except Exception:
        return False
    finally:
        conn.close()


def version_check():
    prefs = helpers.load_prefs()
    if not internet_check() or not prefs["update_check"]:
        return

    version_url = "https://jacobbumgarner.github.io/VesselVio/Version"
    with urllib.request.urlopen(version_url) as response:
        html = response.read()
        page = html.decode("utf8")
        result = re.findall(r"app_version==+\d.+\d.+\d", page)
        if result:
            current_version = result[0].split("==")[1]
            if current_version != local_version:
                alert = updateAlert(local_version, current_version)
                alert.exec_()
                if alert.update_check.isChecked():
                    helpers.silence_update_alerts()

    return
