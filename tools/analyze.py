#!/usr/bin/env python3
"""Measure WAV renders without listening: levels, clipping, stereo, spectrum.

    tools/analyze.py FILE.wav [...] [--plot DIR] [--start S --length S]

Prints integrated loudness (LUFS, ITU-R BS.1770-4 with its gates), true
peak (dBTP, 4x oversampled), peak and RMS (dBFS), clipped samples, crest factor, L/R correlation
and side/mid ratio (stereo width), spectral centroid and the share of energy
above 16 kHz (a crude aliasing sign); with --plot, a PNG of the waveform,
spectrogram and long-term spectrum per file. Needs numpy, scipy, matplotlib."""
import argparse, sys, wave, struct
from pathlib import Path
import numpy as np


def read(path):
    with wave.open(str(path), "rb") as w:
        channels, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(frames)
    if width == 3:
        data = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        ints = (data[:, 0].astype(np.int32) | (data[:, 1].astype(np.int32) << 8) | (data[:, 2].astype(np.int32) << 16))
        ints = np.where(ints >= 1 << 23, ints - (1 << 24), ints)
        samples = ints.astype(np.float64) / 8388608.0
    elif width == 2:
        samples = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    else:
        raise SystemExit(f"{path}: {width * 8}-bit not read")
    return samples.reshape(-1, channels), rate


def db(x):
    return 20.0 * np.log10(max(x, 1e-12))


def loudness(x, rate):
    """Integrated loudness (LUFS): K-weighting, 400 ms blocks overlapping
    75%, the absolute gate at -70 LUFS and the relative one 10 LU down."""
    from scipy.signal import bilinear, lfilter
    # The K-weighting at any rate, from its analog prototype (Mansbridge et al.).
    import math
    f0, gain, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = math.tan(math.pi * f0 / rate)
    vh = 10 ** (gain / 20.0)
    vb = vh ** 0.4996667741545416
    a0 = 1.0 + k / q + k * k
    b1 = [(vh + vb * k / q + k * k) / a0, 2.0 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    a1 = [1.0, 2.0 * (k * k - 1.0) / a0, (1.0 - k / q + k * k) / a0]
    f1, q1 = 38.13547087602444, 0.5003270373238773
    k = math.tan(math.pi * f1 / rate)
    a2 = [1.0, 2.0 * (k * k - 1.0) / (1.0 + k / q1 + k * k), (1.0 - k / q1 + k * k) / (1.0 + k / q1 + k * k)]
    b2 = [1.0, -2.0, 1.0]
    weighted = lfilter(b2, a2, lfilter(b1, a1, x, axis=0), axis=0)
    block, hop = int(0.4 * rate), int(0.1 * rate)
    powers = []
    for start in range(0, weighted.shape[0] - block + 1, hop):
        powers.append(np.sum(np.mean(weighted[start:start + block] ** 2, axis=0)))
    powers = np.array(powers)
    if len(powers) == 0:
        return -70.0
    louder = powers[-0.691 + 10 * np.log10(powers + 1e-30) > -70.0]
    if len(louder) == 0:
        return -70.0
    relative = -0.691 + 10 * np.log10(np.mean(louder)) - 10.0
    gated = louder[-0.691 + 10 * np.log10(louder) > relative]
    return -0.691 + 10 * np.log10(np.mean(gated))


def true_peak(x):
    from scipy.signal import resample_poly
    return np.max(np.abs(resample_poly(x, 4, 1, axis=0)))


def measure(path, start, length):
    x, rate = read(path)
    a = int(start * rate)
    b = x.shape[0] if length <= 0 else min(x.shape[0], a + int(length * rate))
    x = x[a:b]
    left, right = x[:, 0], x[:, -1]
    mono = (left + right) * 0.5
    side = (left - right) * 0.5
    peak = np.max(np.abs(x))
    rms = np.sqrt(np.mean(x ** 2))
    clipped = np.mean(np.abs(x) >= 0.999)
    corr = np.corrcoef(left, right)[0, 1] if np.std(left) > 0 and np.std(right) > 0 else 1.0
    width = np.sqrt(np.mean(side ** 2)) / max(np.sqrt(np.mean(mono ** 2)), 1e-12)
    spectrum = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2
    freqs = np.fft.rfftfreq(len(mono), 1.0 / rate)
    total = np.sum(spectrum) + 1e-30
    centroid = np.sum(freqs * spectrum) / total
    high = np.sum(spectrum[freqs > 16000]) / total
    lufs = loudness(x, rate)
    print(f"{Path(path).name}: {x.shape[0] / rate:.2f} s  {lufs:6.1f} LUFS  true peak {db(true_peak(x)):5.1f} dBTP  peak {db(peak):6.1f} dBFS  RMS {db(rms):6.1f} dBFS  crest {db(peak) - db(rms):4.1f} dB  "
          f"clipped {clipped * 100:.3f}%  L/R corr {corr:+.2f}  side/mid {width:.2f}  centroid {centroid:6.0f} Hz  >16k {high * 100:.3f}%")
    return x, rate


def plot(path, x, rate, directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal
    mono = x.mean(axis=1)
    fig, axes = plt.subplots(3, 1, figsize=(12, 9))
    t = np.arange(len(mono)) / rate
    axes[0].plot(t, x[:, 0], linewidth=0.4, label="L")
    axes[0].plot(t, x[:, -1], linewidth=0.4, alpha=0.6, label="R")
    axes[0].set_xlim(0, t[-1])
    axes[0].set_title(Path(path).name + " — waveform")
    axes[0].legend(loc="upper right")
    f, tt, s = signal.spectrogram(mono, rate, nperseg=2048, noverlap=1536)
    axes[1].pcolormesh(tt, f, 10 * np.log10(s + 1e-14), shading="auto", vmin=-140, vmax=-20)
    axes[1].set_yscale("symlog", linthresh=200)
    axes[1].set_ylim(20, rate / 2)
    axes[1].set_title("spectrogram (dB)")
    f2, p2 = signal.welch(mono, rate, nperseg=8192)
    axes[2].semilogx(f2[1:], 10 * np.log10(p2[1:] + 1e-20))
    axes[2].set_xlim(20, rate / 2)
    axes[2].set_title("long-term spectrum (dB)")
    axes[2].grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    out = Path(directory) / (Path(path).stem + ".png")
    fig.savefig(out, dpi=80)
    plt.close(fig)
    print(f"  plot: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--plot", default="")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--length", type=float, default=0.0)
    parser.add_argument("--f0", type=float, default=0.0, help="a fundamental: report energy off its harmonics (aliasing)")
    arguments = parser.parse_args()
    for path in arguments.files:
        x, rate = measure(path, arguments.start, arguments.length)
        if arguments.f0 > 0:
            mono = x.mean(axis=1)
            mono = mono[len(mono) // 4: len(mono) // 4 + rate]
            spectrum = np.abs(np.fft.rfft(mono * np.blackman(len(mono)))) ** 2
            freqs = np.fft.rfftfreq(len(mono), 1.0 / rate)
            harmonic = np.zeros_like(spectrum, dtype=bool)
            k = 1
            while k * arguments.f0 < rate / 2:
                harmonic |= np.abs(freqs - k * arguments.f0) < 6.0
                k += 1
            band = (freqs < 20000) & (freqs > 20)
            alias = np.sum(spectrum[band & ~harmonic]) / max(np.sum(spectrum[band & harmonic]), 1e-30)
            print(f"  alias floor below 20 kHz: {10 * np.log10(alias + 1e-30):.1f} dB relative to the harmonics")
        if arguments.plot:
            Path(arguments.plot).mkdir(parents=True, exist_ok=True)
            plot(path, x, rate, arguments.plot)
