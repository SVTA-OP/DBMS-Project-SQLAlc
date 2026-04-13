import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QDateEdit,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
)
from PyQt6.QtCore import QDate

# Import your existing SQLAlchemy configuration and models
from database import SessionLocal, engine, Base
from models import Policyholder


class ICPSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICPS - Policyholder Management (Full CRUD)")
        self.resize(900, 700)

        # Ensure database tables exist before launching the UI
        Base.metadata.create_all(engine)

        # Set up the main central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # ─── 1. Input Form ──────────────────────────────────────────────────
        self.form_layout = QFormLayout()

        self.input_id = QLineEdit()
        self.input_name = QLineEdit()
        self.input_gender = QLineEdit()
        self.input_email = QLineEdit()
        self.input_phone = QLineEdit()
        self.input_proof_type = QLineEdit()
        self.input_proof_num = QLineEdit()

        self.input_dob = QDateEdit()
        self.input_dob.setCalendarPopup(True)
        self.input_dob.setDate(QDate.currentDate())

        self.form_layout.addRow("Policyholder ID:", self.input_id)
        self.form_layout.addRow("Full Name:", self.input_name)
        self.form_layout.addRow("Date of Birth:", self.input_dob)
        self.form_layout.addRow("Gender:", self.input_gender)
        self.form_layout.addRow("Email:", self.input_email)
        self.form_layout.addRow("Phone:", self.input_phone)
        self.form_layout.addRow("ID Proof Type:", self.input_proof_type)
        self.form_layout.addRow("ID Proof Number:", self.input_proof_num)

        self.layout.addLayout(self.form_layout)

        # ─── 2. Action Buttons (Create, Update, Delete, Clear) ───────────────
        self.button_layout = QHBoxLayout()

        self.btn_add = QPushButton("Create (Add New)")
        self.btn_add.setStyleSheet(
            "background-color: #2E8B57; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_add.clicked.connect(self.add_policyholder)

        self.btn_update = QPushButton("Update Selected")
        self.btn_update.setStyleSheet(
            "background-color: #4682B4; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_update.clicked.connect(self.update_policyholder)

        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setStyleSheet(
            "background-color: #B22222; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_delete.clicked.connect(self.delete_policyholder)

        self.btn_clear = QPushButton("Clear Form")
        self.btn_clear.clicked.connect(self.clear_form)

        self.button_layout.addWidget(self.btn_add)
        self.button_layout.addWidget(self.btn_update)
        self.button_layout.addWidget(self.btn_delete)
        self.button_layout.addWidget(self.btn_clear)
        self.layout.addLayout(self.button_layout)

        # ─── 3. Data Table ──────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "DOB",
                "Gender",
                "Email",
                "Phone",
                "Proof Type",
                "Proof Number",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )  # Prevent direct table editing

        # When a row is clicked, load its data into the form
        self.table.itemSelectionChanged.connect(self.populate_form_from_selection)

        self.layout.addWidget(self.table)

        self.btn_refresh = QPushButton("Refresh Table Data")
        self.btn_refresh.clicked.connect(self.load_data)
        self.layout.addWidget(self.btn_refresh)

        # Load data immediately upon startup
        self.load_data()

    # ─── CRUD OPERATIONS ────────────────────────────────────────────────────

    def add_policyholder(self):  # CREATE
        db = SessionLocal()
        try:
            new_ph = Policyholder(
                policyholder_id=self.input_id.text(),
                full_name=self.input_name.text(),
                dob=self.input_dob.date().toPyDate(),
                gender=self.input_gender.text(),
                email=self.input_email.text(),
                phone=self.input_phone.text(),
                id_proof_type=self.input_proof_type.text(),
                id_proof_number=self.input_proof_num.text(),
                created_at=datetime.utcnow(),
            )
            db.add(new_ph)
            db.commit()
            QMessageBox.information(self, "Success", "Policyholder added!")
            self.clear_form()
            self.load_data()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(
                self, "Database Error", f"Failed to add record:\n{str(e)}"
            )
        finally:
            db.close()

    def load_data(self):  # READ
        db = SessionLocal()
        try:
            records = db.query(Policyholder).all()
            self.table.setRowCount(len(records))

            for row_idx, ph in enumerate(records):
                self.table.setItem(
                    row_idx, 0, QTableWidgetItem(str(ph.policyholder_id))
                )
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(ph.full_name)))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(ph.dob)))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(ph.gender)))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(ph.email)))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(ph.phone)))
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(ph.id_proof_type)))
                self.table.setItem(
                    row_idx, 7, QTableWidgetItem(str(ph.id_proof_number))
                )
        finally:
            db.close()

    def update_policyholder(self):  # UPDATE
        ph_id = self.input_id.text()
        if not ph_id:
            QMessageBox.warning(
                self,
                "Selection Error",
                "Please select a record or enter an ID to update.",
            )
            return

        db = SessionLocal()
        try:
            # Find the existing record
            ph = (
                db.query(Policyholder)
                .filter(Policyholder.policyholder_id == ph_id)
                .first()
            )

            if not ph:
                QMessageBox.warning(
                    self, "Not Found", "No Policyholder found with that ID."
                )
                return

            # Update fields
            ph.full_name = self.input_name.text()
            ph.dob = self.input_dob.date().toPyDate()
            ph.gender = self.input_gender.text()
            ph.email = self.input_email.text()
            ph.phone = self.input_phone.text()
            ph.id_proof_type = self.input_proof_type.text()
            ph.id_proof_number = self.input_proof_num.text()

            db.commit()
            QMessageBox.information(
                self, "Success", "Policyholder updated successfully!"
            )
            self.load_data()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(
                self, "Database Error", f"Failed to update record:\n{str(e)}"
            )
        finally:
            db.close()

    def delete_policyholder(self):  # DELETE
        ph_id = self.input_id.text()
        if not ph_id:
            QMessageBox.warning(
                self, "Selection Error", "Please select a record to delete."
            )
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete Policyholder {ph_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                ph = (
                    db.query(Policyholder)
                    .filter(Policyholder.policyholder_id == ph_id)
                    .first()
                )
                if ph:
                    db.delete(ph)
                    db.commit()
                    QMessageBox.information(
                        self, "Deleted", "Record deleted successfully."
                    )
                    self.clear_form()
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Not Found", "Record not found.")
            except Exception as e:
                db.rollback()
                QMessageBox.critical(
                    self, "Database Error", f"Failed to delete record:\n{str(e)}"
                )
            finally:
                db.close()

    # ─── HELPER METHODS ─────────────────────────────────────────────────────

    def populate_form_from_selection(self):
        """Fills the form inputs when a row is clicked in the table."""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()

        # Map table columns back to input fields
        self.input_id.setText(self.table.item(row, 0).text())
        self.input_name.setText(self.table.item(row, 1).text())

        # Parse date string back to QDate
        date_str = self.table.item(row, 2).text()
        date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
        self.input_dob.setDate(date_obj)

        self.input_gender.setText(self.table.item(row, 3).text())
        self.input_email.setText(self.table.item(row, 4).text())
        self.input_phone.setText(self.table.item(row, 5).text())
        self.input_proof_type.setText(self.table.item(row, 6).text())
        self.input_proof_num.setText(self.table.item(row, 7).text())

    def clear_form(self):
        """Clears all input fields."""
        self.input_id.clear()
        self.input_name.clear()
        self.input_gender.clear()
        self.input_email.clear()
        self.input_phone.clear()
        self.input_proof_type.clear()
        self.input_proof_num.clear()
        self.input_dob.setDate(QDate.currentDate())
        self.table.clearSelection()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ICPSMainWindow()
    window.show()
    sys.exit(app.exec())
