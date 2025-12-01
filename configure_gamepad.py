import sys
import json
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

class GamepadConfig(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configurar Gamepad")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: rgb(25, 25, 40); color: white; font-size: 14px;")
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.config = {'up': [], 'down': [], 'left': [], 'right': [], 'enter': [], 'focus_input': []}
        self.current_action = None
        self.actions = ['up', 'down', 'left', 'right', 'enter', 'focus_input']
        self.action_index = 0
        
        self.init_ui()
        self.next_action()
    
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QtWidgets.QLabel("Configuração de Gamepad")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: rgb(69, 207, 81);")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.instruction = QtWidgets.QLabel("")
        self.instruction.setStyleSheet("font-size: 16px; padding: 20px; background-color: rgb(50, 50, 60); border-radius: 5px;")
        self.instruction.setAlignment(Qt.AlignCenter)
        self.instruction.setWordWrap(True)
        layout.addWidget(self.instruction)
        
        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("font-size: 14px; color: rgb(200, 200, 200);")
        self.status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status)
        
        btn_skip = QtWidgets.QPushButton("Pular")
        btn_skip.setStyleSheet("font-size: 14px; padding: 10px; background-color: rgb(100, 100, 110); border-radius: 5px;")
        btn_skip.clicked.connect(self.skip_action)
        layout.addWidget(btn_skip)
        
        layout.addStretch()
    
    def next_action(self):
        if self.action_index >= len(self.actions):
            self.save_config()
            return
        
        self.current_action = self.actions[self.action_index]
        action_names = {
            'up': 'CIMA (navegar para cima)',
            'down': 'BAIXO (navegar para baixo)',
            'left': 'ESQUERDA (desmarcar)',
            'right': 'DIREITA (marcar completo)',
            'enter': 'ENTER (processar QR Code)',
            'focus_input': 'VOLTAR (focar no input)'
        }
        self.instruction.setText(f"Pressione a tecla para:\n{action_names[self.current_action]}")
        self.status.setText(f"Configurando {self.action_index + 1} de {len(self.actions)}")
    
    def skip_action(self):
        self.action_index += 1
        self.next_action()
    
    def keyPressEvent(self, event):
        event.accept()
        if self.current_action:
            key = event.key()
            print(f"Tecla capturada: {key} para ação: {self.current_action}")
            self.config[self.current_action].append(key)
            self.action_index += 1
            self.next_action()
    
    def save_config(self):
        with open('gamepad_keys.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
        
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Sucesso")
        msg.setText("Configuração salva com sucesso!")
        msg.setStyleSheet("QMessageBox { background-color: rgb(25, 25, 40); color: white; } QPushButton { background-color: rgb(69, 207, 81); color: white; padding: 5px 15px; }")
        msg.exec_()
        self.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = GamepadConfig()
    window.show()
    sys.exit(app.exec_())
