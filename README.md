# SRU Query Tool

Das SRU Query Tool ist im Rahmen des [DNBLabs](https://www.dnb.de/dnblab) der [Deutschen Nationalbibliothek](https://www.dnb.de) entstanden. Es ermöglicht das einfache Erstellen von Metadatendumps im XML-Format auf Basis einer Abfrage der SRU-Schnittstelle der DNB.

Es gibt zwei Möglichkeiten, um die SRU Query App zu nutzen: 

1) SRUQueryTool-1.0-win64.msi (portable)  

   Die Datei SRUQueryTool-1.0-win64.msi enthält alle benötigten Python-Bibliotheken und kann als Standalone-Anwendung nach Download auch ohne Admin-Rechte installiert werden. Heruntergeladene Datensets werden im Ordner, in dem das SRUQueryTool installiert wird, abgelegt.
   
3) sru_dump_allin1.py  

   Alternativ kann die Datei sru_dump_allin1.py genutzt werden.  
   Hierfür muss Python installiert sein, zudem werden folgende Bibliotheken benötigt:
   - sys
   - PyQt5
   - datetime
   - requests
   - bs4 
   - time 
   - re
