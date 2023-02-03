import sqlite3
import sys
import loc_api
import config_api
from PyQt5 import QtCore, QtGui, QtWidgets

DB: sqlite3.Connection
CURSOR: sqlite3.Cursor

SYSTEM_TABLES = ('sqlite_master', 'sqlite_sequence',
                 'sqlite_stat1', 'sqlite_stat2', 'sqlite_stat3', 'sqlite_stat4')

PROVIDED_TYPES = ('INTEGER', 'REAL', 'TEXT', 'BLOB')


def load_table(table: str, scope: QtWidgets.QTableWidget) -> None:
    """Loads all records from SQLite table to QTableWidget

        table: str - SQLite table name
        scope: QTableWidget - table into which the values will be loaded,
    """

    columns = CURSOR.execute(
        f"PRAGMA table_info({table})").fetchall()
    print(columns)
    scope.setColumnCount(len(columns))
    scope.setHorizontalHeaderLabels([i[1] for i in columns])
    records = CURSOR.execute(f"SELECT * FROM {table}").fetchall()
    scope.setRowCount(len(records))
    for i in range(len(records)):
        for j in range(len(columns)):
            cell = DatabaseLabel(columns[j][2])
            cell.setText(str(records[i][j]))
            scope.setCellWidget(i, j, cell)


def close_app() -> None:
    """Closes SQLite Database connection and its cursor"""

    CURSOR.close()
    DB.close()


class MainWindow(QtWidgets.QWidget):
    """Main window of app, where SQLite database can be created or opened"""

    def __init__(self):
        """Initialize the MainWindow with its UI"""

        super().__init__()
        self.setGeometry(200, 200, 350, 350)
        self.setObjectName('mainWindow')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title'))
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        project_group = QtWidgets.QGroupBox()
        project_group.setObjectName('projectGroup')
        logo = QtWidgets.QLabel()
        logo.setObjectName('dbmLogo')
        logo.setPixmap(QtGui.QPixmap('res/ico/common/dbmLogo.png'))
        layout.addWidget(logo)
        layout.addWidget(project_group)
        project_group.setWindowTitle(loc_api.get_lang(project_group))
        vbox = QtWidgets.QVBoxLayout()
        project_group.setLayout(vbox)
        new = QtWidgets.QPushButton()
        new.setObjectName('dbCreate')
        new.setIcon(QtGui.QIcon('res/ico/common/dbCreateIcon.png'))
        vbox.addWidget(new)
        new.setText(loc_api.get_lang(new))
        new.clicked.connect(self.new_db)
        open_ = QtWidgets.QPushButton()
        open_.setObjectName('dbOpen')
        open_.setIcon(QtGui.QIcon('res/ico/common/dbOpenIcon.png'))
        vbox.addWidget(open_)
        open_.setText(loc_api.get_lang(open_))
        open_.clicked.connect(self.open_db)
        self.settings = QtWidgets.QPushButton(parent=self)
        self.settings.setObjectName('dbmSettings')
        self.settings.setFixedWidth(25)
        self.settings.setFixedHeight(25)
        self.settings.setIcon(QtGui.QIcon('res/ico/common/dbmSettings.png'))
        self.settings.move(self.width() - 40, 20)
        self.settings.clicked.connect(self.open_settings)

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()

    def new_db(self):
        """Creates new database"""

        db_create_dialog = QtWidgets.QInputDialog()
        db_create_dialog.setWindowIcon(QtGui.QIcon('res/ico/common/dbEditIcon.png'))
        db_create_dialog.setObjectName('dbCreateDialog')
        db_create_dialog.setWindowTitle(loc_api.get_lang(f'{db_create_dialog.objectName()}.title'))
        db_create_dialog.setLabelText(loc_api.get_lang(f'{db_create_dialog.objectName()}.name'))
        db_create_dialog.setOkButtonText(loc_api.get_lang('dialogGroup.dialogAccept'))
        db_create_dialog.setCancelButtonText(loc_api.get_lang('dialogGroup.dialogDecline'))
        if db_create_dialog.exec_() == QtWidgets.QInputDialog.Accepted:
            db = db_create_dialog.textValue()
            if db != '':
                global DB, CURSOR
                DB = sqlite3.connect(f'db/{db}.s3db')
                CURSOR = DB.cursor()
                self.db_win = DatabaseWindow(f'db/{db}.s3db')
                self.db_win.show()
                self.hide()
            else:
                self.error = ErrorDialog('emptyDbName')
                self.error.show()

    def open_db(self):
        """Opens existing database"""

        db_open_dialog = QtWidgets.QFileDialog()
        db_open_dialog.setObjectName('dbOpenDialog')
        db = db_open_dialog.getOpenFileName(directory='db',
                                            filter='SQLite3 Database Files (*.s3db);;Database Files (*.db)')[0]
        if db != '':
            global DB, CURSOR
            DB = sqlite3.connect(db)
            CURSOR = DB.cursor()
            self.db_win = DatabaseWindow(db)
            self.db_win.show()
            self.hide()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        self.settings.move(self.width() - 40, 20)
        super().resizeEvent(a0)


class DatabaseWindow(QtWidgets.QWidget):
    def __init__(self, db_name):
        """Creates database window, which contains tables"""

        super().__init__()
        tables = [''.join(i).strip() for i in
                  CURSOR.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if
                  (i,) not in SYSTEM_TABLES]
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.setGeometry(200, 200, 800, 600)
        self.setObjectName('databaseWindow')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title').format(db_name))
        self.table_widget = QtWidgets.QTabWidget()
        self.table_widget.setObjectName('tableWidget')
        self.table_widget.setWindowTitle(loc_api.get_lang(self.table_widget))
        self.table_widget.setMovable(True)
        layout.addWidget(self.table_widget)
        for i in range(len(tables)):
            if tables[i] in SYSTEM_TABLES:
                continue
            tab = DatabaseTable()
            tab.setObjectName(tables[i])
            self.table_widget.addTab(tab, tables[i])
            load_table(tables[i], tab)

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        """Calls context menu by RBM clicking"""

        menu = QtWidgets.QMenu()
        menu.setObjectName('dbEditMenu')
        add_table = QtWidgets.QAction(parent=menu)
        add_table.setObjectName('tbAdd')
        add_table.setIcon(QtGui.QIcon('res/ico/common/tbAddIcon.png'))
        add_table.triggered.connect(self.add_table)
        delete_table = QtWidgets.QAction(parent=menu, icon=QtGui.QIcon(f''))
        delete_table.setObjectName('tbRemove')
        delete_table.setIcon(QtGui.QIcon('res/ico/common/tbRemoveIcon.png'))
        delete_table.triggered.connect(self.delete_table)
        menu.addAction(add_table)
        menu.addAction(delete_table)
        add_table.setText(loc_api.get_lang(add_table))
        delete_table.setText(loc_api.get_lang(delete_table))
        menu.exec(a0.globalPos())

    def add_table(self) -> None:
        """Adds new table, which content is fully similar to relevant SQLite table"""

        tb_create_dialog = QtWidgets.QInputDialog()
        tb_create_dialog.setObjectName('tbCreateDialog')
        tb_create_dialog.setWindowTitle(loc_api.get_lang(f'{tb_create_dialog.objectName()}.title'))
        tb_create_dialog.setWindowIcon(QtGui.QIcon('res/ico/common/tbAddIcon.png'))
        tb_create_dialog.setLabelText(loc_api.get_lang(f'{tb_create_dialog.objectName()}.name'))
        if tb_create_dialog.exec_() == QtWidgets.QInputDialog.Accepted:
            tb = tb_create_dialog.textValue()
            if tb != '':
                if tb.startswith('sqlite_'):
                    self.error = ErrorDialog('wrongTbName')
                    self.error.show()
                    return
                elif tb[0] in [str(i) for i in range(10)] + []:
                    pass
                tab = DatabaseTable()
                tab.setObjectName(tb)
                self.cl_edit = ColumnCreateDialog()
                if self.cl_edit.exec_() == QtWidgets.QDialog.Accepted:
                    CURSOR.execute(f"CREATE TABLE IF NOT EXISTS {tb} {self.cl_edit.get_sql_command()}")
                    DB.commit()
                    self.table_widget.addTab(tab, tb)
                    load_table(tb, tab)
            else:
                self.error = ErrorDialog('emptyTbName')
                self.error.show()

    def delete_table(self):
        """Deletes selected table both from DatabaseWindow and from SQLite database"""

        if self.table_widget.currentWidget():
            table = self.table_widget.currentWidget().objectName()
            self.table_widget.removeTab(self.table_widget.currentIndex())
            CURSOR.execute(f'DROP TABLE {table}')
            DB.commit()


class SettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName('settingWindow')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title'))
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.item_group = QtWidgets.QListWidget()
        self.item_group.setObjectName('itemGroup')
        self.item_group.setFixedWidth(100)
        for i in range(len(config_api.CONFIG)):
            item = QtWidgets.QListWidgetItem()
            item.setText(list(config_api.CONFIG.keys())[i])
            self.item_group.addItem(item)
        layout.addWidget(self.item_group)
        self.configurator = QtWidgets.QWidget()
        layout.addWidget(self.configurator)
        self.item_group.setCurrentRow(1)
        self.load_settings()
        self.item_group.itemActivated.connect(self.load_settings)

    def load_settings(self):
        block = self.item_group.currentItem().text()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(15)
        self.configurator.setObjectName(f'{block.lower()}Configuration')
        self.configurator.setLayout(vbox)
        block_options = config_api.CONFIG[block]
        for i in range(len(block_options)):
            param_group = QtWidgets.QWidget()
            param_group.setObjectName(f'{list(block_options.keys())[i]}ParamGroup')
            hbox = QtWidgets.QHBoxLayout()
            param_group.setLayout(hbox)

            param_name = QtWidgets.QLabel()
            param_name.setObjectName(f'{list(block_options.keys())[i]}ParamName')
            param_name.setText(loc_api.get_lang(param_name) if loc_api.is_valid_key(loc_api.get_loc_key(param_name))
                               else list(block_options.keys())[i])

            param_value = QtWidgets.QLineEdit()
            param_value.setObjectName(f'{list(block_options.keys())[i]}')
            param_value.setText(list(block_options.values())[i])

            hbox.addWidget(param_name)
            hbox.addWidget(param_value)

            vbox.addWidget(param_group)


class DatabaseTable(QtWidgets.QTableWidget):
    """Representation of SQLite 3 Database Table"""

    def __init__(self):
        super().__init__()
        self.verticalHeader().setVisible(False)

    def contextMenuEvent(self, a0: QtGui.QContextMenuEvent) -> None:
        tb_edit_menu = QtWidgets.QMenu()
        tb_edit_menu.setObjectName('tbEditMenu')
        add_rcd = QtWidgets.QAction(parent=tb_edit_menu)
        add_rcd.setObjectName('tbAddRcd')
        remove_rcd = QtWidgets.QAction(parent=tb_edit_menu)
        remove_rcd.setObjectName('tbRemoveRcd')
        add_rcd.setText(loc_api.get_lang(add_rcd))
        remove_rcd.setText(loc_api.get_lang(remove_rcd))
        add_rcd.triggered.connect(self.add_rcd)
        remove_rcd.triggered.connect(self.remove_rcd)
        add_rcd.setIcon(QtGui.QIcon('res/ico/common/rcdAddIcon.png'))
        remove_rcd.setIcon(QtGui.QIcon('res/ico/common/rcdRemoveIcon.png'))
        add_cl = QtWidgets.QAction(parent=tb_edit_menu)
        add_cl.setObjectName('tbAddCl')
        remove_cl = QtWidgets.QAction(parent=tb_edit_menu)
        remove_cl.setObjectName('tbRemoveCl')
        add_cl.setText(loc_api.get_lang(add_cl))
        remove_cl.setText(loc_api.get_lang(remove_cl))
        add_cl.setIcon(QtGui.QIcon('res/ico/common/tbAddIcon.png'))
        remove_cl.setIcon(QtGui.QIcon('res/ico/common/tbRemoveIcon.png'))
        tb_edit_menu.addAction(add_cl)
        tb_edit_menu.addAction(remove_cl)
        tb_edit_menu.addSeparator()
        tb_edit_menu.addAction(add_rcd)
        tb_edit_menu.addAction(remove_rcd)
        tb_edit_menu.exec(a0.globalPos())

    def add_rcd(self):  # TODO
        columns = CURSOR.execute(
            f"PRAGMA table_info({self.objectName()})").fetchall()
        self.rcd_edit = RecordCreateDialog(columns)
        self.rcd_edit.show()
        if self.rcd_edit.exec_() == QtWidgets.QDialog.Accepted:
            comm = f"INSERT into {self.objectName()} " \
                   f"({', '.join([column[1] for column in columns])}) {self.rcd_edit.get_sql_command()}"
            CURSOR.execute(comm)
            DB.commit()

    def remove_rcd(self):  # TODO
        pass


class ColumnCreateDialog(QtWidgets.QDialog):
    """Creates a widget, that generates a part of SQL command, that makes table columns"""

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.setWindowIcon(QtGui.QIcon('res/ico/common/tbEditIcon.png'))
        self.setObjectName('clCreateDialog')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title'))
        cl_group = QtWidgets.QWidget()
        cl_group.setObjectName('clGroup')
        cl_group_vbox = QtWidgets.QVBoxLayout()
        cl_group.setLayout(cl_group_vbox)

        cl_name_group = QtWidgets.QWidget()
        cl_name_group.setObjectName('clNameGroup')
        cl_name_vbox = QtWidgets.QVBoxLayout()
        cl_name_group.setLayout(cl_name_vbox)
        cl_name_label = QtWidgets.QLabel()
        cl_name_label.setObjectName('clNameLabel')
        self.cl_name = QtWidgets.QLineEdit()
        self.cl_name.setObjectName('clName')
        cl_name_vbox.addWidget(cl_name_label)
        cl_name_vbox.addWidget(self.cl_name)
        cl_name_label.setText(loc_api.get_lang(cl_name_label))
        self.cl_name.setPlaceholderText(loc_api.get_lang(self.cl_name))

        cl_type_group = QtWidgets.QWidget()
        cl_type_group.setObjectName('clTypeGroup')
        cl_type_vbox = QtWidgets.QVBoxLayout()
        cl_type_group.setLayout(cl_type_vbox)
        cl_type_label = QtWidgets.QLabel()
        cl_type_label.setObjectName('clTypeLabel')
        self.cl_type = QtWidgets.QComboBox()
        self.cl_type.setObjectName('clType')
        for i in PROVIDED_TYPES:
            self.cl_type.addItem(QtGui.QIcon(f'res/ico/type/{i.lower()}_128.png'), i, userData=i)
        self.cl_type.currentIndexChanged.connect(self.cl_type_changed)
        cl_type_vbox.addWidget(cl_type_label)
        cl_type_vbox.addWidget(self.cl_type)
        cl_type_label.setText(loc_api.get_lang(cl_type_label))

        cl_is_primary_group = QtWidgets.QWidget()
        cl_is_primary_group.setObjectName('clIsPrimaryGroup')
        cl_is_primary_vbox = QtWidgets.QVBoxLayout()
        cl_is_primary_group.setLayout(cl_is_primary_vbox)
        self.cl_is_primary = QtWidgets.QCheckBox()
        cl_is_primary_vbox.addWidget(self.cl_is_primary)
        self.cl_is_primary.setObjectName('clIsPrimary')
        self.cl_is_primary.clicked.connect(self.checked_is_primary)
        self.cl_is_primary.setText(loc_api.get_lang(self.cl_is_primary))

        cl_is_autoincrement_group = QtWidgets.QWidget()
        cl_is_autoincrement_group.setObjectName('clIsAutoIncrementGroup')
        cl_is_autoincrement_vbox = QtWidgets.QVBoxLayout()
        cl_is_autoincrement_group.setLayout(cl_is_autoincrement_vbox)
        self.cl_is_autoincrement = QtWidgets.QCheckBox()
        cl_is_autoincrement_vbox.addWidget(self.cl_is_autoincrement)
        self.cl_is_autoincrement.setObjectName('clIsAutoIncrement')
        self.cl_is_autoincrement.setText(loc_api.get_lang(self.cl_is_autoincrement))

        cl_is_unique_group = QtWidgets.QWidget()
        cl_is_unique_group.setObjectName('clIsUniqueGroup')
        cl_is_unique_vbox = QtWidgets.QVBoxLayout()
        cl_is_unique_group.setLayout(cl_is_unique_vbox)
        self.cl_is_unique = QtWidgets.QCheckBox()
        self.cl_is_unique.setObjectName('clIsUnique')
        cl_is_unique_vbox.addWidget(self.cl_is_unique)
        self.cl_is_unique.clicked.connect(self.checked_is_unique)
        self.cl_is_unique.setText(loc_api.get_lang(self.cl_is_unique))

        cl_is_null_group = QtWidgets.QWidget()
        cl_is_null_group.setObjectName('clIsNullGroup')
        cl_is_null_vbox = QtWidgets.QVBoxLayout()
        cl_is_null_group.setLayout(cl_is_null_vbox)
        self.cl_is_null = QtWidgets.QCheckBox()
        self.cl_is_null.setObjectName('clIsNull')
        cl_is_null_vbox.addWidget(self.cl_is_null)
        self.cl_is_null.setText(loc_api.get_lang(self.cl_is_null))

        cl_default_group = QtWidgets.QWidget()
        cl_default_group.setObjectName('clDefaultGroup')
        cl_default_vbox = QtWidgets.QVBoxLayout()
        cl_default_group.setLayout(cl_default_vbox)
        cl_default_label = QtWidgets.QLabel()
        cl_default_label.setObjectName('clDefaultLabel')
        self.cl_default = QtWidgets.QLineEdit()
        self.cl_default.setObjectName('clDefault')
        cl_default_vbox.addWidget(cl_default_label)
        cl_default_vbox.addWidget(self.cl_default)
        cl_default_label.setText(loc_api.get_lang(cl_default_label))
        self.cl_default.setPlaceholderText(loc_api.get_lang(self.cl_default))

        cl_group_vbox.addWidget(cl_name_group)
        cl_group_vbox.addWidget(cl_type_group)
        cl_group_vbox.addWidget(cl_is_primary_group)
        cl_group_vbox.addWidget(cl_is_autoincrement_group)
        cl_group_vbox.addWidget(cl_is_unique_group)
        cl_group_vbox.addWidget(cl_is_null_group)
        cl_group_vbox.addWidget(cl_default_group)

        dialog_group = QtWidgets.QWidget()
        dialog_group.setObjectName('dialogGroup')
        dialog_group_hbox = QtWidgets.QHBoxLayout()
        dialog_group.setLayout(dialog_group_hbox)
        dialog_accept = QtWidgets.QPushButton()
        dialog_accept.setObjectName('dialogAccept')
        dialog_decline = QtWidgets.QPushButton()
        dialog_decline.setObjectName('dialogDecline')
        dialog_accept.clicked.connect(self.accept)
        dialog_decline.clicked.connect(self.hide)
        dialog_group_hbox.addWidget(dialog_accept)
        dialog_group_hbox.addWidget(dialog_decline)
        dialog_accept.setText(loc_api.get_lang(dialog_accept))
        dialog_decline.setText(loc_api.get_lang(dialog_decline))

        layout.addWidget(cl_group)
        layout.addWidget(dialog_group)
        self.show()

    def accept(self) -> None:
        """ Closes TableColumnEdit dialog and excepts errors in data format, if there are"""

        if self.cl_name.text() == '':
            self.error = ErrorDialog('emptyClName')
        elif self.cl_default.text() and self.cl_type.itemData(self.cl_type.currentIndex()) == 'INTEGER' and \
                not all(i in '-1234567890' for i in self.cl_default.text()):
            self.error = ErrorDialog('wrongClDefaultInteger')
        elif self.cl_default.text() and self.cl_type.itemData(self.cl_type.currentIndex()) == 'REAL' and \
                not all(i in '-.1234567890' for i in self.cl_default.text()):
            self.error = ErrorDialog('wrongClDefaultReal')
        else:
            super().accept()
            return
        self.error.show()

    def checked_is_primary(self) -> None:
        """If checked, user can't input UNIQUE, NOT NULL and DEFAULT field"""

        if self.cl_is_primary.isChecked():
            self.cl_is_unique.setChecked(False)
            self.cl_is_null.setChecked(False)
            self.cl_default.setText('')
            self.cl_is_unique.parentWidget().setVisible(False)
            self.cl_is_null.parentWidget().setVisible(False)
            self.cl_default.parentWidget().setVisible(False)
        else:
            self.cl_is_unique.parentWidget().setVisible(True)
            self.cl_is_null.parentWidget().setVisible(True)
            self.cl_default.parentWidget().setVisible(True)

    def checked_is_unique(self):
        """If checked, user can't input DEFAULT and PRIMARY KEY field"""

        if self.cl_is_unique.isChecked():
            self.cl_default.setText('')
            self.cl_is_primary.setChecked(False)
            self.cl_default.parentWidget().setVisible(False)
            self.cl_is_primary.parentWidget().setVisible(False)
        else:
            self.cl_is_primary.parentWidget().setVisible(True)
            self.cl_default.parentWidget().setVisible(True)

    def cl_type_changed(self):
        """If type is INTEGER, user can select AUTOINCREMENT field
        If type is BLOB, user can enter big multi-string text"""

        if self.cl_type.currentData(self.cl_type.currentIndex()) == 'INTEGER':
            self.cl_is_autoincrement.parentWidget().setVisible(True)
        else:
            self.cl_is_autoincrement.setChecked(False)
            self.cl_is_autoincrement.parentWidget().setVisible(False)

        if self.cl_type.currentData(self.cl_type.currentIndex()) == 'BLOB':
            self.cl_default = QtWidgets.QTextEdit()
        else:
            self.cl_default = QtWidgets.QLineEdit()

    def get_sql_command(self) -> str:
        """Returns part of SQL command, that makes table columns"""
        name = self.cl_name.text()
        type_ = self.cl_type.itemData(self.cl_type.currentIndex())
        is_primary = self.cl_is_primary.isChecked()
        is_autoincrement = self.cl_is_autoincrement.isChecked()
        is_null = self.cl_is_null.isChecked()
        is_unique = self.cl_is_unique.isChecked()
        default = self.cl_default.text()
        return f'({name} {type_} {"PRIMARY KEY" if is_primary else ""} {"AUTOINCREMENT" if is_autoincrement else ""} ' \
               f'{"NOT NULL" if is_null else ""}' \
               f' {"UNIQUE" if is_unique else ""} {f"DEFAULT {default}" if default != "" else ""})'


class RecordCreateDialog(QtWidgets.QDialog):
    def __init__(self, columns):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.fields = []
        self.setObjectName('rcdCreateDialog')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title'))
        self.setWindowIcon(QtGui.QIcon('res/ico/common/rcdAddIcon.png'))
        self.setLayout(layout)
        for i in range(len(columns)):
            field_group = QtWidgets.QWidget()
            hbox = QtWidgets.QHBoxLayout()
            field_group.setLayout(hbox)
            field_label = QtWidgets.QLabel()
            field_label.setText(f'{columns[i][1]}:')
            field_input = DatabaseLineEdit(columns[i][2], columns[i][4], columns[i][3])
            hbox.addWidget(field_label)
            hbox.addWidget(field_input)
            self.fields.append(field_input)
            layout.addWidget(field_group)
        self.fields = tuple(self.fields)
        dialog_group = QtWidgets.QGroupBox()
        dialog_group.setObjectName('dialogGroup')
        dialog_hbox = QtWidgets.QHBoxLayout()
        dialog_group.setLayout(dialog_hbox)
        accept = QtWidgets.QPushButton()
        decline = QtWidgets.QPushButton()
        accept.setObjectName('dialogAccept')
        decline.setObjectName('dialogDecline')
        dialog_hbox.addWidget(accept)
        dialog_hbox.addWidget(decline)
        accept.setText(loc_api.get_lang(accept))
        decline.setText(loc_api.get_lang(decline))
        accept.clicked.connect(self.accept)
        decline.clicked.connect(self.hide)
        layout.addWidget(dialog_group)

    def get_sql_command(self):
        comm = ', '.join(['\'' + field.text() + '\'' for field in self.fields])
        return f'VALUES ({comm})'

    def accept(self):
        super().accept()


class DatabaseLineEdit(QtWidgets.QLineEdit):
    def __init__(self, sql_type: str, default: str = None, not_null: bool = 0):
        super().__init__()
        self.setObjectName('rcdEl')
        self.type = sql_type
        dflt = '' if default is None else default
        self.not_null = not_null
        self.setPlaceholderText(
            loc_api.get_lang(f"{self.objectName()}.{'required' if self.not_null else 'notRequired'}"))
        self.setText(dflt)
        self.setStyleSheet('\n'.join(open(f'stylesheet/default/type/{self.type.lower()}.qss').readlines()))


class DatabaseLabel(QtWidgets.QLabel):
    def __init__(self, sql_type: str):
        super().__init__()
        self.setObjectName('rcdEl')
        self.type = sql_type
        self.setStyleSheet('\n'.join(open(f'stylesheet/default/type/{self.type.lower()}.qss').readlines()))


class ErrorDialog(QtWidgets.QMessageBox):
    def __init__(self, err_key: str):
        super().__init__()
        self.setObjectName('errorDialog')
        self.setWindowTitle(loc_api.get_lang(f'{self.objectName()}.title'))
        self.setWindowIcon(QtGui.QIcon('res/ico/common/errorIcon.png'))
        self.setText(loc_api.get_lang(f'{self.objectName()}.{err_key}'))


if __name__ == '__main__':
    config_api.load_config()
    sys.excepthook = lambda cls, exception, traceback: sys.__excepthook__(cls, exception, traceback)
    loc_api.load_lang()
    with open(f'stylesheet/{config_api.CONFIG["APPEARANCE"]["style"]}') as style:
        stylesheet = '\n'.join(style.readlines())
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    app.setWindowIcon(QtGui.QIcon('res/ico/common/dbmIcon.png'))
    win = MainWindow()
    win.show()
    if app.exec_():
        close_app()
