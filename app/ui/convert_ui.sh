# file for automatically create ui.py file before executing main.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_main.ui -o ui_main.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_add_addresses.ui -o ui_add_addresses.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_add_contract.ui -o ui_add_contract.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_set_gas_limit.ui -o ui_set_gas_limit.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_set_gas_price.ui -o ui_set_gas_price.py
python3 -m PyQt5.uic.pyuic -x qt_templates/ui_set_storage.ui -o ui_set_storage.py