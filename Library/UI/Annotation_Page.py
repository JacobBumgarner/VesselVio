
"""
The PyQt5 code used to build the annotation processing page for the program.
"""

__author__    = 'Jacob Bumgarner <jrbumgarner@mix.wvu.edu>'
__license__   = 'GPLv3 - GNU General Pulic License v3 (see LICENSE)'
__copyright__ = 'Copyright 2022 by Jacob Bumgarner'
__webpage__   = 'https://jacobbumgarner.github.io/VesselVio/'
__download__  = 'https://jacobbumgarner.github.io/VesselVio/Downloads'


import sys, os
import json

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QWidget, QMainWindow,  QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit, QCompleter, QLabel, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QDialog, QGroupBox, QFileDialog, QPushButton, QMessageBox, QAbstractItemView)

from library import helpers
from library import annotation_processing as AnProc
from library.ui import qt_objects as QtO
from library.ui import stylesheets as Styles


class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Annotation Testing")
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        layout = QtO.new_layout(None, 'H', True, 'None')
        self.centralWidget.setLayout(layout)
        
        annotationpage = AnnotationPage()
        
        layout.addWidget(annotationpage)
        
        self.show()
         

# Page organized into four columns
class AnnotationPage(QWidget):
    def __init__(self):
        super().__init__()
        
        
        ## Default annotation file setup
        self.tree_file = helpers.std_path(os.path.join(helpers.get_cwd(),
                                            'library', 'annotation_trees',
                                             'p56 Mouse Brain.json'))

        
        pageLayout = QtO.new_layout(self, 'H',spacing=0,
                                    margins=(0, 20, 40,20))
        
                
        # Load a_tree for column 1 buttons   
        self.aTree = AnnotationTree()
                
        ## Column one
        # Three buttons
        column1 = QtO.new_widget(fixed_width=140)
        c1Layout = QtO.new_layout(column1, 'V')
        loadButton = QtO.new_button('Load Tree', self.load_annotation_file, 120)     
        checkSelected = QtO.new_button('Check Selected', self.aTree.check_selected, 120)   
        uncheckAll = QtO.new_button('Uncheck All', self.aTree.uncheck_all, 120)
        # Add some form of spacing
        QtO.add_widgets(c1Layout, 
                        [50, loadButton, checkSelected, uncheckAll, 0], 'Center')
    
        
        ## Column two
        # Search bar
        column2 = QtO.new_widget()
        c2Layout = QtO.new_layout(column2, 'V', spacing=0, margins=(0, 20, 0, 0))
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Find region...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.editingFinished.connect(self.find_search)
        
        # Annotation Tree
        self.aTree.load_tree(self.tree_file)
        self.aTree.currentItemChanged.connect(self.update_search_bar)
        
        # Set up search completer
        search_keys = self.aTree.search_index
        completer = QCompleter(search_keys, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_bar.setCompleter(completer)
        completer.activated.connect(self.find_search)
        
        spacingwidget = QtO.new_widget(fixed_height=40)
        spacinglayout = QtO.new_layout(spacingwidget, no_spacing=True)
        
        QtO.add_widgets(c2Layout,
                        [self.search_bar, 5, self.aTree, spacingwidget])
        
        ## Column Three
        column3 = QtO.new_widget(fixed_width=120, min_width=120)
        c3Layout = QtO.new_layout(column3, 'V')
        
        addROIs = QtO.new_button("Add ROIs", self.add_checked_ROIs)
        removeROI = QtO.new_button("Remove ROI", self.remove_ROI)
        clearROIs = QtO.new_button("Remove All", self.clear_ROIs)
        newROI = QtO.new_button("New ROI", self.new_ROI)
        
        QtO.add_widgets(c3Layout, 
                        [0, 20, addROIs, removeROI, clearROIs, 20, newROI, 0], 'Center')
        
        
        ## Column Four
        column4 = QtO.new_widget(min_width=300)
        c4Layout = QtO.new_layout(column4, 'V', spacing=0, margins=(0,20,0,0))
        table_label = QLabel("Selected Annotations")
        self.annTable = AnnotationTable()
        
        exportWidget = QtO.new_widget(fixed_height=40)
        exportLayout = QtO.new_layout(exportWidget, no_spacing=True)
        exportButton = QtO.new_button("Export ROIs", self.export_ROIs)
        QtO.add_widgets(exportLayout, [exportButton], 'Right')
        
        
        QtO.add_widgets(c4Layout,
                        [10, table_label, self.annTable, exportWidget])
                
        QtO.add_widgets(pageLayout, 
                        [column1, column2, column3, column4])
        
     
     
    ## Search bar
    def update_search_bar(self):
        item = self.aTree.identify_selected()
        self.search_bar.setText(item)
        return

    def find_search(self):
        text = self.search_bar.text()
        self.aTree.find_child(text)
        return

    ## Annotation Tree Processing
    def load_annotation_file(self):
        loader = LoadTreeFile()
        if loader.exec_():
            self.tree_file = loader.file_name
            
            # Update our tree_info information
            self.aTree.tree_info.name = loader.nameEdit.text()
            self.aTree.tree_info.children = loader.childrenEdit.text()
            self.aTree.tree_info.id = loader.idEdit.text()
            self.aTree.tree_info.color = loader.colorEdit.text()
            
            try:
                self.aTree.load_tree(loader.file_name)
            except KeyError:
                msgbox = QMessageBox()
                message = """
                <center>Error loading tree file.<br><br> Make sure all tree information was typed correctly and that the tree item contains the following identifiers:<br> 
                - Name<br>
                - ID<br> 
                - Color<br>
                - Children<br><br>
                Each tree should be loaded with a root structure that contains all items.
                """
                msgbox.setText(message)
                msgbox.exec_()
                pass
        del(loader)
        return
    
    ## ROI Table processing
    def add_ROI_row(self, ROI):
        row = self.annTable.rowCount()
        self.annTable.insertRow(row)
        for i in range(3):
            self.annTable.setItem(row, i, QTableWidgetItem(str(ROI[i])))
        return
    
    def add_checked_ROIs(self):
        self.aTree.identify_checked()
        ROIs = self.aTree.checked
        if ROIs:
            ROI_info = AnProc.tree_processing(self.tree_file, ROIs, self.aTree.tree_info)
            for key in ROI_info.keys():
                # This is the most convoluted way to deal with this, but whatever.
                # Couldn't figure out how to assign lists to QTableWidgetItems
                colors = ', '.join(ROI_info[key]['colors'])
                ids = ', '.join([str(id) for id in ROI_info[key]['ids']])
                self.add_ROI_row([key, colors, ids])
        self.aTree.uncheck_all()
        return
    
    def clear_ROIs(self):
        self.annTable.setRowCount(0)
        return
    
    def remove_ROI(self):
        selected = self.annTable.selectionModel().hasSelection()
        if selected:
            self.annTable.removeRow(self.annTable.currentRow())
        return
    
    def new_ROI(self):
        dialog = AddROI()
        if dialog.exec_():
            hex = '#%02x%02x%02x' % (dialog.R.value(), dialog.G.value(), dialog.B.value())
            name = dialog.nameEdit.text()
            if len(name) == 0:
                name = 'None'
            ROI = [name, hex, dialog.idBox.value()]
            self.add_ROI_row(ROI)
        return
    
    
    def export_ROIs(self):
        annotations = {}
        row_count = self.annTable.rowCount()
        
        if row_count:
            for i in range(row_count):
                colors = self.annTable.item(i,1).text()
                colors = [color for color in colors.split(', ')]
                ids = self.annTable.item(i,2).text()
                ids = [int(id) for id in ids.split(', ')]
                annotations[self.annTable.item(i, 0).text()] = {
                    'colors':colors,
                    'ids':ids}
            
            file_name = helpers.get_save_file("Save File As...", helpers.get_dir('Desktop'), 'json')

            if file_name:
                with open(file_name, "w") as f:
                    annotation_data = {"VesselVio Annotations":annotations}
                    file_info = json.dumps(annotation_data)
                    f.write(file_info)
                    f.close()
                    
                self.annTable.clear()
                self.annTable.setRowCount(0)
        else:
            msg = QMessageBox()   
            message = "At least one ROI must be added to the list."
            msg.setText(message)
            msg.exec_()     
        
        return
        


class AnnotationTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setShowGrid(False)
        
        self.setSelectionBehavior(QTreeWidget.SelectRows)
        # self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QTreeWidget.NoEditTriggers)
        
        
        self.setHorizontalHeaderLabels(["ROI Name", "Colors (Hex)", "IDs"])
        
        self.verticalHeader().hide()
        self.horizontalHeader().setMinimumSectionSize(100)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


class AnnotationTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.search_index = [] # For search functionality
        self.checked = []
        
        self.tree_info = AnProc.JSON_Options()
        
        self.setHeaderLabel("Annotation Selection")  
        self.setCurrentItem(self.invisibleRootItem().child(0))
        
        header = self.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        header.setMinimumSectionSize(400)
        header.setStretchLastSection(True)
        
        self.itemChanged[QTreeWidgetItem, int].connect(self.check_selections)
        
    def none(self, event):
        selected = self.selectedItems()
        if len(selected) > 1 and QApplication.keyboardModifiers()&(Qt.ShiftModifier|Qt.ControlModifier):
            former_check_states = [item.checkState(0) == Qt.Checked for item in selected]
            QTreeWidget.mousePressEvent(self, event)
            self.selection_test(former_check_states)
        else:
            QTreeWidget.mousePressEvent(self, event)
    
    def check_selections(self, item, column):
        if QApplication.keyboardModifiers()&(Qt.ShiftModifier|Qt.ControlModifier):
            selected_items = self.selectedItems()
            if len(selected_items) > 1:
                checked = Qt.Checked if item.checkState(column) == Qt.Checked else Qt.Unchecked
                for item in selected_items:
                    item.setCheckState(0, checked)
        return
            
    def identify_selected(self):
        item = self.currentItem()
        if item:
            return item.text(0)   
    
    def check_selected(self):
        for item in self.selectedItems():
            item.setCheckState(0, Qt.Checked)
        return
    
    def uncheck_all(self):
        root = self.invisibleRootItem() # Why tf is it set up like this?
        for i in range(root.childCount()):
            child = root.child(i)
            child.setCheckState(0, Qt.Unchecked)
            self.uncheck_children(child)
        return
    
    def uncheck_children(self, parent):
        for i in range(parent.childCount()):
            child = parent.child(i)
            child.setCheckState(0, Qt.Unchecked)
            self.uncheck_children(child)
        return
        
    def find_child(self, text):
        text = text.capitalize()
        item = self.findItems(text, Qt.MatchContains | Qt.MatchRecursive)
        if item:
            self.setCurrentItem(item[0])
        
    def load_tree(self, file):
        self.clear()
            
        with open(file) as f:
            tree = json.load(f)
            
        if 'msg' in tree.keys():
            tree = tree['msg']
        
        for branch in tree[self.tree_info.children]:
            parent = QTreeWidgetItem(self)
            parent.setText(0, branch[self.tree_info.name])
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.Unchecked)
            self.populate_tree(parent, branch)
            
            # Add the index to our search index
            self.search_index.append(branch[self.tree_info.name])
        
    def populate_tree(self, parent, branch):
        for annotation in branch[self.tree_info.children]:
            child = QTreeWidgetItem(parent)
            child.setText(0, annotation[self.tree_info.name])
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Unchecked)
            
            # Add to the search index
            self.search_index.append(annotation[self.tree_info.name])
            
            if annotation[self.tree_info.children]:
                self.populate_tree(child, annotation)

 
    # Starting function to export :the selected items from the annotation tree
    def identify_checked(self):
        self.checked = []
        root = self.invisibleRootItem() # Why tf is it set up like this?
        for i in range(root.childCount()):
            child = root.child(i)
            if child.checkState(0) == Qt.Checked:
                self.checked.append(child.text(0))
            else:
                self.tree_iterator(child)
        return
        
    # Recursive tree evaluation to identify checked children in the atlas
    def tree_iterator(self, parent):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.checkState(0) == Qt.Checked:
                self.checked.append(child.text(0))
            else:
                self.tree_iterator(child)    
        return


class AddROI(QDialog):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Add New ROI")
        self.setFixedSize(350, 200)
        
        dialogLayout = QtO.new_layout(None, 'V')
        
        nameLayout = QtO.new_layout()
        nameLabel = QLabel("ROI Name:")
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("ROI name...") 
        QtO.add_widgets(nameLayout, 
                        [nameLabel, self.nameEdit])
        
        colorLayout = QtO.new_layout()
        colorLabel = QLabel("ROI Color:")
        self.R = QtO.new_spinbox(0, 255,  alignment='Left')
        self.R.setPrefix("R: ")
        self.G = QtO.new_spinbox(0, 255, alignment='Left')
        self.G.setPrefix("G: ")
        self.B = QtO.new_spinbox(0, 255, alignment='Left')
        self.B.setPrefix("B: ")
        
        QtO.add_widgets(colorLayout, 
                        [colorLabel, self.R, self.G, self.B])
        
        
        idLayout = QtO.new_layout()
        idLabel = QLabel("ROI Integer ID:")
        self.idBox = QtO.new_spinbox(-5000, 5000, alignment='Right')
        self.idBox.setMinimumWidth(100)
        QtO.add_widgets(idLayout,
                        [idLabel, self.idBox, 0])
        
        buttonLayout = QtO.new_layout()
        addButton = QPushButton("Add ROI")
        addButton.clicked.connect(self.accept)
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.reject)
        
        QtO.add_widgets(buttonLayout, 
                       [0, addButton, cancelButton])
        
        
        QtO.add_widgets(dialogLayout,
                        [nameLayout, colorLayout, idLayout, buttonLayout])

        self.setLayout(dialogLayout)


class LoadTreeFile(QDialog):
    def __init__(self):
        super().__init__()
        self.file_name = None
        
        self.setWindowTitle("Tree Ontology Loading")
        self.setFixedSize(520, 250)
        
        dialogLayout = QtO.new_layout(spacing=5)
        self.setLayout(dialogLayout)
        
        ## Left layout
        defaultBox = QGroupBox("Default Trees (Allen Brain Institute)")
        defaultBox.setFixedSize(225, 210)
        boxLayout = QtO.new_layout(defaultBox, 'V', spacing=0)
        
        self.defaultList = QListWidget()
        QListWidgetItem('p56 Mouse Brain', self.defaultList)
        QListWidgetItem('Developing Mouse Brain', self.defaultList)
        QListWidgetItem('Human Brain', self.defaultList)
        self.defaultList.setCurrentRow(0)

        loadLayout = QtO.new_layout(no_spacing=True)
        loadDefault = QtO.new_button("Load Default", self.load_default, width=120)
        QtO.add_widgets(loadLayout, [0, loadDefault])

        QtO.add_widgets(boxLayout,
                        [self.defaultList, 5, loadLayout], 'Right')
        
        ## Right layout
        right = QGroupBox("New Trees")
        right.setFixedSize(250, 210)
        rightLayout = QtO.new_layout(right, 'V', spacing=0)
        advanced_help = "<b>Case Sensitive</b> processing options for JSON file loading."
        advancedOptions = QtO.CollapsibleBox("AdvancedOptions", advanced_help)
        advancedLayout = QtO.new_layout(None, 'V', no_spacing=True)
        
        info = QLabel("<b><center>JSON Identifiers - Case Sensitive!</b>")
        nameLayout = QtO.new_layout()
        name = QLabel("Name: ")
        self.nameEdit = QtO.new_line_edit('name', 'Right', 150)
        QtO.add_widgets(nameLayout, [name, self.nameEdit])
        
        colorLayout = QtO.new_layout()
        color = QLabel("Color: ")
        self.colorEdit = QtO.new_line_edit('color_hex_triplet', 'Right', 150)
        QtO.add_widgets(colorLayout, [color, self.colorEdit])
        
        childrenLayout = QtO.new_layout()
        children = QLabel("Children: ")
        self.childrenEdit = QtO.new_line_edit('children', 'Right', 150)
        QtO.add_widgets(childrenLayout, [children, self.childrenEdit])
        
        idLayout = QtO.new_layout()
        id = QLabel("ID: ")
        self.idEdit = QtO.new_line_edit('id', 'Right', 150)
        QtO.add_widgets(idLayout, [id, self.idEdit])
        
        QtO.add_widgets(advancedLayout, 
                        [5, nameLayout, 5, colorLayout, 5, childrenLayout, 5, idLayout])
        
        advancedOptions.setContentLayout(advancedLayout)
        
        # advancedOptions.toggle_button.setChecked(False)  
        advancedOptions.on_pressed()

        
        loadLayout = QtO.new_layout(no_spacing=True)
        load_JSON = QtO.new_button("Load JSON", self.load_json_file, 120)
        QtO.add_widgets(loadLayout, [0, load_JSON])
        
        QtO.add_widgets(rightLayout, [advancedOptions, 0, loadLayout])
        
        ## Final add
        QtO.add_widgets(dialogLayout, [defaultBox, right])
    

    def load_default(self):
        selection = self.defaultList.currentItem().text()
        self.file_name = os.path.join(helpers.get_cwd(), f"library/annotation_trees/{selection}.json")
        self.accept()
        return
    
    def load_json_file(self):
        loaded_file = helpers.load_JSON(helpers.get_dir('Desktop'))
        if loaded_file:
            self.file_name = loaded_file
            self.accept()
        else:
            self.reject()
        return

###################
### RGB Warning ###
###################
class RGB_Warning(QMessageBox):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warning!")
        message = """<center><b>Warning!</b>
        The same color was found in multiple annotation regions.<br><br>
        Using this annotation file will cause the same structure to be included in multiple regions.<br><br> 
        Are you sure you want to continue with the analysis? <br>
        (Not recommended!)"""
        self.setText(message)
        self.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

###############
### Testing ###    
###############
if __name__ == "__main__":
    # app = QApplication(sys.argv)
    # ex = mainWindow()
    # sys.exit(app.exec_())
    a = RGB_Warning()
    a.exec_()
    
    
