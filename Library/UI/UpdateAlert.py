

import socket
import urllib.request
import re

from PyQt5.Qt import pyqtSlot
from PyQt5.QtWidgets import QDialog, QLabel

from Library.UI import QtObjects as QtO
from Library import helpers

#####################
### Version Check ###
#####################
# Check to see if there is an updated version of the app available. If so, point to the download site.

local_version = None

class updateAlert(QDialog):
    def __init__(self, current_version, local_version):
        super().__init__()
        layout = QtO.new_layout(self, 'V')
        self.setWindowTitle("Version Update")
        
        URL = "https://jacobbumgarner.github.io/VesselVio_Web/Downloads"
        
        message = QLabel(f"""<center>An updated version of VesselVio is available to download!<br><br>
                         <b>Current version:</b> {current_version}<br>
                         <b>Your version:</b> {local_version}<br><br>
                         You can download the update by clicking <u><a href={URL}>here</u></a>.<br>""")
        message.setOpenExternalLinks(True)
        
        self.update_check = QtO.new_checkbox("Hide these updates in the future")
        okButton = QtO.new_button("Ok", self.accept)
        
        QtO.add_widgets(layout, [message, self.update_check, 5, [okButton, 'Right']], 'Center')
        
        self.window().setFixedSize(self.window().sizeHint())
        
        
# Thanks to 7h3rAM for the code
"""https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python"""
def internet_check(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

def version_check():
    prefs = helpers.load_prefs()
    if not internet_check() or not prefs['update_check']:
        return

    version_url = "https://jacobbumgarner.github.io/VesselVio_Web/Version"
    with urllib.request.urlopen(version_url) as response:
        html = response.read()
        page = html.decode('utf8')
        result = re.findall(r'app_version==+\d.+\d.+\d', page)
        if result:
            current_version = result[0].split('==')[1]
            if current_version != local_version:
                alert = updateAlert(local_version, current_version)
                alert.exec_()
                if alert.update_check.isChecked():
                    helpers.silence_update_alerts()
                
    return
