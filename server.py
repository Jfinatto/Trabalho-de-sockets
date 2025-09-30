import socket
import time
import threading
import os

# --- Constantes ---
HOST = '127.0.0.1'  # Endereço do servidor (localhost)
TCP_PORT = 9998
UDP_PORT = 9999
FILENAME = 'file_example_MP4_1920_18MG.mp4'
BUFFER_SIZE_TCP = 4096
BUFFER_SIZE_UDP = 1400
EOF_MARKER = b"<EOF>" # Marcador de fim de arquivo para UDP

def handle_tcp_client(conn, addr):
    """Lida com uma conexão de cliente TCP."""
    print(f"[TCP] Conexão recebida de {addr}")
    try:
        # 1. Verificar se o arquivo existe
        if not os.path.exists(FILENAME):
            print(f"[TCP] Erro: Arquivo '{FILENAME}' não encontrado.")
            conn.sendall(b"ERRO: ARQUIVO NAO ENCONTRADO")
            return

        # 2. Enviar o tamanho do arquivo primeiro para o cliente saber o que esperar
        file_size = os.path.getsize(FILENAME)
        conn.sendall(str(file_size).encode().ljust(16)) # Cabeçalho de tamanho fixo
        print(f"[TCP] Enviando arquivo '{FILENAME}' ({file_size} bytes)")

        # 3. Iniciar a contabilização do tempo e enviar o arquivo
        start_time = time.time()
        with open(FILENAME, 'rb') as f:
            while True:
                data = f.read(BUFFER_SIZE_TCP)
                if not data:
                    break # Fim do arquivo
                conn.sendall(data)
        
        end_time = time.time()
        
        # 4. Calcular e enviar o tempo de transmissão
        duration = end_time - start_time
        print(f"[TCP] Arquivo enviado em {duration:.4f} segundos.")
        
        # O envio do tempo é feito após o fechamento do arquivo
        # O cliente espera por esta mensagem final
        conn.sendall(str(duration).encode())

    except socket.error as e:
        print(f"[TCP] Erro de socket: {e}")
    finally:
        conn.close()
        print(f"[TCP] Conexão com {addr} fechada.")

def start_tcp_server():
    """Inicia o servidor TCP em uma thread separada."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, TCP_PORT))
    server_socket.listen(1)
    print(f"[TCP] Servidor escutando em {HOST}:{TCP_PORT}")

    while True:
        conn, addr = server_socket.accept()
        # Para cada cliente, uma nova thread seria ideal, mas para 1 cliente é ok
        handle_tcp_client(conn, addr)

def start_udp_server():
    """Inicia o servidor UDP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST, UDP_PORT))
    print(f"[UDP] Servidor escutando em {HOST}:{UDP_PORT}")

    while True:
        # 1. Espera por uma mensagem inicial do cliente
        print("[UDP] Aguardando mensagem do cliente para iniciar a transferência...")
        try:
            message, client_address = server_socket.recvfrom(BUFFER_SIZE_UDP)
        except ConnectionResetError:
            # No Windows, um sendto() para um socket que não está mais ouvindo pode gerar este erro
            print("[UDP] Erro de conexão resetada. Cliente pode ter fechado. Reiniciando.")
            continue

        if message.decode() == 'START':
            print(f"[UDP] Requisição recebida de {client_address}. Iniciando transferência.")

            # 2. Verificar se o arquivo existe
            if not os.path.exists(FILENAME):
                print(f"[UDP] Erro: Arquivo '{FILENAME}' não encontrado.")
                server_socket.sendto(b"ERRO: ARQUIVO NAO ENCONTRADO", client_address)
                continue

            file_size = os.path.getsize(FILENAME)
            print(f"[UDP] Enviando arquivo '{FILENAME}' ({file_size} bytes)")

            # 3. Iniciar a contabilização do tempo e enviar o arquivo
            start_time = time.time()
            with open(FILENAME, 'rb') as f:
                while True:
                    data = f.read(BUFFER_SIZE_UDP)
                    if not data:
                        break # Fim do arquivo
                    server_socket.sendto(data, client_address)
            
            # 4. Enviar um marcador de fim de arquivo
            server_socket.sendto(EOF_MARKER, client_address)
            
            end_time = time.time()

            # 5. Calcular e enviar o tempo de transmissão
            duration = end_time - start_time
            print(f"[UDP] Arquivo enviado em {duration:.4f} segundos.")
            server_socket.sendto(str(duration).encode(), client_address)
            print(f"[UDP] Transferência para {client_address} concluída.")


if __name__ == "__main__":
    print("Servidor de Transferência de Arquivos")
    # Usar threads para que ambos servidores possam rodar "simultaneamente"
    # Neste caso, vamos rodá-los sequencialmente para simplificar, 
    # pois o UDP só começa após uma interação inicial. 
    # Uma abordagem com threads seria mais robusta, mas esta funciona para o teste.
    
    # A melhor abordagem é rodar os dois listeners em threads separadas
    tcp_thread = threading.Thread(target=start_tcp_server)
    udp_thread = threading.Thread(target=start_udp_server)

    tcp_thread.daemon = True
    udp_thread.daemon = True

    tcp_thread.start()
    udp_thread.start()

    print("\nServidores TCP e UDP iniciados. Pressione Ctrl+C para sair.")
    try:
        # Mantém a thread principal viva para que as threads daemons continuem rodando
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServidor encerrado.")