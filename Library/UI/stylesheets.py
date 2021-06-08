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

MenuSheet = """
    QListWidget{
        color: rgb(220,220,220);
        font-weight: bold;
    }
    QListWidget::item:selected {
        background: rgb(75,75,75);
        color: white;
        border-left: 2px solid orange;
    }
"""

FilesSheet = """
    QListWidget{
        border-right: none;
        border-bottom: 1px solid rgb(209, 209, 209);
    }
    QListWidget::item:selected {
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


