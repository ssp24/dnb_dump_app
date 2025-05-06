import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QComboBox, QProgressBar, QSpacerItem, QSizePolicy, QShortcut
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeySequence
from datetime import date
# from sru_functions import dnb_sru, dnb_sru_number
import requests
from bs4 import BeautifulSoup as soup
from time import sleep
import re


def dnb_sru_number(query, metadata, base_url):
    params = {'recordSchema': metadata,
              'operation': 'searchRetrieve',
              'version': '1.1',
              'query': query
              }

    if metadata != "mods-xml":
        params.update({'maximumRecords': '100'})
    try:
        r1 = requests.get(base_url, params=params)
        r1.raise_for_status()  # Raise an exception for bad status codes
        xml1 = soup(r1.content, features="xml")
        treffer = xml1.find_all("numberOfRecords")
        if treffer:
            treffer = int(treffer[0].text)
        else:
            treffer = 0
    except requests.RequestException as e:
        print(f"Error in API request: {e}")
        treffer = 0
    except Exception as e:
        print(f"Error processing response: {e}")
        treffer = 0

    return treffer


def dnb_sru(query, metadata, base_url, progress_signal, filename, is_running):
    session = requests.Session()

    params = {'recordSchema': metadata,
              'operation': 'searchRetrieve',
              'version': '1.1',
              'query': query
              }

    if metadata != "mods-xml":
        params.update({'maximumRecords': '100'})

    r = requests.get(base_url, params=params)
    xml = soup(r.content, features="xml")
    diagnostics = xml.find_all('diagnostics')
    if diagnostics:
        error = "error"
        return error
    else:
        if metadata == "oai_dc":
            records = xml.find_all('record')
        elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb":
            records = xml.find_all('record', {'type': 'Bibliographic'})
        elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb":
            records = xml.find_all('record', {'type': 'Bibliographic'})
        elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/authorities":
            records = xml.find_all('record', {'type': 'Authority'})
        elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb.dma":
            records = xml.find_all('record', {'type': 'Bibliographic'})
        else:
            records = xml.find_all('record')

        treffer = xml.find_all("numberOfRecords")[0].text
        treffer = int(treffer)
        if treffer > 100:
            loops = int(treffer / 100) + 1
        else:
            loops = 1
        print("Records found: ", treffer)
        print("Anzahl notwendiger Abfragen: ", loops)

        if treffer == 0:
            print("No results found.")
            progress_signal.emit(100)
        elif metadata != "mods-xml" and 1 <= treffer <= 100:
            with open(f"{filename}.xml", 'w', encoding="utf-8") as f:
                f.write(str(xml))
                progress_signal.emit(100)
                return True
        elif metadata == "mods-xml" and 1 <= treffer <= 10:
            with open(f"{filename}.xml", 'w', encoding="utf-8") as f:
                f.write(str(xml))
                progress_signal.emit(100)
                return True
        elif metadata != "mods-xml" and treffer > 100:
            progress_increment = 100 / loops

            # Define XML-header and footer:
            header_marc = f'''<?xml version="1.0" encoding="utf-8"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"> 
                <version>1.1</version><numberOfRecords>{str(treffer)}</numberOfRecords>
                <records><record><recordSchema>MARC21-xml</recordSchema><recordPacking>xml</recordPacking><recordData>'''
            header_dc = f'''<searchRetrieveResponse><version>1.1</version><numberOfRecords>{str(treffer)}</numberOfRecords><records>'''
            header_pica = f'''<?xml version="1.0" encoding="utf-8"?><searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/"><version>1.1</version>
                <numberOfRecords>{str(treffer)}</numberOfRecords><records>'''
            footer_marc = f'''</recordData></record></records><echoedSearchRetrieveRequest><version>1.1</version>
                <query>{query}</query><xQuery xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>
                <recordSchema>MARC21-xml</recordSchema></echoedSearchRetrieveRequest>
                </searchRetrieveResponse>'''
            footer_dc = f'''</records><echoedSearchRetrieveRequest><version>1.1</version><query>{query}</query>
                <recordSchema>oai_dc</recordSchema></echoedSearchRetrieveRequest></searchRetrieveResponse>'''
            footer_rdf = f'''</records><echoedSearchRetrieveRequest><version>1.1</version><query>{query}</query>
                <recordSchema>RDFxml</recordSchema></echoedSearchRetrieveRequest></searchRetrieveResponse>'''
            footer_pica = f'''</records><echoedSearchRetrieveRequest><version>1.1</version><query>{query}</query>
                <xQuery xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/><maximumRecords>100</maximumRecords><recordSchema>PicaPlus-xml</recordSchema>
                </echoedSearchRetrieveRequest></searchRetrieveResponse>'''

            if metadata == "oai_dc":
                header = header_dc
            elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb":
                header = header_marc
            elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/authorities":
                header = header_marc
            elif metadata == "RDFxml":
                header = header_dc
            elif metadata == "PicaPlus-xml":
                header = header_pica
            else:
                header = " "

            # Open file and write header and first records:
            with open(f"{filename}.xml", 'w', encoding="utf-8") as f:
                f.write(header)
                for record in records:
                    f.write(str(record))

            print("successfully written header and first records")

            num_results = 100
            i = 101
            count = 0
            progress_percent = progress_increment  # Start with progress after first request

            while num_results == 100:
                if not is_running():
                    # Download abgebrochen
                    progress_signal.emit(0)
                    return

                params.update({'startRecord': i})
                r = requests.get(base_url, params=params)
                xml = soup(r.content, features="xml")
                if metadata == "oai_dc":
                    new_records = xml.find_all('record')
                elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb":
                    new_records = xml.find_all('record', {'type': 'Bibliographic'})
                elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/authorities":
                    new_records = xml.find_all('record', {'type': 'Authority'})
                elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb.dma":
                    new_records = xml.find_all('record', {'type': 'Bibliographic'})
                else:
                    new_records = xml.find_all('record')
                records += new_records
                i += 100
                count += 1
                num_results = len(new_records)
                progress_percent += progress_increment
                progress_signal.emit(int(min(progress_percent, 100)))

                # Add records:
                with open(f"{filename}.xml", 'a', encoding="utf-8") as f:
                    for record in new_records:
                        f.write(str(record))

                if num_results < 100:
                    if metadata == "oai_dc":
                        footer = footer_dc
                    elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/dnb":
                        footer = footer_marc
                    elif metadata == "MARC21-xml" and base_url == "https://services.dnb.de/sru/authorities":
                        footer = footer_marc
                    elif metadata == "RDFxml":
                        footer = footer_rdf
                    elif metadata == "PicaPlus-xml":
                        footer = footer_pica
                    else:
                        footer = ""

                    with open(f"{filename}.xml", 'a', encoding="utf-8") as f:
                        f.write(footer)

                    print("successfully written all records and footer.")
                    progress_signal.emit(100)
                    return True

                if count % 50 == 0:
                    if not is_running():
                        # Download abgebrochen
                        progress_signal.emit(0)
                        return
                    print("sleeping...")
                    sleep(3)
                else:
                    continue


        # Sonderlocke für mods...
        elif metadata == "mods-xml" and treffer > 10:
            loops = int(treffer / 10) + 1
            progress_increment = 100 / loops

            # Define XML-header and footer:
            header_mods = f'''<?xml version="1.0" encoding="utf-8"?>
                                <searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
                                    <version>1.1</version>
                                    <numberOfRecords>{str(treffer)}</numberOfRecords>
                                        <records>'''
            footer_mods = f'''</records><echoedSearchRetrieveRequest><version>1.1</version><query>{query}</query>
                                <xQuery xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/><recordSchema>mods-xml</recordSchema>
                                </echoedSearchRetrieveRequest></searchRetrieveResponse>'''

            num_results = 10
            i = 11
            progress_percent = progress_increment  # Start with progress after first request

            count = 0

            while num_results == 10:
                if not is_running():
                    # Download abgebrochen
                    progress_signal.emit(0)
                    return

                params.update({'startRecord': i})
                r = requests.get(base_url, params=params)
                xml = soup(r.content, features="xml")
                new_records = xml.find_all('record')
                records += new_records
                i += 10
                count += 1
                num_results = len(new_records)
                progress_percent += progress_increment
                progress_signal.emit(int(min(progress_percent, 100)))

                if count % 50 == 0:
                    print("sleeping...")
                    sleep(3)
                else:
                    continue

            recordlist = ""
            for record in records:
                recordlist += str(record)

            xmlplus = header_mods + recordlist + footer_mods

            with open(f"{filename}.xml", 'w', encoding='utf-8') as f1:
                f1.write(xmlplus)

            return True

        else:
            print("Something went wrong.")


class DNBSRUThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(bool)

    def __init__(self, query, metadata, base_url, filename):
        super().__init__()
        self.query = query
        self.metadata = metadata
        self.base_url = base_url
        self.filename = filename
        self._is_running = True

    def run(self):
        # Übergabe `is_running` Funktion an `dnb_sru`
        success = dnb_sru(self.query, self.metadata, self.base_url, self.progress_signal, self.filename,
                          self.is_running)
        self.result_signal.emit(success)

    def stop(self):
        self._is_running = False

    def is_running(self):
        return self._is_running

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.logo_label.setGeometry(self.width() - 60, 10, 50, 50)


class SRUQueryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        font = app.font()
        font.setFamily("Verdana")
        app.setFont(font)

        self.setWindowTitle("SRU Query Tool")
        self.setGeometry(100, 100, 750, 750)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)  # Abstand zwischen Widgets
        layout.setContentsMargins(20, 20, 20, 20)  # Ränder des Layouts

        heading = QLabel("SRU Query Tool")
        heading.setStyleSheet("""
            font-size: 16pt;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)
        layout.addWidget(QLabel(" "))  # Empty label for spacing

        # Create a QLabel with the text
        intro_label = QLabel("Mit diesem Tool können Sie die SRU-Schnittstelle der Deutschen Nationalbibliothek "
                             "abfragen und die Ergebnisse als Metadatendump herunterladen. <br> Allgemeine Informationen "
                             "zur SRU-Schnittstelle und den zur Verfügung stehenden Katalogen finden Sie unter "
                             "<a href='https://www.dnb.de/sru'>www.dnb.de/sru</a>. Weiterführende Informationen "
                             "zur Suche sowie Möglichkeiten zur Eingrenzung der Ergebnisse finden Sie unter "
                             "<a href='https://www.dnb.de/expertensuche'>www.dnb.de/expertensuche</a>.")
        # intro_label.setAlignment(Qt.AlignCenter)
        intro_label.setWordWrap(True)  # wrap text
        intro_label.setOpenExternalLinks(True)  # This allows the links to be clickable
        layout.addWidget(intro_label)
        layout.addWidget(QLabel(" "))  # Empty label for spacing

        todo_label = QLabel("Wählen Sie einen Katalog und ein Metadatenformat aus und geben Sie Ihre Suchanfrage ein:")
        todo_label.setAlignment(Qt.AlignCenter)
        todo_label.setWordWrap(True)  # wrap text

        # Add the label to the layout
        layout.addWidget(todo_label)
        layout.addWidget(QLabel(" "))  # Empty label for spacing

        layout.addWidget(QLabel("Katalog:"))
        self.catalogue_combo = QComboBox()
        self.catalogue_combo.addItems(["DNB (Titeldaten)", "GND (Normdaten)", "DMA (Deutsches Musikarchiv)",
                                       "ZDB (Zeitschriftendatenbank)", "Adressdaten (ISIL- und Siegelverzeichnis)"])
        layout.addWidget(self.catalogue_combo)
        self.catalogue_combo.currentIndexChanged.connect(self.update_metadata_formats)

        layout.addWidget(QLabel("Metadatenformat:"))
        self.metadata_combo = QComboBox()
        layout.addWidget(self.metadata_combo)

        layout.addWidget(QLabel(" "))
        layout.addWidget(QLabel("Ihre Suchanfrage ('search query'):"))
        self.query_input = QLineEdit()
        layout.addWidget(self.query_input)
        self.query_input.textChanged.connect(self.disable_download_button)  # Track changes in entered text

        self.output_label = QLabel("")
        self.output_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.output_label)

        # Button Layout
        button_layout = QHBoxLayout()

        # Check Search Query Button
        self.check_button = QPushButton("Suchanfrage prüfen")
        self.check_button.clicked.connect(self.check_search_query)
        self.check_button.setFixedSize(180, 40)
        self.return_shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.return_shortcut.activated.connect(self.check_search_query)

        # Download XML Button
        self.download_button = QPushButton("Download XML")
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.get_xml)
        self.download_button.setFixedSize(180, 40)
        layout.addWidget(self.download_button)

        # Buttons zentrieren
        button_layout.addStretch()
        button_layout.addWidget(self.check_button)
        button_layout.addSpacing(10)  # Abstand zwischen den Buttons
        button_layout.addWidget(self.download_button)
        button_layout.addStretch()

        # Fügt das Button-Layout zum Hauptlayout hinzu
        layout.addLayout(button_layout)

        # Result Anzeige:
        self.results_label = QLabel(" ")
        self.results_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.results_label)

        # WARNING Anzeige
        self.warning_label = QLabel("")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        # Progress Bar:
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Cancel Button
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.setVisible(False)
        self.cancel_button.setFixedSize(180, 40)
        self.cancel_button.clicked.connect(self.stop_download)
        cancel_layout.addWidget(self.cancel_button)
        cancel_layout.addStretch()
        layout.addLayout(cancel_layout)

        # Adding spacer to push the exit button to the bottom
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Right-aligning the Exit button
        exit_layout = QHBoxLayout()
        exit_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.exit_button = QPushButton("Schließen")
        self.exit_button.setFixedSize(180, 40)
        self.exit_button.clicked.connect(self.close)
        exit_layout.addWidget(self.exit_button)

        # Add logo:
        self.logo_label = QLabel(self)
        pixmap = QPixmap("logo.gif")
        self.logo_label.setPixmap(pixmap.scaled(80, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.logo_label.setGeometry(self.width() - 110, 10, 90, 80)
        self.logo_label.raise_()

        layout.addLayout(exit_layout)

        self.update_metadata_formats()
        self.apply_styles()

    def update_metadata_formats(self):
        self.metadata_combo.clear()
        selected_catalogue = self.catalogue_combo.currentText()
        if selected_catalogue == "DNB (Titeldaten)":
            formats = ["MARC21-xml", "oai_dc", "RDFxml", "mods-xml"]
        elif selected_catalogue == "GND (Normdaten)":
            formats = ["MARC21-xml", "RDFxml"]
        elif selected_catalogue == "DMA (Deutsches Musikarchiv)":
            formats = ["MARC21-xml", "oai_dc", "RDFxml", "mods-xml"]
        elif selected_catalogue == "ZDB (Zeitschriftendatenbank)":
            formats = ["MARC21-xml", "MARC21plus-1-xml", "oai_dc", "RDFxml"]
        else:
            formats = ["RDFxml", "PicaPlus-xml"]
        self.metadata_combo.addItems(formats)

    def check_search_query(self):
        try:
            catalogue = self.catalogue_combo.currentText()
            metadata = self.metadata_combo.currentText()
            query = self.query_input.text()

            if catalogue == "DNB (Titeldaten)":
                cat_url = "https://services.dnb.de/sru/dnb"
            elif catalogue == "DMA (Deutsches Musikarchiv)":
                cat_url = "https://services.dnb.de/sru/dnb.dma"
            elif catalogue == "GND (Normdaten)":
                cat_url = "https://services.dnb.de/sru/authorities"
            elif catalogue == "ZDB (Zeitschriftendatenbank)":
                cat_url = "https://services.dnb.de/sru/zdb"
            elif catalogue == "Adressdaten (ISIL- und Siegelverzeichnis)":
                cat_url = "https://services.dnb.de/sru/bib"

            if cat_url and metadata and query:
                result = dnb_sru_number(query, metadata, cat_url)
                display_text = f"Ihre Suchanfrage ergibt {result} Treffer."
                self.results_label.setText(display_text)
                if result < 100000:
                    self.warning_label.setVisible(False)
                    self.download_button.setEnabled(True)
                else:
                    self.warning_label.setText(
                        "Warnung! Ihre Anfrage ergibt mehr als 100.000 Treffer! "
                        "Bitte teilen Sie Ihre Anfrage so auf, dass Sie immer nur "
                        "Anfragen mit maximal 100.000 Treffern stellen (bspw. indem Sie "
                        "Zeitabschnitte hinzufügen).")
                    self.warning_label.setVisible(True)
                    self.warning_label.setWordWrap(True)
                    self.download_button.setEnabled(False)
            else:
                self.warning_label.setText(
                    "Bitte wählen Sie zuerst einen Katalog und ein Metadatenformat aus und "
                    "geben Sie eine Suchanfrage ein.")
                self.warning_label.setAlignment(Qt.AlignCenter)
                self.warning_label.setWordWrap(True)
                self.warning_label.setVisible(True)
                self.download_button.setEnabled(False)
        except Exception as e:
            self.results_label.setText(f"Ein Fehler ist aufgetreten: {str(e)}")
            print(f"Error: {str(e)}")

    def get_xml(self):
        catalogue = self.catalogue_combo.currentText()
        metadata = self.metadata_combo.currentText()
        query = self.query_input.text()
        self.download_button.setEnabled(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Downloading...")

        if catalogue == "DNB (Titeldaten)":
            cat_url = "https://services.dnb.de/sru/dnb"
        elif catalogue == "DMA (Deutsches Musikarchiv)":
            cat_url = "https://services.dnb.de/sru/dnb.dma"
        elif catalogue == "GND (Normdaten)":
            cat_url = "https://services.dnb.de/sru/authorities"
        elif catalogue == "ZDB (Zeitschriftendatenbank)":
            cat_url = "https://services.dnb.de/sru/zdb"
        elif catalogue == "Adressdaten (ISIL- und Siegelverzeichnis)":
            cat_url = "https://services.dnb.de/sru/bib"

        if cat_url and metadata and query:
            today = str(date.today())
            today = today.replace("-", "")
            name = query.replace(" ", "_")
            name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name).strip('. ')
            filename = today + "_" + metadata + "_" + name
            print(filename)
            self.dnb_sru_thread = DNBSRUThread(query, metadata, cat_url, filename)
            self.dnb_sru_thread.progress_signal.connect(self.update_progress)
            self.dnb_sru_thread.result_signal.connect(self.handle_result)
            self.dnb_sru_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def handle_result(self, success):
        if success:
            self.status_label.setText("Download erfolgreich!")
            self.download_button.setEnabled(True)
            self.cancel_button.setVisible(False)
        else:
            self.status_label.setText("Download fehlgeschlagen.")

        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)

    def stop_download(self):
        self.dnb_sru_thread.stop()
        self.status_label.setText("Download abgebrochen!")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def disable_download_button(self):
        self.download_button.setEnabled(False)
        self.results_label.setText(" ")  # Optional: Leeren Sie das Ergebnislabel
        self.warning_label.setVisible(False)  # Stelle sicher, dass keine Warnung mehr angezeigt wird.

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-size: 14px;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 2px solid #007BFF;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007BFF;
            }

        """)

        # Exit-Button
        self.exit_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF0000;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #FF5733;
                }
            """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SRUQueryApp()
    window.show()
    sys.exit(app.exec_())
