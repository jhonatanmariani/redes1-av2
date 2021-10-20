from libs import *

class Pacote:
    def __init__(self, pickled=None, seq_num=0, dados_coletados=b'', ack='', arquivo='', status=''):
        if pickled is not None:
            self.pacote = pickle.loads(pickled)
        else:
            self.pacote = {
                "status": status,
                "arquivo": arquivo,
                "ack": ack,
                "seq_num": seq_num,
                "checksum": self.checksum(sha1(dados_coletados).hexdigest()) if dados_coletados else '',
                "dados_coletados": dados_coletados
            }

    def __print__(self):
        status = self.__get__('status')
        arquivo = self.__get__('arquivo')
        ack = self.__get__('ack')
        seq_num = str(self.__get__('seq_num'))

        if ack == '+':
            print(colored('ACK positivo ' + seq_num, color='green'))
        elif ack == '-':
            print(colored('ACK negativo ' + seq_num, color='red'))
        elif arquivo:
            print(colored('Requisitando arquivo: ' + arquivo, color='cyan'))
        elif status == 'encontrado':
            print(colored('Arquivo encontrado, recebendo', color='blue'))
        elif status == 'nao_encontrado':
            print(colored('Arquivo não encontrado', color='red'))
        else:
            print(colored('Pacote recebido ' + seq_num, color='yellow'))

    def __get__(self, campo):
        if campo == 'seq_num':
            return str(self.pacote[campo])
        else:
            return self.pacote[campo]
    
    def checksum(self, dados_coletados):
        """
        Cálcula e retorna o checksum de uma dado
        """
        # 16 bit chunk
        tamanho_dado = len(dados_coletados)
        if (tamanho_dado % 2) != 0:
            dados_coletados += "0"

        sum = 0
        for i in range(0, tamanho_dado, 2):
            data16 = ord(dados_coletados[i]) + (ord(dados_coletados[i+1]) << 8)
            sum = self.carry(sum, data16)

        return ~sum & 0xffff

    def __dumb__(self):
        return pickle.dumps(self.pacote)

    def carry(self, sum, data16):
        sum = sum + data16
        return (sum & 0xffff) + (sum >> 16)
