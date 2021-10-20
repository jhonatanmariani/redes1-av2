from Libs import *

DELIMITADOR_B = b'\'\'^||^\'\''  # 8

class Pacote:
    def __init__(self, res=None, seq_num=0, dados_coletados=b'',
                 ack='', arquivo='', status=''):
        self.keys = [
            "status",
            "arquivo",
            "ack",
            "seq_num",
            "checksum",
            "dados_coletados"
        ]
        if res is not None:
            self.packet = self.carregar(res)
        else:
            self.packet = {
                "status": status.encode(),
                "arquivo": arquivo.encode(),
                "ack": ack.encode(),
                "seq_num": int(seq_num).to_bytes(8, byteorder='little', signed=True),
                "checksum": self.checksum(dados_coletados),
                "dados_coletados": dados_coletados if dados_coletados else b'',
            }

        bytes_ficticios = 2000
        for val in self.packet.values():
            bytes_ficticios -= len(val)
        self.packet['dummy'] = b'x' * bytes_ficticios

    def __dump__(self):
        return DELIMITADOR_B.join(self.packet.values()) 

    def checksum(self, dados_coletados):
        """
        Cálcula e retorna o checksum de uma dado
        """
        # 16 bit chunk
        tamanho_dado = len(dados_coletados)
        dados_originais = dados_coletados

        if dados_originais == dados_coletados:
            return sha1(dados_coletados).hexdigest().encode()

        if (tamanho_dado % 2) != 0:
            dados_coletados += "0"

        soma = 0
        for i in range(0, tamanho_dado, 2):
            data16 = ord(dados_coletados[i]) + (ord(dados_coletados[i+1]) << 8)
            soma = self.carry(soma, data16)

        return ~soma & 0xffff

    def carry(self, soma, data16):
        soma += data16
        return (soma & 0xffff) + (soma >> 16)

    def carregar(self, res):
        packet = {}
        valores = res.split(DELIMITADOR_B)
        for key, val in zip(self.keys, valores):
            packet[key] = val
        return packet

    def validar(self):
        return self.packet['checksum'] == sha1(
            self.packet['dados_coletados']).hexdigest().encode()

    def __get__(self, campo_visualizado):
        if campo_visualizado == 'seq_num':
            return str(int.from_bytes((self.packet[campo_visualizado]),
                                      byteorder='little',
                                      signed=True))
        elif campo_visualizado == 'dados_coletados':
            return self.packet[campo_visualizado]
        else:
            return self.packet[campo_visualizado].decode()

    def __print__(self, endereco_origem='', endereco_de_envio=''):
        endereco_origem = str(endereco_origem)
        endereco_de_envio = str(endereco_de_envio)

        status = self.__get__('status')
        arquivo = self.__get__('arquivo')
        ack = self.__get__('ack')
        seq_num = self.__get__('seq_num')

        if ack == '+':
            print(colored('Ack Positivo ' + seq_num + (' => a partir de ' + endereco_origem if endereco_origem else ''), color='green'))
        elif ack == '-':
            print(colored('Ack Negativo ' + seq_num + (' => a partir de ' + endereco_origem if endereco_origem else ''), color='red'))
        elif arquivo:
            print(colored('Solicitando arquivo: ' + arquivo, color='cyan'))
        elif status == 'encontrado':
            print(colored('Arquivo encontrado, recebendo do servidor', color='green'))
        elif status == 'nao_encontrado':
            print(colored('Arquivo não encontrado', color='red'))
        else:
            print(colored('Pacote ' + seq_num + (' => a partir de ' + endereco_de_envio if endereco_de_envio else ''), color='yellow'))
