import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QDateEdit,
    QMessageBox,
    QHeaderView,
)
from PyQt6.QtCore import QDate

# Import your existing SQLAlchemy configuration and models
from database import SessionLocal, engine, Base
from models import Policyholder


class ICPSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICPS - Policyholder Management")
        self.resize(800, 600)

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

        self.btn_add = QPushButton("Add New Policyholder")
        self.btn_add.setStyleSheet(
            "background-color: #2E8B57; color: white; padding: 8px; font-weight: bold;"
        )
        self.btn_add.clicked.connect(self.add_policyholder)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.btn_add)

        # ─── 2. Data Table ──────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "DOB", "Email", "Phone"])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.layout.addWidget(self.table)

        self.btn_refresh = QPushButton("Refresh Table Data")
        self.btn_refresh.clicked.connect(self.load_data)
        self.layout.addWidget(self.btn_refresh)

        # Load data immediately upon startup
        self.load_data()

    def add_policyholder(self):
        """Creates a new SQLAlchemy session, adds the record, and commits."""
        db = SessionLocal()
        try:
            # Map UI inputs to your SQLAlchemy model
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
            QMessageBox.information(
                self, "Success", "Policyholder securely added to the database!"
            )

            # Clear inputs and refresh table
            self.input_id.clear()
            self.input_name.clear()
            self.load_data()

        except Exception as e:
            db.rollback()
            # If a unique constraint fails (e.g., duplicate email), it catches it here
            QMessageBox.critical(
                self, "Database Error", f"Failed to add record:\n{str(e)}"
            )
        finally:
            db.close()

    def load_data(self):
        """Fetches all policyholders from the database and populates the table."""
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
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(ph.email)))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(ph.phone)))
        finally:
            db.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ICPSMainWindow()
    window.show()
    sys.exit(app.exec())
