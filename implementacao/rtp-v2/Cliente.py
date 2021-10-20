from Servidor import *
from libs import *

PROBABILIDADE_CORROMPIMENTO = 15 # Porcentagem
TIME_OUT = 2
PASTA_CLIENTE = 'cliente/'
TIMEOUT_TENTATIVAS_CLIENTE = 50000
TAMANHO_PACKET = 3 * 1024

class Cliente:
    def __init__(self, ip='localhost', porta=9999):
        self.ip = ip
        self.porta = porta
        self.endereco_servidor = (self.ip, self.porta)
        print(self.endereco_servidor)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def fn_arquivo_recebido(self, arquivo):
        self.socket.settimeout(None)
        arquivo_recebido = PASTA_CLIENTE + arquivo

        open(file=arquivo_recebido, mode='wb').close()
        f = open(file=arquivo_recebido, mode='ab')

        while True:
            try:
                resposta = self.socket.recv(TAMANHO_PACKET)
                if not resposta:
                    print('Desconectado do ', self.endereco_servidor)
                    break

                pacote = Pacote(pickled=resposta)
                pacote.__print__()

                # print(type(pacote.__get__('data')))
                # print(pacote.__get__('checksum'))
                # print(bin(pacote.__get__('checksum')))
                
                # Simulador de corrompimento de pacote
                if randint(1, 100) > PROBABILIDADE_CORROMPIMENTO:
                    f.write(pacote.__get__('dados_coletados'))
                    # Envia ACK positivo
                    ack = Pacote(seq_num=pacote.__get__('seq_num'), ack='+')
                    self.socket.send(ack.__dumb__())
                else:# Envia ACK negativo
                    print(
                        colored(
                            'Simulando corrompimento de pacote (ACK negativo): ' +
                            pacote.__get__('seq_num'), color='red')
                    )
                    ack = Pacote(seq_num=pacote.__get__('seq_num'), ack='-')
                    self.socket.send(ack.__dumb__())
            except Exception as e:
                print(e)
                break
        f.close()
        self.socket.close()

    def request(self, arquivo):
        # Conexão com servidor
        self.socket.connect(self.endereco_servidor)
        self.socket.settimeout(TIME_OUT)
        print('Conectado com ', self.endereco_servidor)

        # Envia uma requisição com arquivo e espera a resposta
        timeout_tentativas = TIMEOUT_TENTATIVAS_CLIENTE
        while timeout_tentativas:
            # Envia a requisição
            pacote = Pacote(arquivo=arquivo)
            self.socket.send(pacote.__dumb__())
            try:
                resposta = self.socket.recv(TAMANHO_PACKET)
                if not resposta:
                    print('Desconectado do ', self.endereco_servidor)
                    break

                pacote = Pacote(pickled=resposta)
                pacote.__print__()
                if pacote.__get__('status') == 'encontrado':
                    break
                elif pacote.__get__('status') == 'nao_encontrado':
                    print('Arquivo não encontrado')
                    break
                else:
                    print('Bad response')
                    break
            except timeout:
                print('Timeout')
                timeout_tentativas -= 1

        if timeout_tentativas:
            self.fn_arquivo_recebido(arquivo)

cliente = Cliente(ip='127.0.0.1', porta=9999)
cliente.request('text.txt')
