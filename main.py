import json
import xml.etree.ElementTree as ET
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.image import AsyncImage, Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget  # Certifique-se de importar o Widget correto
from kivy.uix.widget import Widget  # Certifique-se de importar o Widget correto
import subprocess
import os

# Impede que Kivy processe argumentos de linha de comando
os.environ['KIVY_NO_ARGS'] = '1'

# Configuração da janela principal
Window.clearcolor = (0.125, 0.125, 0.125, 1)  # Cor de fundo cinza escuro
Window.icon = 'iconeSite.png'

# Carregar o arquivo XML da Bíblia
def carregar_biblia():
    arvore = ET.parse('pt_nvi.xml')
    return arvore.getroot()

# Função para carregar o plano de leitura de um arquivo JSON
def carregar_plano_leitura():
    with open('plano_leitura.json', 'r', encoding='utf-8') as arquivo:
        return json.load(arquivo)

# Função para filtrar o texto do XML baseado no livro, capítulos e versículos
def buscar_trecho(biblia, livro, trechos):
    texto_completo = ""

    for trecho in trechos:
        try:
            capitulo, versiculo_intervalo = trecho.split(':')
            capitulo = int(capitulo)
            verso_inicial, verso_final = map(int, versiculo_intervalo.split('-'))
        except ValueError:
            # Formato inválido de trecho
            continue

        texto_completo += f"{livro} {capitulo}:{verso_inicial}-{verso_final}\n\n"
        
        texto_capitulo = biblia.find(f".//b[@n='{livro}']/c[@n='{capitulo}']")
        if texto_capitulo is not None:
            for versiculo in texto_capitulo.findall('v'):
                num_versiculo = int(versiculo.attrib['n'])
                if verso_inicial <= num_versiculo <= verso_final:
                    texto_completo += f"{num_versiculo} {versiculo.text}\n\n"
            texto_completo += "\n"
        else:
            texto_completo += "Capítulo não encontrado.\n\n"

    return texto_completo.strip()

# Tela de Carregamento
class LoadingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text='Carregando Bíblia e Plano de Leitura', font_size=24, color=(1, 1, 1, 1))
        layout.add_widget(label)
        
        # Adicionar ícone animado de carregamento
        loading_gif = AsyncImage(source='leituraDia.png')
        layout.add_widget(loading_gif)
        
        self.add_widget(layout)

# Tela de Leitura
class TelaLeitura(Screen):
    def __init__(self, texto, data_selecionada, **kwargs):
        super(TelaLeitura, self).__init__(**kwargs)

        self.layout_principal = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Título com "Leitura do Dia + Data no formato dd-mm-aaaa"
        self.titulo = Label(text=f'Leitura do Dia {data_selecionada}', font_size=24, size_hint_y=0.1, color=(1, 1, 1, 1))
        self.layout_principal.add_widget(self.titulo)

        self.scroll_view = ScrollView(size_hint_y=0.8)

        self.label_texto = Label(text=texto, font_size=18, halign='left', valign='top', size_hint_y=None, color=(1, 1, 1, 1))
        self.label_texto.bind(size=self.label_texto.setter('text_size'))
        self.label_texto.bind(texture_size=self.atualizar_tamanho_label)

        self.scroll_view.add_widget(self.label_texto)
        self.layout_principal.add_widget(self.scroll_view)

        # Botão Voltar
        self.botao_voltar = Button(text="Voltar", size_hint=(0.1, 0.1), on_release=self.voltar_principal, 
                                   pos_hint={'right': 1, 'top': 1}, background_color=(0, 0, 0, 0),
                                   color=(1, 1, 1, 1))
        self.layout_principal.add_widget(self.botao_voltar)

        self.add_widget(self.layout_principal)

    def atualizar_tamanho_label(self, instance, value):
        self.label_texto.height = self.label_texto.texture_size[1]
        self.label_texto.text_size = (self.scroll_view.width - 20, None)  # Ajuste a largura com uma pequena margem

    def voltar_principal(self, instance):
        self.manager.current = 'home_screen'
        self.manager.remove_widget(self)

# Botão de Imagem Personalizado
class ImageButton(ButtonBehavior, BoxLayout):
    def __init__(self, image_source, label_text, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint = (None, None)
        self.size = (100, 100)  # Ajuste o tamanho conforme necessário

        self.image = Image(source=image_source, size_hint_y=0.8)
        self.label = Label(text=label_text, size_hint_y=0.2, color=(1, 1, 1, 1), font_size=14)
        
        # Adiciona a imagem e a legenda ao layout
        self.add_widget(self.image)
        self.add_widget(self.label)

# Tela Principal (Home)
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout principal em BoxLayout para organização vertical
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # Espaço vazio no topo para ajudar na centralização dos ícones
        layout.add_widget(Label(size_hint_y=0.3, text=''))

        # Layout em BoxLayout horizontal para centralizar os ícones
        icon_container = BoxLayout(orientation='horizontal', size_hint_y=0.4)

        # Layout em grid para organizar os ícones em colunas
        icon_layout = GridLayout(cols=4, spacing=20, size_hint=(None, None))
        icon_layout.bind(minimum_width=icon_layout.setter('width'))

        # Carrega a Bíblia e o plano de leitura
        self.biblia = carregar_biblia()
        self.plano_leitura = carregar_plano_leitura()

        # Ícone e legenda da Bíblia
        button_bible = ImageButton(image_source='biblia.png', label_text='Bíblia')
        button_bible.bind(on_press=self.open_bible)
        icon_layout.add_widget(button_bible)

        # Ícone e legenda do Plano Anual
        # button_plan = ImageButton(image_source='iconeCalendario.png', label_text='Plano Anual')
        # button_plan.bind(on_press=self.open_plan)
        # icon_layout.add_widget(button_plan)

        # Ícone para acessar diretamente a leitura do dia
        self.botao_leitura_dia = ImageButton(image_source='leituraDia.png', label_text='Leitura do Dia')
        self.botao_leitura_dia.bind(on_press=self.abrir_leitura_dia)
        icon_layout.add_widget(self.botao_leitura_dia)

        # Ícone e legenda para fechar o app
        button_exit = ImageButton(image_source='sair.png', label_text='Fechar App')
        button_exit.bind(on_press=self.close_app)
        icon_layout.add_widget(button_exit)

        # Centralizando o GridLayout no BoxLayout horizontal
        icon_container.add_widget(Widget())  # Espaço vazio à esquerda
        icon_container.add_widget(icon_layout)  # Adiciona os ícones centralizados
        icon_container.add_widget(Widget())  # Espaço vazio à direita

        # Adiciona o container de ícones ao layout principal
        layout.add_widget(icon_container)

        # Espaço vazio abaixo dos ícones para centralização
        layout.add_widget(Label(size_hint_y=0.3, text=''))

        # Título da data atual
        self.date_label = Label(
            text='Mensagem do Dia',  # Formato da data
            size_hint_y=None, height=40,
            color=(1, 1, 1, 1), halign='center', valign='middle',
            font_size=20
        )
        self.date_label.bind(size=self.update_text_size)
        layout.add_widget(self.date_label)

        # Label para mostrar a mensagem do dia
        self.message_label = Label(
            text=self.load_daily_message(),  # Método atualizado para carregar a mensagem do JSON
            size_hint_y=None,
            height=100,
            color=(1, 1, 1, 1),
            halign='center', valign='middle',
            font_size=16
        )
        self.message_label.bind(size=self.update_text_size)
        layout.add_widget(self.message_label)

        self.add_widget(layout)

    def load_daily_message(self):
        try:
            with open('mensagens.json', 'r', encoding='utf-8') as arquivo:
                mensagens = json.load(arquivo)
            data_atual = datetime.now().strftime('%d-%m')
            return mensagens.get(data_atual, "Nenhuma mensagem para hoje.")
        except Exception as e:
            return "Erro ao carregar a mensagem do dia."


    def abrir_leitura_dia(self, instance):
        data_atual = datetime.now().strftime('%d-%m')
        leituras = self.plano_leitura.get(data_atual)

        if leituras:
            texto_completo = ""
            for livro, detalhes in leituras.items():
                texto_completo += buscar_trecho(self.biblia, livro, detalhes) + "\n\n"
            
            tela_leitura = TelaLeitura(texto=texto_completo, data_selecionada=datetime.now().strftime('%d-%m-%Y'), name='leitura')
            self.manager.add_widget(tela_leitura)
            self.manager.current = 'leitura'
        else:
            self.message_label.text = "Nenhuma leitura programada para hoje."

    def update_text_size(self, instance, value):
        instance.text_size = (instance.width, None)  # Atualiza o tamanho do texto

    def open_bible(self, instance):
        self.manager.current = 'book_screen'

    def open_plan(self, instance):
        # Aqui você pode integrar a tela do calendário diretamente
        # Em vez de abrir um subprocesso, seria melhor integrar diretamente no ScreenManager
        # Porém, para manter a estrutura atual, vamos abrir um subprocesso
        subprocess.Popen(["python", "calendario.py"])  # Certifique-se de que 'calendario.py' está no mesmo diretório

    def close_app(self, instance):
        App.get_running_app().stop()

# Classe para representar cada livro na Bíblia
class BookRow(Button):
    def __init__(self, abbreviation, name, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{name}"
        self.size_hint_y = None
        self.height = 40
        self.background_color = (0, 0, 0, 1)
        self.color = (1, 1, 1, 1)
        self.abbreviation = abbreviation
        self.name = name
        self.halign = 'left'
        self.text_size = (self.width, None)
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args):
        self.text_size = (self.width, None)

# Classe para representar cada capítulo
class ChapterButton(Button):
    def __init__(self, chapter_number, **kwargs):
        super().__init__(**kwargs)
        self.text = str(chapter_number)
        self.size_hint = (None, None)
        self.size = (60, 60)
        self.background_color = (0, 0, 0, 1)
        self.color = (1, 1, 1, 1)
        self.chapter_number = chapter_number

# Exemplo de como exibir a grade de capítulos centralizada
class ChapterGrid(BoxLayout):
    def __init__(self, total_chapters, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        # Cria a grade de capítulos
        chapter_grid = GridLayout(cols=5, spacing=10, size_hint_y=None)
        chapter_grid.bind(minimum_height=chapter_grid.setter('height'))

        # Adiciona os botões de capítulos ao GridLayout
        for i in range(1, total_chapters + 1):
            chapter_button = ChapterButton(chapter_number=i)
            chapter_grid.add_widget(chapter_button)

        # Define a altura da grade
        chapter_grid.height = (60 + 10) * ((total_chapters + 4) // 5)  # Ajusta a altura com base na quantidade de capítulos

        # Layout horizontal para centralizar a grade
        central_layout = BoxLayout(orientation='horizontal', padding=(20, 0), size_hint_y=None, height=100)
        
        # Adiciona espaços vazios nas laterais
        central_layout.add_widget(Widget(size_hint_x=None, width=20))  # Espaço vazio à esquerda
        central_layout.add_widget(chapter_grid)  # Adiciona a grade de capítulos
        central_layout.add_widget(Widget(size_hint_x=None, width=20))  # Espaço vazio à direita

        # Adiciona o layout central ao layout principal
        self.add_widget(central_layout)



# Classe para representar cada versículo
class VerseRow(Label):
    def __init__(self, verse_number, verse_text, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{verse_number}. {verse_text}"
        self.size_hint_y = None
        self.height = 60  # Aumentar a altura para mais espaçamento entre linhas
        self.color = (1, 1, 1, 1)
        self.verse_number = verse_number
        self.verse_text = verse_text
        self.halign = 'left'
        self.valign = 'top'
        self.text_size = (self.width - 20, None)  # Ajuste a largura com margem
        self.bind(size=self._update_text_size)

    def _update_text_size(self, *args):
        self.text_size = (self.width - 20, None)

# Tela de Listagem de Livros
class BookScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

        # Cabeçalho
        header = BoxLayout(size_hint_y=None, height=50, padding=10, spacing=10)
        header.add_widget(Button(text='<', size_hint_x=0.1, background_color=(0, 0, 0, 1), on_press=self.go_back))
        header.add_widget(Label(text='Índice', size_hint_x=0.9, color=(1, 1, 1, 1), font_size=20))
        self.layout.add_widget(header)

        # Lista de livros
        scrollview = ScrollView()
        self.books_layout = GridLayout(cols=1, size_hint_y=None, spacing=5, padding=5)
        self.books_layout.bind(minimum_height=self.books_layout.setter('height'))
        scrollview.add_widget(self.books_layout)

        # Carregar a Bíblia
        self.biblia = carregar_biblia()
        for book in self.biblia.findall('b'):
            abbreviation = book.get('id')
            name = book.get('n')
            book_row = BookRow(abbreviation, name)
            book_row.bind(on_press=self.open_chapters)
            self.books_layout.add_widget(book_row)

        self.layout.add_widget(scrollview)

    def go_back(self, instance):
        self.manager.current = 'home_screen'

    def open_chapters(self, instance):
        App.get_running_app().chapter_screen.load_chapters(instance.abbreviation, instance.name)
        self.manager.current = 'chapter_screen'

# Tela de Listagem de Capítulos
class ChapterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

        # Cabeçalho
        self.header = BoxLayout(size_hint_y=None, height=50, padding=10, spacing=10)
        self.header.add_widget(Button(text='<', size_hint_x=0.1, background_color=(0, 0, 0, 1), on_press=self.go_back))
        self.book_label = Label(text='Capítulos', size_hint_x=0.9, color=(1, 1, 1, 1), font_size=20)
        self.header.add_widget(self.book_label)
        self.layout.add_widget(self.header)

        # Lista de capítulos
        self.scrollview = ScrollView()
        self.chapters_layout = GridLayout(cols=5, size_hint_y=None, spacing=10, padding=10)
        self.chapters_layout.bind(minimum_height=self.chapters_layout.setter('height'))
        self.scrollview.add_widget(self.chapters_layout)
        self.layout.add_widget(self.scrollview)

    def go_back(self, instance):
        self.manager.current = 'book_screen'

    def load_chapters(self, abbreviation, name):
        self.book_label.text = name
        self.chapters_layout.clear_widgets()
        self.book_abbreviation = abbreviation
        book = self.manager.get_screen('book_screen').biblia.find(f".//b[@id='{abbreviation}']")
        if book is not None:
            for chapter in book.findall('c'):
                chapter_number = chapter.get('n')
                chapter_button = ChapterButton(chapter_number)
                chapter_button.bind(on_press=self.open_verses)
                self.chapters_layout.add_widget(chapter_button)
        else:
            self.chapters_layout.add_widget(Label(text="Livro não encontrado.", color=(1,1,1,1)))

    def open_verses(self, instance):
        App.get_running_app().verse_screen.load_verses(self.book_abbreviation, instance.chapter_number)
        self.manager.current = 'verse_screen'

# Tela de Listagem de Versículos
class VerseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)

        # Cabeçalho
        self.header = BoxLayout(size_hint_y=None, height=50, padding=10, spacing=10)
        self.header.add_widget(Button(text='<', size_hint_x=0.1, background_color=(0, 0, 0, 1), on_press=self.go_back))
        self.chapter_label = Label(text='Versículos', size_hint_x=0.9, color=(1, 1, 1, 1), font_size=20)
        self.header.add_widget(self.chapter_label)
        self.layout.add_widget(self.header)

        # Lista de versículos
        self.scrollview = ScrollView()
        self.verses_layout = GridLayout(cols=1, size_hint_y=None, spacing=10, padding=10)
        self.verses_layout.bind(minimum_height=self.verses_layout.setter('height'))
        self.scrollview.add_widget(self.verses_layout)
        self.layout.add_widget(self.scrollview)

    def go_back(self, instance):
        self.manager.current = 'chapter_screen'

    def load_verses(self, book_abbreviation, chapter_number):
        self.chapter_label.text = f"Capítulo {chapter_number}"
        self.verses_layout.clear_widgets()
        book = self.manager.get_screen('book_screen').biblia.find(f".//b[@id='{book_abbreviation}']")
        if book is not None:
            chapter = book.find(f".//c[@n='{chapter_number}']")
            if chapter is not None:
                for verse in chapter.findall('v'):
                    verse_number = verse.get('n')
                    verse_text = verse.text
                    verse_row = VerseRow(verse_number, verse_text)
                    self.verses_layout.add_widget(verse_row)
            else:
                self.verses_layout.add_widget(Label(text="Capítulo não encontrado.", color=(1,1,1,1)))
        else:
            self.verses_layout.add_widget(Label(text="Livro não encontrado.", color=(1,1,1,1)))

# Aplicativo Principal
class BibliaApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoadingScreen(name='loading_screen'))
        sm.add_widget(HomeScreen(name='home_screen'))
        sm.add_widget(BookScreen(name='book_screen'))
        sm.add_widget(ChapterScreen(name='chapter_screen'))
        sm.add_widget(VerseScreen(name='verse_screen'))

        # Armazenando referências para ChapterScreen e VerseScreen
        self.chapter_screen = sm.get_screen('chapter_screen')
        self.verse_screen = sm.get_screen('verse_screen')

        # Mudar para a tela de carregamento e, em seguida, para a tela inicial
        Clock.schedule_once(lambda dt: setattr(sm, 'current', 'home_screen'), 3)

        return sm

if __name__ == '__main__':
    BibliaApp().run()