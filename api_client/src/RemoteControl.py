import socket
import sys
import os
from progress.bar import Bar

BUFFER_SIZE = 4096
PROPS_PATH = '../app/src/main/assets/server_config.properties'
SUPPORTED_SERVER_VERSIONS = [
    'v.0.1.1'
]
NUM_SENSORS = 3

class RemoteControl:
    """
    Provides communication methods with the smartphone
    running OpenCamera Sensors application
    """

    def __init__(self, hostname, timeout=None):
        """
        Args:
            hostname (str): Smartphones hostname (IP address) in the current network.
            Is displayed in the dialog when starting OpenCamera Sensors on the smartphone.
            timeout (float): Connection timeout in seconds
        """
        self._load_properties(PROPS_PATH)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(timeout)
        try:
            self.socket.connect((hostname, int(self.props['RPC_PORT'])))
            self.socket.settimeout(None)
        except socket.timeout:
            print("Connection timed out")
            sys.exit()

    def get_ts_file(self):
        """
        Gets last timestamp file contents
        """

        status, socket_file = self._send_and_get_response_status(
            self.props['GET_TS_FILE_REQUEST']
        )
        data = ""

        line = socket_file.readline()
        filename = line.strip("\n")

        # accept file contents
        line = socket_file.readline()
        while line.strip("\n") != self.props['CHUNK_END_DELIMITER']:
            # print('Received: %s' % (line.strip('\n')))
            data += line
            line = socket_file.readline()

        socket_file.close()
        return data, filename

    def start_video(self):
        """
        Starts video recording and receives phase and duration info
        :return: Tuple (phase, average duration, exposure time) - all in nanoseconds
        """
        status, socket_file = self._send_and_get_response_status(
            self.props['VIDEO_START_REQUEST']
        )
        # print(status)

        line = socket_file.readline()
        phase_ns = int(line)

        line = socket_file.readline()
        avg_duration_ns = float(line)

        line = socket_file.readline()
        exposure_time = int(line)

        socket_file.readline()
        return phase_ns, avg_duration_ns, exposure_time

    def stop_video(self):
        """
        Stops video recording
        """

        # receive response
        status, socket_file = self._send_and_get_response_status(
            self.props['VIDEO_STOP_REQUEST']
        )
        # print(status)

        line = socket_file.readline()
        while line.strip('\n') != self.props['CHUNK_END_DELIMITER']:
            # print(line)
            line = socket_file.readline()

    def get_hostnames(self):
        status, socket_file = self._send_and_get_response_status(
                    self.props['GET_HOSTNAMES_REQUEST']
                )
        line = socket_file.readline()
        hostnames = line.split(',')
        return hostnames

    def get_video(self, want_progress_bar, custom_filename, subdir):
        """
        Receives the last recorded video file, saves it in current directory
        :param want_progress_bar: (boolean) display progress bar during video loading
        :return: Saved video's filename
        """

        # open socket as a file with no buffering (to avoid losing part of the video bytes)
        socket_file = self.socket.makefile('rwb', 0)
        # send request message
        status, socket_file = self._send_and_get_response_status_bytes(
            (self.props['GET_VIDEO_REQUEST'] + "\n").encode()
        )
        # print(status)
        # get video data length
        line = socket_file.readline()
        data_length = int(line.decode())
        # get video filename
        line = socket_file.readline()
        filename = line.decode()
        filename = filename.strip("\n")
        print(filename)
        # end marker
        marker = socket_file.readline()
        # print(marker)
        # close socket file, start receiving video bytes until length
        socket_file.close()
        if want_progress_bar:
            with Bar('Downloading video', max=data_length) as bar:
                self._recv_video_file(os.path.join(subdir, custom_filename), data_length, bar)
        else:
            self._recv_video_file(os.path.join(subdir, custom_filename), data_length)
        return filename

    def _send_and_get_response_status(self, msg):
        # open socket as a file
        socket_file = self.socket.makefile("rw")
        # send request message
        socket_file.write(msg + '\n')
        socket_file.flush()
        # receive response
        status = socket_file.readline()
        version = socket_file.readline().strip('\n')
        if (version not in SUPPORTED_SERVER_VERSIONS):
            socket_file.close()
            self.socket.close()
            print('Status: %s' % status)
            raise RuntimeError('Unsupported app server version: %s' % version)
        if status.strip('\n') == self.props['ERROR']:
            msg = socket_file.readline()
            socket_file.close()
            self.socket.close()
            raise RuntimeError(msg)

        return status.strip('\n') == self.props['SUCCESS'], socket_file

    def _recv_video_file(self, filename, data_length, bar=None):
        recv_len = 0
        with open(filename, "wb") as video_file:
            while recv_len < data_length:
                more = self.socket.recv(BUFFER_SIZE)
                if not more:
                    raise EOFError()
                recv_len += len(more)
                video_file.write(more)
                if bar is not None:
                    bar.next(len(more))
                    sys.stdout.flush()
        if bar is not None:
            bar.finish()

    def _send_and_get_response_status_bytes(self, msg):
        # open socket as a file
        socket_file = self.socket.makefile("rwb", 0)
        # send request message
        socket_file.write(msg)
        socket_file.flush()
        # receive response
        status = socket_file.readline()
        version = socket_file.readline().decode().strip('\n')
        if (version not in SUPPORTED_SERVER_VERSIONS):
            socket_file.close()
            self.socket.close()
            raise RuntimeError('Unsupported app server version: %s' % version)
        if status.decode().strip('\n') == self.props['ERROR']:
            msg = socket_file.readline()
            socket_file.close()
            self.socket.close()
            raise RuntimeError(msg)

        return status.decode().strip('\n') == self.props['SUCCESS'], socket_file

    def _load_properties(self, filepath, sep='=', comment_char='#'):
        """
        Read the file passed as parameter as a properties file.
        """
        self.props = {}
        with open(filepath, "rt") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(comment_char):
                    key_value = line.split(sep)
                    key = key_value[0].strip()
                    value = sep.join(key_value[1:]).strip().strip('"')
                    self.props[key] = value

    def close(self):
        self.socket.close()
