import sys
import os
import json
import sqlite3
from collections import Counter
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

class QRCodeViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Viewer - Prensas")
        self.setMinimumSize(600, 400)
        self.setStyleSheet("background-color: rgb(25, 25, 40); color: white;")
        
        # Caminho do banco no mesmo diretório do script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.banco_qrcode_path = os.path.join(script_dir, 'banco_qrcode.db')
        self.prensas = []
        self.cabos_dict = {}
        self.aplicacoes_por_prensa = {}
        self.prensas_info = {}
        self.prensa_frames = []
        self.prensa_widgets = []
        self.current_index = 0
        self.completed_frames = set()
        
        self.load_prensas()
        self.load_cabos()
        self.init_ui()
    
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Cabeçalho e Input na mesma linha
        top_frame = QtWidgets.QFrame()
        top_frame.setStyleSheet("background-color: rgb(40, 40, 50); border-radius: 3px;")
        top_frame.setFixedHeight(35)
        top_layout = QtWidgets.QHBoxLayout(top_frame)
        top_layout.setSpacing(3)
        
        header = QtWidgets.QLabel("QR Code")
        header.setStyleSheet("font-size: 12px; font-weight: bold;")
        top_layout.addWidget(header)
        
        self.input_qr = QtWidgets.QLineEdit()
        self.input_qr.setPlaceholderText("ID...")
        self.input_qr.setStyleSheet("font-size: 12px; padding: 1px; background-color: rgb(50, 50, 60); border: none; border-radius: 3px;")
        self.input_qr.returnPressed.connect(self.processar_qr_e_focar)
        top_layout.addWidget(self.input_qr)
        
        btn_ler = QtWidgets.QPushButton("Ler")
        btn_ler.setStyleSheet("font-size: 12px; padding: 1px 8px; background-color: rgb(69, 207, 81); border-radius: 3px; font-weight: bold;")
        btn_ler.clicked.connect(self.processar_qr)
        top_layout.addWidget(btn_ler)
        
        layout.addWidget(top_frame)
        
        # Info QR
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("font-size: 11px; padding: 3px; background-color: rgb(50, 50, 60); border-radius: 3px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.hide()
        layout.addWidget(self.info_label)
        
        # Scroll de aplicações
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.aplicacoes_widget = QtWidgets.QWidget()
        self.aplicacoes_layout = QtWidgets.QVBoxLayout(self.aplicacoes_widget)
        self.aplicacoes_layout.setSpacing(5)
        self.aplicacoes_layout.setContentsMargins(3, 3, 3, 3)
        
        scroll.setWidget(self.aplicacoes_widget)
        layout.addWidget(scroll)
        self.scroll_area = scroll
    
    def load_prensas(self):
        if not os.path.exists('prensas_config.json'):
            return
        try:
            with open('prensas_config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.prensas = data.get('prensas', []) if isinstance(data, dict) else data
        except:
            pass
    
    def load_cabos(self):
        if not os.path.exists('cabos_config.json'):
            return
        try:
            with open('cabos_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.cabos_dict = config.get('cabos', {})
        except:
            pass
    
    def processar_qr(self):
        qr_id = self.input_qr.text().strip()
        if not qr_id:
            return
        
        try:
            qr_texto, carro, job_key, maco = self.buscar_qrcode(qr_id)
            self.info_label.setText(f"Carro: {carro} | Job Key: {job_key} | Maço: {maco}")
            self.info_label.show()
            self.processar_qrcode_texto(qr_texto)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erro", str(e))
    
    def processar_qr_e_focar(self):
        self.processar_qr()
        self.setFocus()
    
    def limpar_e_focar(self):
        self.input_qr.clear()
        self.input_qr.setFocus()
        self.info_label.hide()
        while self.aplicacoes_layout.count():
            item = self.aplicacoes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.prensa_frames = []
        self.prensa_widgets = []
        self.current_index = 0
        self.completed_frames = set()
    
    def buscar_qrcode(self, qr_id):
        if not os.path.exists(self.banco_qrcode_path):
            caminho_completo = os.path.abspath(self.banco_qrcode_path)
            raise FileNotFoundError(f"Banco de dados não encontrado em: {caminho_completo}")
        
        conn = sqlite3.connect(self.banco_qrcode_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM qrcode WHERE ID = ?', (int(qr_id),))
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            raise ValueError(f"ID {qr_id} não encontrado")
        
        if len(resultado) >= 7:
            texto = resultado[6]
            carro = resultado[3] if resultado[3] else 'N/A'
            job_key = resultado[1] if resultado[1] else 'N/A'
            maco = resultado[4] if resultado[4] else 'N/A'
            return texto, carro, job_key, maco
        raise ValueError("Formato de banco inválido")
    
    def processar_qrcode_texto(self, qr_data):
        terminais_list = []
        aplicacoes_detalhadas = []
        
        conjuntos = qr_data.split('#')
        
        for conjunto in conjuntos:
            componentes = conjunto.split('-')
            cabo_atual = None
            terminais_conjunto = []
            
            for comp in componentes:
                if comp.startswith('C') and ':' in comp:
                    cabo_atual = comp.split(':')[1]
                elif ':' in comp:
                    partes = comp.split(':')
                    if partes[0].startswith('T') or partes[0].startswith('S'):
                        terminal = partes[1]
                        if terminal:
                            terminais_list.append(terminal)
                            terminais_conjunto.append(terminal)
            
            for terminal in terminais_conjunto:
                aplicacoes_detalhadas.append((terminal, cabo_atual))
        
        # Organizar por prensa
        self.aplicacoes_por_prensa = {}
        self.prensas_info = {}
        
        for p in self.prensas:
            terminais = p.get('terminais', [])
            if not terminais:
                terminal_antigo = p.get('terminal', '')
                if terminal_antigo:
                    terminais = [terminal_antigo]
            
            prensa_id = p.get('id', '')
            prensa_nome = p.get('nome', '')
            self.prensas_info[prensa_id] = prensa_nome
            self.aplicacoes_por_prensa[prensa_id] = []
            
            for terminal, cabo in aplicacoes_detalhadas:
                if terminal in terminais:
                    self.aplicacoes_por_prensa[prensa_id].append((terminal, cabo))
        
        self.atualizar_display()
    
    def atualizar_display(self):
        while self.aplicacoes_layout.count():
            item = self.aplicacoes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.prensa_frames = []
        self.prensa_widgets = []
        self.current_index = 0
        self.completed_frames = set()
        
        if not self.aplicacoes_por_prensa:
            label = QtWidgets.QLabel("Nenhuma aplicação encontrada")
            label.setStyleSheet("font-size: 16px; padding: 20px;")
            label.setAlignment(Qt.AlignCenter)
            self.aplicacoes_layout.addWidget(label)
            return
        
        for prensa_id, aplicacoes in sorted(self.aplicacoes_por_prensa.items()):
            if not aplicacoes:
                continue
            
            # Frame da prensa
            prensa_frame = QtWidgets.QFrame()
            prensa_frame.setObjectName("prensaFrame")
            prensa_frame.setStyleSheet("background-color: rgb(50, 50, 60); border-radius: 3px; padding: 3px;")
            prensa_layout = QtWidgets.QVBoxLayout(prensa_frame)
            prensa_layout.setSpacing(2)
            prensa_layout.setContentsMargins(3, 3, 3, 3)
            self.prensa_frames.append(prensa_frame)
            
            # Título
            prensa_nome = self.prensas_info.get(prensa_id, '')
            titulo = f"▶ {prensa_id} - {prensa_nome}" if prensa_nome else f"▶ {prensa_id}"
            titulo_label = QtWidgets.QLabel(titulo)
            titulo_label.setStyleSheet("color: rgb(69, 207, 81); font-weight: bold; font-size: 16px; background: transparent; border: none;")
            prensa_layout.addWidget(titulo_label)
            
            # Container de detalhes
            detalhes_widget = QtWidgets.QWidget()
            detalhes_layout = QtWidgets.QVBoxLayout(detalhes_widget)
            detalhes_layout.setSpacing(2)
            detalhes_layout.setContentsMargins(0, 0, 0, 0)
            self.prensa_widgets.append(detalhes_widget)
            
            # Agrupar por terminal
            terminais_dict = {}
            for (terminal, cabo), qtd in Counter(aplicacoes).items():
                if terminal not in terminais_dict:
                    terminais_dict[terminal] = []
                terminais_dict[terminal].append((cabo, qtd))
            
            for terminal, cabos_list in terminais_dict.items():
                total_terminal = sum(qtd for _, qtd in cabos_list)
                
                # Terminal
                terminal_label = QtWidgets.QLabel(f"  {total_terminal}x {terminal}")
                terminal_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; padding: 2px;")
                detalhes_layout.addWidget(terminal_label)
                
                # Cabos
                for cabo, qtd in cabos_list:
                    cabo_desc = self.cabos_dict.get(cabo, cabo) if cabo else "Cabo desconhecido"
                    
                    cor_html = "#5599FF"
                    if cabo_desc:
                        cabo_lower = cabo_desc.lower()
                        if "vermelho" in cabo_lower:
                            cor_html = "#FF3333"
                        elif "amarelo" in cabo_lower:
                            cor_html = "#FFDD33"
                        elif "verde" in cabo_lower:
                            cor_html = "#33FF66"
                        elif "azul" in cabo_lower:
                            cor_html = "#3399FF"
                        elif "laranja" in cabo_lower:
                            cor_html = "#FF9933"
                        elif "roxo" in cabo_lower or "lilas" in cabo_lower or "violeta" in cabo_lower:
                            cor_html = "#CC66FF"
                        elif "marrom" in cabo_lower:
                            cor_html = "#996633"
                        elif "preto" in cabo_lower:
                            cor_html = "#333333"
                        elif "branco" in cabo_lower:
                            cor_html = "#EEEEEE"
                        elif "cinza" in cabo_lower:
                            cor_html = "#999999"
                        elif "rosa" in cabo_lower:
                            cor_html = "#FF99CC"
                    
                    cabo_label = QtWidgets.QLabel(f'    <span style="color: {cor_html}; font-weight: bold; font-size: 14px;">●</span> {qtd}x {cabo_desc}')
                    cabo_label.setStyleSheet("color: rgb(200, 200, 200); font-size: 12px; padding: 1px;")
                    detalhes_layout.addWidget(cabo_label)
            
            prensa_layout.addWidget(detalhes_widget)
            self.aplicacoes_layout.addWidget(prensa_frame)
        
        self.aplicacoes_layout.addStretch()
        
        if self.prensa_frames:
            self.atualizar_selecao()
    
    def keyPressEvent(self, event):
        if not self.prensa_frames:
            return
        
        # Setas do teclado/gamepad
        if event.key() == Qt.Key_Down or event.key() == Qt.Key_S or event.key() == Qt.Key_VolumeDown:
            if self.current_index < len(self.prensa_frames) - 1:
                self.current_index += 1
                self.atualizar_selecao()
        elif event.key() == Qt.Key_Up or event.key() == Qt.Key_W or event.key() == Qt.Key_VolumeUp:
            if self.current_index > 0:
                self.current_index -= 1
                self.atualizar_selecao()
        elif event.key() == Qt.Key_Right or event.key() == Qt.Key_D or event.key() == Qt.Key_Space or event.key() == Qt.Key_MediaNext:
            self.marcar_completo()
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_A or event.key() == Qt.Key_Backspace or event.key() == Qt.Key_MediaPrevious:
            self.desmarcar_completo()
    
    def atualizar_selecao(self):
        for i, frame in enumerate(self.prensa_frames):
            if i == self.current_index:
                if i in self.completed_frames:
                    frame.setStyleSheet("QFrame#prensaFrame { background-color: rgb(40, 100, 40); border: 3px solid rgb(69, 207, 81); border-radius: 3px; padding: 3px; } QLabel { background: transparent; border: none; } QWidget { background: transparent; border: none; }")
                else:
                    frame.setStyleSheet("QFrame#prensaFrame { background-color: rgb(50, 50, 60); border: 3px solid rgb(255, 200, 0); border-radius: 3px; padding: 3px; } QLabel { background: transparent; border: none; } QWidget { background: transparent; border: none; }")
            else:
                if i in self.completed_frames:
                    frame.setStyleSheet("QFrame#prensaFrame { background-color: rgb(40, 100, 40); border: none; border-radius: 3px; padding: 3px; } QLabel { background: transparent; border: none; } QWidget { background: transparent; border: none; }")
                else:
                    frame.setStyleSheet("QFrame#prensaFrame { background-color: rgb(50, 50, 60); border: none; border-radius: 3px; padding: 3px; } QLabel { background: transparent; border: none; } QWidget { background: transparent; border: none; }")
            
            if i in self.completed_frames:
                self.prensa_widgets[i].hide()
            else:
                self.prensa_widgets[i].show()
        
        frame = self.prensa_frames[self.current_index]
        self.scroll_area.ensureWidgetVisible(frame)
    
    def marcar_completo(self):
        self.completed_frames.add(self.current_index)
        self.prensa_widgets[self.current_index].hide()
        
        # Verificar se todos foram completados
        if len(self.completed_frames) == len(self.prensa_frames):
            self.atualizar_selecao()
            reply = QtWidgets.QMessageBox.question(self, "Finalizar Maço", "Deseja finalizar o maço?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.limpar_e_focar()
        elif self.current_index < len(self.prensa_frames) - 1:
            self.current_index += 1
            self.atualizar_selecao()
            QtCore.QTimer.singleShot(50, lambda: self.scroll_area.ensureWidgetVisible(self.prensa_frames[self.current_index], 0, 0))
        else:
            self.atualizar_selecao()
    
    def desmarcar_completo(self):
        if self.current_index in self.completed_frames:
            self.completed_frames.remove(self.current_index)
            self.prensa_widgets[self.current_index].show()
        self.atualizar_selecao()


if __name__ == '__main__':
    import os
    app = QtWidgets.QApplication(sys.argv)
    window = QRCodeViewer()
    window.show()
    sys.exit(app.exec_())
