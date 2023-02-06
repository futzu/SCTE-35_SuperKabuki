"""
Super Kabuki - SCTE-35 Packet injection

"""

import sys
from collections import deque
from operator import itemgetter
from threefive import Stream, Cue, SpliceNull, TimeSignal
from threefive.stream import ProgramInfo
from threefive.crc import crc32
from bitn import NBin
from functools import partial
from new_reader import reader
from iframes import IFramer


class SuperKabuki(Stream):
    """
    Super Kabuki - SCTE-35 Packet injection

    """

    CUEI_DESCRIPTOR = b"\x05\x04CUEI"

    def __init__(self, tsdata):
        self.outfile = "outfile.ts"
        if isinstance(tsdata, str):
            self.outfile = f'superkabuki-{tsdata.rsplit("/",1)[1]}'
        super().__init__(tsdata)
        self.pmt_payload = None
        self.scte35_pid = 0x86
        self.scte35_cc = 0
        self.iframer = IFramer()
        self.sidecar = deque()
        self.sidecar_file = "sidecar.txt"

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

    def encode(self, func=None):
        """
        Stream.decode_proxy writes all ts packets are written to stdout
        for piping into another program like mplayer.
        SCTE-35 cues are printed to stderr.
        """
        if self._find_start():
            with open(self.outfile, "wb") as out_file:
                for pkt in iter(partial(self._tsdata.read, self._PACKET_SIZE), b""):
                    pid = self._parse_info(pkt)
                    if self._pusi_flag(pkt):
                        self._parse_pts(pkt, pid)
                    self._program_stream_map(pkt, pid)
                    pts = self.iframer.parse(pkt)  # insert on iframe
                    if pts:
                        self.load_sidecar(pts)
                        scte35_pkt = self.chk_sidecar_cues(pts)
                        # out_file.write(self._gen_time_signals(pts))
                        if scte35_pkt:
                            print("yes")
                            out_file.write(scte35_pkt)
                    if pid in self.pids.pmt:
                        if self.pmt_payload:
                            pkt = pkt[:4] + self.pmt_payload
                    out_file.write(pkt)

    def _gen_time_signals(self, pts):
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

        with reader(self.sidecar_file) as sidefile:
            for line in sidefile:
                print(line)
                line = line.decode().strip().split("#", 1)[0]
                if len(line):
                    insert_pts, cue = line.split(",", 1)
                    insert_pts = float(insert_pts)
                    if insert_pts == 0.0 and self.args.live:
                        insert_pts = self.next_start
                    if insert_pts >= pts:
                        if [insert_pts, cue] not in self.sidecar:
                            self.sidecar.append([insert_pts, cue])
                            self.sidecar = deque(
                                sorted(self.sidecar, key=itemgetter(0))
                            )

    # with open(self.sidecar_file, "w") as scf:
    #    scf.close()

    def chk_sidecar_cues(self, pts):
        """
        _chk_sidecar_cues checks the insert pts time
        for the next sidecar cue and inserts the cue if needed.
        """
        if self.sidecar:
            if (pts - 10) <= float(self.sidecar[0][0]) <= pts:
                insert_pts, cue_mesg = self.sidecar.popleft()
                return self.gen_scte35(insert_pts, cue_mesg)
        return False

    def gen_scte35(self, pts, cue_mesg):
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
        print(nbin.bites)
        return nbin.bites

    def _program_stream_map(self, pkt, pid):
        pay = self._parse_payload(pkt)
        if pay.startswith(b"\x00\x00\x01\xbc"):
            print("psm")
            print(pid, pay)

    def _program_map_table(self, pay, pid):
        """
        parse program maps for streams
        """
        pay = self._chk_partial(pay, pid, self._PMT_TID)
        if not pay:
            return False
        seclen = self._parse_length(pay[1], pay[2])
        print("seclen", seclen)
        n_seclen = seclen + 11
        if not self._section_done(pay, pid, seclen):
            return False
        program_number = self._parse_program(pay[3], pay[4])
        print("program_number", program_number, pay[3], pay[4])
        pcr_pid = self._parse_pid(pay[8], pay[9])
        print("pcr_pid", pcr_pid)
        self.pids.pcr.add(pcr_pid)
        self.maps.pid_prgm[pcr_pid] = program_number
        proginfolen = self._parse_length(pay[10], pay[11])
        print("pif", proginfolen)
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
            print(f"type: {d_type} len: { d_len} bytes: {d_bytes}")
        si_len = seclen - 9
        si_len -= proginfolen
        streams = self._parse_program_streams(si_len, pay, idx, program_number)
        n_streams = self._pmt_scte35_stream() + streams
        nbin = NBin()
        #  nbin.add_bites(pay)
        # nbin.add_int(0,8)  # pointer field
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
        print(nbin.bites)
        n_payload = nbin.bites
        pad = 187 - (len(n_payload) + 4)
        pointer_field = b"\x00"
        if pad > 0:
            n_payload = pointer_field + n_payload + (b"\xff" * pad)
        self.pmt_payload = n_payload
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
        while idx < end_idx - 5:
            stream_type, pid, ei_len = self._parse_stream_type(pay, idx)
            print("Stream: ", stream_type, pid, ei_len)
            idx += chunk_size
            idx += ei_len
            self.maps.pid_prgm[pid] = program_number
            self._chk_pid_stream_type(pid, stream_type)
        crc = pay[idx : idx + 4]
        streams = pay[start:end_idx]

        return streams

    def _parse_stream_type(self, pay, idx):
        """
        extract stream pid and type
        """
        npay = pay
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

    sk = SuperKabuki(sys.argv[1])
    sk.encode()
