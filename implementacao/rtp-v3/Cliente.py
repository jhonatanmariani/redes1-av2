from Libs import *
from Pacote import *

PASTA_CLIENTE              = 'cliente/'
NOME_ARQUIVO               = 'text.txt'
PORTA_SERVIDOR             = 9998
ENDERECO_SERVIDOR          = '127.0.0.1'
PROBABILIDADE_PERDA        = 15
TIME_OUT                   = 2
TIMEOUT_TENTATIVAS_CLIENTE = 50000
TAMANHO_PACKET             = 3 * 1024

class Cliente:
    def __init__(self, ip='localhost', port=9999):
        self.ip, self.port = ip, port
        self.endereco_servidor = (self.ip, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def fn_arquivo_recebido(self, arquivo):
        self.socket.settimeout(None)

        arquivo_recebido = PASTA_CLIENTE + arquivo
        open(arquivo_recebido, mode='wb').close()
        f = open(arquivo_recebido, mode='ab')
        esperado = 0

        while True:
            try:
                res = self.socket.recv(TAMANHO_PACKET)
                if not res:
                    print('Desconectado de', self.endereco_servidor)
                    break

                pkt = Pacote(res=res)
                pkt.__print__()

                # Simulação de corrompimento de pacote
                if randint(1, 100) > PROBABILIDADE_PERDA:
                    if int(pkt.__get__('seq_num')) == esperado:
                        f.write(pkt.__get__('dados_coletados'))
                        # Envia ACK positivo
                        ack = Pacote(seq_num=pkt.__get__('seq_num'), ack='+')
                        self.socket.send(ack.__dump__())
                        esperado += 1
                    elif int(pkt.__get__('seq_num')) < esperado:
                        # Envia ACK positivo
                        ack = Pacote(seq_num=pkt.__get__('seq_num'), ack='+')
                        self.socket.send(ack.__dump__())
                    else:
                        print(
                            colored(
                                'Pacote inesperado, esperando por ' +
                                str(esperado) +
                                ', derrubado: ' +
                                pkt.__get__('seq_num'), color='red')
                        )
                else:  # Envia ACK negativo
                    print(
                        colored(
                            'Simulando corrompimento de pacote (Ack negativo): ' +
                            pkt.__get__('seq_num'), color='red')
                    )
                    ack = Pacote(seq_num=pkt.__get__('seq_num'), ack='-')
                    self.socket.send(ack.__dump__())
            except Exception as e:
                print(e)
                break
        f.close()
        self.socket.close()

    def requisicao(self, arquivo):
        # Conexão com servidor
        self.socket.connect(self.endereco_servidor)
        self.socket.settimeout(TIME_OUT)
        print('Conectado a', self.endereco_servidor)

        # Envia uma requisição com arquivo e espera a resposta
        tentativas_tempo_limite = TIMEOUT_TENTATIVAS_CLIENTE
        while tentativas_tempo_limite:
            # Envia a requisição
            pkt = Pacote(arquivo=arquivo)
            self.socket.send(pkt.__dump__())
            try:
                res = self.socket.recv(TAMANHO_PACKET)
                if not res:
                    print('Desconectado de', self.endereco_servidor)
                    break

                pkt = Pacote(res=res)
                pkt.__print__()
                if pkt.__get__('status') == 'encontrado':
                    break
                elif pkt.__get__('status') == 'nao_encontrado':
                    print('Arquivo não encontrado')
                    break
                else:
                    print('Bad response')
                    break
            except timeout:
                print('Tempo limite de solicitação de arquivo')
                tentativas_tempo_limite -= 1

        if tentativas_tempo_limite:
            self.fn_arquivo_recebido(arquivo)

arquivo_solicitado = NOME_ARQUIVO
c = Cliente(port=PORTA_SERVIDOR)
c.requisicao(arquivo_solicitado)
