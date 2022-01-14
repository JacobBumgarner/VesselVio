
"""
Application stylesheets.
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


# Style Sheets
buttonstyle = """
    QPushButton{
        border: 1px solid rgb(217, 209, 207); 
        border-radius: 0.3em; 
        padding: 1px; 
        width: 60px; 
        color: black; 
        background: white;}
    QPushButton:pressed{
        border: none; 
        color: white; 
        background-color:rgb(42, 113, 227);}
    """


MenuBackground = "background: rgb(32, 34, 37)"


InfoPush = """
    QPushButton{
    font-size: 15px;
    font-weight: bold;
    color: white;
    border: 2px solid white;
    border-radius: 0.5em;
    }

    QPushButton:pressed{
    background-color: rgb(100,100,100);
    }
    """


MenuSheet = """
    QListWidget{
        color: rgb(220,220,220);
        font-size: 12px;
        font-weight: bold;
    }
    QListWidget::item:selected {
        background: rgb(75,75,75);
        color: white;
        border-left: 2px solid orange;
    }
    """


FilesSheet = """
    QTableWidget{
        border-right: none;
        border-bottom: 1px solid rgb(209, 209, 209);
    }
    QTableWidget::item:selected {
        background: rgb(75,75,75);
        color: white;
        border-left: 2px solid orange;
    }
    """


AnnotationTree = """
    QTreeWidget::branch:selected:open {
        background: rgb(75,75,75);
        image: Qt::RightArrow;
    }
    QTreeWidget::branch:selected:closed {
        background: rgb(75,75,75);
        image: Qt::RightArrow;
    }
    QTreeWidget::item:selected {
        background: rgb(75,75,75);
        color: white;
        border-left: 2px solid orange;
    }
    """


StatusSheet = """
    QListWidget{
        border-left: none;
    }
    QListWidget::item:selected {
        background: rgb(75,75,75);
        color: white;
    }
    """


