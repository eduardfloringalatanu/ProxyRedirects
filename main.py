import random
import time
import sys
import threading
import socket
import struct

REDIRECT_ADDRESS = "ip:port"

LOCK = threading.Lock()

HEARTBEAT = 1  # time interval (in minutes) register-to-master-server requests

CONNECTIONLESS_PACKET_PREFIX = b"\xFF\xFF\xFF\xFF"

SERVER_NAMES = ["server_name"]

MAP_NAMES = ["de_dust2", "de_train", "de_aztec", "cs_office", "cs_italy", "cs_assault", "ka_acer_2", "35hp_2",
             "1hp_final_3", "fy_snow", "de_inferno", "de_vertigo", "awp_india", "zm_ice_attack3", "zm_dust_world",
             "zm_deko2", "zm_foda", "deathrun_arctic", "deathrun_temple", "deathrun_forest", "deathrun_projetocs2"]

PLAYER_NAMES = ["player_name"]

MAXIMUM_NUMBERS_OF_PLAYERS = [32, 64, 128, 255]

MASTER_SERVER_ADDRESSES = [("hl1master.steampowered.com", 27011),
                           ("hl2master.steampowered.com", 27011),
                           ("hl2master.steampowered.com", 27012)]

def listener(port: int, previous_time: float):
    LOCK.acquire()

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("", port))
            s.setblocking(False)

            print("Redirect opened on port " + str(port) + ".")

            break
        except OSError:
            port += 1

    LOCK.release()

    while True:
        current_time = time.time()

        if (current_time - previous_time) >= (HEARTBEAT * 60):
            challenge_request = b"\x71"

            for master_server_address in MASTER_SERVER_ADDRESSES:
                s.sendto(challenge_request, master_server_address)

            previous_time = current_time

        try:
            data, address = s.recvfrom(1024)

            if data[0:4] == CONNECTIONLESS_PACKET_PREFIX:
                maximum_number_of_players = random.choice(MAXIMUM_NUMBERS_OF_PLAYERS)
                number_of_players = random.randint(0, maximum_number_of_players - 1)
                map_name = random.choice(MAP_NAMES)

                if data[4:6] == b"\x73\x0A":  # register to master server
                    challenge = int.from_bytes(data[6:10], "little")

                    challenge_response = b"\x30\x0A"
                    challenge_response += b"\\protocol\\48"
                    challenge_response += b"\\challenge\\" + str(challenge).encode()
                    challenge_response += b"\\players\\" + str(number_of_players).encode()
                    challenge_response += b"\\max\\" + str(maximum_number_of_players).encode()
                    challenge_response += b"\\bots\\0"
                    challenge_response += b"\\gamedir\\cstrike"
                    challenge_response += b"\\map\\" + map_name.encode()
                    challenge_response += b"\\type\\d"
                    challenge_response += b"\\password\\0"
                    challenge_response += b"\\os\\l"
                    challenge_response += b"\\secure\\0"
                    challenge_response += b"\\lan\\0"
                    challenge_response += b"\\version\\1.1.2.7/Stdio"
                    challenge_response += b"\\region\\255"
                    challenge_response += b"\\product\\cstrike"
                    challenge_response += b"\x0A"

                    s.sendto(challenge_response, address)

                if data[4:16] == b"getchallenge":
                    s2a_proxy_redirect_request = b"\x4C" + REDIRECT_ADDRESS.encode()  # + b"\x00"

                    s.sendto(CONNECTIONLESS_PACKET_PREFIX + s2a_proxy_redirect_request, address)

                if data[4:24] == b"TSource Engine Query":
                    a2s_info_response = b"\x49"  # a2s_info prefix
                    a2s_info_response += b"\x30"  # protocol (48)
                    a2s_info_response += b"Redirect by Magister\x00"  # server name
                    a2s_info_response += map_name.encode() + b"\x00"  # map name
                    a2s_info_response += b"cstrike\x00"  # game directory
                    a2s_info_response += b"Counter-Strike\x00"  # game description
                    a2s_info_response += b"\x0A\x00"  # app id (10)
                    a2s_info_response += number_of_players.to_bytes(1, "little")  # number of players
                    a2s_info_response += maximum_number_of_players.to_bytes(1, "little")  # maximum number of players
                    a2s_info_response += b"\x00"  # number of bots
                    a2s_info_response += b"d"  # server type (dedicated)
                    a2s_info_response += b"l"  # operating system (linux)
                    a2s_info_response += b"\x00"  # password protected (False)
                    a2s_info_response += b"\x00"  # VAC protected (False)
                    a2s_info_response += b"1.1.2.7/Stdio\x00"  # version

                    s.sendto(CONNECTIONLESS_PACKET_PREFIX + a2s_info_response, address)

                if data[4:5] == b"U":
                    a2s_player_response = b"\x44"

                    for i in range(0, number_of_players):
                        a2s_player_response += i.to_bytes(1, "little")  # player index
                        a2s_player_response += b"player_name\x00"  # player name

                        score = random.randint(0, 30)
                        duration = float(random.randint(600, 1800))

                        a2s_player_response += score.to_bytes(4, "little")  # player score
                        a2s_player_response += struct.pack("f", duration)  # player duration

                    s.sendto(CONNECTIONLESS_PACKET_PREFIX + a2s_player_response, address)
        except BlockingIOError:
            pass


threads = []


def main():
    random.seed(time.time())

    if len(sys.argv) < 2:
        return print("Syntax: main.py <redirects> <port>")

    redirects = int(sys.argv[1])

    if len(sys.argv) < 3:
        port = 27015
    else:
        port = int(sys.argv[2])

    for i in range(redirects):
        threads.append(threading.Thread(target=listener, args=(port, 0.0,)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
