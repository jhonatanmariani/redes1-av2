from Pacote import Pacote
from Libs import *

PASTA_SERVIDOR             = 'servidor/'
PORTA_SERVIDOR             = 9998
PROBABILIDADE_PERDA        = 15
TAMANHO_JANELA             = 1000
TIME_OUT                   = 2
TIMEOUT_TENTATIVAS_CLIENTE = 50000
TAMANHO_PACKET             = 3 * 1024
TAMANHO_PEDACO             = 2 * 1024 # CHUNK
DELIMITADOR_B              = b'\'\'^||^\'\''  # 8

class Servidor:
    def __init__(self, ip='localhost', port=9999):
        self.ip, self.port = ip, port
        self.endereco = (self.ip, self.port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.endereco)
        self.threads = []
        self.thread_count = 0

    def listener(self):
        self.socket.listen()
        print('[Ouvindo em ]', self.endereco)
        while True: 
            try:
                cliente, endereco = self.socket.accept()
                print('Cliente conectado, endereço: ', endereco)
                # Criação de nova thread para prover o cliente
                thread = Thread(target=self.serve_client,
                                args=(cliente, endereco)) 
                self.threads.append(thread)
                thread.start()
                self.thread_count += 1
                print('Cliente No: ' + str(self.thread_count))
            except KeyboardInterrupt:
                print('\nServidor encerrado, aguardando que todos os threads se juntem')
                break

    def enviar_janela(self, packets, base, cliente, endereco):
        fim = base + TAMANHO_JANELA
        fim = fim if fim < len(packets) else len(packets)

        # Envia pacote de janelas
        for pkt in packets[base:fim]:
            if randint(1, 100) > PROBABILIDADE_PERDA :
                pkt.__print__(endereco_de_envio=endereco)
                cliente.send(pkt.__dump__())
            else:
                print(colored('Simulando perda de pacote: ' + pkt.__get__('seq_num'), 'red'))

    # Envia pacote para o cliente e espera um ACK positivo
    # Retorna 1 para sucesso ou 0
    def comeca_transmissao(self, packets, cliente, endereco):
        base = 0
        self.enviar_janela(packets, base, cliente, endereco)

        contagem_tempo_limite_cliente = TIMEOUT_TENTATIVAS_CLIENTE
        while contagem_tempo_limite_cliente:
            if base >= len(packets):
                break

            fim = base + TAMANHO_JANELA
            fim = fim if fim < len(packets) else len(packets)

            cliente.settimeout(TIME_OUT)
            try:  # Aguarda por resposta ou timeout
                res = cliente.recv(TAMANHO_PACKET)
                if not res:
                    break
                pkt = Pacote(res=res)
                pkt.__print__(endereco_origem=endereco)
                seq_num = int(pkt.__get__('seq_num'))
                if base <= seq_num <= base + TAMANHO_JANELA:
                    if pkt.__get__('ack') == '+':
                        cliente.settimeout(None)
                        slots_livres = int(pkt.__get__('seq_num')) - base + 1
                        nFim = fim + slots_livres
                        nFim = nFim if nFim < len(packets) else len(packets)
                        new_pkts = packets[fim:nFim]
                        for pkt in new_pkts:
                            if randint(1, 100) > PROBABILIDADE_PERDA:
                                pkt.__print__(endereco_de_envio=endereco)
                                cliente.send(pkt.__dump__())
                            else:
                                print(colored('Simulando perda de pacote: ' +
                                              pkt.__get__('seq_num'), 'red'))
                        base += slots_livres
                else:
                    print(colored('Ack fora da janela, descarte ' + str(seq_num) + ' => para: ' + str(endereco), color='blue'))
            except timeout:
                print(colored('Tempo limite, janela de reenvio. => para: ' +
                              str(endereco), color='red'))
                self.enviar_janela(packets, base, cliente, endereco)
                contagem_tempo_limite_cliente -= 1
        # Retorna a quantidade de timeouts
        return TIMEOUT_TENTATIVAS_CLIENTE - contagem_tempo_limite_cliente

    # Retorna o pacote da requisição ou zero em caso de timeout
    def esperar_pedido(self, cliente, endereco):
        contagem_tempo_limite_cliente = TIMEOUT_TENTATIVAS_CLIENTE
        while contagem_tempo_limite_cliente:
            try:
                requisicao = cliente.recv(TAMANHO_PACKET)
                if requisicao:
                    pkt = Pacote(res=requisicao)
                    pkt.__print__(endereco_origem=endereco)
                    return pkt
                else:
                    print('Cliente desconectado, endereço:', endereco)
                    break
            except timeout:
                contagem_tempo_limite_cliente -= 1
        return 0

    def serve_client(self, cliente, endereco):
        tempo_total = datetime.now()
        pkt = self.esperar_pedido(cliente, endereco)
        if not pkt:
            return 1
        arquivo = PASTA_SERVIDOR + pkt.__get__('arquivo')
        if os.path.isfile(arquivo):  # Se o arquivo for encontrado no servidor
            pkt = Pacote(status='encontrado')
            cliente.send(pkt.__dump__())

            f = open(arquivo, mode='rb')
            dados_coletados = f.read()
            bits = len(dados_coletados) * 8

            # Constrói pacote
            packets = [
                Pacote(dados_coletados=dados_coletados[i: i + TAMANHO_PEDACO],
                       seq_num=i // TAMANHO_PEDACO)
                for i in range(0, len(dados_coletados), TAMANHO_PEDACO)
            ]

            timeout_count = self.comeca_transmissao(
                packets=packets, cliente=cliente, endereco=endereco)

            tempo_total = (datetime.now() - tempo_total).total_seconds()

            print('Enviado ' + str(bits) + ' bits, em ' +
                  str(tempo_total) + ' segundos, com ' +
                  str(timeout_count) + ' timeouts')

            with open('log.txt', 'a') as log:
                executar_metricas = DELIMITADOR_B.decode() + '\n'
                executar_metricas += 'TIPO=GO-BACK-N\n'
                executar_metricas += 'TAXA_TRANSFERENCIA=' + \
                    str(bits / tempo_total) + '\n'
                executar_metricas += 'PERDA_PACOTE=' + \
                    str(PROBABILIDADE_PERDA ) + '\n'

                log.write(executar_metricas)

        else:  # Se o arquivo não for encontrador, envia mensagem de não encontrado
            pkt = Pacote(status='nao_encontrado')
            cliente.send(pkt.__dump__())

        print('Cliente desconectado, endereço: ', endereco)
        cliente.close()


if __name__ == '__main__':
    Servidor(port=PORTA_SERVIDOR).listener()
