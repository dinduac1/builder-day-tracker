"""Generate the app's notification sounds into app/src/main/res/raw (16-bit mono WAV).

Each block gets its own short motif so you can tell what's starting without looking at the phone.
Re-run after editing a motif, then bump Notifs.CH_VERSION so Android picks up the new sounds.
"""
import math, os, struct, wave, random

RATE = 44100
OUT = os.path.join(os.path.dirname(__file__), "app", "src", "main", "res", "raw")
NOTE = {n: 440 * 2 ** ((i - 9) / 12 + o - 4)
        for o in range(2, 8) for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])
        for n in [f"{n}{o}"]}

def tone(freq, dur, kind="bell", vol=1.0):
    n = int(RATE * dur); out = []
    for i in range(n):
        t = i / RATE
        if kind == "bell":      # struck bell: fundamental + inharmonic partials, exponential decay
            env = math.exp(-t * 4.0)
            s = math.sin(2*math.pi*freq*t) + 0.45*math.sin(2*math.pi*freq*2.76*t)*math.exp(-t*6) + 0.25*math.sin(2*math.pi*freq*5.4*t)*math.exp(-t*9)
        elif kind == "marimba":  # wooden mallet: fast decay, octave partial
            env = math.exp(-t * 9.0)
            s = math.sin(2*math.pi*freq*t) + 0.35*math.sin(2*math.pi*freq*4*t)*math.exp(-t*20)
        elif kind == "pluck":    # bright pluck
            env = math.exp(-t * 7.0)
            s = sum(math.sin(2*math.pi*freq*k*t) / k for k in range(1, 6))
        elif kind == "pad":      # soft swell
            env = math.sin(math.pi * min(t / dur, 1.0)) ** 2
            s = math.sin(2*math.pi*freq*t) + 0.3*math.sin(2*math.pi*freq*2*t) + 0.15*math.sin(2*math.pi*freq*0.5*t)
        elif kind == "square":   # punchy, energetic
            env = math.exp(-t * 5.0)
            s = (1 if math.sin(2*math.pi*freq*t) > 0 else -1) * 0.55 + 0.45*math.sin(2*math.pi*freq*t)
        elif kind == "beep":     # clean electronic beep
            env = 1.0 if t < dur - 0.01 else max(0.0, (dur - t) / 0.01)
            s = math.sin(2*math.pi*freq*t)
        elif kind == "knock":    # low thump with noise click
            env = math.exp(-t * 25.0)
            s = math.sin(2*math.pi*freq*t*(1 + math.exp(-t*30))) + (random.random()*2-1)*math.exp(-t*80)*0.6
        else:
            raise ValueError(kind)
        attack = min(1.0, t / 0.004)
        out.append(s * env * attack * vol)
    return out

def seq(*parts, gap=0.0):
    """parts: (note_or_freq, dur, kind[, vol]) or ('rest', dur)"""
    out = []
    for p in parts:
        if p[0] == "rest":
            out += [0.0] * int(RATE * p[1]); continue
        f = NOTE[p[0]] if isinstance(p[0], str) else p[0]
        out += tone(f, p[1], p[2], p[3] if len(p) > 3 else 1.0)
        out += [0.0] * int(RATE * gap)
    return out

def chord(notes, dur, kind, vol=1.0):
    layers = [tone(NOTE[n], dur, kind, vol) for n in notes]
    return [sum(x) / len(layers) for x in zip(*layers)]

def save(name, samples, peak=0.85):
    m = max(1e-9, max(abs(x) for x in samples))
    tail = int(RATE * 0.02)
    for i in range(tail):                         # fade the last 20 ms to avoid a click
        samples[-1 - i] *= i / tail
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x / m * peak)) * 32767)) for x in samples))

os.makedirs(OUT, exist_ok=True)
random.seed(7)

# Wake alarm: insistent rising pattern, loops seamlessly (played on the alarm stream)
save("wake_alarm", seq(("C6", .14, "beep"), ("rest", .06), ("E6", .14, "beep"), ("rest", .06), ("G6", .14, "beep"), ("rest", .06),
                       ("C7", .22, "beep"), ("rest", .45),
                       ("C6", .14, "beep"), ("rest", .06), ("E6", .14, "beep"), ("rest", .06), ("G6", .14, "beep"), ("rest", .06),
                       ("C7", .22, "beep"), ("rest", .70)), peak=0.95)
save("s_train",   seq(("A3", .12, "square"), ("rest", .04), ("A3", .12, "square"), ("rest", .04), ("E4", .35, "square")))           # punchy, energetic
save("s_study",   seq(("E6", 1.1, "bell", .9)))                                                                                    # single clear bell
save("s_build",   seq(("C5", .16, "marimba"), ("E5", .16, "marimba"), ("G5", .16, "marimba"), ("C6", .5, "marimba")))            # rising marimba: go time
save("s_break",   seq(("G5", .35, "pluck"), ("E5", .6, "pluck")))                                                                  # relaxed falling pair
save("s_publish", seq(("D5", .1, "pluck"), ("F#5", .1, "pluck"), ("A5", .1, "pluck"), ("D6", .1, "pluck"), ("F#6", .5, "pluck")))  # bright arpeggio: ship it
save("s_connect", seq(("B5", .12, "bell"), ("rest", .05), ("E6", .55, "bell")))                                                  # message ping
save("s_lunch",   seq(("C5", .45, "bell"), ("E5", .8, "bell")))                                                                    # warm two-tone chime
save("s_exec",    seq((110, .18, "knock"), ("rest", .05), (110, .18, "knock"), ("G4", .5, "marimba")))                           # knock-knock, back to work
save("s_drills",  seq(("A5", .09, "beep", .8), ("rest", .06), ("A5", .09, "beep", .8), ("rest", .06), ("A5", .09, "beep", .8), ("rest", .06), ("D6", .3, "beep", .8)))  # practice drill
save("s_life",    chord(["C4", "E4", "G4", "B4"], 1.4, "pad"))                                                                    # warm chord
save("s_review",  seq(("G5", .5, "bell"), ("E5", .5, "bell"), ("C5", 1.0, "bell")))                                              # descending bells: close the day
save("s_wind",    chord(["A3", "C4", "E4"], 1.8, "pad"))                                                                          # soft low swell
save("s_sleep",   chord(["F3", "A3", "C4"], 2.2, "pad"))                                                                          # softest, lowest
save("s_warn",    seq(("E6", .07, "beep", .8), ("rest", .07), ("E6", .07, "beep", .8), ("rest", .18), ("E6", .07, "beep", .8), ("rest", .07), ("E6", .07, "beep", .8)))  # tick-tick: time's nearly up
print("sounds:", sorted(os.listdir(OUT)))
