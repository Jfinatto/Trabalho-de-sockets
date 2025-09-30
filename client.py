import socket
import os

# --- Constantes ---
SERVER_HOST = '127.0.0.1'
TCP_PORT = 9998
UDP_PORT = 9999
FILENAME_TCP = 'recebido_tcp.mp4'
FILENAME_UDP = 'recebido_udp.mp4'
BUFFER_SIZE_TCP = 4096
BUFFER_SIZE_UDP = 1400 # Deve ser o mesmo do servidor
EOF_MARKER = b"<EOF>" # Marcador de fim de arquivo para UDP

def receive_file_tcp():
    """Cliente para receber o arquivo via TCP."""
    # Limpa arquivo antigo se existir
    if os.path.exists(FILENAME_TCP):
        os.remove(FILENAME_TCP)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"[TCP] Conectando ao servidor em {SERVER_HOST}:{TCP_PORT}...")
        client_socket.connect((SERVER_HOST, TCP_PORT))
        print("[TCP] Conectado.")

        # 1. Receber o tamanho do arquivo
        header = client_socket.recv(16).strip()
        if not header:
            print("[TCP] Erro: Não recebeu o cabeçalho do tamanho do arquivo.")
            return

        # Checar por mensagem de erro do servidor
        if header.startswith(b"ERRO"):
            print(f"[TCP] Erro do servidor: {header.decode()}")
            return
            
        file_size = int(header.decode())
        bytes_recebidos = 0
        print(f"[TCP] Recebendo arquivo de {file_size} bytes...")

        # 2. Receber o arquivo
        with open(FILENAME_TCP, 'wb') as f:
            while bytes_recebidos < file_size:
                # Calcula quanto ainda falta receber para não ultrapassar
                bytes_a_ler = min(BUFFER_SIZE_TCP, file_size - bytes_recebidos)
                data = client_socket.recv(bytes_a_ler)
                if not data:
                    break # Conexão fechada inesperadamente
                f.write(data)
                bytes_recebidos += len(data)
        
        print(f"[TCP] Arquivo '{FILENAME_TCP}' recebido com sucesso ({bytes_recebidos} bytes).")

        # 3. Receber o tempo de transmissão
        duration_data = client_socket.recv(1024)
        duration = float(duration_data.decode())
        
        print("\n--- RESULTADO DA TRANSMISSÃO TCP ---")
        print(f"Tempo de transmissão medido pelo servidor: {duration:.4f} segundos.")
        print("-------------------------------------\n")

    except ConnectionRefusedError:
        print("[TCP] Erro: A conexão foi recusada. O servidor está rodando?")
    except Exception as e:
        print(f"[TCP] Ocorreu um erro: {e}")
    finally:
        client_socket.close()

def receive_file_udp():
    """Cliente para receber o arquivo via UDP."""
    # Limpa arquivo antigo se existir
    if os.path.exists(FILENAME_UDP):
        os.remove(FILENAME_UDP)
        
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # 1. Enviar mensagem para iniciar a transferência
        print(f"[UDP] Solicitando arquivo do servidor em {SERVER_HOST}:{UDP_PORT}...")
        client_socket.sendto(b'START', (SERVER_HOST, UDP_PORT))

        # 2. Receber o arquivo
        print(f"[UDP] Aguardando para receber o arquivo '{FILENAME_UDP}'...")
        with open(FILENAME_UDP, 'wb') as f:
            while True:
                data, server_addr = client_socket.recvfrom(BUFFER_SIZE_UDP + 50) # Buffer um pouco maior para segurança
                
                # Checa por mensagem de erro
                if data.startswith(b"ERRO"):
                    print(f"[UDP] Erro do servidor: {data.decode()}")
                    return
                    
                # Checa se é o marcador de fim de arquivo
                if data == EOF_MARKER:
                    break
                
                f.write(data)
        
        print(f"[UDP] Arquivo '{FILENAME_UDP}' recebido.")
        
        # 3. Receber o tempo de transmissão
        duration_data, _ = client_socket.recvfrom(1024)
        duration = float(duration_data.decode())
        
        print("\n--- RESULTADO DA TRANSMISSÃO UDP ---")
        print(f"Tempo de transmissão medido pelo servidor: {duration:.4f} segundos.")
        print("-------------------------------------\n")

    except Exception as e:
        print(f"[UDP] Ocorreu um erro: {e}")
    finally:
        client_socket.close()

def main_menu():
    """Apresenta o menu de escolha para o usuário."""
    while True:
        print("Escolha o protocolo para a transferência do arquivo:")
        print("1. TCP (Confiável)")
        print("2. UDP (Rápido, não confiável)")
        print("3. Sair")
        
        choice = input("Digite sua escolha (1/2/3): ")
        
        if choice == '1':
            receive_file_tcp()
        elif choice == '2':
            receive_file_udp()
        elif choice == '3':
            print("Encerrando o cliente.")
            break
        else:
            print("Opção inválida. Tente novamente.\n")

if __name__ == "__main__":
    main_menu()