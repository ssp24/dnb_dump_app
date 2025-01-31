# dnb_dump_app

Es gibt zwei Möglichkeiten, um die SRU Query App zu nutzen: 

1) SRUQueryTool.exe (portable)  

   Die SRUQueryTool.exe enthält alle benötigten Python-Bibliotheken und kann als Standalone-Anwendung nach Download einfach ausgeführt werden. Heruntergeladene Datensets werden im Ordner, in dem das SRUQueryTool liegt und ausgeführt wird, abgelegt.
   
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
