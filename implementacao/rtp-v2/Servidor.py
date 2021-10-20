from libs import *
from Pacote import Pacote

PORTA_SERVIDOR = 9999
PROBABILIDADE_PERDA = 15
TIME_OUT = 2
PASTA_SERVIDOR = 'servidor/'
TIMEOUT_TENTATIVAS_CLIENTE = 50000
TAMANHO_PACKET = 3 * 1024
TAMANHO_PEDACO = 2 * 1024 # CHUNK

class Servidor:
    def __init__(self, ip='localhost', porta=9999):
        self.ip = ip
        self.porta = porta
        self.endereco = (self.ip, self.porta)
        self.threads = []
        self.thread_contador = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(self.endereco)

        print('Servidor: ', self.ip, self.endereco)

    # Retorna o pacote da requisição ou zero em caso de timeout
    def aguarda_requisicao(self, cliente, endereco):
        timeout_tentativas_cliente = TIMEOUT_TENTATIVAS_CLIENTE
        while timeout_tentativas_cliente:
            try:
                requisicao = cliente.recv(TAMANHO_PACKET)
                if requisicao:
                    pacote = Pacote(pickled=requisicao)
                    pacote.__print__()
                    return pacote
                else:
                    print('Cliente desconectado, endereco:', endereco)
                    break
            except timeout:
                timeout_tentativas_cliente -= 1
        return 0

    
    def listener(self):
        self.socket.listen()
        print('[Conectado no]', self.endereco)

        while True:
            try:
                cliente, endereco = self.socket.accept()
                print('Cliente connected, endereco: ', endereco)

                # Timeout do cliente em segundos
                cliente.settimeout(TIME_OUT)

                # Criação de nova thread para prover o cliente
                thread = Thread(target=self.disponibiliza_pacote_cliente, args=(cliente, endereco))
                self.threads.append(thread)
                thread.start()

                self.thread_contador += 1
                print('Cliente #:' + str(self.thread_contador))
            except KeyboardInterrupt:
                print('\nServidor finalizado, esperando todas as threads retornar')
                break

    def disponibiliza_pacote_cliente(self, cliente, endereco):
        tempo_total = datetime.now()
        pacote = self.aguarda_requisicao(cliente, endereco)
        if not pacote:
            return 1
        arquivo = PASTA_SERVIDOR + pacote.__get__('arquivo')

        # Se o arquivo for encontrado no servidor
        if os.path.isfile(arquivo):
            pacote = Pacote(status='encontrado')
            cliente.send(pacote.__dumb__())

            seq_num = 0
            bits = 0
            f = open(file=arquivo, mode='rb')
            dados_coletados = f.read(TAMANHO_PEDACO)

            while dados_coletados:
                bits += 8 * len(dados_coletados)

                # Construir pacote
                pacote = Pacote(dados_coletados=dados_coletados, seq_num=seq_num)

                # Envia e verifica arquivo corrompido    
                sender_checksum = pacote.__get__('checksum')
                reciever_checksum = pacote.checksum(sha1(dados_coletados).hexdigest())

                bin_sender_checksum = bin(pacote.checksum(sha1(dados_coletados).hexdigest()))
                bin_reciever_checksum = bin(pacote.__get__('checksum'))

                integer_sum = int(bin_sender_checksum, 2) + int(bin_reciever_checksum, 2)
                binary_sum = bin(integer_sum)
                only_bin = binary_sum.replace('0b', "")
                arquivo_corrompido = bin_sender_checksum == bin_reciever_checksum
                print(arquivo_corrompido)

                if not self.envia_pacote(pacote, cliente):
                    break
                seq_num += 1
                dados_coletados = f.read(TAMANHO_PEDACO)

            tempo_total = (datetime.now() - tempo_total).total_seconds()
            print('Enviado ' + str(bits) + ' bits, em ' +
                  str(tempo_total) + ' segundos')

            with open('log.txt', 'a') as log:
                run_metrics = '\'\'^||^\'\'' + '\n'
                run_metrics += 'THROUGHPUT=' + str(bits / tempo_total) + '\n'
                log.write(run_metrics)

        else: # caso o arquivo não seja encontrado, envia mensagem de arquivo não encontrado
            pacote = Pacote(status='nao_encontrado')
            cliente.send(pacote.__dumb__())

        print('Cliente desconectado, endereco: ', endereco)
        cliente.close()
    
    # Envia pacote apra o cliente e espera um ACK positivo
    # Retorna 1 para sucesso ou 0
    def envia_pacote(self, pacote, cliente):
        seq_num = pacote.__get__('seq_num')
        timeout_tentativas_cliente = TIMEOUT_TENTATIVAS_CLIENTE

        while timeout_tentativas_cliente:
            if randint(1, 100) > PROBABILIDADE_PERDA:
                cliente.send(pacote.__dumb__())
            else:
                print(colored('Simulando perda de pacote: ' + seq_num, 'red'))
            try:  # Aguarda por resposta ou timeout
                resposta = cliente.recv(TAMANHO_PACKET)

                if not resposta:
                    print('Cliente desconectado')
                    return 0

                pacote = Pacote(pickled=resposta)
                pacote.__print__()

                if pacote.__get__('ack') == '+':
                    return 1
                else:
                    print(colored('ACK negativo, reenviando : ' + seq_num, color='red'))
            except timeout:
                print(colored('Timeout, reenviando pacote: ' + seq_num, color='red'))
                timeout_tentativas_cliente -= 1
        return 0

if __name__ == '__main__':
    Servidor(porta=PORTA_SERVIDOR).listener()
