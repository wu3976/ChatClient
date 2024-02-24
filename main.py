import sys
import tkinter as tk
import threading
import socket

# Modifiable configs
HOST = "107.23.176.51"  # IP address of the server
PORT = 8400  # Port to connect to
######### End ###############

MODE_RENAME = 0
MODE_PUBLIC_CHAT = 1
MODE_PRIVATE_CHAT = 2
MODE_GET_UNAME = 3 # mode for getting remote username for private chat


class ReceiveAndPrint(threading.Thread):
    def __init__(self, thread_name, thread_ID, client):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.thread_ID = thread_ID
        self.client = client

    # helper function to execute the threads
    def run(self):
        while True:
            data = self.client.skt.recv(4096)
            if not data:
                print("Remote server has closed the connection")
                self.client.skt.close()
                return
            data = data.decode("utf-8")
            print("[LOG] received from remote server: " + data)
            # detect if current response is a success for rename
            if len(data) >= 8 and data[:8] == "Success!":
                self.client.enable_all_buttons()
            self.client.append_to_eroutput(data)
class ChatClient:
    def __init__(self):
        self.tkroot = tk.Tk()
        self.remote_uname = ""
        self.buttonframe = tk.Frame(self.tkroot)
        self.sandlblframe = tk.Frame(self.tkroot)
        self.e_input = tk.Text(self.tkroot, width=30, height=10)
        self.e_output = tk.Text(self.tkroot, width=30, height=10, state=tk.DISABLED)
        self.e_routput = tk.Text(self.tkroot, width=30, height=10, state=tk.DISABLED)

        # root: sandlblframe
        self.b_send = tk.Button(self.sandlblframe, text="Send", command=self.send_message)
        self.b_send.grid(row=0, column=0)
        self.l_mode = tk.Label(self.sandlblframe, text="Mode: Rename")
        self.l_mode.grid(row=0, column=1)
        ####################################

        # root: buttonframe
        self.b_rename = tk.Button(self.buttonframe, text="Rename", command=self.switch_rename_mode)
        self.b_public_chat = tk.Button(self.buttonframe, text="Public Chat", command=self.switch_public_chat_mode)
        self.b_private_chat = tk.Button(self.buttonframe, text="Private Chat", command=self.switch_get_uname_mode)
        self.b_exit = tk.Button(self.buttonframe, text="Exit", command=self.exit_program)

        self.b_rename.grid(row=0, column=0)
        self.b_public_chat.grid(row=0, column=1)
        self.b_private_chat.grid(row=0, column=2)
        self.b_exit.grid(row=0, column=3)
        #################################

        self.buttonframe.grid(row=0, column=0)
        self.sandlblframe.grid(row=0, column=1)
        self.e_routput.grid(row=1, column=0)
        self.e_input.grid(row=1, column=2)
        self.e_output.grid(row=1, column=1)

        # default mode is rename mode
        self.mode = MODE_RENAME
        self.append_to_eoutput("[ACTION] Entering rename mode.\n"
                               "[PROMPT] Type in new username and click send button.\n")

        self.host = HOST
        self.port = PORT
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Connect to the server
            self.skt.connect((self.host, self.port))
        except Exception as e:
            print("Error:", e)
        print("Connected to server %s:%d" % (self.host, self.port))

    def start(self):
        self.recv_p_thread = ReceiveAndPrint("receive_and_print", 1000, self)
        self.recv_p_thread.start()
        #print("xxxxxxx")
        self.tkroot.mainloop()

    def append_to_eoutput(self, s):
        self.e_output.config(state=tk.NORMAL)
        self.e_output.insert(tk.END, s)
        self.e_output.see(tk.END)
        self.e_output.config(state=tk.DISABLED)

    def append_to_eroutput(self, s):
        self.e_routput.config(state=tk.NORMAL)
        self.e_routput.insert(tk.END, s)
        self.e_routput.see(tk.END)
        self.e_routput.config(state=tk.DISABLED)

    # disable all buttons except exit
    def disable_all_buttons(self):
        self.b_send.config(state=tk.DISABLED)
        self.b_public_chat.config(state=tk.DISABLED)
        self.b_rename.config(state=tk.DISABLED)
        self.b_private_chat.config(state=tk.DISABLED)

    # enable all buttons except exit
    def enable_all_buttons(self):
        self.b_send.config(state=tk.NORMAL)
        self.b_public_chat.config(state=tk.NORMAL)
        self.b_rename.config(state=tk.NORMAL)
        self.b_private_chat.config(state=tk.NORMAL)

    def update_mode_label(self):
        if self.mode == MODE_RENAME:
            self.l_mode.config(text="Mode: Rename")
        elif self.mode == MODE_PUBLIC_CHAT:
            self.l_mode.config(text="Mode: Public Chat")
        elif self.mode == MODE_PRIVATE_CHAT:
            self.l_mode.config(text="Mode: Private Chat")
        elif self.mode == MODE_GET_UNAME:
            self.l_mode.config(text="Enter remote username")
        else:
            print("Unknown mode: ", self.mode)
            sys.exit(1)

    def switch_rename_mode(self):
        self.mode = MODE_RENAME
        self.update_mode_label()
        self.append_to_eoutput("[ACTION] Entering rename mode.\n"
                               "[PROMPT] Type in new username and click send button.\n")

    def switch_public_chat_mode(self):
        self.mode = MODE_PUBLIC_CHAT
        self.update_mode_label()
        self.append_to_eoutput("[ACTION] Entering public chat mode.\n")

    def switch_private_chat_mode(self):
        self.mode = MODE_PRIVATE_CHAT
        self.update_mode_label()
        self.append_to_eoutput("[ACTION] Entering private chat mode.\n")

    def switch_get_uname_mode(self):
        self.mode = MODE_GET_UNAME
        self.update_mode_label()
        self.append_to_eoutput("[LOCAL] Requesting username list from server.\n" +
        "[PROMPT] Type in a username you want to chat and click send button to begin chat.\n")
        self.skt.sendall(b"who\n")

    def exit_program(self):
        self.skt.close()
        sys.exit(0)

    def send_message(self):
        msg = ""
        if self.mode == MODE_GET_UNAME:
            msg = self.e_input.get("1.0", tk.END)
            self.remote_uname = msg.strip()
            self.e_input.delete("1.0", tk.END)
            self.switch_private_chat_mode()
            return
        elif self.mode == MODE_RENAME:
            msg = "rename|" + self.e_input.get("1.0", tk.END)
            self.append_to_eoutput("[INFO] Rename request sent to server.\n")
            # Disable all ops temporarily to avoid contaminate socket buffer
            self.disable_all_buttons()
        elif self.mode == MODE_PUBLIC_CHAT:
            msg = self.e_input.get("1.0", tk.END)
            self.append_to_eoutput("[INFO] Message broadcasted to all online users.\n")
        elif self.mode == MODE_PRIVATE_CHAT:
            msg = "to|" + self.remote_uname + "|" + self.e_input.get("1.0", tk.END)
            self.append_to_eoutput("[INFO] Message sent to <" + self.remote_uname + ">.\n")
        print("[LOG] " + msg)
        self.e_input.delete("1.0", tk.END)
        self.skt.sendall(msg.encode("utf-8"))

    #def receive_and_print(self):
    #    while True:
    #        data = self.skt.recv(4096)
    #        if not data:
    #            print("Remote server has closed the connection")
    #            self.skt.close()
    #        data = data.decode("utf-8")
    #        self.e_routput.insert(tk.END, data)

if __name__ == "__main__":
    cli = ChatClient()
    cli.start()