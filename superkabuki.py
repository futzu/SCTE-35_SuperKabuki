"""
Super Kabuki - SCTE-35 Packet injection

"""
import argparse
import sys
from collections import deque
from functools import partial
from operator import itemgetter
from threefive import Stream, Cue, TimeSignal
from threefive.crc import crc32
from threefive.bitn import NBin
from new_reader import reader
from iframes import IFramer

MAJOR = "0"
MINOR = "0"
MAINTAINENCE = "41"


def version():
    """
    version prints version as a string

    Odd number versions are releases.
    Even number versions are testing builds between releases.

    Used to set version in setup.py
    and as an easy way to check which
    version you have installed.

    """
    return f"{MAJOR}.{MINOR}.{MAINTAINENCE}"


def version_number():
    """
    version_number returns version as an int.
    if version() returns 2.3.01
    version_number will return 2301
    """
    return int(f"{MAJOR}{MINOR}{MAINTAINENCE}")


def to_stderr(data):
    """
    print to sys.stderr.buffer aka 2
    """
    print(data, file=sys.stderr)


class SuperKabuki(Stream):
    """
    Super Kabuki - SCTE-35 Packet injection

    """

    CUEI_DESCRIPTOR = b"\x05\x04CUEI"

    def __init__(self, tsdata=None):
        self.infile = None
        self.outfile = "outfile.ts"
        if isinstance(tsdata, str):
            self.outfile = f'superkabuki-{tsdata.rsplit("/",1)[1]}'
        super().__init__(tsdata)
        self.pmt_payload = None
        self.scte35_pid = 0x86
        self.scte35_cc = 0
        self.iframer = IFramer(shush=True)
        self.sidecar = deque()
        self.sidecar_file = "sidecar.txt"
        self.time_signals = False
        self._parse_args()
        super().__init__(self.infile)

    def _parse_args(self):
        """
        _parse_args parse command line args
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-i",
            "--input",
            default=sys.stdin.buffer,
            help=""" Input source, like "/home/a/vid.ts"
                                    or "udp://@235.35.3.5:3535"
                                    or "https://futzu.com/xaa.ts"
                                    (default sys.stdin.buffer)
                                    """,
        )

        parser.add_argument(
            "-o",
            "--output",
            default=sys.stdout.buffer,
            help="""Output file  (default sys.stdout.buffer)""",
        )

        parser.add_argument(
            "-s",
            "--sidecar",
            default="sidecar.txt",
            help=""" Sidecar file for SCTE35 (default sidecar.txt)""",
        )
        parser.add_argument(
            "-p",
            "--scte35_pid",
            default=0x86,
            type=int,
            help="""Pid for SCTE-35 packets, can be hex or integer. (default 0x86)""",
        )

        parser.add_argument(
            "-t",
            "--time_signals",
            action="store_const",
            default=False,
            const=True,
            help="Flag to insert Time Signal cues at iframes.",
        )
        parser.add_argument(
            "-v",
            "--version",
            action="store_const",
            default=False,
            const=True,
            help="Show version",
        )

        args = parser.parse_args()
        self._apply_args(args)

    def _apply_args(self, args):
        if args.scte35_pid and args.input:
            self.outfile = args.output
            self.infile = args.input
            self.sidecar_file = args.sidecar
            self._tsdata = reader(args.input)
            #self.pid2int(args.scte35_pid)
            self.scte35_pid = args.scte35_pid
            self.time_signals = args.time_signals
        #else:
         #   sys.exit()

    def _bump_cc(self):
        self.scte35_cc = (self.scte35_cc + 1) % 16

    def _pmt_scte35_stream(self):
        if self.scte35_pid:
            nbin = NBin()
            stream_type = b"\x86"
            nbin.add_bites(stream_type)
            nbin.add_int(7, 3)  # reserved  0b111
            nbin.add_int(self.scte35_pid, 13)
            nbin.add_int(15, 4)  # reserved 0b1111
            es_info_length = 0
            nbin.add_int(es_info_length, 12)
            scte35_stream = nbin.bites
            return scte35_stream

    def encode(self):
        """
        encode parses the video input,
        adds the SCTE-35 PID to the PMT,
        parses the sidecar file,
        and injects SCTE-35 Packets,

        """
        to_stderr(f"Writing {self.outfile}")
        if isinstance(self.outfile, str):
            self.outfile = open(self.outfile, "wb")
        with self.outfile as out_file:
            for pkt in self._find_start():
                pid = self._parse_info(pkt)
                if self._pusi_flag(pkt):
                    self._parse_pts(pkt, pid)
                self._program_stream_map(pkt, pid)
                pts = self.iframer.parse(pkt)  # insert on iframe
                if pts:
                    if self.time_signals:
                        out_file.write(self._gen_time_signal(pts))
                    self.load_sidecar(pts)
                    scte35_pkt = self.chk_sidecar_cues(pts)
                    if scte35_pkt:
                        out_file.write(scte35_pkt)
                if pid in self.pids.pmt:
                    if self.pmt_payload:
                        pkt = pkt[:4] + self.pmt_payload
                out_file.write(pkt)

    def _gen_time_signal(self, pts):
        cue = Cue()
        cue.command = TimeSignal()
        cue.command.time_specified_flag = True
        cue.command.pts_time = pts
        cue.encode()
        cue.decode()
        nbin = NBin()
        nbin.add_int(71, 8)  # sync byte
        nbin.add_flag(0)  # tei
        nbin.add_flag(1)  # pusi
        nbin.add_flag(0)  # tp
        nbin.add_int(self.scte35_pid, 13)
        nbin.add_int(0, 2)  # tsc
        nbin.add_int(1, 2)  # afc
        nbin.add_int(self.scte35_cc, 4)  # cont
        nbin.add_bites(b"\x00")
        nbin.add_bites(cue.bites)
        pad_size = 188 - len(nbin.bites)
        padding = b"\xff" * pad_size
        nbin.add_bites(padding)
        self._bump_cc()
        return nbin.bites

    def load_sidecar(self, pts):
        """
        _load_sidecar reads (pts, cue) pairs from
        the sidecar file and loads them into X9K3.sidecar
        if live, blank out the sidecar file after cues are loaded.
        """
        try:
            with reader(self.sidecar_file) as sidefile:
                for line in sidefile:
                    line = line.decode().strip().split("#", 1)[0]
                    if len(line):
                        insert_pts, cue = line.split(",", 1)
                        insert_pts = float(insert_pts)
                        if insert_pts == 0.0:
                            insert_pts = pts
                        if insert_pts >= pts:
                            if [insert_pts, cue] not in self.sidecar:
                                to_stderr((insert_pts, cue))
                                self.sidecar.append([insert_pts, cue])
                                self.sidecar = deque(
                                    sorted(self.sidecar, key=itemgetter(0))
                                )
        except:
            pass

    # with open(self.sidecar_file, "w") as scf:
    #    scf.close()

    def chk_sidecar_cues(self, pts):
        """
        _chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            if (pts - 10) <= float(self.sidecar[0][0]) <= pts:
                cue_mesg = self.sidecar.popleft()[1]
                return self.mk_scte35_pkt(cue_mesg)
        return False

    def mk_scte35_pkt(self, cue_mesg):
        """
        Make a SCTE-35 packet,
        with cue_mesg as the payload.
        """
        cue = Cue(cue_mesg)
        cue.decode()
        nbin = NBin()
        nbin.add_int(71, 8)  # sync byte
        nbin.add_flag(0)  # tei
        nbin.add_flag(1)  # pusi
        nbin.add_flag(0)  # tp
        nbin.add_int(self.scte35_pid, 13)
        nbin.add_int(0, 2)  # tsc
        nbin.add_int(1, 2)  # afc
        nbin.add_int(self.scte35_cc, 4)  # cont
        nbin.add_bites(b"\x00")
        nbin.add_bites(cue.bites)
        pad_size = 188 - len(nbin.bites)
        padding = b"\xff" * pad_size
        nbin.add_bites(padding)
        self._bump_cc()
        # to_stderr(nbin.bites)
        return nbin.bites

    def _program_stream_map(self, pkt, pid):
        pay = self._parse_payload(pkt)
        if pay.startswith(b"\x00\x00\x01\xbc"):
            to_stderr("psm")
            to_stderr((pid, pay))

    def _regen_pmt(self, n_seclen, pcr_pid, n_proginfolen, n_info_bites, n_streams):
        nbin = NBin()
        nbin.add_int(2, 8)  # 0x02
        nbin.add_int(1, 1)  # section Syntax indicator
        nbin.add_int(0, 1)  # 0
        nbin.add_int(3, 2)  # reserved
        nbin.add_int(n_seclen, 12)  # section length
        nbin.add_int(1, 16)  # program number
        nbin.add_int(3, 2)  # reserved
        nbin.add_int(0, 5)  # version
        nbin.add_int(1, 1)  # current_next_indicator
        nbin.add_int(0, 8)  # section number
        nbin.add_int(0, 8)  # last section number
        nbin.add_int(7, 3)  # res
        nbin.add_int(pcr_pid, 13)
        nbin.add_int(15, 4)  # res
        nbin.add_int(n_proginfolen, 12)
        nbin.add_bites(n_info_bites)
        nbin.add_bites(n_streams)
        a_crc = crc32(nbin.bites)
        nbin.add_int(a_crc, 32)
        n_payload = nbin.bites
        pad = 187 - (len(n_payload) + 4)
        pointer_field = b"\x00"
        if pad > 0:
            n_payload = pointer_field + n_payload + (b"\xff" * pad)
        self.pmt_payload = n_payload

    def _parse_pmt(self, pay, pid):
        """
        parse program maps for streams
        """
        pay = self._chk_partial(pay, pid, self._PMT_TID)
        if not pay:
            return False
        seclen = self._parse_length(pay[1], pay[2])
        # to_stderr("seclen", seclen)
        n_seclen = seclen + 6
        if self._section_incomplete(pay, pid, seclen):
            return False
        program_number = self._parse_program(pay[3], pay[4])
        # to_stderr("program_number", program_number)
        pcr_pid = self._parse_pid(pay[8], pay[9])
        # to_stderr("pcr_pid", pcr_pid)
        self.pids.pcr.add(pcr_pid)
        self.maps.pid_prgm[pcr_pid] = program_number
        proginfolen = self._parse_length(pay[10], pay[11])
        # to_stderr("pif", proginfolen)
        idx = 12
        n_proginfolen = proginfolen + len(self.CUEI_DESCRIPTOR)
        end = idx + proginfolen
        info_bites = pay[idx:end]
        n_info_bites = info_bites + self.CUEI_DESCRIPTOR
        while idx < end:
            d_type = pay[idx]
            idx += 1
            d_len = pay[idx]
            idx += 1
            d_bytes = pay[idx - 2 : idx + d_len]
            idx += d_len
            to_stderr(f"type: {d_type} len: { d_len} bytes: {d_bytes}")
        si_len = seclen - 9
        si_len -= proginfolen
        streams = self._parse_program_streams(si_len, pay, idx, program_number)
        n_streams = self._pmt_scte35_stream() + streams
        self._regen_pmt(n_seclen, pcr_pid, n_proginfolen, n_info_bites, n_streams)
        return True

    def _parse_program_streams(self, si_len, pay, idx, program_number):
        """
        parse the elementary streams
        from a program
        """
        # 5 bytes for stream_type info
        chunk_size = 5
        end_idx = (idx + si_len) - 4
        start = idx
        while idx < end_idx:
            stream_type, pid, ei_len = self._parse_stream_type(pay, idx)
            # to_stderr("Stream: type:", stream_type,"PID:", pid, "EI Len:",ei_len)
            idx += chunk_size
            idx += ei_len
            self.maps.pid_prgm[pid] = program_number
            self._chk_pid_stream_type(pid, stream_type)
        # crc = pay[idx : idx + 4]
        streams = pay[start:end_idx]
        return streams

    def _parse_stream_type(self, pay, idx):
        """
        extract stream pid and type
        """
        # npay = pay
        stream_type = pay[idx]
        el_pid = self._parse_pid(pay[idx + 1], pay[idx + 2])
        ei_len = self._parse_length(pay[idx + 3], pay[idx + 4])
        return stream_type, el_pid, ei_len

    def _chk_pid_stream_type(self, pid, stream_type):
        """
        if stream_type is 0x06 or 0x86
        add it to self._scte35_pids.
        """
        if stream_type in ["0x6", "0x86"]:
            self.pids.scte35.add(pid)


if __name__ == "__main__":
    sk = SuperKabuki()
    sk.encode()
